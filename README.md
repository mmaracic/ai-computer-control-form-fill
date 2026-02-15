# README
Project implements AI-powered computer control for automated form filling.

## Running the Application
1. Install dependencies using UV:
   ```bash
   uv sync
   ```
2. Start the FastAPI server:
   ```bash
   uv run -m src.main
   ```

## Features
- Using project Copilot instructions that augment the global instructions and help the model understand the context of the application and its purpose.
- FastAPI application with startup and shutdown events for resource management.
- Application configuration through yaml file or .env file or env variables using Pydantic settings management