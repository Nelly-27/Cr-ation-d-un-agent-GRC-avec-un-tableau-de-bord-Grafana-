
import os
import unicodedata
import psycopg
from dotenv import load_dotenv

load_dotenv(".env")


def normalize_criticality(value):
    """Normaliser et valider la criticité."""
    criticality = unicodedata.normalize(
        "NFC", str(value or "moyen")
    ).strip().lower()

    criticality = criticality.replace("e\u0301leve\u0301", "\u00e9lev\u00e9")
    criticality = criticality.replace("eleve", "\u00e9lev\u00e9")

    allowed = {"faible", "moyen", "\u00e9lev\u00e9", "critique"}

    if criticality not in allowed:
        print("[AVERTISSEMENT] Criticité invalide :", repr(criticality))
        return "moyen"

    return criticality


def save_articles(articles):
    """Enregistrer les actualités analysées dans PostgreSQL."""

    inserted_count = 0
    updated_count = 0
    skipped_count = 0

    try:
        with psycopg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        ) as connection:

            with connection.cursor() as cursor:

                for article in articles:
                    if not article.get("link"):
                        skipped_count += 1
                        continue

                    criticality = normalize_criticality(
                        article.get("criticality", "moyen")
                    )

                    # Diagnostic temporaire : valeur exacte envoyée à PostgreSQL
                    print(
                        "[DEBUG CRITICITY]",
                        repr(criticality),
                        criticality.encode("utf-8").hex()
                    )

                    cursor.execute(
                        """
                        SELECT
                            %s::varchar IN (
                                'faible',
                                'moyen',
                                convert_from(
                                    decode('c3a96c6576c3a9', 'hex'),
                                    'UTF8'
                                ),
                                'critique'
                            )
                        """,
                        (criticality,)
                    )

                    accepted = cursor.fetchone()[0]
                    print("[DEBUG POSTGRES]", accepted)

                    if not accepted:
                        raise ValueError(
                            f"Criticité refusée avant INSERT : {criticality!r}"
                        )

                    cursor.execute(
                        """
                        INSERT INTO actualites (
                            source, title, link, published_at,
                            original_summary, ai_summary, criticality,
                            category, justification
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (link)
                        DO UPDATE SET
                            source = EXCLUDED.source,
                            title = EXCLUDED.title,
                            published_at = EXCLUDED.published_at,
                            original_summary = EXCLUDED.original_summary,
                            ai_summary = EXCLUDED.ai_summary,
                            criticality = EXCLUDED.criticality,
                            category = EXCLUDED.category,
                            justification = EXCLUDED.justification
                        RETURNING (xmax = 0);
                        """,
                        (
                            article.get("source"),
                            article.get("title", "Sans titre"),
                            article.get("link"),
                            article.get("published", ""),
                            article.get("summary", ""),
                            article.get("ai_summary", ""),
                            criticality,
                            article.get("category"),
                            article.get("justification")
                        )
                    )

                    result = cursor.fetchone()

                    if result[0]:
                        inserted_count += 1
                    else:
                        updated_count += 1

        print("\n[BASE DE DONNEES]")
        print(f"Nouvelles actualités : {inserted_count}")
        print(f"Actualités mises à jour : {updated_count}")
        print(f"Actualités ignorées : {skipped_count}")

        return inserted_count + updated_count

    except Exception as error:
        print(f"\n[ERREUR PostgreSQL] {error}")
        raise
