"""Tests for main application startup and configuration."""

import logging
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import yaml
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def test_config_in_cwd() -> Generator[None, None, None]:
    """Create test config.yml and temporarily rename .env to prevent env overrides."""
    test_config = {"host": "127.0.0.1", "port": 9000, "data_directory": "./test_data"}

    config_exists = os.path.exists("config.yml")
    env_exists = os.path.exists(".env")

    if config_exists:
        os.rename("config.yml", "config.yml.backup")
    if env_exists:
        os.rename(".env", ".env.backup")

    with open("config.yml", "w") as f:
        yaml.dump(test_config, f)

    yield

    os.unlink("config.yml")
    if config_exists:
        os.rename("config.yml.backup", "config.yml")
    if env_exists:
        os.rename(".env.backup", ".env")


class TestApplicationStructure:
    """Tests for FastAPI app structure (no config loading required)."""

    def test_app_instance_created(self) -> None:
        """Test that the FastAPI app instance is created successfully."""
        assert app is not None
        assert hasattr(app, "router")
        assert hasattr(app, "state")

    def test_app_metadata(self) -> None:
        """Test that the app has correct metadata configured."""
        assert app.title == "Email Parser & Aggregator"
        assert app.description == "API for fetching and processing emails"
        assert app.version == "0.1.0"

    def test_app_has_lifespan(self) -> None:
        """Test that the app has lifespan context manager configured."""
        assert app.router.lifespan_context is not None


class TestApplicationStartupWithTestConfig:
    """Tests for app startup using test configuration (isolated from production)."""

    def test_lifespan_startup_and_shutdown_logs(
        self, test_config_in_cwd: None, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test lifespan logs startup and shutdown messages with test config."""
        with caplog.at_level(logging.INFO):
            with TestClient(app) as client:
                assert (
                    "Starting up AI Computer Control Form Fill service..."
                    in caplog.text
                )
                assert client.app == app

        assert "Shutting down AI Computer Control Form Fill service..." in caplog.text

    def test_app_accepts_requests_with_test_config(
        self, test_config_in_cwd: None
    ) -> None:
        """Test app accepts HTTP requests with test config."""
        with TestClient(app) as client:
            response = client.get("/docs")
            assert response.status_code == 200

    def test_openapi_schema_generated_with_test_config(
        self, test_config_in_cwd: None
    ) -> None:
        """Test OpenAPI schema generation with test config."""
        with TestClient(app) as client:
            response = client.get("/openapi.json")
            assert response.status_code == 200
            openapi_schema = response.json()
            assert openapi_schema["info"]["title"] == "Email Parser & Aggregator"
            assert openapi_schema["info"]["version"] == "0.1.0"

    def test_config_loaded_into_app_state(self, test_config_in_cwd: None) -> None:
        """Test configuration is loaded and stored in app.state with test config."""
        with TestClient(app) as client:
            assert hasattr(client.app.state, "config")
            assert client.app.state.config is not None

    def test_test_config_values_loaded_correctly(
        self, test_config_in_cwd: None
    ) -> None:
        """Test configuration values match test config.yml values."""
        with TestClient(app) as client:
            config = client.app.state.config
            assert hasattr(config, "host")
            assert hasattr(config, "port")
            assert hasattr(config, "data_directory")
            assert isinstance(config.host, str)
            assert isinstance(config.port, int)
            assert isinstance(config.data_directory, Path)
            assert config.host == "127.0.0.1"
            assert config.port == 9000
            assert str(config.data_directory) == "test_data"

    def test_config_logged_during_startup_with_test_config(
        self, test_config_in_cwd: None, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test configuration is logged during startup with test config."""
        with caplog.at_level(logging.INFO):
            with TestClient(app):
                assert "Configuration loaded:" in caplog.text


class TestApplicationStartupWithProductionConfig:
    """Tests using production config.yml (requires config.yml to exist)."""

    def test_production_config_loads_successfully(self) -> None:
        """Test app starts successfully with production config.yml."""
        with TestClient(app) as client:
            assert hasattr(client.app.state, "config")
            config = client.app.state.config
            assert config is not None
            assert hasattr(config, "host")
            assert hasattr(config, "port")
            assert hasattr(config, "data_directory")

    def test_production_config_has_valid_types(self) -> None:
        """Test production config has correct types for all fields."""
        with TestClient(app) as client:
            config = client.app.state.config
            assert isinstance(config.host, str)
            assert isinstance(config.port, int)
            assert isinstance(config.data_directory, Path)

    def test_production_app_startup_without_errors(self) -> None:
        """Test app starts without exceptions using production config.yml."""
        with TestClient(app) as client:
            assert client.app == app
            response = client.get("/openapi.json")
            assert response.status_code == 200
