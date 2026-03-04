import logging

from agents import Agent, RunConfig, Runner, SessionABC
from agents.extensions.models.litellm_model import LitellmModel
from langfuse import get_client
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor

logger = logging.getLogger(__name__)

OpenAIAgentsInstrumentor().instrument()

langfuse = get_client()

# Verify connection
if langfuse.auth_check():
    logger.info("Langfuse client is authenticated and ready!")
else:
    logger.error("Authentication failed. Please check your credentials and host.")


class CustomAgent:

    def __init__(
        self,
        application: str,
        name: str,
        instructions: str,
        model: str,
        api_key: str,
        session: SessionABC,
    ) -> None:
        self._application = application
        self._agent = Agent(
            name=name,
            instructions=instructions,
            model=LitellmModel(model=model, api_key=api_key),
            tools=[],
        )
        self._session = session

    async def act(self, input: str, conversation_id: str) -> str:
        run_config = RunConfig(
            group_id=conversation_id,
            workflow_name=self._application,
        )
        result = await Runner.run(
            starting_agent=self._agent,
            input=input,
            run_config=run_config,
            session=self._session,
        )
        return result.final_output
