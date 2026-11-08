# Architecture

```
 Sources officielles        Agent IA (Python)            Stockage        Restitution
 ───────────────────        ─────────────────            ────────        ───────────
 CERT-FR (flux RSS) ─┐      collecte toutes les heures                   Grafana (dashboard)
                     ├────▶ déduplication           ──▶ PostgreSQL ──▶      │ lecture seule
 EUR-Lex (flux RSS) ─┘      résumé + criticité (LLM)     (items)            ▼
                            ou règles si pas de LLM                     MCP Grafana ──▶ Chatbot Next.js
                                                                       (lecture seule)   (réponses sourcées)
```

| Composant | Dossier | Technologie | Rôle |
| --- | --- | --- | --- |
| Agent | `agent/` | Python 3.12 | Collecte, analyse, enregistrement ; boucle horaire |
| Base | `db/init.sh` | PostgreSQL 17 | Tables `items` et `collection_runs`, rôle lecture seule |
| Dashboard | `grafana/` | Grafana 12 | Source de données et dashboard provisionnés automatiquement |
| MCP | `docker-compose.yml` | `grafana/mcp-grafana` 2.2.0 | Accès des clients MCP au dashboard et aux requêtes |
| Chatbot | `chatbot/` | Next.js 16, AI SDK 7 | Interface de questions-réponses |
| Documentation | `docs/` | VitePress | Ce site |

## Modèle de données

Table `items` : une ligne par actualité.

| Colonne | Contenu |
| --- | --- |
| `source`, `category` | `certfr` / `cyber` ou `eurlex` / `reglementaire` |
| `external_id` | identifiant officiel (URL de l'avis CERT-FR, numéro CELEX) : **clé de déduplication** |
| `title`, `url`, `published_at` | titre, **lien vers la source officielle**, date de publication |
| `description` | texte d'origine du flux (permet de réanalyser) |
| `summary`, `rationale` | résumé et justification du niveau |
| `risk_level`, `risk_score` | `faible`=1, `moyen`=2, `élevé`=3, `critique`=4 |
| `method` | `llm:<modèle>`, `regles` ou `regles (repli LLM)` : traçabilité de l'analyse |

Table `collection_runs` : une ligne par collecte et par source (lues, nouvelles, erreur). Affichée dans le panneau « Santé de l'agent ».

## Sécurité

- **Moindre privilège** : l'agent est le seul à écrire. Grafana, le MCP et le chatbot utilisent `grc_reader`, rôle PostgreSQL dont **toutes les transactions sont en lecture seule** (`default_transaction_read_only`).
- **MCP** : compte Grafana de rôle *Viewer*, outils d'écriture désactivés (`--disable-write`), seuls les outils nécessaires activés.
- **Chatbot** : les outils PostgreSQL sont des requêtes fixes et paramétrées ; le texte du modèle est affiché sans HTML brut.
- **Secrets** : uniquement dans `.env`, exclu de Git.
