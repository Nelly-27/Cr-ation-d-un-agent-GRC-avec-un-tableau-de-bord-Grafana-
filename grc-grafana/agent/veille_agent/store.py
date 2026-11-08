"""Enregistrement dans PostgreSQL (le schéma est créé par db/init.sh)."""
from __future__ import annotations

from datetime import datetime

import psycopg

from .assessment import Assessment
from .sources import FeedItem


def known_ids(conn: psycopg.Connection, external_ids: list[str]) -> set[str]:
    rows = conn.execute("SELECT external_id FROM items WHERE external_id = ANY(%s)", (external_ids,)).fetchall()
    return {r[0] for r in rows}


def insert_item(conn: psycopg.Connection, item: FeedItem, a: Assessment) -> bool:
    cur = conn.execute(
        """INSERT INTO items (source, category, external_id, title, url, published_at, description,
                              summary, risk_level, risk_score, rationale, method)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (external_id) DO NOTHING""",
        (item.source, item.category, item.external_id, item.title, item.url, item.published_at, item.description,
         a.summary, a.risk_level, a.risk_score, a.rationale, a.method),
    )
    return cur.rowcount == 1


def stored_items(conn: psycopg.Connection) -> list[FeedItem]:
    rows = conn.execute(
        "SELECT source, category, external_id, title, url, description, published_at FROM items ORDER BY id"
    ).fetchall()
    return [FeedItem(*r) for r in rows]


def update_assessment(conn: psycopg.Connection, external_id: str, a: Assessment) -> None:
    conn.execute(
        """UPDATE items SET summary = %s, risk_level = %s, risk_score = %s, rationale = %s, method = %s, updated_at = now()
           WHERE external_id = %s""",
        (a.summary, a.risk_level, a.risk_score, a.rationale, a.method, external_id),
    )


def record_run(conn: psycopg.Connection, source: str, started: datetime, finished: datetime,
               fetched: int, inserted: int, error: str | None) -> None:
    conn.execute(
        "INSERT INTO collection_runs (source, started_at, finished_at, fetched, inserted, error) VALUES (%s, %s, %s, %s, %s, %s)",
        (source, started, finished, fetched, inserted, error),
    )
