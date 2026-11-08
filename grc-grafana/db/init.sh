#!/bin/sh
# Exécuté une seule fois par PostgreSQL, au premier démarrage du volume.
# Crée le schéma et un rôle en lecture seule pour Grafana et le chatbot.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE TABLE IF NOT EXISTS items (
  id            SERIAL PRIMARY KEY,
  source        TEXT NOT NULL CHECK (source IN ('certfr', 'eurlex')),
  category      TEXT NOT NULL CHECK (category IN ('cyber', 'reglementaire')),
  external_id   TEXT NOT NULL UNIQUE,          -- identifiant officiel (URL ou CELEX) : déduplication
  title         TEXT NOT NULL,
  url           TEXT NOT NULL,                 -- lien vers la source officielle
  published_at  TIMESTAMPTZ,
  description   TEXT NOT NULL DEFAULT '',      -- texte d'origine du flux (permet de réanalyser)
  summary       TEXT NOT NULL,
  risk_level    TEXT NOT NULL CHECK (risk_level IN ('faible', 'moyen', 'élevé', 'critique')),
  risk_score    SMALLINT NOT NULL CHECK (risk_score BETWEEN 1 AND 4),
  rationale     TEXT NOT NULL,                 -- pourquoi ce niveau
  method        TEXT NOT NULL,                 -- 'llm:<modèle>' ou 'regles'
  collected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS items_published_idx ON items (published_at DESC);
CREATE INDEX IF NOT EXISTS items_risk_idx ON items (risk_score DESC);

CREATE TABLE IF NOT EXISTS collection_runs (
  id           SERIAL PRIMARY KEY,
  source       TEXT NOT NULL,
  started_at   TIMESTAMPTZ NOT NULL,
  finished_at  TIMESTAMPTZ NOT NULL,
  fetched      INTEGER NOT NULL,
  inserted     INTEGER NOT NULL,
  error        TEXT
);

CREATE ROLE "$POSTGRES_READER_USER" LOGIN PASSWORD '$POSTGRES_READER_PASSWORD';
GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO "$POSTGRES_READER_USER";
GRANT USAGE ON SCHEMA public TO "$POSTGRES_READER_USER";
GRANT SELECT ON ALL TABLES IN SCHEMA public TO "$POSTGRES_READER_USER";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "$POSTGRES_READER_USER";
ALTER ROLE "$POSTGRES_READER_USER" SET default_transaction_read_only = on;
SQL
