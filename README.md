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
### Structural and agentic features:
- Using project Copilot instructions that augment the global instructions and help the model understand the context of the application and its purpose.
- FastAPI application with startup and shutdown events for resource management.
- Application configuration through yaml file or .env file or env variables using Pydantic settings management
- LangFuse docker compose file. openinference-instrumentation-openai-agents and langfuse library
 are used to integrate agents with LangFuse
- Playwright for browser automation to perform form filling tasks
- Custom agent implementation using OpenAI Agent API and LiteLLM for model inference (through openai optional dependency of openai-agents library)
- Langfuse integration enabled (without sessions) on the agent implementation.
- Session handling and storage into database, default is Postgres using json data type and psycopg3 driver.
- Dependencies are fixated to specific versions to ensure stability and reproducibility.

### Data extraction features:
- Data extraction from documents using a DocumentDataExtractor class and storing the extracted data in the data repository.
- DocumentDataExtractor uses Docling library to extrct data from documents. It uses EasyOCR and PyTorch. PyTorch and Torchvision were declared as explicit dependencies in pyproject.toml to ensure that CPU version is installed using tool.uv.sources and avoid Nvidia GPU dependencies.
- Tiktoken library is used to estimate token count in extrcacted data using a specified OpenAI tokenizer model. This is used to ensure that the documents would not be too long for arbitraty models (although the actual token count may differ from the estimation).