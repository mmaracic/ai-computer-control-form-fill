"""AI Computer Control Form Fill - Main package."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI

from src.config.config import Config
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
    yield
    logger.info("Shutting down AI Computer Control Form Fill service...")
    # Perform any cleanup tasks here (e.g., close resources, save state)


app = FastAPI(
    title="Email Parser & Aggregator",
    description="API for fetching and processing emails",
    version="0.1.0",
    lifespan=lifespan,
)

if __name__ == "__main__":
    config = load_config()
    uvicorn.run(app, host=config.host, port=config.port)
