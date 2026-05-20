import psycopg2
import psycopg2.extras
import os

def get_conn():
    db_url = os.getenv("DB_URL", "postgresql://postgres:7020@localhost:5432/cellsense")
    return psycopg2.connect(db_url)

def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)