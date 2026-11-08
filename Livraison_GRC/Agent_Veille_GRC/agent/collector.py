
import os
import calendar
import requests
import feedparser

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timezone


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

SOURCES = {
    "CERT-FR": "https://www.cert.ssi.gouv.fr/feed/",
    "EUR-Lex": os.getenv("EUR_LEX_RSS_URL", "")
}

HEADERS = {
    "User-Agent": "AgentVeilleGRC/1.0 (veille documentaire)"
}

# Nombre maximum de pages complémentaires à consulter
MAX_PAGE_FETCHES = 20


# ============================================================
# NETTOYAGE HTML
# ============================================================

def clean_html(content):
    """Convertir un contenu HTML en texte lisible."""

    soup = BeautifulSoup(content or "", "html.parser")

    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    return " ".join(
        soup.get_text(separator=" ", strip=True).split()
    )


# ============================================================
# EXTRACTION DU CONTENU DES PAGES
# ============================================================

def extract_page_content(url):
    """
    Récupérer le contenu d'une page officielle lorsque
    le flux RSS ne fournit pas de résumé exploitable.
    """

    if not url:
        return ""

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=8
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        # Supprimer les éléments inutiles.
        for element in soup([
            "script",
            "style",
            "noscript",
            "nav",
            "footer",
            "header"
        ]):
            element.decompose()

        # Sélecteurs possibles selon la structure des sites.
        selectors = [
            "#document1",
            "#PP1Contents",
            "main",
            "article",
            "[role='main']",
            "body"
        ]

        candidates = []

        for selector in selectors:

            element = soup.select_one(selector)

            if element:
                text = " ".join(
                    element.get_text(
                        separator=" ",
                        strip=True
                    ).split()
                )

                if len(text) > 200:
                    candidates.append(text)

        if not candidates:
            return ""

        # Retenir le contenu le plus complet.
        content = max(candidates, key=len)

        return content[:6000]

    except requests.RequestException as error:

        print(
            f"[INFO] Page non récupérée : {error}"
        )

        return ""

    except Exception as error:

        print(
            f"[INFO] Extraction impossible : {error}"
        )

        return ""


# ============================================================
# COLLECTE RSS
# ============================================================

def collect_feed(source_name, feed_url):
    """Récupérer les actualités d'un flux RSS."""

    articles = []

    if not feed_url:

        print(
            f"[INFO] Flux {source_name} non configuré."
        )

        return articles

    print(
        f"\n[COLLECTE] Lecture de {source_name}..."
    )

    try:

        response = requests.get(
            feed_url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        feed = feedparser.parse(response.content)

        if feed.bozo and not feed.entries:

            print(
                f"[ERREUR] Flux RSS invalide : {source_name}"
            )

            return articles

        page_fetches = 0

        for entry in feed.entries:

            # ------------------------------------------------
            # INFORMATIONS DE BASE
            # ------------------------------------------------

            title = entry.get(
                "title",
                "Sans titre"
            )

            link = entry.get(
                "link",
                ""
            )

            # ------------------------------------------------
            # DATE DE PUBLICATION
            # ------------------------------------------------

            published = entry.get(
                "published",
                ""
            )

            if (
                not published
                and entry.get("published_parsed")
            ):

                timestamp = calendar.timegm(
                    entry.published_parsed
                )

                published = datetime.fromtimestamp(
                    timestamp,
                    tz=timezone.utc
                ).isoformat()

            # ------------------------------------------------
            # RESUME RSS
            # ------------------------------------------------

            raw_summary = entry.get(
                "summary",
                ""
            )

            if (
                not raw_summary
                and entry.get("description")
            ):

                raw_summary = entry.get(
                    "description",
                    ""
                )

            summary = clean_html(raw_summary)

            # ------------------------------------------------
            # COMPLEMENT DU CONTENU DEPUIS LA PAGE OFFICIELLE
            # ------------------------------------------------

            if (
                len(summary) < 100
                and link
                and page_fetches < MAX_PAGE_FETCHES
            ):

                page_fetches += 1

                print(
                    f"[COLLECTE] Récupération du contenu : "
                    f"{title[:65]}"
                )

                page_content = extract_page_content(link)

                if page_content:

                    summary = page_content

                    print(
                        "[OK] Contenu de la page récupéré."
                    )

                else:

                    print(
                        "[INFO] Aucun contenu supplémentaire disponible."
                    )

            # ------------------------------------------------
            # CONSTRUCTION DE L'ARTICLE
            # ------------------------------------------------

            article = {
                "source": source_name,
                "title": title,
                "link": link,
                "published": published,
                "summary": summary
            }

            articles.append(article)

        print(
            f"[OK] {len(articles)} actualité(s) "
            f"récupérée(s) depuis {source_name}."
        )

    except requests.RequestException as error:

        print(
            f"[ERREUR] Impossible de contacter "
            f"{source_name} : {error}"
        )

    except Exception as error:

        print(
            f"[ERREUR] Problème avec "
            f"{source_name} : {error}"
        )

    return articles


# ============================================================
# COLLECTE DE TOUTES LES SOURCES
# ============================================================

def collect_all():
    """Collecter les actualités de toutes les sources."""

    all_articles = []

    for source_name, feed_url in SOURCES.items():

        articles = collect_feed(
            source_name,
            feed_url
        )

        all_articles.extend(articles)

    print(
        f"\n[TOTAL] {len(all_articles)} actualité(s) collectée(s)."
    )

    return all_articles


# ============================================================
# AFFICHAGE DES RESULTATS
# ============================================================

def display_articles(articles):
    """Afficher les résultats de la veille et de l'analyse IA."""

    print("\n" + "=" * 70)

    print(
        "                 RESULTATS DE LA VEILLE GRC"
    )

    print("=" * 70)

    if not articles:

        print(
            "Aucune actualité récupérée."
        )

        return

    for index, article in enumerate(
        articles,
        start=1
    ):

        print(
            f"\nACTUALITE {index}"
        )

        print("-" * 70)

        print(
            f"Source : {article.get('source', '')}"
        )

        print(
            f"Titre : {article.get('title', '')}"
        )

        print(
            f"Date : {article.get('published', '')}"
        )

        print(
            f"Lien : {article.get('link', '')}"
        )

        print("\nRésumé original :")

        print(
            article.get("summary", "")[:500]
            or "Indisponible"
        )

        print("\nAnalyse IA :")

        print(
            article.get(
                "ai_summary",
                "Analyse non effectuée"
            )
        )

        print(
            f"Criticité : "
            f"{article.get('criticality', 'Non classée')}"
        )

        print(
            f"Catégorie : "
            f"{article.get('category', 'Non classée')}"
        )

        print(
            f"Justification : "
            f"{article.get('justification', 'Non disponible')}"
        )

        print("-" * 70)


# ============================================================
# EXECUTION DIRECTE DU COLLECTEUR
# ============================================================

if __name__ == "__main__":

    articles = collect_all()

    display_articles(articles)
