# AI Computer Control Form Fill - Copilot Instructions

## Project Overview
Project implements AI-powered computer control for automated form filling.

Keep the file updated with the information from conversation with uaer and the codebase. This file serves as a reference for developers working on the project to understand the technology stack, code style, architecture, testing strategies, security considerations, and documentation guidelines.

## Project components
- Chat API to communicate with the AI and receive instructions for form filling and define input documents with data to fill in the forms
- Input documents can be only .docx files that are present in data subfolder of the project
- AI agent that processes user input and input documents and determines which form fields to fill and how
- FastAPI backend that receives instructions from the AI agent and performs the actual form filling using browser automation (e.g., Selenium, Playwright)

## Technology Stack
- Python 3.12 for core logic and AI integration present on machine
- UV as the build tool for managing dependencies and packaging present on machine
- FastAPI for creating a RESTful API to expose form filling functionality present on machine
- OpenAI Agent API to implement AI agents
- LiteLLM for lightweight provider independent AI model inference
- Pydantic for data validation and settings management
- Pyyaml to read configuration from YAML files
- Pytest for testing the application

## Code Style
- Follow Python best practices and PEP 8 conventions
- Use descriptive variable and function names that reflect the form filling domain
- Keep functions focused and single-purpose

## Architecture
- Separate UI automation logic from AI decision-making logic
- Use dependency injection for better testability
- Implement proper error handling for web interactions and form field detection

## Testing
- Write tests for form detection and filling logic
- Mock external dependencies (browsers, AI services)
- Include edge cases for different form field types

## Security
- Never hard-code credentials or API keys
- Sanitize user input before form submission
- Handle sensitive form data (passwords, payment info) with extra care

## Documentation
- Document assumptions about form structure and browser compatibility
- Include examples of supported form types
- Explain AI model selection and configuration options
