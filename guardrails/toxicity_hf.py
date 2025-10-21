from agno.guardrails import BaseGuardrail
from agno.exceptions import InputCheckError, CheckTrigger
from agno.run.team import TeamRunInput

from transformers import pipeline

# Carrega uma vez (processo) — ajuste o modelo para PT-BR se preferir
_hf_pipe = pipeline("text-classification", model="unitary/toxic-bert", top_k=None)

class ToxicityHFGuardrail(BaseGuardrail):
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold

    def _score(self, text: str) -> float:
        preds = _hf_pipe(text)
        # preds é lista de dicts; pegue a label “toxic” ou agregue as correlatas
        score = 0.0
        for p in preds[0]:
            if p["label"].lower() in ("toxic", "insult", "identity_hate", "obscene", "threat"):
                score = max(score, float(p["score"]))
        return score

    def _check(self, run_input: TeamRunInput):
        text = run_input.input_content if isinstance(run_input.input_content, str) else ""
        if not text:
            return
        score = self._score(text)
        if score >= self.threshold:
            raise InputCheckError(
                f"Conteúdo potencialmente tóxico (score={score:.2f} ≥ {self.threshold}).",
                check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
            )

    def check(self, run_input: TeamRunInput): self._check(run_input)
    async def async_check(self, run_input: TeamRunInput): self._check(run_input)
