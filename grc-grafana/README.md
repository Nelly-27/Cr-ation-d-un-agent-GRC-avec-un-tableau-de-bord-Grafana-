# Agent GRC avec tableau de bord Grafana

Un robot qui **lit chaque heure les alertes de cybersécurité (CERT-FR) et les nouveaux textes européens (EUR-Lex)**, les résume, leur donne un niveau de risque (faible, moyen, élevé, critique), les range dans une base de données, les affiche dans un **tableau de bord Grafana**, et répond à vos questions dans un **chatbot**.

```
CERT-FR + EUR-Lex → Agent (Python) → PostgreSQL → Grafana → MCP Grafana → Chatbot (Next.js)
```

> TP « Création d'un agent GRC avec un tableau de bord Grafana » — EPITA Lab GRC 2026.

---

## ✅ Étape 1 — Installer Docker (une seule fois)

Docker fait tourner tout le projet : **vous n'avez rien d'autre à installer** (ni Python, ni Node.js, ni base de données).

1. Téléchargez **Docker Desktop** : <https://www.docker.com/products/docker-desktop/>
2. Installez-le et **ouvrez-le**. Attendez que l'icône de la baleine 🐳 indique « Docker Desktop is running ».
3. Vérifiez qu'il reste **au moins 10 Go libres** sur votre disque.

## ✅ Étape 2 — Ouvrir un terminal dans le dossier du projet

1. Décompressez le zip (vous obtenez un dossier `grc-grafana`).
2. Ouvrez un terminal :
   - **Mac** : application « Terminal ».
   - **Windows** : « PowerShell ».
