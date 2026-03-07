from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import BaseModel, SecretStr

from src.config.base_config import BaseConfig


class LLMConfig(BaseModel):
    """Configuration for the language model."""

    model: str
    api_key: SecretStr


class PostgresConfig(BaseModel):
    """Configuration for PostgreSQL connection."""

    conninfo: SecretStr
    db_schema: str


class Config(BaseConfig):
    """Configuration for the application."""

    host: str
    port: int
    data_directory: Path
    llm: LLMConfig
    postgres: PostgresConfig
    session_table_name: str
    data_table_name: str
