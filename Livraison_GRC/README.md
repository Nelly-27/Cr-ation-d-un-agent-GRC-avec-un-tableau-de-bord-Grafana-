# TP – Agent GRC et tableau de bord Grafana

## Présentation
Solution de veille réglementaire et cybersécurité utilisant CERT-FR, EUR-Lex, Python, Ollama, PostgreSQL et Grafana.

## Architecture
- Collecte : CERT-FR et EUR-Lex.
- Traitement : agent Python.
- Intelligence artificielle : Ollama, modèle qwen2.5:3b.
- Stockage : PostgreSQL.
- Visualisation : Grafana Cloud.
- Interopérabilité : serveur MCP Grafana en lecture seule.
- Interface conversationnelle : chatbot Next.js.

## Résultats de l'agent
- 140 articles collectés.
- 54 articles retenus après filtrage.
- 42 analyses réutilisées depuis le cache.
- 12 nouvelles analyses.
- 0 classification provisoire.

## Tableau de bord
Dashboard : https://cosmicmallard3261.grafana.net/d/BQnjzl-iz/dashboard-grc-veille-reglementaire

Le tableau de bord présente le nombre d'articles, leur criticité et les actualités récentes. Son export JSON est fourni dans le dossier Dashboard.

## MCP Grafana
Les tests MCP Inspector ont confirmé la recherche du dashboard et l'exécution de requêtes sur les panneaux. Le serveur a été testé en lecture seule avec --disable-write.

## Chatbot
Application Next.js permettant d'interroger les informations du projet. Lancement avec npm.cmd install puis npm.cmd run dev.

## Limite technique
L'analyse des 54 articles a fonctionné, mais leur insertion dans PostgreSQL a échoué sur une contrainte CHECK de la colonne criticality. La base conserve donc les 66 enregistrements précédents.

## Captures
- Captures/01-dashboard.png
- Captures/02-chatbot.png
- Captures/03-mcp.png
- Captures/04-agent.png

## Sécurité
Ne pas publier les fichiers .env, les clés API, les mots de passe, les dossiers venv, node_modules ou .next.