3. Allez dans le dossier. Le plus simple : tapez `cd ` (avec l'espace), **glissez le dossier `grc-grafana` dans la fenêtre du terminal**, puis appuyez sur Entrée.

Pour vérifier : la commande `ls` (Mac) ou `dir` (Windows) doit afficher `docker-compose.yml` et `README.md`.

## ✅ Étape 3 — Créer le fichier de configuration

Copiez-collez cette commande, puis Entrée :

**Mac / Linux**
```bash
cp .env.example .env
```

**Windows (PowerShell)**
```powershell
Copy-Item .env.example .env
```

👉 **C'est tout : le projet marche déjà sans rien modifier.** (Sans clé d'IA, il classe les risques avec des règles simples. Pour brancher une IA, voir l'étape 6.)

## ✅ Étape 4 — Lancer

```bash
docker compose up -d --build
```

⏳ La **première fois, comptez 3 à 5 minutes** (téléchargements). Les fois suivantes : quelques secondes.

Vérifiez que tout tourne :

```bash
docker compose ps
```

Vous devez voir **5 lignes « running »** : `postgres`, `agent`, `grafana`, `mcp-grafana`, `chatbot`.
(`grafana-init` en « exited » est **normal** : il prépare un compte puis s'arrête.)

## ✅ Étape 5 — Ouvrir et utiliser

| Quoi | Ouvrir dans le navigateur | Identifiant / mot de passe |
| --- | --- | --- |
| 📊 **Tableau de bord** | <http://localhost:3300> | aucun (consultation libre). Pour administrer : « S'inscrire / Se connecter » en haut à droite, `admin` / `change-me-admin` |
| 💬 **Chatbot** | <http://localhost:3100> | aucun |

**Ce que vous devez voir :**

- **Tableau de bord** : des compteurs colorés (Critique, Élevé, Moyen, Faible), un graphique, un camembert, puis les dernières actualités. Cliquez sur un titre pour ouvrir le texte officiel.
  *Vide ?* Attendez 30 secondes puis rechargez la page (la première collecte est en cours).
- **Chatbot** : cliquez sur une des trois questions proposées. La réponse liste les risques et se termine par **« Sources »** avec les liens officiels et le lien du tableau de bord.

L'agent recommence la collecte **automatiquement toutes les heures** tant que Docker tourne.

---

## 🤖 Étape 6 (facultative) — Brancher une IA

Sans IA, tout fonctionne. Avec une IA, les résumés et les réponses du chatbot sont rédigés par le modèle.

**N'importe quel fournisseur marche.** Il suffit de remplir **3 lignes** dans le fichier `.env`.

### 1. Ouvrir le fichier `.env`

Il est dans le dossier du projet. Il peut être **invisible** car son nom commence par un point :
- **Mac** : dans le Finder, appuyez sur `Cmd + Maj + .` pour afficher les fichiers cachés, puis ouvrez `.env` avec TextEdit. Ou dans le terminal : `open -e .env`
- **Windows** : dans le terminal : `notepad .env`

### 2. Remplir les 3 lignes

Repérez ces lignes (vides au départ) :

```ini
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

Remplacez-les par **le bloc de votre fournisseur** :

| Fournisseur | Où obtenir la clé | À mettre dans `.env` |
| --- | --- | --- |
| **Claude** (Anthropic) | <https://console.anthropic.com> → API Keys | `LLM_BASE_URL=https://api.anthropic.com/v1`<br>`LLM_API_KEY=sk-ant-…votre clé…`<br>`LLM_MODEL=claude-haiku-5-5` |
| **ChatGPT** (OpenAI) | <https://platform.openai.com/api-keys> | `LLM_BASE_URL=https://api.openai.com/v1`<br>`LLM_API_KEY=sk-…votre clé…`<br>`LLM_MODEL=gpt-5-mini` |
| **Mistral** | <https://console.mistral.ai> → API Keys | `LLM_BASE_URL=https://api.mistral.ai/v1`<br>`LLM_API_KEY=…votre clé…`<br>`LLM_MODEL=mistral-small-latest` |
| **Gemini** (Google) | <https://aistudio.google.com/apikey> | `LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai`<br>`LLM_API_KEY=…votre clé…`<br>`LLM_MODEL=gemini-2.5-flash` |
| **Ollama** (gratuit, sur votre ordinateur, sans clé) | Installez <https://ollama.com>, puis dans un terminal : `ollama pull qwen3:8b` | `LLM_BASE_URL=http://host.docker.internal:11434/v1`<br>`LLM_API_KEY=ollama`<br>`LLM_MODEL=qwen3:8b` |
| **Autre** (Groq, OpenRouter, Azure…) | site du fournisseur | l'adresse de son API « compatible OpenAI » (finit souvent par `/v1`), votre clé, le nom du modèle |

⚠️ **Règles importantes :**
- Pas d'espace autour du `=`, pas de guillemets.
- Le **nom du modèle** doit être **exactement** celui affiché par le fournisseur (les catalogues changent : vérifiez sur son site).
- Ne partagez jamais votre fichier `.env` : il contient votre clé.

### 3. Appliquer

Enregistrez le fichier, puis dans le terminal :

```bash
docker compose up -d
```

Optionnel — refaire l'analyse des actualités déjà collectées avec l'IA :

```bash
docker compose run --rm agent python -m veille_agent --reanalyze
```

### 4. Vérifier que l'IA est utilisée

- Le **chatbot** affiche en haut « modèle `<nom du modèle>` » au lieu de « mode sans LLM ».
- Dans le terminal :
  ```bash
  docker compose logs agent
  ```
  la ligne « Collecte – mode d'analyse » doit afficher `LLM <nom du modèle>` (et non « règles (sans LLM) »).

**Ça ne marche pas ?** L'agent continue avec ses règles (rien ne casse). Pour voir l'erreur du fournisseur (clé invalide, nom de modèle faux…), lancez `docker compose logs agent` et cherchez la ligne « LLM indisponible ».

💡 Option : `CHAT_MODEL=` permet de donner au chatbot un modèle plus puissant que l'agent (ex. `claude-sonnet-5-5`). Vide = même modèle.

---

## 🔧 Autres réglages du `.env` (facultatif)

| Ligne | Sert à | Par défaut |
| --- | --- | --- |
| `GRAFANA_ADMIN_PASSWORD` | Mot de passe administrateur de Grafana | `change-me-admin` |
| `GRAFANA_ANONYMOUS` | `false` = connexion obligatoire même pour regarder | `true` |
| `COLLECT_INTERVAL_SECONDS` | Fréquence de collecte | `3600` (1 heure) |
| `GRAFANA_PORT`, `CHATBOT_PORT`, `MCP_PORT`, `POSTGRES_PORT` | Adresses `localhost:…` | 3300, 3100, 8000, 5433 |
| `POSTGRES_PASSWORD`, `POSTGRES_READER_PASSWORD`, `GRAFANA_MCP_PASSWORD` | Mots de passe internes | `change-me-…` |

⚠️ Les mots de passe sont créés **au tout premier lancement**. Pour les changer ensuite : `docker compose down -v` (⚠️ efface les données collectées), modifier `.env`, puis `docker compose up -d --build`.

Après toute modification du `.env` : `docker compose up -d`.

---

## 🧰 Commandes utiles

| Je veux… | Commande |
| --- | --- |
| Arrêter (les données sont gardées) | `docker compose down` |
| Relancer | `docker compose up -d` |
| Voir ce que fait l'agent | `docker compose logs -f agent` (Ctrl+C pour sortir) |
| Forcer une collecte maintenant | `docker compose run --rm agent python -m veille_agent` |
| Tout effacer et repartir de zéro | `docker compose down -v` puis `docker compose up -d --build` |

## 🆘 Problèmes fréquents

| Message / symptôme | Solution |
| --- | --- |
| `Cannot connect to the Docker daemon` | Docker Desktop n'est pas ouvert : lancez-le et attendez « running ». |
| `port is already allocated` | Un autre logiciel utilise ce port : changez `GRAFANA_PORT` ou `CHATBOT_PORT` dans `.env` (ex. 3301), puis `docker compose up -d`. Utilisez ensuite la nouvelle adresse. |
| `no space left on device` ou Docker figé | Disque plein : libérez au moins 10 Go, redémarrez Docker Desktop. |
| Tableau de bord vide | Attendez 30 s et rechargez. Sinon : `docker compose logs agent`. |
| Chatbot : « Serveur MCP Grafana injoignable » | `docker compose ps -a` : `grafana-init` doit être « Exited (0) ». Sinon `docker compose up -d`. |
| `.env.example` introuvable | Vous n'êtes pas dans le bon dossier : refaites l'étape 2. |

---

## 🔌 Connecter un assistant IA au MCP Grafana (pour la démo du TP)

Le serveur MCP officiel de Grafana tourne sur `http://localhost:8000/mcp`, **en lecture seule**. Dans Claude Desktop, Claude Code, Cursor… ajoutez :

```json
{ "mcpServers": { "grafana": { "type": "http", "url": "http://localhost:8000/mcp" } } }
```

Puis demandez par exemple : « Trouve le dashboard Veille GRC et donne-moi le nombre de risques par criticité. »
Il utilisera `search_dashboards`, `get_dashboard_summary` et `query_sql`. Toute modification est refusée.

---

## 📚 Pour aller plus loin

- **Documentation complète** (site VitePress) : nécessite Node.js 22+
  ```bash
  cd docs && npm install && npm run dev
  ```
  puis <http://localhost:5173>. Les pages sont aussi lisibles directement dans `docs/guide/`.
- **Ce que demande le TP, et où c'est fait :**

| Exigence | Où |
| --- | --- |
| Agent Python CERT-FR + EUR-Lex, résumé LLM, 4 niveaux de risque | `agent/` |
| PostgreSQL avec liens sources | `db/init.sh` (colonne `url`) |
| Dashboard Grafana (modèle Faraday 14608 adapté) | `grafana/dashboards/veille-grc.json` |
| MCP Grafana officiel en lecture seule | service `mcp-grafana` dans `docker-compose.yml` |
| Chatbot Next.js, 3 questions, réponses sourcées | `chatbot/` |
| Collecte automatique toutes les heures | service `agent` (`COLLECT_INTERVAL_SECONDS=3600`) |
| Documentation VitePress | `docs/` |

- **Tests** (Python 3.11+ et Node.js 22+) :
  ```bash
  python3 -m venv .venv && source .venv/bin/activate && pip install -r agent/requirements.txt pytest
  (cd agent && python -m pytest -q tests)
  (cd chatbot && npm install && npm test)
  ```
- `.claude/skills/` et `AGENTS.md` : 60 compétences GRC pour assistants de code, issues du dépôt du TP [scortalabs/epitalab](https://github.com/scortalabs/epitalab).
