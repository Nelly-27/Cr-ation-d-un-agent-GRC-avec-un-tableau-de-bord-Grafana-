# Démonstration

Scénario de 5 minutes montrant la chaîne complète :
**Sources → Agent IA → PostgreSQL → Grafana → MCP → Chatbot Next.js**.

1. **Démarrage** : `docker compose up -d --build`, puis `docker compose ps` (6 services, `grafana-init` terminé).
2. **Sources → Agent** : `docker compose logs agent` montre le mode d'analyse, puis « certfr : 30 lue(s), N nouvelle(s) » et « eurlex : … ».
3. **Agent → PostgreSQL** :
   ```bash
   docker compose exec postgres psql -U grc_agent -d grc \
     -c "SELECT source, risk_level, count(*) FROM items GROUP BY 1, 2 ORDER BY 1, 2"
   ```
4. **PostgreSQL → Grafana** : ouvrir <http://localhost:3300>. Montrer les compteurs, la répartition, cliquer un titre EUR-Lex (ouvre le texte officiel).
5. **Grafana → MCP** : dans un client MCP (inspecteur ou Claude), appeler `search_dashboards` puis `query_sql` (voir [Connexion MCP](./mcp)).
6. **MCP → Chatbot** : ouvrir <http://localhost:3100>, cliquer les trois questions. Montrer les sources et le lien du dashboard « trouvé via MCP Grafana ».
7. **Planification** : `docker compose logs agent | grep "Prochaine collecte"` → toutes les 3600 s ; panneau « Santé de l'agent ».
8. **Changement de modèle** (si une clé est disponible) : renseigner `LLM_*` dans `.env`, `docker compose up -d`, puis `--reanalyze` ; la colonne `method` passe à `llm:<modèle>`.
