# Connexion MCP Grafana

Le serveur MCP **officiel** [grafana/mcp-grafana](https://github.com/grafana/mcp-grafana) (version 2.2.0, figée) tourne dans le conteneur `mcp-grafana`, en transport HTTP « streamable » : <http://localhost:8000/mcp>.

## Accès en lecture seule

Trois verrous indépendants :

1. **Compte Grafana Viewer** `mcp-reader`, créé au démarrage par `grafana/init/create_mcp_user.py` : il ne peut modifier ni dashboard ni réglage.
2. **`--disable-write`** : les outils d'écriture (créer / modifier un dashboard, une alerte…) ne sont pas exposés.
3. **Source PostgreSQL en lecture seule** : `query_sql` est réactivé (`--enable-query`) parce que le compte `grc_reader` refuse toute écriture (`cannot execute DELETE in a read-only transaction`).

Seules les familles d'outils utiles sont activées : `--enabled-tools search,datasource,dashboard,folder,navigation,sql`.

## Vérifier ce qu'un client MCP peut faire

| Exigence du TP | Outil MCP | Résultat attendu |
| --- | --- | --- |
| Retrouver le dashboard | `search_dashboards` (`query: "Veille"`) | `uid: grc-veille` |
| Lire ses indicateurs | `get_dashboard_summary` / `get_dashboard_panel_queries` (`uid: grc-veille`) | titres et requêtes des 11 panneaux |
| Consulter les résultats des requêtes autorisées | `query_sql` (`datasourceUid: grc-postgres`) | lignes de la table `items` |

### Avec Claude Code, Claude Desktop, Cursor…

```json
{
  "mcpServers": {
    "grafana": { "type": "http", "url": "http://localhost:8000/mcp" }
  }
}
```

### Avec l'inspecteur MCP officiel

```bash
npx @modelcontextprotocol/inspector
# Transport : Streamable HTTP — URL : http://localhost:8000/mcp
```

### En ligne de commande

```bash
# ouvre une session et liste les outils
curl -s -D - -X POST http://localhost:8000/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'
```

Le chatbot est lui-même un client MCP : voir [Chatbot](./chatbot).
