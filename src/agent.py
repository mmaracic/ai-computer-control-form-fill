import logging

from agents import Agent, RunConfig, Runner, SessionABC
from agents.extensions.models.litellm_model import LitellmModel
from langfuse import get_client
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor

from src.config.config import PostgresConfig
from src.postgres_session import PostgresSession

logger = logging.getLogger(__name__)

OpenAIAgentsInstrumentor().instrument()

langfuse = get_client()

# Verify connection
if langfuse.auth_check():
    logger.info("Langfuse client is authenticated and ready!")
else:
    logger.error("Authentication failed. Please check your credentials and host.")


class CustomAgent:
    """AI agent for form filling using OpenAI Agents SDK with browser control tools."""

    _application: str
    _agent: Agent
    _session_postgres_config: PostgresConfig
    _session_table_name: str

    def __init__(
        self,
        application: str,
        name: str,
        instructions: str,
        model: str,
        api_key: str,
        session_postgres_config: PostgresConfig,
        session_table_name: str,
        tools: list,
    ) -> None:
        """Initialize the agent with model configuration, session, and browser tools.

        Args:
            application: Application name used for LangFuse workflow grouping.
            name: Display name of the agent.
            instructions: System prompt / instructions for the agent.
            model: LiteLLM model string (e.g. "openrouter/...").
            api_key: API key for the model provider.
            session_postgres_config: PostgresConfig for managing conversation sessions.
            session_table_name: Name of the Postgres table for session management.
            tools: List of function_tool-decorated async callables for browser control.
        """
        self._application = application
        self._agent = Agent(
            name=name,
            instructions=instructions,
            model=LitellmModel(model=model, api_key=api_key),
            tools=tools,
        )
        self._session_postgres_config = session_postgres_config
        self._session_table_name = session_table_name

    async def act(self, message: str, conversation_id: str, clear_history: bool) -> str:
        """Run the agent for the given message within a conversation context.

        Sets current_conversation_id so browser tools operate on the correct
        Playwright page for this conversation.

        Args:
            message: The user message or instruction to process.
            conversation_id: Unique identifier for the conversation session.
            clear_history: Whether to clear the conversation history for this conversation_id before processing.

        Returns:
            The agent's final text output.

        """
        run_config = RunConfig(
            group_id=conversation_id,
            workflow_name=self._application,
        )
        session = PostgresSession(
            session_id=conversation_id,
            conninfo=self._session_postgres_config.conninfo.get_secret_value(),
            schema_name=self._session_postgres_config.db_schema,
            table_name=self._session_table_name,
        )
        if clear_history:
            await session.clear_session()
            logger.info(
                "Cleared conversation history for conversation_id=%s", conversation_id
            )
        try:
            result = await Runner.run(
                starting_agent=self._agent,
                input=message,
                run_config=run_config,
                session=session,
            )
            return result.final_output
        except Exception:
            logger.exception("Error occurred while running the agent")
            return "An error occurred while processing your request."
