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
- LangFuse docker compose file. openinference-instrumentation-openai-agents and langfuse library
 are used to integrate agents with LangFuse
- Playwright for browser automation to perform form filling tasks
- Custom agent implementation using OpenAI Agent API and LiteLLM for model inference (through openai optional dependency of openai-agents library)
- Langfuse integration enabled (without sessions) on the agent implementation.
- Session handling and storage into database, default is Postgres using json data type and psycopg3 driver.