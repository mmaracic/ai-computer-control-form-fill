from pathlib import Path

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


class BrowserConfig(BaseModel):
    """Configuration for the Playwright browser automation."""

    headless: bool


class Config(BaseConfig):
    """Configuration for the application."""

    host: str
    port: int
    data_directory: Path
    llm: LLMConfig
    tokenizer_llm_model: str
    postgres: PostgresConfig
    browser: BrowserConfig
    session_table_name: str
    config_table_name: str
    data_table_name: str
    use_extracted_data: bool
    extract_data: bool
