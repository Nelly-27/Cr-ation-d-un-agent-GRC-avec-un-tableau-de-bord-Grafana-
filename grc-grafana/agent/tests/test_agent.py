"""Tests sans réseau ni base : extraits réels des flux (tests/fixtures) et LLM simulé."""
from pathlib import Path

import pytest
import requests

from veille_agent import assessment
from veille_agent.assessment import assess, assess_with_rules, parse_llm_answer
from veille_agent.config import LlmConfig
from veille_agent.sources import FeedItem, parse_certfr, parse_eurlex

FIXTURES = Path(__file__).parent / "fixtures"
NO_LLM = LlmConfig(base_url="", api_key="", model="", timeout=5)
LLM = LlmConfig(base_url="https://llm.example/v1", api_key="k", model="modele-test", timeout=5)


def item(source="certfr", title="t", description="", url="https://www.cert.cyber.gouv.fr/avis/X/") -> FeedItem:
    return FeedItem(source, "cyber" if source == "certfr" else "reglementaire", url, title, url, description, None)


def test_certfr_feed_is_parsed_with_official_links():
    items = parse_certfr((FIXTURES / "certfr.xml").read_bytes(), limit=10)
    assert len(items) == 6
    assert all(i.url.startswith("https://www.cert.cyber.gouv.fr/") for i in items)
    assert all(i.published_at is not None for i in items)
    assert items[0].title.startswith("Multiples vulnérabilités")


def test_eurlex_feed_skips_foreign_rectificatifs_and_extracts_celex():
    items = parse_eurlex((FIXTURES / "eurlex.xml").read_bytes(), limit=10)
    assert items, "au moins un acte attendu"
    assert all(i.external_id.startswith("CELEX:") for i in items)
    assert all("/./" not in i.url for i in items)
    assert not any("ne concerne pas la version française" in i.description for i in items)
    assert not any(i.title.startswith("CELEX:") for i in items)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"url": "https://www.cert.cyber.gouv.fr/alerte/CERTFR-2026-ALE-001/"}, "critique"),
        ({"description": "Elle est activement exploitée."}, "critique"),
        ({"description": "permet une exécution de code arbitraire à distance"}, "élevé"),
        ({"description": "permet une élévation de privilèges"}, "moyen"),
        ({"description": "permet un déni de service"}, "faible"),
        ({"source": "eurlex", "title": "Règlement relatif à la cybersécurité", "url": "u"}, "élevé"),
        ({"source": "eurlex", "title": "Directive sur les services numériques", "url": "u"}, "moyen"),
        ({"source": "eurlex", "title": "Agence européenne pour la sécurité et la santé au travail", "url": "u"}, "faible"),
        ({"source": "eurlex", "title": "Rectificatif au règlement sur la cybersécurité", "url": "u"}, "faible"),
        ({"source": "eurlex", "title": "Décision portant nomination d'un suppléant", "url": "u"}, "faible"),
    ],
)
def test_rules_classify_risk_levels(kwargs, expected):
    assert assess_with_rules(item(**kwargs)).risk_level == expected


def test_llm_answer_is_parsed_whatever_the_wrapping():
    raw = '<think>raisonnement</think>```json\n{"resume": "Faille RCE.", "niveau": "Eleve", "justification": "RCE."}\n```'
    a = parse_llm_answer(raw, "m")
    assert (a.risk_level, a.risk_score, a.method) == ("élevé", 3, "llm:m")


def test_llm_answer_with_unknown_level_is_rejected():
    with pytest.raises(ValueError):
        parse_llm_answer('{"resume": "x", "niveau": "énorme", "justification": "y"}', "m")


def test_without_llm_config_rules_are_used(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: pytest.fail("aucun appel réseau attendu"))
    assert assess(item(description="exécution de code arbitraire à distance"), NO_LLM).method == "regles"


def test_llm_is_called_in_openai_compatible_format(monkeypatch):
    seen = {}

    class Response:
        ok = True

        def json(self):
            return {"choices": [{"message": {"content": '{"resume": "R.", "niveau": "critique", "justification": "J."}'}}]}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, auth=headers.get("Authorization"), body=json)
        return Response()

    monkeypatch.setattr(assessment.requests, "post", fake_post)
    a = assess(item(), LLM)
    assert seen["url"] == "https://llm.example/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
    assert set(seen["body"]) == {"model", "messages"}  # rien que certains fournisseurs refuseraient
    assert (a.risk_level, a.method) == ("critique", "llm:modele-test")


def test_llm_failure_falls_back_to_rules(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("injoignable")

    monkeypatch.setattr(assessment.requests, "post", boom)
    a = assess(item(description="permet une élévation de privilèges"), LLM)
    assert (a.risk_level, a.method) == ("moyen", "regles (repli LLM)")
