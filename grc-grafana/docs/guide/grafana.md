# Dashboard Grafana

Ouvrez <http://localhost:3300> : le dashboard **« Veille GRC – risques et réglementation »** est la page d'accueil.

Tout est **provisionné** au démarrage, sans clic :

- `grafana/provisioning/datasources/postgres.yml` : source PostgreSQL (`uid: grc-postgres`), compte lecture seule ;
- `grafana/provisioning/dashboards/provider.yml` + `grafana/dashboards/veille-grc.json` : le dashboard.

## Adaptation du modèle Faraday (14608)

Le TP impose le modèle [Vulnerability Dashboard (Faraday)](https://grafana.com/grafana/dashboards/14608-vulnerability-faraday/). Nous avons gardé sa structure et l'avons branché sur nos données :

| Modèle Faraday | Notre dashboard |
| --- | --- |
| Rangée de compteurs Critical / High / Medium / Low / Hosts | **Risques détectés**, Critique, Élevé, Moyen, Faible, Dernière collecte |
| Graphe « Vulnerabilities in scope » par sévérité | **Risques par criticité dans le temps** (barres empilées) |
| Camemberts par sévérité | **Répartition par criticité** |
| — | **Dernières actualités réglementaires** (EUR-Lex), titre cliquable vers la source |
| — | **Risques cyber les plus importants** (CERT-FR), triés par criticité |
| — | **Santé de l'agent** (dernières collectes, erreurs) |

Les panneaux d'origine (`singlestat`, `graph`, `grafana-piechart-panel`) sont des types obsolètes, retirés des versions récentes de Grafana : ils ont été remplacés par leurs équivalents actuels (`stat`, `timeseries`, `piechart`, `table`). Les requêtes Faraday (tables `host`, `vulnerability`) ont été réécrites sur la table `items`.

Les panneaux suivent la période choisie en haut à droite (90 derniers jours par défaut).

## Modifier le dashboard

Le fichier JSON est la référence (`allowUiUpdates: false`). Pour le modifier : faites vos changements dans Grafana, « Export → JSON », remplacez `grafana/dashboards/veille-grc.json`, puis `docker compose restart grafana`.
