---
layout: home
hero:
  name: Agent GRC + Grafana
  text: Veille cyber et réglementaire automatisée
  tagline: CERT-FR et EUR-Lex → agent IA → PostgreSQL → Grafana → MCP → chatbot Next.js
  actions:
    - theme: brand
      text: Démarrer en 3 commandes
      link: /guide/demarrage
    - theme: alt
      text: Choisir son modèle de langage
      link: /guide/modele
features:
  - title: Agent de veille Python
    details: Collecte le CERT-FR et EUR-Lex toutes les heures, résume avec un LLM, classe chaque risque (faible, moyen, élevé, critique) et garde le lien officiel.
  - title: Dashboard Grafana
    details: Adapté du modèle Faraday 14608 — nombre de risques, répartition par criticité, dernières actualités réglementaires.
  - title: MCP Grafana en lecture seule
    details: Le serveur MCP officiel retrouve le dashboard, lit ses indicateurs et exécute les requêtes autorisées, sans pouvoir rien modifier.
  - title: Chatbot sourcé
    details: Répond aux trois questions du TP en citant ses sources. Fonctionne avec n'importe quel LLM compatible OpenAI, ou sans LLM.
---
