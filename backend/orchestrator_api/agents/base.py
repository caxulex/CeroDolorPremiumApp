from typing import Any

from backend.orchestrator_api.services.mistral_client import MistralClient


class AgentBase:
    def __init__(self, client: MistralClient, agent_id: str):
        self.client = client
        self.agent_id = agent_id

    async def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.client.invoke_agent(self.agent_id, payload)
