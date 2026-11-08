"""Collecte des flux RSS officiels : CERT-FR (cyber) et EUR-Lex (réglementaire)."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime

import requests
from defusedxml import ElementTree

USER_AGENT = "grc-grafana-agent/1.0 (prototype pedagogique EPITA)"
CELEX_PREFIX = re.compile(r"^CELEX:([^\s:]+):?\s*")
NOT_FRENCH = "ne concerne pas la version française"


@dataclass(frozen=True)
class FeedItem:
    source: str          # 'certfr' | 'eurlex'
    category: str        # 'cyber' | 'reglementaire'
    external_id: str
    title: str
    url: str
    description: str
    published_at: datetime | None


def fetch_xml(url: str, timeout: int = 30) -> bytes:
    res = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    res.raise_for_status()
    return res.content  # octets bruts : l'analyseur XML respecte l'encodage déclaré


def _text(node, tag: str) -> str:
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(text))
    return re.sub(r"\s+", " ", text).strip()


def _date(raw: str) -> datetime | None:
    try:
        return parsedate_to_datetime(raw) if raw else None
    except (TypeError, ValueError):
        return None


def parse_rss(xml: bytes) -> list[dict[str, str]]:
    root = ElementTree.fromstring(xml)
    return [
        {
            "title": _clean(_text(item, "title")),
            "link": _text(item, "link"),
            "guid": _text(item, "guid"),
            "description": _clean(_text(item, "description")),
            "pubDate": _text(item, "pubDate"),
        }
        for item in root.iter("item")
    ]


def parse_certfr(xml: bytes, limit: int) -> list[FeedItem]:
    return [
        FeedItem(
            source="certfr",
            category="cyber",
            external_id=raw["guid"] or raw["link"],
            title=raw["title"],
            url=raw["link"],
            description=raw["description"],
            published_at=_date(raw["pubDate"]),
        )
        for raw in parse_rss(xml)[:limit]
    ]


def parse_eurlex(xml: bytes, limit: int) -> list[FeedItem]:
    items = []
    # Rectificatifs d'autres langues : aucun effet pour une organisation française.
    relevant = [r for r in parse_rss(xml) if NOT_FRENCH not in r["description"]]
    for raw in relevant[:limit]:
        # Titre EUR-Lex : « CELEX:32026D2493: Décision (UE) 2026/2493… » (parfois le seul numéro)
        match = CELEX_PREFIX.match(raw["title"])
        celex = match.group(1) if match else ""
        title = CELEX_PREFIX.sub("", raw["title"]) or f"Acte CELEX:{celex}"
        # Les liens du flux contiennent « /./ » : on les normalise.
        url = raw["link"].replace("europa.eu/./", "europa.eu/")
        items.append(
            FeedItem(
                source="eurlex",
                category="reglementaire",
                external_id=f"CELEX:{celex}" if celex else (raw["guid"] or url),
                title=title,
                url=url,
                description=raw["description"],
                published_at=_date(raw["pubDate"]),
            )
        )
    return items
