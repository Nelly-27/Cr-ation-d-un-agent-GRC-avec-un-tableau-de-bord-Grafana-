"""Configuration lue dans l'environnement (fichier .env à la racine du projet)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# En local, on lit le .env de la racine ; dans Docker, les variables sont déjà injectées.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as err:
        raise SystemExit(f"Variable {name} invalide : « {raw} » n'est pas un nombre entier") from err


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    api_key: str
    model: str
    timeout: int

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.model)


@dataclass(frozen=True)
class Config:
    database_url: str
    llm: LlmConfig
    certfr_feed_url: str
    eurlex_feed_url: str
    max_items_per_source: int
    collect_interval_seconds: int


def load_config() -> Config:
    database_url = os.getenv("DATABASE_URL") or (
        f"postgresql://{os.getenv('POSTGRES_USER', 'grc_agent')}:{os.getenv('POSTGRES_PASSWORD', '')}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'grc')}"
    )
    llm = LlmConfig(
        base_url=os.getenv("LLM_BASE_URL", "").strip().rstrip("/"),
        api_key=os.getenv("LLM_API_KEY", "").strip(),
        model=os.getenv("LLM_MODEL", "").strip(),
        timeout=_int("LLM_TIMEOUT", 60),
    )
    if bool(llm.base_url) != bool(llm.model):
        raise SystemExit("LLM_BASE_URL et LLM_MODEL doivent être renseignés ensemble (ou laissés vides tous les deux).")
    return Config(
        database_url=database_url,
        llm=llm,
        certfr_feed_url=os.getenv("CERTFR_FEED_URL") or "https://www.cert.cyber.gouv.fr/feed/",
        eurlex_feed_url=os.getenv("EURLEX_FEED_URL") or "https://eur-lex.europa.eu/FR/display-feed.rss?rssId=162",
        max_items_per_source=_int("MAX_ITEMS_PER_SOURCE", 30),
        collect_interval_seconds=_int("COLLECT_INTERVAL_SECONDS", 3600),
    )
