# AI Computer Control Form Fill - Copilot Instructions

## Project Overview
Project implements AI-powered computer control for automated form filling.

Keep the file updated with the information from conversation with uaer and the codebase. This file serves as a reference for developers working on the project to understand the technology stack, code style, architecture, testing strategies, security considerations, and documentation guidelines.

## Project components
- Chat API to communicate with the AI and receive instructions for form filling and define input documents with data to fill in the forms
- Input documents can be only .docx files that are present in data subfolder of the project
- AI agent that processes user input and input documents and determines which form fields to fill and how
- FastAPI backend that receives instructions from the AI agent and performs the actual form filling using browser automation (Playwright)

## Project technology Stack
- Python 3.12 for core logic and AI integration present on machine
- UV as the build tool for managing dependencies and packaging present on machine
- FastAPI for creating a RESTful API to expose form filling functionality present on machine
- OpenAI Agent API to implement AI agents
- LiteLLM for lightweight provider independent AI model inference
- Pydantic for data validation and settings management
- Pyyaml to read configuration from YAML files
- Pytest for testing the application
- LangFuse for monitoring and logging AI interactions and performance
- Playwright for browser automation to perform form filling tasks
- Psycopg3 driver for Postgres database interactions to store session data

## Project agentic features
- Custom agent implementation using OpenAI Agent API and LiteLLM for model inference (through openai optional dependency of openai-agents library)
- Tracing and instrumentation of agent interactions with LangFuse using openinference-instrumentation-openai-agents library
- Session handling and storage into Postgres database using json data type for flexibility in storing different session data structures

## Project code style
- Follow Python best practices and PEP 8 conventions
- Use descriptive variable and function names that reflect the form filling domain
- Keep functions focused and single-purpose

## Project code organisation
- single module uv application
- source files in src subfolder
- tests in tests subfolder
- virtual environment in .venv subfolder
- bruno api tests in bruno subfolder
- docker related files in docker subfolder
- configuration yml file in the module root folder of each module
- packages: subfolders of src folder divide code by functionality, e.g. src/agents for agent code, src/api for FastAPI code, src/utils for utility functions, etc. Functional subfolder can be divided into structural subfolders e.g. services, models, util, config etc. It is also possible that src subfolders are structural on the top level; this is the decision of the developer.

## Project architecture
- Always create wrappers and interfaces around external dependencies (browsers, AI services, databases) to abstract away implementation details and make it easier to swap out dependencies in the future
- Use dependency injection for better testability, decouple components whenever possible.
- Implement proper error handling
- Prefer synchronous code for simplicity unless there is a clear need for asynchronous code (performance considerations, I/O bound operations, parallelism, etc.)
- Design the system to be modular and extensible, allowing for easy addition of new features and components in the future
- Design the system as modular monolith or microservice architecture with event driven communication between components when there is a high level of parallelism in the system and need for scaling.
- Prefer Kafka for event driven communication and as a measure to limit concurrency with partitions.


## Project testing
- Use pytest for unit and integration testing, use pytest-mock for mocking dependencies, pytest-asyncio for testing async code, and pytest-cov for test coverage reporting
- Write unit tests for every function and class.
- Mock external dependencies (browsers, AI services, databases, files) in unit tests
- Include edge cases every function and class
- Integration tests should include testscontainers or harnesses and never include calls to cloud services, browsers or LLM providers

## Project security
- Never hard-code credentials or API keys
- Sanitize user input before form submission using pydantic SecureStr type.
- Handle sensitive form data (passwords, payment info) with extra care

## Project documentation
- Document assumptions about form structure and browser compatibility
- Document structural and architectural decisions both in README.md and in inline code documentation
- Include examples input files
- Explain AI model selection and configuration options
