# Démarrage rapide

## Prérequis

- **Docker Desktop** (ou Docker Engine + Compose v2), lancé.
- C'est tout pour faire tourner le projet. Pour développer : Python 3.11+ et Node.js 22+.

## Trois commandes

```bash
cp .env.example .env          # 1. configuration (fonctionne telle quelle, sans clé)
docker compose up -d --build  # 2. démarre toute la chaîne
docker compose ps             # 3. vérifie que tout tourne
```

Le premier démarrage prend quelques minutes (construction des images). Ensuite :

| Service | Adresse | Identifiants |
| --- | --- | --- |
| Dashboard Grafana | <http://localhost:3300> | `admin` / valeur de `GRAFANA_ADMIN_PASSWORD` |
| Chatbot | <http://localhost:3100> | — |
| Serveur MCP Grafana | <http://localhost:8000/mcp> | — (lecture seule) |
| PostgreSQL | `localhost:5433`, base `grc` | `grc_reader` (lecture) ou `grc_agent` (écriture) |

L'agent collecte **dès le démarrage**, puis **toutes les heures**. Le dashboard est rempli en quelques secondes.

::: tip Sans clé, tout fonctionne
Par défaut, aucun modèle de langage n'est configuré : l'agent classe les risques avec des règles explicables et le chatbot construit ses réponses directement à partir des données. Pour brancher un LLM, voir [Choisir le modèle](./modele).
:::

## Ports déjà utilisés ?

Changez `GRAFANA_PORT`, `CHATBOT_PORT`, `MCP_PORT` ou `POSTGRES_PORT` dans `.env`, puis `docker compose up -d`.

## Commandes utiles

```bash
docker compose logs -f agent                                 # suivre les collectes
docker compose run --rm agent python -m veille_agent         # forcer une collecte maintenant
docker compose run --rm agent python -m veille_agent --reanalyze   # réanalyser tout (après changement de modèle)
docker compose down                                          # arrêter (les données sont conservées)
docker compose down -v                                       # arrêter ET effacer les données
```

## Développer sans Docker (facultatif)

Les services PostgreSQL, Grafana et MCP restent dans Docker ; l'agent et le chatbot tournent en local :

```bash
docker compose up -d postgres grafana grafana-init mcp-grafana

# Agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r agent/requirements.txt pytest
cd agent && python -m veille_agent && python -m pytest -q tests

# Chatbot (lit le .env de la racine)
cd chatbot && npm install && npm run dev      # http://localhost:3100
```
