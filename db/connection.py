import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "cellsense",
    "user":     "postgres",
    "password": "7020"
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
