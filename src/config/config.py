from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import BaseModel

from src.config.base_config import BaseConfig


class LLMConfig(BaseModel):
    """Configuration for the language model."""

    model: str
    api_key: str


class PostgresConfig(BaseModel):
    """Configuration for PostgreSQL connection."""

    conninfo: str
    db_schema: str
    table: str


class Config(BaseConfig):
    """Configuration for the application."""

    host: str
    port: int
    data_directory: Path
    llm: LLMConfig
    postgres: PostgresConfig
