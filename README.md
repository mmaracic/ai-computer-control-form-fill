# README
Project implements AI-powered computer control for automated form filling.

## Running the Application
1. Install dependencies using UV:
   ```bash
   uv sync
   ```
2. Install Playwright browsers (first time only):
   ```bash
   uv run playwright install chromium
   ```
3. Start the FastAPI server:
   ```bash
   uv run -m src.main
   ```

### Using Computer Control with the Agent
Send instructions to the agent via the `POST /chat` endpoint. The agent will autonomously navigate to pages, discover form fields, and fill them using the data extracted from provided documents.

Example is located in bruno subfolder.

## About Computer Control
The application controls a real browser (Chromium via Playwright) on behalf of the user. The AI agent receives natural language instructions, reasons about what needs to be done, and calls browser tools in a loop until the task is complete.

The agent follows a perceive-act loop:
1. **navigate** — opens the target URL in a Playwright-controlled browser
2. **get_form_fields** — inspects the page and returns all available fields with their labels, types, and current values
3. **fill_field** / **select_option** — fills text inputs and selects dropdown options by label, placeholder, name, or id
4. **click_element** — clicks buttons (e.g. submit), checkboxes, or radio buttons

The same `conversation_id` keeps the browser page open between messages, so you can have a multi-turn conversation to guide the agent, correct mistakes, or fill multi-step forms.



### Browser Tools
| Tool | Description |
|---|---|
| `navigate(url)` | Opens a URL; waits for DOM content to load |
| `get_form_fields()` | Returns a JSON list of all fillable fields on the current page (label, type, options, current value) |
| `fill_field(identifier, value)` | Fills a text, email, number, date, or textarea field located by label, placeholder, name, or id |
| `select_option(identifier, value)` | Selects a dropdown option by visible text or value attribute |
| `click_element(identifier)` | Clicks a button, link, checkbox, or radio button located by visible text, aria-label, or id |

### Element Location Strategy
All tools resolve elements using Playwright's accessibility-first locators — `get_by_label`, `get_by_placeholder`, `get_by_role` — falling back to `[name=...]` and `#id` selectors. This makes the agent resilient to minor HTML structure changes as long as accessible attributes are present.

### Browser Lifecycle
A single persistent Playwright Chromium instance is started when the FastAPI application starts and shut down on application exit. The page survives across multiple chat turns so the agent can navigate multi-step forms without losing state.

### Configuration
Configuration for computer control Playwright browser is under the `browser` section in `config.yml`. You can set `headless: false` to see the browser in action during development. When headless mode is enabled, the browser runs in the background without a UI, which is suitable for production deployments.

## Application features
### Structural and agentic features:
- Using project Copilot instructions that augment the global instructions and help the model understand the context of the application and its purpose.
- FastAPI application with startup and shutdown events for resource management.
- Application configuration through yaml file or .env file or env variables using Pydantic settings management
- LangFuse docker compose file. openinference-instrumentation-openai-agents and langfuse library
 are used to integrate agents with LangFuse
- Custom agent implementation using OpenAI Agent API and LiteLLM for model inference (through openai optional dependency of openai-agents library)
- Langfuse integration enabled (without sessions) on the agent implementation.
- Session handling and storage into database, default is Postgres using json data type and psycopg3 driver.
- Dependencies are fixated to specific versions to ensure stability and reproducibility.

### Data extraction features:
- Data extraction from documents using a DocumentDataExtractor class and storing the extracted data in the data repository.
- DocumentDataExtractor uses Docling library to extrct data from documents. It uses EasyOCR and PyTorch. PyTorch and Torchvision were declared as explicit dependencies in pyproject.toml to ensure that CPU version is installed using tool.uv.sources and avoid Nvidia GPU dependencies.
- Tiktoken library is used to estimate token count in extrcacted data using a specified OpenAI tokenizer model. This is used to ensure that the documents would not be too long for arbitraty models (although the actual token count may differ from the estimation).

### Computer control features:
- Playwright for browser automation to perform form filling tasks
- The implementation doesnt rely on image recognition; it uses Playwright's accessibility locators to find and interact with form fields in the DOM based on their labels, placeholders, names, or ids.

## Issues
When the application fails to start due to missing Playwright dependency (although playwright was installeld as per running instructions):
```
ms-playwright/chromium-1208/chrome-linux64/chrome: error while loading shared libraries: libnspr4.so: cannot open shared object file: No such file or directory
```
Install dependencies using Playwright instructions (using npx):
https://playwright.dev/docs/browsers#install-system-dependencies
```
npx playwright install-deps chromium
```