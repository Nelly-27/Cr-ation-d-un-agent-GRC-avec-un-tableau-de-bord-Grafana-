# Chatbot

<http://localhost:3100> — code dans `chatbot/` (Next.js 16, AI SDK 7).

Trois boutons posent les questions du TP :

1. Quels sont les risques cyber les plus importants ?
2. Quelles nouvelles réglementations devons-nous surveiller ?
3. Quels risques devons-nous traiter en priorité ?

**Chaque réponse se termine par ses sources** : liens officiels CERT-FR / EUR-Lex et lien du dashboard Grafana.

## Deux modes

| | Sans LLM (par défaut) | Avec LLM |
| --- | --- | --- |
| Déclenchement | `LLM_BASE_URL` vide | `LLM_BASE_URL` + `LLM_MODEL` (ou `CHAT_MODEL`) renseignés |
| Données | Requêtes PostgreSQL + MCP Grafana (`search_dashboards`, `query_sql`) | Le modèle choisit lui-même ses outils |
| Réponse | Liste structurée, construite par le code | Rédigée par le modèle |
| Questions acceptées | Les trois questions du TP (et variantes) | Questions libres |

Dans les deux cas, le chatbot passe **par le MCP Grafana** : le mode sans LLM retrouve le dashboard et lit les compteurs par criticité via MCP. L'interface indique les outils appelés (« MCP Grafana · search_dashboards », « PostgreSQL · risques_prioritaires »).

## Outils donnés au modèle

| Outil | Origine | Contenu |
| --- | --- | --- |
| `risques_cyber_majeurs` | PostgreSQL | CERT-FR, du plus grave au plus récent |
| `nouvelles_reglementations` | PostgreSQL | EUR-Lex, du plus pertinent au plus récent |
| `risques_prioritaires` | PostgreSQL | élevé ou critique, 30 derniers jours |
| `search_dashboards`, `get_dashboard_summary`, `get_dashboard_panel_queries`, `list_datasources`, `query_sql`, `generate_deeplink` | MCP Grafana | dashboard et données via Grafana |

La consigne système (`app/api/chat/route.ts`) impose : ne rien affirmer qui ne vienne d'un outil, et terminer par une section « Sources ».

## Tests

```bash
cd chatbot && npm test && npm run typecheck
```
