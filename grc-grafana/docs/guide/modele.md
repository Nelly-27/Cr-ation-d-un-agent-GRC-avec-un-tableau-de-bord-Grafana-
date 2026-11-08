# Choisir le modèle de langage

Le projet n'est lié à **aucun fournisseur**. L'agent et le chatbot utilisent l'API « chat completions » **compatible OpenAI**, proposée par la quasi-totalité des fournisseurs et des serveurs locaux. Changer de modèle = changer **trois lignes** du fichier `.env`, sans toucher au code.

```ini
LLM_BASE_URL=   # adresse de l'API, se termine en général par /v1
LLM_API_KEY=    # clé du fournisseur (n'importe quelle valeur pour Ollama)
LLM_MODEL=      # nom exact du modèle chez ce fournisseur
```

Puis :

```bash
docker compose up -d                                              # prend en compte le nouveau .env
docker compose run --rm agent python -m veille_agent --reanalyze  # facultatif : réanalyser l'existant
```

## Exemples prêts à copier

::: code-group

```ini [Anthropic (Claude)]
LLM_BASE_URL=https://api.anthropic.com/v1
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-haiku-5-5
```

```ini [OpenAI]
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-5-mini
```

```ini [Mistral]
LLM_BASE_URL=https://api.mistral.ai/v1
LLM_API_KEY=...
LLM_MODEL=mistral-small-latest
```

```ini [Google Gemini]
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_API_KEY=...
LLM_MODEL=gemini-2.5-flash
```

```ini [Ollama (local, gratuit)]
# 1. installer Ollama (https://ollama.com), puis : ollama pull qwen3:8b
# 2. depuis Docker, la machine hôte s'appelle host.docker.internal
LLM_BASE_URL=http://host.docker.internal:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen3:8b
```

:::

::: warning Noms de modèles
Les noms ci-dessus sont des exemples : les catalogues évoluent souvent. Vérifiez le nom exact sur la page « modèles » de votre fournisseur. Un nom invalide ne bloque rien : l'agent se replie sur ses règles (méthode `regles (repli LLM)` en base) et le chatbot affiche l'erreur renvoyée par le fournisseur.
:::

Tout autre service compatible fonctionne de la même façon : Groq, OpenRouter, Azure OpenAI, vLLM, LM Studio, un serveur interne…

## Un modèle différent pour le chatbot

Le chatbot doit savoir **appeler des outils** (MCP Grafana, PostgreSQL). Les petits modèles résument bien mais utilisent parfois mal les outils. Vous pouvez donc garder un modèle économique pour l'agent et un modèle plus capable pour le chatbot :

```ini
LLM_MODEL=claude-haiku-5-5      # agent : un appel court par actualité
CHAT_MODEL=claude-sonnet-5-5    # chatbot : raisonnement + outils
```

Sans `CHAT_MODEL`, le chatbot utilise `LLM_MODEL`.

## Ce qui est envoyé au modèle

- **Agent** : un seul appel par **nouvelle** actualité (titre, lien, texte du flux). Demande volontairement minimale (`model` + `messages`, sans température ni limite de jetons) : ce sont ces paramètres que certains fournisseurs refusent. La réponse attendue est un petit objet JSON ; elle est validée (niveau parmi les 4 autorisés, résumé non vide), sinon l'agent utilise ses règles.
- **Chatbot** : la conversation et la liste des outils. Le modèle ne voit que ce que les outils lui renvoient (base en lecture seule, Grafana en lecture seule).

Les données envoyées sont des publications officielles et publiques (CERT-FR, EUR-Lex) : aucune donnée interne de l'organisation ne quitte la machine. Pour un traitement 100 % local, utilisez Ollama.

## Vérifier quel mode est actif

- Agent : `docker compose logs agent | grep "mode d'analyse"`
- Chatbot : l'en-tête de la page affiche le modèle, ou « mode sans LLM ».
- Base : la colonne `method` vaut `llm:<modèle>`, `regles` ou `regles (repli LLM)`.
