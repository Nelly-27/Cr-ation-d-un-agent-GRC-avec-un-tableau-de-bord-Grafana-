# Agent de veille

Code : `agent/veille_agent/`.

| Fichier | Rôle |
| --- | --- |
| `sources.py` | Lecture des flux RSS CERT-FR et EUR-Lex |
| `assessment.py` | Résumé et niveau de risque : LLM, ou règles |
| `store.py` | Enregistrement PostgreSQL, déduplication |
| `__main__.py` | Ligne de commande et boucle horaire |

## Sources

| Source | Flux | Ce qui est retenu |
| --- | --- | --- |
| CERT-FR | `https://www.cert.cyber.gouv.fr/feed/` | Alertes, avis, actualités ; lien de l'avis comme identifiant |
| EUR-Lex | `https://eur-lex.europa.eu/FR/display-feed.rss?rssId=162` (législation du Parlement et du Conseil) | Actes, identifiés par leur numéro CELEX ; les rectificatifs qui « ne concernent pas la version française » sont ignorés |

Les adresses sont réglables dans `.env` (`CERTFR_FEED_URL`, `EURLEX_FEED_URL`).

## Exécution planifiée

Le conteneur `agent` lance `python -m veille_agent --loop` : une collecte au démarrage, puis toutes les `COLLECT_INTERVAL_SECONDS` (3600 = **toutes les heures**). Il redémarre automatiquement (`restart: unless-stopped`).

Seules les **nouvelles** entrées sont analysées : une collecte horaire ne repaie pas le LLM pour l'historique. Une source en panne n'empêche pas l'autre ; l'erreur est enregistrée dans `collection_runs`.

## Classement des risques

Avec un LLM, la consigne (`SYSTEM_PROMPT` dans `assessment.py`) définit les 4 niveaux :

| Niveau | Définition |
| --- | --- |
| critique | menace exploitée activement, ou obligation majeure applicable immédiatement |
| élevé | exécution de code à distance, fuite de données probable, nouvelle obligation cyber / données / IA |
| moyen | vulnérabilité limitée (élévation de privilèges, contournement), texte numérique d'impact indirect |
| faible | information, rectificatif, texte sans lien avec la sécurité de l'information |

Sans LLM (ou si sa réponse est invalide), des **règles explicables** s'appliquent : une alerte CERT-FR est critique, une exécution de code à distance est élevée, etc. La justification enregistrée commence par « Règle : ».

## Tests

```bash
cd agent && python -m pytest -q tests
```

Sans réseau ni base : extraits réels des flux dans `tests/fixtures/`, LLM simulé (format de la requête, réponses mal formées, panne → repli sur les règles).
