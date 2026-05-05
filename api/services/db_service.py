import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()  # Încărcăm variabilele din .env


def extrage_filtre_din_db() -> str:
    """
    Se conectează la TiDB Cloud, extrage tabela filters și returnează un string.
    """
    try:
        # Preluam portul în siguranță (dacă lipsește din env, folosim 4000)
        port_env = os.getenv("DB_PORT", 4000)

        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(port_env),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
            ssl_disabled=False,
            ssl_verify_cert=False,
            ssl_verify_identity=False
        )

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM filters;")
        filtre_db = cursor.fetchall()

        cursor.close()
        conn.close()

        # Transformăm dicționarul primit din DB în formatul cerut de prompt
        text_filtre = "\n".join([f"{f['id']}: {f['name']}" for f in filtre_db])
        return text_filtre

    except Exception as err:
        print(f"Eroare la baza de date: {err}")
        return ""