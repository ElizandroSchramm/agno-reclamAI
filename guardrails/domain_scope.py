"""
Mantém o agente focado no domínio (ex.: negociação de dívidas).

Híbrido:
1) Heurística por palavras-chave (barata)
2) Similaridade semântica via embeddings (opcional)
   Ative com env SCOPE_USE_EMBEDDINGS=true (requires sentence-transformers).
"""
import os
from typing import List
from agno.guardrails import BaseGuardrail
from agno.exceptions import InputCheckError, CheckTrigger
from agno.run.team import TeamRunInput

_USE_EMB = os.getenv("SCOPE_USE_EMBEDDINGS", "false").lower() == "true"
_EMB_THRESHOLD = float(os.getenv("SCOPE_EMB_THRESHOLD", "0.45"))  # 0–1 cosine
_DEBT_KEYWORDS = [
    "negociação de dívida", "acordo", "parcelamento", "desconto", "inadimplência",
    "credor", "empresa", "Vivo", "Nubank", "atraso", "valor da dívida", "prazo",
    "nome negativado", "proposta", "boleto", "juros", "multa", "renegociação",
]

if _USE_EMB:
    try:
        from sentence_transformers import SentenceTransformer, util
        _emb_model = SentenceTransformer(
            os.getenv("SCOPE_EMB_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        )
        _domain_text = (
            "Negociação de dívidas: acordos, parcelamentos, descontos, prazos, valores, "
            "credores, nome negativado, propostas, boletos, juros, multas, renegociação."
        )
        _domain_vec = _emb_model.encode([_domain_text], normalize_embeddings=True)
    except Exception:
        _USE_EMB = False
        _emb_model = None
        _domain_vec = None

class DomainScopeGuardrail(BaseGuardrail):
    def __init__(self, keywords: List[str] = None, min_hits: int = 1):
        self.keywords = [k.lower() for k in (keywords or _DEBT_KEYWORDS)]
        self.min_hits = min_hits

    def _heuristic_relevance(self, text: str) -> bool:
        tl = text.lower()
        hits = sum(1 for k in self.keywords if k in tl)
        return hits >= self.min_hits

    def _embedding_relevance(self, text: str) -> bool:
        if not _USE_EMB or not text.strip():
            return True  # skip if embeddings disabled
        vec = _emb_model.encode([text], normalize_embeddings=True)
        from sentence_transformers import util
        score = float(util.cos_sim(vec, _domain_vec)[0][0])
        return score >= _EMB_THRESHOLD

    def _off_topic_message(self) -> str:
        return (
            "Este agente é focado em *negociação de dívidas*. "
            "Se preferir, reformule, por exemplo: "
            "'Quero negociar minhas dívidas com o banco Y. Conte os detalhes que vamos lhe auxiliar na negociação.'"
        )

    def _check(self, run_input: TeamRunInput):
        text = run_input.input_content if isinstance(run_input.input_content, str) else ""
        if not text.strip():
            return
        if not self._heuristic_relevance(text) or not self._embedding_relevance(text):
            raise InputCheckError(
                self._off_topic_message(),
                check_trigger=CheckTrigger.INPUT_NOT_ALLOWED,
            )

    def check(self, run_input: TeamRunInput): self._check(run_input)
    async def async_check(self, run_input: TeamRunInput): self._check(run_input)
