import psycopg2

CLOUD_DB = "postgresql://postgres:CellSense2026@db.qjhpatciiitdwputpqjk.supabase.co:5432/postgres"

conn = psycopg2.connect(CLOUD_DB)
conn.autocommit = True
cur = conn.cursor()

print("Creating spatial index...")
cur.execute("SET statement_timeout = '300000';")  # 5 minutes
cur.execute("CREATE INDEX IF NOT EXISTS idx_towers_geom ON towers USING GIST(geom);")
print("Spatial index done.")

cur.execute("CREATE INDEX IF NOT EXISTS idx_towers_state ON towers(state_circle);")
print("State index done.")

cur.execute("CREATE INDEX IF NOT EXISTS idx_towers_operator ON towers(operator);")
print("Operator index done.")

cur.close()
conn.close()
print("All indexes created.")