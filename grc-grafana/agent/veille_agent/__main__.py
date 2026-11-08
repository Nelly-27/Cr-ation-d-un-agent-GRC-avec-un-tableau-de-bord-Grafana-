"""Point d'entrée.

    python -m veille_agent               collecte une fois
    python -m veille_agent --loop        collecte puis recommence toutes les COLLECT_INTERVAL_SECONDS
    python -m veille_agent --reanalyze   réanalyse les entrées déjà en base (après un changement de modèle)
"""
from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timezone

import psycopg

from . import store
from .assessment import assess
from .config import Config, load_config
from .sources import fetch_xml, parse_certfr, parse_eurlex

log = logging.getLogger("veille_agent")


def collect_source(conn: psycopg.Connection, cfg: Config, name: str, url: str, parser) -> None:
    started = datetime.now(timezone.utc)
    fetched = inserted = 0
    error = None
    try:
        items = parser(fetch_xml(url), cfg.max_items_per_source)
        fetched = len(items)
        # Seules les nouveautés passent par le LLM : une collecte horaire ne repaie pas l'historique.
        already = store.known_ids(conn, [i.external_id for i in items])
        for item in (i for i in items if i.external_id not in already):
            if store.insert_item(conn, item, assess(item, cfg.llm)):
                inserted += 1
                conn.commit()
    except Exception as err:  # une source en panne ne doit pas arrêter l'autre
        error = f"{type(err).__name__}: {err}"[:500]
        log.error("%s : échec de la collecte (%s)", name, error)
        conn.rollback()
    store.record_run(conn, name, started, datetime.now(timezone.utc), fetched, inserted, error)
    conn.commit()
    log.info("%s : %d lue(s), %d nouvelle(s)", name, fetched, inserted)


def collect_once(cfg: Config) -> None:
    mode = f"LLM {cfg.llm.model} via {cfg.llm.base_url}" if cfg.llm.enabled else "règles (sans LLM)"
    log.info("Collecte – mode d'analyse : %s", mode)
    with psycopg.connect(cfg.database_url) as conn:
        collect_source(conn, cfg, "certfr", cfg.certfr_feed_url, parse_certfr)
        collect_source(conn, cfg, "eurlex", cfg.eurlex_feed_url, parse_eurlex)


def reanalyze(cfg: Config) -> None:
    """Repasse toutes les entrées dans l'analyse actuelle (nouveau modèle, nouvelles règles)."""
    with psycopg.connect(cfg.database_url) as conn:
        items = store.stored_items(conn)
        for n, item in enumerate(items, 1):
            store.update_assessment(conn, item.external_id, assess(item, cfg.llm))
            conn.commit()
            if n % 10 == 0 or n == len(items):
                log.info("Réanalyse : %d/%d", n, len(items))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Agent de veille GRC (CERT-FR + EUR-Lex)")
    parser.add_argument("--loop", action="store_true", help="collecter à intervalle régulier")
    parser.add_argument("--reanalyze", action="store_true", help="réanalyser les entrées déjà en base, puis s'arrêter")
    args = parser.parse_args()
    cfg = load_config()
    if args.reanalyze:
        return reanalyze(cfg)
    while True:
        try:
            collect_once(cfg)
        except psycopg.OperationalError as err:
            if not args.loop:
                raise SystemExit(f"Base PostgreSQL injoignable : {err}") from err
            log.error("Base PostgreSQL injoignable, nouvel essai au prochain cycle : %s", err)
        if not args.loop:
            return
        log.info("Prochaine collecte dans %d s", cfg.collect_interval_seconds)
        time.sleep(cfg.collect_interval_seconds)


if __name__ == "__main__":
    main()
