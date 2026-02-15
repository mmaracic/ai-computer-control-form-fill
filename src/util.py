import os
from typing import Any

import yaml


def load_config_from_yml(file_path: str) -> dict[str, Any]:
    """Load configuration settings from a YAML file.

    Args:
        file_path: Path to the YAML configuration file

    Returns:
        Dictionary with configuration settings

    Raises:
        FileNotFoundError: If the configuration file does not exist
        yaml.YAMLError: If there is an error parsing the YAML file

    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(file_path, "r") as f:
        try:
            config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {str(e)}")
