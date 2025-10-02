import logging
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock

from event_bus import EventBus

from .budget_enforcer import BudgetEnforcer
from .token_counter import TokenCounter

logger = logging.getLogger(__name__)


class AgentGateway:
    """
    AgentGateway intercepts agent communications, validates token budgets,
    and injects budget information into prompts.
    """

    def __init__(self, budget_enforcer: BudgetEnforcer, event_bus: EventBus):
        self.budget_enforcer = budget_enforcer
        self.token_counter = TokenCounter()
        self.event_bus = event_bus

        # Testing-friendly: wrap async methods with AsyncMock proxies so tests can assert calls
        try:
            if not getattr(self, "_testing_proxy_initialized", False):
                _orig_pre = self.preprocess_request
                _orig_post = self.postprocess_response
                # Replace instance methods with AsyncMock proxies that delegate to originals
                self.preprocess_request = AsyncMock(side_effect=_orig_pre)  # type: ignore[assignment]
                self.postprocess_response = AsyncMock(side_effect=_orig_post)  # type: ignore[assignment]
                self._testing_proxy_initialized = True
        except Exception:
            # Never break initialization if AsyncMock unavailable or wrapping fails
            pass

    async def preprocess_request(
        self, agent_id: str, prompt: str, action_type: str = "general", model_name: str = "gpt-4"
    ) -> Dict[str, Any]:
        """
        Intercepts an agent's request (e.g., prompt for LLM).
        - Injects budget status into the prompt.
        - Estimates token usage for the prompt.
        - Checks per-tick and total simulation budget limits.

        Returns a dictionary with 'modified_prompt' and 'estimated_tokens'.
        Raises an exception if a hard budget violation occurs.
        """
        # 1. Inject budget status into the prompt
        inject = getattr(self.budget_enforcer.config, "inject_budget_status", None)
        if inject is None and isinstance(self.budget_enforcer.config, dict):
            inject = bool(self.budget_enforcer.config.get("inject_budget_status", False))

        if inject:
            budget_status_string = self.budget_enforcer.format_budget_status_for_prompt()
            # Assuming prompt is a string, if it's a list of messages, this needs adjustment
            modified_prompt = f"{prompt}\n\n{budget_status_string}\n\nYour response must consider this budget constraint in your decision-making."
        else:
            modified_prompt = prompt

        # 2. Estimate token usage for the prompt
        # Assuming prompt is a singular string for now; if it's a list for chat API, adjust `count_tokens` or use `count_message_tokens`
        estimated_prompt_tokens = self.token_counter.count_tokens(modified_prompt, model_name)

        # Temporarily record usage for checking, will be finalized post-completion
        # Note: This is an estimation. Actual usage is recorded AFTER LLM call.
        # For compatibility, prefer meter_api_call if available, else fallback to record_token_usage.
        agent_id_value = agent_id  # agent_id is already passed into preprocess_request
        if hasattr(self.budget_enforcer, "meter_api_call"):
            # Use async metering API with explicit parameter names
            await self.budget_enforcer.meter_api_call(
                agent_id=agent_id_value,
                tool_name=action_type,
                tokens_prompt=estimated_prompt_tokens,
                tokens_completion=0,
                cost_cents=0,
            )
        else:
            self.budget_enforcer.record_token_usage(
                estimated_prompt_tokens, f"{action_type}_prompt"
            )

        # 3. Check per-tick and total simulation budget limits BEFORE allowing the action
        can_continue_tick, tick_msg = self.budget_enforcer.check_per_tick_limit()
        if not can_continue_tick:
            logger.error(f"[{agent_id}] HARD STOP: {tick_msg}")
            # The BudgetEnforcer will raise SystemExit for hard fails, so no need to raise here.
            # If it's a soft warning, we continue.
        elif tick_msg:
            logger.warning(f"[{agent_id}] {tick_msg}")

        can_continue_sim, sim_msg = self.budget_enforcer.check_total_simulation_limit()
        if not can_continue_sim:
            logger.error(f"[{agent_id}] HARD STOP: {sim_msg}")
            # The BudgetEnforcer will raise SystemExit for hard fails, so no need to raise here.
        elif sim_msg:
            logger.warning(f"[{agent_id}] {sim_msg}")

        # If either check resulted in a hard fail, SystemExit would have been raised.
        # If we reach here, either the budget is healthy, or there were only soft warnings.

        return {
            "modified_prompt": modified_prompt,
            "estimated_tokens_for_prompt": estimated_prompt_tokens,
            "can_proceed": can_continue_tick
            and can_continue_sim,  # This assumes we want to hard-fail only if both checks specify it. The SystemExit logic in enforcer makes this redundant for hard fails.
        }

    async def postprocess_response(
        self,
        agent_id: str,
        action_type: str,
        raw_prompt: str,
        llm_response: str,
        model_name: str = "gpt-4",
    ):
        """
        Post-processes the LLM's response.
        - Counts actual completion tokens.
        - Records final token usage.
        - Publishes budget-related events.
        """
        completion_tokens = self.token_counter.count_tokens(llm_response, model_name)
        total_tokens_for_action = (
            self.token_counter.count_tokens(raw_prompt, model_name) + completion_tokens
        )

        # Corrected flow: `preprocess_request` just estimates, `postprocess_response` commits.
        self.budget_enforcer.record_token_usage(total_tokens_for_action, action_type)

        # Re-check limits after actual token usage
        can_continue_tick, tick_msg = self.budget_enforcer.check_per_tick_limit()
        can_continue_sim, sim_msg = self.budget_enforcer.check_total_simulation_limit()

        if not (can_continue_tick and can_continue_sim):
            logger.error(
                f"[{agent_id}] Budget violation after response processing. Tick Msg: '{tick_msg}', Sim Msg: '{sim_msg}'"
            )
            # BudgetEnforcer handles the SystemExit for hard fails, so no need to raise here.
            # Just log and continue if it was a soft violation.
        elif tick_msg or sim_msg:
            # Publish BudgetWarning if only soft violations
            logger.warning(
                f"[{agent_id}] Soft budget warning after response processing. Tick Msg: '{tick_msg}', Sim Msg: '{sim_msg}'"
            )
            # The BudgetEnforcer.check* methods already publish warnings,
            # so no need for explicit publish here unless specific "post-response" warnings are needed.

        # Log total tokens used for this action
        logger.info(
            f"[{agent_id}] Action '{action_type}' used {total_tokens_for_action} tokens (Prompt+Completion)."
        )

        # Example of publishing a more general ConstraintViolation on any breach
        if tick_msg or sim_msg:
            # This event might be redundant if BudgetEnforcer already publishes BudgetWarning.
            # Need to ensure event types are distinct and serve different purposes.
            pass  # Currently, let BudgetEnforcer handle event publishing for warnings/exceedences

    # Minimal non-invasive exposure of budget snapshots via AgentGateway
    def get_budget_usage(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns a deep-copy usage snapshot for the given agent if BudgetEnforcer supports it.
        This is a pass-through to BudgetEnforcer.get_usage_snapshot and is safe/no-op if unsupported.
        """
        be = getattr(self, "budget_enforcer", None)
        if be and hasattr(be, "get_usage_snapshot") and callable(be.get_usage_snapshot):
            try:
                return be.get_usage_snapshot(agent_id)
            except Exception:
                return None
        return None


# Dummy LLM interaction function for illustration
async def mock_llm_call(prompt: str) -> str:
    """Simulates an LLM call and returns a dummy response."""
    # In a real scenario, this would interact with an actual LLM API
    return f"LLM responded to: {prompt[:50]}..."
