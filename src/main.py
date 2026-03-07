"""AI Computer Control Form Fill - Main package."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from src.agent import CustomAgent
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
    prompt_description = "prompt"
    default_prompt = """
        You are an agent that should obtain knowledge from the files in the data subfolder
        and then based on that knowledge fill in the form that is currently open in the browser.
        Fill in as much information as possible based on the knowledge you have obtained, but
        do not use any information that is not present in the data files.
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """Lifespan context manager for FastAPI application."""
    logger.info("Starting up AI Computer Control Form Fill service...")
    # Perform any startup tasks here (e.g., initialize resources, warm up models)
    config = load_config()
    logger.info("Configuration loaded: %s", config)
    app.state.config = config
    prompt_repo = PostgresRepository(
        conninfo=config.postgres.conninfo.get_secret_value(),
        schema_name=config.postgres.db_schema,
        table_name=config.data_table_name,
    )
    agent = CustomAgent(
        application="AI Computer Control Form Fill",
        name="FormFillAgent",
        instructions=get_prompt(prompt_repo),
        model=config.llm.model,
        api_key=config.llm.api_key.get_secret_value(),
        session=PostgresSession(
            session_id="default_session",
            conninfo=config.postgres.conninfo.get_secret_value(),
            schema_name=config.postgres.db_schema,
            table_name=config.session_table_name,
        ),
    )
    app.state.agent = agent
    yield
    logger.info("Shutting down AI Computer Control Form Fill service...")
    # Perform any cleanup tasks here (e.g., close resources, save state)


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


@app.post("/chat")
async def chat(request: ChatRequest) -> str:
    """Endpoint to handle chat interactions with the agent."""
    agent: CustomAgent = app.state.agent
    response = await agent.act(
        input=request.input, conversation_id=request.conversation_id
    )
    return response


if __name__ == "__main__":
    config = load_config()
    uvicorn.run(app, host=config.host, port=config.port)
