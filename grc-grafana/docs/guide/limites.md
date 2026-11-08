# Limites et dépannage

## Limites connues

- **Règles sans LLM** : classement par mots-clés, explicable mais grossier (un avis sans exécution de code à distance est au plus « moyen »). Le LLM nuance davantage.
- **Contexte de l'organisation** : le niveau de risque est générique. Il ne tient pas compte du parc réel (un avis sur un produit non utilisé reste classé). Piste : un inventaire des actifs à croiser avec les produits cités.
- **EUR-Lex** : le flux RSS donne le titre de l'acte, rarement son contenu. L'analyse porte donc sur le titre ; une lecture du texte intégral (via le numéro CELEX) améliorerait le résumé.
- **Historique** : chaque collecte lit les 30 dernières entrées de chaque flux (`MAX_ITEMS_PER_SOURCE`). Une interruption de plusieurs jours peut faire manquer des entrées anciennes.
- **Réanalyse** : `--reanalyze` appelle le LLM pour chaque ligne (coût proportionnel au volume).
- **Chatbot sans LLM** : comprend les trois questions du TP et leurs variantes, pas les questions libres.

## Dépannage

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `port is already allocated` | Port déjà pris sur la machine | Changer `*_PORT` dans `.env` |
| Dashboard vide | Première collecte pas encore faite, ou période trop courte | `docker compose logs agent` ; élargir la période en haut à droite |
| Chatbot : « Serveur MCP Grafana injoignable » | `mcp-grafana` arrêté ou `grafana-init` en échec | `docker compose ps -a`, `docker compose logs grafana-init mcp-grafana` |
| Méthode `regles (repli LLM)` en base | Clé, adresse ou nom de modèle invalide | `docker compose logs agent | grep LLM` affiche l'erreur du fournisseur |
| Ollama injoignable depuis Docker | `localhost` désigne le conteneur | Utiliser `http://host.docker.internal:11434/v1` |
| Mot de passe changé dans `.env` sans effet sur PostgreSQL | Les comptes sont créés au premier démarrage du volume | `docker compose down -v` puis `up -d` (efface les données) |
