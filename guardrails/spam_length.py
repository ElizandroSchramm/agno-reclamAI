from agno.exceptions import CheckTrigger, InputCheckError
from agno.guardrails import BaseGuardrail
from agno.run.team import TeamRunInput


class SpamAndLengthGuardrail(BaseGuardrail):
    """Blocks excessively long or spammy inputs to protect cost and UX."""
    MAX_INPUT_CHARS = 1000


    def check(self, run_input: TeamRunInput) -> None:
        self._check(run_input)

    async def async_check(self, run_input: TeamRunInput) -> None:
        self._check(run_input)

    def _check(self, run_input: TeamRunInput) -> None:
        content = run_input.input_content if isinstance(run_input.input_content, str) else ""
        if content and len(content) > self.MAX_INPUT_CHARS:
            raise InputCheckError(
                f"Mensagem longa demais ({len(content)} chars). Limite atual: {self.MAX_INPUT_CHARS}.",
                check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
            )