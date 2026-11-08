
from agent.ai_analyzer import analyze_article

article_test = {
    "source": "CERT-FR",
    "title": "Exemple de vulnérabilité dans un logiciel",
    "summary": (
        "Une vulnérabilité a été découverte dans un logiciel. "
        "Elle pourrait permettre à un attaquant distant "
        "d'exécuter du code sur un système vulnérable."
    )
}

result = analyze_article(article_test)

print("\n========== RESULTAT DU TEST ==========")

for key, value in result.items():
    print(f"\n{key} : {value}")

print("\n========== FIN DU TEST ==========")
