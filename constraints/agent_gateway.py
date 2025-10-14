"""Agent Gateway for preprocessing/postprocessing LLM requests."""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AgentGateway:
    """
    Gateway for agent requests - handles preprocessing (budget injection)
    and postprocessing (usage tracking, event routing).
    """

    def __init__(self):
        """Initialize gateway (can add budget enforcer integration later)."""
        pass

    async def preprocess_request(
        self, agent_id: str, prompt: str
    ) -> Dict[str, Any]:
        """
        Preprocess agent request before sending to LLM.

        Args:
            agent_id: The agent making the request
            prompt: The raw prompt

        Returns:
            Dict with "modified_prompt" (str) after budget checks/injection
        """
        # Simple passthrough for demo/test - can add budget constraints later
        return {"modified_prompt": prompt}

    async def postprocess_response(
        self,
        agent_id: str,
        request_type: str,
        request_content: str,
        response_content: str,
    ) -> None:
        """
        Postprocess agent response after LLM call.

        Args:
            agent_id: The agent that made the request
            request_type: Type of request (e.g., "llm_decision")
            request_content: The request that was sent
            response_content: The response received

        Returns:
            None (logs usage, routes events, etc.)
        """
        # Simple logging for demo/test - can add usage tracking later
        logger.debug(
            f"AgentGateway postprocess: agent={agent_id}, "
            f"type={request_type}, response_len={len(response_content)}"
        )
