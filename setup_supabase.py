import psycopg2
import psycopg2.extras
import csv
import json
import os
from tqdm import tqdm

# ─── SUPABASE CONNECTION ──────────────────────────────────
CLOUD_DB = "postgresql://postgres:CellSense2026@db.qjhpatciiitdwputpqjk.supabase.co:5432/postgres"

BASE        = r"C:\Users\Rishi Agrawal\Documents\CellSense"
TOWERS_CSV  = BASE + r"\data\towers_cloud.csv"
GEOJSON     = BASE + r"\states_india.geojson"
CSV_5G      = BASE + r"\data\RS_Session_265_AU_1136_1.csv"

BATCH_SIZE  = 1000

def create_tables(cur):
    print("Creating tables...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS towers (
            tower_id        INTEGER PRIMARY KEY,
            operator        VARCHAR(50),
            radio_type      VARCHAR(10),
            frequency_band  INTEGER,
            latitude        DECIMAL(9,6),
            longitude       DECIMAL(9,6),
            geom            GEOGRAPHY(POINT, 4326),
            avg_signal_dbm  INTEGER,
            sample_count    INTEGER,
            range_m         INTEGER,
            state_circle    VARCHAR(50)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS districts (
            district_id         SERIAL PRIMARY KEY,
            district_name       VARCHAR(100),
            state_name          VARCHAR(100),
            population          INTEGER,
            area_sqkm           DECIMAL(10,2),
            towers_5g           INTEGER DEFAULT 0,
            towers_5g_fiberized INTEGER DEFAULT 0,
            geom                GEOGRAPHY(MULTIPOLYGON, 4326)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS trai_qos (
            qos_id              SERIAL PRIMARY KEY,
            operator            VARCHAR(20),
            state_circle        VARCHAR(50),
            quarter             VARCHAR(10),
            avg_download_mbps   DECIMAL(6,2),
            avg_upload_mbps     DECIMAL(6,2),
            call_drop_rate      DECIMAL(5,2),
            complaint_count     INTEGER
        );
    """)

    print("Tables created.")

def create_indexes(cur):
    print("Creating spatial index...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_towers_geom ON towers USING GIST(geom);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_towers_state ON towers(state_circle);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_towers_operator ON towers(operator);")
    print("Indexes created.")

def load_towers(cur, conn):
    print("\nLoading towers...")
    with open(TOWERS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows   = list(reader)

    INSERT = """
        INSERT INTO towers (
            tower_id, operator, radio_type, frequency_band,
            latitude, longitude, geom,
            avg_signal_dbm, sample_count, range_m, state_circle
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s, %s, %s, %s
        ) ON CONFLICT DO NOTHING;
    """

    batch = []
    total = 0

    for row in tqdm(rows, desc="Inserting towers"):
        batch.append((
            int(row['tower_id']),
            row['operator'],
            row['radio_type'],
            int(row['frequency_band'])   if row['frequency_band']   else None,
            float(row['latitude']),
            float(row['longitude']),
            float(row['longitude']),
            float(row['latitude']),
            int(row['avg_signal_dbm'])   if row['avg_signal_dbm']   else None,
            int(row['sample_count'])     if row['sample_count']     else None,
            int(row['range_m'])          if row['range_m']          else None,
            row['state_circle']          if row['state_circle']     else None,
        ))

        if len(batch) >= BATCH_SIZE:
            cur.executemany(INSERT, batch)
            conn.commit()
            total += len(batch)
            batch = []

    if batch:
        cur.executemany(INSERT, batch)
        conn.commit()
        total += len(batch)

    print(f"Towers inserted: {total:,}")

def load_districts(cur, conn):
    print("\nLoading districts...")
    with open(GEOJSON) as f:
        gj = json.load(f)

    STATE_MAP = {
        'Andaman and Nicobar Islands': 'Andaman & Nicobar Island',
        'Jammu and Kashmir':           'Jammu & Kashmir',
        'Delhi':                       'NCT of Delhi',
    }

    INSERT = """
        INSERT INTO districts (district_name, state_name, geom)
        VALUES (%s, %s, ST_Multi(ST_GeomFromGeoJSON(%s))::geography)
        ON CONFLICT DO NOTHING;
    """

    count = 0
    for feature in gj['features']:
        name     = feature['properties'].get('st_nm', 'Unknown')
        name     = STATE_MAP.get(name, name)
        geom_str = json.dumps(feature['geometry'])
        cur.execute(INSERT, (name, name, geom_str))
        count += 1

    conn.commit()

    # Compute area from geometry
    cur.execute("""
        UPDATE districts
        SET area_sqkm = ROUND(
            CAST(ST_Area(geom::geography) / 1000000 AS DECIMAL), 2
        );
    """)
    conn.commit()
    print(f"Districts inserted: {count}")

def load_5g(cur, conn):
    print("\nLoading 5G BTS data...")
    import pandas as pd

    STATE_MAP = {
        'Andaman and Nicobar Islands':              'Andaman & Nicobar Island',
        'Jammu and Kashmir':                        'Jammu & Kashmir',
        'Jammu & Kashmir':                          'Jammu & Kashmir',
        'Laddakh':                                  'Ladakh',
        'Tamilnadu':                                'Tamil Nadu',
        'Delhi':                                    'NCT of Delhi',
        'Chattisgarh':                              'Chhattisgarh',
        'Total':                                    'SKIP',
    }

    df = pd.read_csv(CSV_5G)
    df.columns = ['sl_no', 'state', 'district', 'bts_installed', 'bts_fiberized']
    df['bts_installed'] = pd.to_numeric(df['bts_installed'], errors='coerce').fillna(0).astype(int)
    df['bts_fiberized'] = pd.to_numeric(df['bts_fiberized'], errors='coerce').fillna(0).astype(int)
    df['state'] = df['state'].str.strip()
    df = df[df['state'] != 'Total']

    state_agg = df.groupby('state').agg(
        towers_5g=('bts_installed', 'sum'),
        towers_5g_fiberized=('bts_fiberized', 'sum')
    ).reset_index()

    state_agg['state_mapped'] = state_agg['state'].apply(lambda x: STATE_MAP.get(x, x))

    updated = 0
    for _, row in state_agg.iterrows():
        if row['state_mapped'] == 'SKIP':
            continue
        cur.execute("""
            UPDATE districts
            SET towers_5g = %s, towers_5g_fiberized = %s
            WHERE district_name = %s
        """, (int(row['towers_5g']), int(row['towers_5g_fiberized']), row['state_mapped']))
        if cur.rowcount > 0:
            updated += 1

    conn.commit()
    print(f"5G data updated for {updated} states")

def main():
    print("Connecting to Supabase...")
    conn = psycopg2.connect(CLOUD_DB)
    cur  = conn.cursor()
    print("Connected.\n")

    create_tables(cur)
    conn.commit()

    # create_indexes(cur)
    # conn.commit()

    load_towers(cur, conn)
    load_districts(cur, conn)
    load_5g(cur, conn)

    cur.close()
    conn.close()
    print("\nSupabase setup complete.")

if __name__ == "__main__":
    main()
