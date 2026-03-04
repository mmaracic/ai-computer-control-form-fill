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
from src.postgres_session import PostgresSession
from src.util import load_config_from_yml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config() -> Config:
    """Load configuration settings from YAML file and return a Config instance."""
    config_dict = load_config_from_yml("config.yml")
    return Config(**config_dict)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """Lifespan context manager for FastAPI application."""
    logger.info("Starting up AI Computer Control Form Fill service...")
    # Perform any startup tasks here (e.g., initialize resources, warm up models)
    config = load_config()
    logger.info(f"Configuration loaded: {config}")
    app.state.config = config
    agent = CustomAgent(
        application="AI Computer Control Form Fill",
        name="FormFillAgent",
        instructions="You are an assistant that helps fill out forms based on user input and conversation history.",
        model=config.llm.model,
        api_key=config.llm.api_key,
        session=PostgresSession(
            session_id="default_session",
            conninfo=config.postgres.conninfo,
            schema_name=config.postgres.db_schema,
            table_name=config.postgres.table,
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
