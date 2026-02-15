"""Tests for utility functions in util.py module."""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from src.util import load_config_from_yml


class TestLoadConfigFromYml:
    """Tests for load_config_from_yml function."""

    def test_load_valid_yaml_file(self) -> None:
        """Test loading a valid YAML configuration file."""
        config_data = {"database": {"host": "localhost", "port": 5432}, "debug": True}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            result = load_config_from_yml(temp_file)
            assert result == config_data
            assert result["database"]["host"] == "localhost"
            assert result["database"]["port"] == 5432
            assert result["debug"] is True
        finally:
            os.unlink(temp_file)

    def test_load_empty_yaml_file(self) -> None:
        """Test loading an empty YAML file returns None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            temp_file = f.name

        try:
            result = load_config_from_yml(temp_file)
            assert result is None
        finally:
            os.unlink(temp_file)

    def test_load_nested_yaml_structure(self) -> None:
        """Test loading a YAML file with nested structure."""
        config_data = {
            "app": {
                "name": "test-app",
                "settings": {
                    "timeout": 30,
                    "retries": 3,
                    "features": ["auth", "logging"],
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            result = load_config_from_yml(temp_file)
            assert result == config_data
            assert result["app"]["settings"]["features"] == ["auth", "logging"]
        finally:
            os.unlink(temp_file)

    def test_file_not_found_raises_error(self) -> None:
        """Test that FileNotFoundError is raised when file doesn't exist."""
        non_existent_file = "/path/to/nonexistent/config.yml"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_config_from_yml(non_existent_file)

        assert "Configuration file not found" in str(exc_info.value)
        assert non_existent_file in str(exc_info.value)

    def test_invalid_yaml_raises_error(self) -> None:
        """Test that ValueError is raised for invalid YAML content."""
        invalid_yaml = "key: value\n  invalid indentation:\n\twrong tabs"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(invalid_yaml)
            temp_file = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_config_from_yml(temp_file)

            assert "Error parsing YAML configuration" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_load_yaml_with_different_data_types(self) -> None:
        """Test loading YAML with various data types."""
        test_datetime = datetime(2026, 2, 14, 12, 30, 45)
        config_data = {
            "string_value": "test",
            "integer_value": 42,
            "float_value": 3.14,
            "boolean_value": True,
            "null_value": None,
            "list_value": [1, 2, 3],
            "dict_value": {"nested": "data"},
            "datetime_value": test_datetime,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            result = load_config_from_yml(temp_file)
            assert result == config_data
            assert isinstance(result["string_value"], str)
            assert isinstance(result["integer_value"], int)
            assert isinstance(result["float_value"], float)
            assert isinstance(result["boolean_value"], bool)
            assert result["null_value"] is None
            assert isinstance(result["list_value"], list)
            assert isinstance(result["dict_value"], dict)
            assert isinstance(result["datetime_value"], datetime)
            assert result["datetime_value"] == test_datetime
        finally:
            os.unlink(temp_file)

    def test_load_yaml_file_with_yaml_extension(self) -> None:
        """Test loading a file with .yaml extension."""
        config_data = {"key": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name

        try:
            result = load_config_from_yml(temp_file)
            assert result == config_data
        finally:
            os.unlink(temp_file)
