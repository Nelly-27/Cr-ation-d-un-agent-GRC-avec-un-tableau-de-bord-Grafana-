
import os
import psycopg
from dotenv import load_dotenv

# Charger les paramètres du fichier .env
load_dotenv()

try:
    # Connexion à PostgreSQL
    connection = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    print("Connexion à PostgreSQL réussie !")

    # Vérifier la base utilisée
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database();")
        database = cursor.fetchone()
        print("Base connectée :", database[0])

    connection.close()

except Exception as error:
    print("Erreur de connexion :", error)
