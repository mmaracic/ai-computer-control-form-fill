"""AI Computer Control Form Fill - Main package."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import tiktoken
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from src.agent import CustomAgent, SessionItem
from src.browser.browser_service import BrowserService
from src.browser.browser_tools import create_browser_tools
from src.browser.handlers.button_field_handler import ButtonFieldHandler
from src.browser.handlers.checkbox_field_handler import CheckboxFieldHandler
from src.browser.handlers.date_field_handler import DateFieldHandler
from src.browser.handlers.email_field_handler import EmailFieldHandler
from src.browser.handlers.number_field_handler import NumberFieldHandler
from src.browser.handlers.password_field_handler import PasswordFieldHandler
from src.browser.handlers.radio_field_handler import RadioFieldHandler
from src.browser.handlers.select_field_handler import SelectFieldHandler
from src.browser.handlers.text_field_handler import TextFieldHandler
from src.browser.handlers.textarea_field_handler import TextareaFieldHandler
from src.config.config import Config
from src.postgres_repository import PostgresRepository
from src.postgres_session import PostgresSession
from src.util import load_config_from_yml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config() -> Config:
    """Load configuration settings from YAML file and return a Config instance."""
    config_dict = load_config_from_yml("config.yml")
    return Config(**config_dict)


def get_prompt(prompt_repo: PostgresRepository) -> str:
    """Retrieve the prompt from the repository or use the default prompt if not found."""
    prompt_description = "prompt"
    default_prompt = """
        You are an agent that has information about one or more persons extracted from CV and similar documents.
        Based on that information, fill in the form that is currently open in the browser.
        Fill in as much information as possible in the form based on the information you have.
        (skills, project data, education, etc.).
        Do not use any information that is not present in the context given to you in the system prompt.
        If you don't have enough information to fill in a field, leave it blank.
    """
    prompt: str = default_prompt
    prompt_list = prompt_repo.read_items_by_description(prompt_description)
    if not prompt_list or len(prompt_list) < 1:
        item = prompt_repo.create_item(
            description=prompt_description,
            data={
                "prompt": default_prompt.strip(),
            },
        )
        prompt = item.data.get("prompt") or default_prompt
    elif len(prompt_list) > 1:
        logger.warning(
            "Multiple items found with description '%s'. Using the first one.",
            prompt_description,
        )
        prompt = prompt_list[0].data.get("prompt") or default_prompt
    else:
        prompt = prompt_list[0].data.get("prompt") or default_prompt
    return prompt.strip()


def store_extracted_data(
    data_repo: PostgresRepository, extracted_data: dict[str, str], token_model: str
) -> None:
    """Store the extracted data in the repository."""
    enc = tiktoken.encoding_for_model(token_model)
    for key, value in extracted_data.items():
        token_count = len(enc.encode(str(value)))
        logger.info(
            "Storing data for key '%s' with token count %d for model '%s'.",
            key,
            token_count,
            token_model,
        )
        item = data_repo.read_items_by_description(key)
        if item and len(item) > 0:
            logger.info("Updating existing item with description '%s'.", key)
            data_repo.update_item(
                item_id=item[0].id,
                description=key,
                data={"text": value, "token_count": token_count},
            )
        else:
            logger.info("Creating new item with description '%s'.", key)
            data_repo.create_item(
                description=key,
                data={"text": value, "token_count": token_count},
            )


def load_extracted_data(data_repo: PostgresRepository) -> dict[str, str]:
    """Load the extracted data from the repository and return it as a dictionary."""
    extracted_data: dict[str, str] = {}
    items = data_repo.read_all_items()
    for item in items:
        extracted_data[item.description] = item.data.get("text", "")
    logger.info(
        "Loaded extracted data for %d items from the repository.", len(extracted_data)
    )
    return extracted_data


def _get_instructions(
    prompt_repo: PostgresRepository,
    extracted_data: dict[str, str],
    use_extracted_data: bool,
) -> str:
    """Get the instructions for the agent from the repository."""
    instructions = get_prompt(prompt_repo)
    if use_extracted_data:
        instructions += "\n\n" + "Personal information:\n" + str(extracted_data)
    return instructions


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """Lifespan context manager for FastAPI application."""
    logger.info("Starting up AI Computer Control Form Fill service...")
    # Perform any startup tasks here (e.g., initialize resources, warm up models)
    config = load_config()
    logger.info("Configuration loaded: %s", config)
    app.state.config = config
    data_repo = PostgresRepository(
        conninfo=config.postgres.conninfo.get_secret_value(),
        schema_name=config.postgres.db_schema,
        table_name=config.data_table_name,
    )
    if config.extract_data:
        from src.document_data_extractor import DocumentDataExtractor

        data_extractor = DocumentDataExtractor(data_folder=config.data_directory)
        extracted_data = data_extractor.extract_data()
        store_extracted_data(data_repo, extracted_data, config.tokenizer_llm_model)
    else:
        extracted_data = load_extracted_data(data_repo)
    prompt_repo = PostgresRepository(
        conninfo=config.postgres.conninfo.get_secret_value(),
        schema_name=config.postgres.db_schema,
        table_name=config.config_table_name,
    )
    browser_service = BrowserService(
        headless=config.browser.headless,
        handlers=[
            TextFieldHandler(),
            EmailFieldHandler(),
            PasswordFieldHandler(),
            NumberFieldHandler(),
            DateFieldHandler(),
            TextareaFieldHandler(),
            SelectFieldHandler(),
            CheckboxFieldHandler(),
            RadioFieldHandler(),
            ButtonFieldHandler(),
        ],
    )
    await browser_service.start()
    tools = create_browser_tools(browser_service)
    agent = CustomAgent(
        application="AI Computer Control Form Fill",
        name="FormFillAgent",
        instructions=_get_instructions(
            prompt_repo, extracted_data, config.use_extracted_data
        ),
        model=config.llm.model,
        api_key=config.llm.api_key.get_secret_value(),
        session_postgres_config=config.postgres,
        session_table_name=config.session_table_name,
        tools=tools,
        max_turns=config.max_turns,
    )
    app.state.agent = agent
    app.state.browser_service = browser_service
    yield
    logger.info("Shutting down AI Computer Control Form Fill service...")
    await browser_service.stop()


app = FastAPI(
    title="AI Computer Control Form Fill",
    description="API for AI-powered form filling based on user input and conversation history.",
    version="0.1.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""

    input: str
    conversation_id: str
    clear_history: bool


@app.post("/chat")
async def chat(request: ChatRequest) -> str:
    """Endpoint to handle chat interactions with the agent."""
    agent: CustomAgent = app.state.agent
    return await agent.act(
        message=request.input,
        conversation_id=request.conversation_id,
        clear_history=request.clear_history,
    )


@app.get("/session")
async def get_session(conversation_id: str) -> list[SessionItem]:
    """Endpoint to handle chat interactions with the agent."""
    agent: CustomAgent = app.state.agent
    return await agent.get_session_data(conversation_id=conversation_id)


class ClickRequest(BaseModel):
    """Request model for the click endpoint."""

    identifier: str


@app.post("/click")
async def click_element(request: ClickRequest) -> None:
    """Endpoint to handle chat interactions with the agent."""
    browser_service: BrowserService = app.state.browser_service
    await browser_service.click_element(identifier=request.identifier)


if __name__ == "__main__":
    config = load_config()
    uvicorn.run(app, host=config.host, port=config.port)
