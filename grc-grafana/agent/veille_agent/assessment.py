"""Résumé et niveau de risque d'une actualité : par LLM si configuré, sinon par règles."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import requests

from .config import LlmConfig
from .sources import FeedItem

log = logging.getLogger(__name__)

LEVELS = ("faible", "moyen", "élevé", "critique")
SCORES = {level: i + 1 for i, level in enumerate(LEVELS)}
# Variantes que renvoient parfois les modèles (sans accent, en anglais…)
LEVEL_ALIASES = {"eleve": "élevé", "elevé": "élevé", "low": "faible", "medium": "moyen", "high": "élevé", "critical": "critique"}
SUMMARY_MAX_CHARS = 400


@dataclass(frozen=True)
class Assessment:
    summary: str
    risk_level: str
    rationale: str
    method: str

    @property
    def risk_score(self) -> int:
        return SCORES[self.risk_level]


# --------------------------------------------------------------------------- règles

CERTFR_RULES: list[tuple[str, str, str]] = [
    # (motif recherché, niveau, justification) : le premier motif trouvé l'emporte.
    (r"activement exploit|exploitation active|est exploitée", "critique", "vulnérabilité signalée comme exploitée"),
    (r"exécution de code arbitraire à distance|exécution de code à distance", "élevé", "exécution de code à distance possible"),
    (r"élévation de privilèges|contournement de la politique de sécurité|contournement de l'authentification", "moyen", "élévation de privilèges ou contournement de sécurité"),
    (r"atteinte à la confidentialité|injection|falsification de requêtes", "moyen", "atteinte possible à la confidentialité des données"),
]
EURLEX_RULES: list[tuple[str, str, str]] = [
    (r"rectificatif", "faible", "rectificatif sans nouvelle obligation"),
    (r"cybersécurité|cyberrésilience|résilience opérationnelle numérique|données à caractère personnel|intelligence artificielle"
     r"|NIS ?2|sécurité des réseaux et des systèmes d'information|incidents? (majeurs? )?liés aux TIC",
     "élevé", "texte touchant la cybersécurité, les données personnelles ou l'IA"),
    # « sécurité » seul est trop large (sécurité au travail, sécurité alimentaire, PESC…) : termes précis uniquement.
    (r"numérique|données|identité électronique|communications électroniques|services financiers|plateformes? en ligne"
     r"|sécurité de l'information|mesures restrictives",
     "moyen", "texte touchant le numérique, les données ou les sanctions internationales"),
]


def _short_summary(item: FeedItem) -> str:
    text = item.description or item.title
    if len(text) <= SUMMARY_MAX_CHARS:
        return text
    cut = text[:SUMMARY_MAX_CHARS]
    return (cut[: cut.rfind(". ") + 1] or cut.rsplit(" ", 1)[0] + "…").strip()


def assess_with_rules(item: FeedItem) -> Assessment:
    text = f"{item.title} {item.description}"
    if item.source == "certfr" and "/alerte/" in item.url:
        level, why = "critique", "alerte CERT-FR (menace active)"
    else:
        rules, default = (
            (CERTFR_RULES, ("faible", "avis de sécurité sans impact majeur identifié"))
            if item.source == "certfr"
            else (EURLEX_RULES, ("faible", "texte sans lien direct avec la sécurité de l'information"))
        )
        level, why = next(((lvl, w) for pattern, lvl, w in rules if re.search(pattern, text, re.IGNORECASE)), default)
    return Assessment(_short_summary(item), level, f"Règle : {why}.", "regles")


# --------------------------------------------------------------------------- LLM

SYSTEM_PROMPT = """Tu es analyste GRC (gouvernance, risques, conformité) pour une organisation française.
On te donne une actualité officielle (avis du CERT-FR ou acte publié sur EUR-Lex).
Réponds UNIQUEMENT par un objet JSON, sans texte autour, de la forme :
{"resume": "...", "niveau": "...", "justification": "..."}
- resume : 2 phrases maximum, en français, factuelles, sans rien inventer au-delà du texte fourni.
- niveau : exactement l'un de "faible", "moyen", "élevé", "critique".
    critique = menace exploitée activement ou obligation majeure applicable immédiatement ;
    élevé    = exécution de code à distance, fuite de données probable, ou nouvelle obligation cyber/données/IA ;
    moyen    = vulnérabilité limitée (élévation de privilèges, contournement) ou texte numérique d'impact indirect ;
    faible   = information, rectificatif, ou texte sans lien avec la sécurité de l'information.
- justification : une phrase expliquant le niveau."""


def _extract_json(content: str) -> dict:
    # Certains modèles ajoutent un raisonnement (<think>…</think>) ou des balises ```json.
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError("aucun objet JSON dans la réponse")
    return json.loads(match.group(0))


def parse_llm_answer(content: str, model: str) -> Assessment:
    data = _extract_json(content)
    raw_level = str(data.get("niveau", "")).strip().lower()
    level = LEVEL_ALIASES.get(raw_level, raw_level)
    summary = str(data.get("resume", "")).strip()
    rationale = str(data.get("justification", "")).strip()
    if level not in LEVELS or not summary:
        raise ValueError(f"réponse incomplète ou niveau inconnu : {raw_level!r}")
    return Assessment(summary[:1000], level, rationale[:500] or "—", f"llm:{model}")


def call_llm(cfg: LlmConfig, messages: list[dict[str, str]]) -> str:
    """Appel « chat completions » compatible OpenAI. Volontairement minimal (ni température
    ni max_tokens) : ce sont les paramètres que certains fournisseurs ou modèles refusent."""
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    res = requests.post(
        f"{cfg.base_url}/chat/completions",
        headers=headers,
        json={"model": cfg.model, "messages": messages},
        timeout=cfg.timeout,
    )
    if not res.ok:
        raise RuntimeError(f"HTTP {res.status_code} : {res.text[:300]}")
    return res.json()["choices"][0]["message"]["content"] or ""


def assess(item: FeedItem, cfg: LlmConfig) -> Assessment:
    if not cfg.enabled:
        return assess_with_rules(item)
    user = f"Source : {item.source}\nTitre : {item.title}\nLien : {item.url}\nTexte : {item.description or '(aucun)'}"
    try:
        content = call_llm(cfg, [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}])
        return parse_llm_answer(content, cfg.model)
    except (requests.RequestException, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as err:
        # Le LLM ne doit jamais bloquer la veille : repli explicite sur les règles.
        log.warning("LLM indisponible pour %s (%s) : repli sur les règles", item.external_id, err)
        fallback = assess_with_rules(item)
        return Assessment(fallback.summary, fallback.risk_level, fallback.rationale, "regles (repli LLM)")
