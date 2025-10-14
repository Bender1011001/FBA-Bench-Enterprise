from __future__ import annotations

from typing import Any, Dict, Optional

from .gpt_3_5_bot import GPT35Bot as _BaseLLMBot

# Reuse the shared SimulationState dataclass and GPT35Bot implementation


class GPT4oMiniBot(_BaseLLMBot):
    """
    Thin wrapper around the shared LLM bot implementation to satisfy imports and
    allow model-specific defaults via model_params when constructed in tests.
    """

    def __init__(
        self,
        agent_id: str,
        llm_client: Any,
        prompt_adapter: Any,
        response_parser: Any,
        agent_gateway: Any,
        model_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            llm_client=llm_client,
            prompt_adapter=prompt_adapter,
            response_parser=response_parser,
            agent_gateway=agent_gateway,
            model_params=model_params,
        )

    # Inherit decide(self, state: SimulationState) from _BaseLLMBot
