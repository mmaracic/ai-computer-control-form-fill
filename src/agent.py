import logging

from agents import Agent, RunConfig, Runner, SessionABC, TResponseInputItem
from agents.extensions.models.litellm_model import LitellmModel
from langfuse import get_client
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from pydantic import BaseModel

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


class SessionItem(BaseModel):
    role: str | None
    content: str | None
    type: str | None
    name: str | None
    output: str | None
    summary: str | None
    arguments: str | None


class CustomAgent:
    """AI agent for form filling using OpenAI Agents SDK with browser control tools."""

    _application: str
    _agent: Agent
    _session_postgres_config: PostgresConfig
    _session_table_name: str
    _max_turns: int

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
        max_turns: int,
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
            max_turns: Maximum number of agent turns before raising MaxTurnsExceeded.
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
        self._max_turns = max_turns

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
                max_turns=self._max_turns,
            )
            return result.final_output
        except Exception:
            logger.exception("Error occurred while running the agent")
            return "An error occurred while processing your request."

    async def get_session_data(self, conversation_id: str) -> list[SessionItem]:
        """Retrieve the session data for a given conversation_id.

        Args:
            conversation_id: Unique identifier for the conversation session.

        Returns:
            A list of session data objects for the given conversation_id.
        """
        session = PostgresSession(
            session_id=conversation_id,
            conninfo=self._session_postgres_config.conninfo.get_secret_value(),
            schema_name=self._session_postgres_config.db_schema,
            table_name=self._session_table_name,
        )
        items = await session.get_items()
        return [self._map_to_session_item(item) for item in items]

    def _map_to_session_item(self, item: TResponseInputItem) -> SessionItem:
        """Map a session item dictionary to a SessionItem model.

        Args:
            item: A dictionary representing a session item.

        Returns:
            A SessionItem model instance.
        """
        return SessionItem(
            role=item.get("role"),
            content=(
                str(item.get("content")) if item.get("content") is not None else None
            ),
            type=item.get("type"),
            name=item.get("name"),
            output=str(item.get("output")) if item.get("output") is not None else None,
            summary=(
                str(item.get("summary")) if item.get("summary") is not None else None
            ),
            arguments=(
                str(item.get("arguments"))
                if item.get("arguments") is not None
                else None
            ),
        )
