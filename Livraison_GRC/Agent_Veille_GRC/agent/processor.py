
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


# Mots-clés liés à la GRC et à la cybersécurité
KEYWORDS = [
    # Vulnérabilités et menaces
    "cybersecurity",
    "cyber security",
    "cybersécurité",
    "cyberattaque",
    "cyber attack",
    "vulnerability",
    "vulnérabilité",
    "ransomware",
    "phishing",
    "malware",

    # Réglementations et conformité numérique
    "NIS2",
    "DORA",
    "GDPR",
    "RGPD",
    "ISO 27001",
    "2022/2555",
    "2019/881",
    "cybersecurity act",
    "cyber resilience act",

    # Sécurité des systèmes d'information
    "information security",
    "network and information security",
    "ICT security",
    "sécurité des systèmes d'information",
    "protection des données",
    "data protection",
    "personal data",
    "données personnelles",

    # Acteurs et organismes spécialisés
    "ENISA",
    "CERT-FR",
    "ANSSI",
    "cyber threat",
    "cyber risk"
]

def normalize_text(text):
    """Uniformiser un texte pour faciliter les comparaisons."""
    text = text or ""
    return re.sub(r"\s+", " ", text).strip().lower()


def normalize_url(url):
    """Normaliser une URL pour repérer les doublons."""
    if not url:
        return ""

    try:
        parts = urlsplit(url)
        query = sorted(
            (key, value)
            for key, value in parse_qsl(parts.query)
            if key.lower() not in ["utm_source", "utm_medium", "utm_campaign"]
        )

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(query),
            ""
        ))
    except ValueError:
        return url.strip()


def is_relevant(article):
    """Vérifier si une actualité concerne la GRC."""
    text = normalize_text(
        article.get("title", "") + " " +
        article.get("summary", "")
    )

    return any(keyword.lower() in text for keyword in KEYWORDS)


def remove_duplicates(articles):
    """Supprimer les doublons en utilisant les URL et les titres."""

    unique_articles = []
    seen_urls = set()
    seen_titles = set()

    for article in articles:
        url = normalize_url(article.get("link", ""))
        title = normalize_text(article.get("title", ""))

        if url and url in seen_urls:
            continue

        if title and title in seen_titles:
            continue

        if url:
            seen_urls.add(url)

        if title:
            seen_titles.add(title)

        unique_articles.append(article)

    return unique_articles


def process_articles(articles):
    """Filtrer les actualités et supprimer les doublons."""

    print("\n[TRAITEMENT] Nettoyage des actualités...")

    filtered_articles = [
        article for article in articles
        if is_relevant(article)
    ]

    unique_articles = remove_duplicates(filtered_articles)

    print(f"[INFO] Actualités collectées : {len(articles)}")
    print(f"[INFO] Actualités pertinentes : {len(filtered_articles)}")
    print(f"[INFO] Actualités sans doublons : {len(unique_articles)}")

    return unique_articles
