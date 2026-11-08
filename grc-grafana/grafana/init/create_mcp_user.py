"""Crée (ou remet à jour) le compte Grafana « Viewer » utilisé par le serveur MCP.

Un Viewer peut lire les dashboards et exécuter leurs requêtes, mais ne peut rien modifier :
c'est l'accès en lecture seule demandé par le TP. Lancé une fois par docker compose.
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

GRAFANA = os.environ.get("GRAFANA_URL", "http://grafana:3000")
ADMIN = base64.b64encode(f"{os.environ['GRAFANA_ADMIN_USER']}:{os.environ['GRAFANA_ADMIN_PASSWORD']}".encode()).decode()
LOGIN = os.environ["GRAFANA_MCP_USER"]
PASSWORD = os.environ["GRAFANA_MCP_PASSWORD"]


def call(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"{GRAFANA}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": f"Basic {ADMIN}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"{}")


for _ in range(60):
    try:
        if call("GET", "/api/health")[0] == 200:
            break
    except OSError:
        pass
    time.sleep(2)
else:
    sys.exit("Grafana ne répond pas")

status, user = call("GET", f"/api/users/lookup?loginOrEmail={LOGIN}")
if status == 404:
    status, created = call("POST", "/api/admin/users", {"name": "Serveur MCP (lecture seule)", "login": LOGIN, "password": PASSWORD})
    if status != 200:
        sys.exit(f"Création du compte {LOGIN} impossible : {status} {created}")
    user_id = created["id"]
else:
    user_id = user["id"]
    call("PUT", f"/api/admin/users/{user_id}/password", {"password": PASSWORD})

status, res = call("PATCH", f"/api/orgs/1/users/{user_id}", {"role": "Viewer"})
if status != 200:
    sys.exit(f"Attribution du rôle Viewer impossible : {status} {res}")
print(f"Compte Grafana « {LOGIN} » prêt (rôle Viewer, lecture seule).")
