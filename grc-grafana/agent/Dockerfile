FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY veille_agent ./veille_agent
# Collecte immédiate au démarrage, puis toutes les COLLECT_INTERVAL_SECONDS (3600 = 1 h).
CMD ["python", "-m", "veille_agent", "--loop"]
