from pathlib import Path

from pydantic_settings import BaseSettings

from src.config.base_config import BaseConfig


class Config(BaseConfig):
    """Configuration for the application."""

    host: str
    port: int
    data_directory: Path
