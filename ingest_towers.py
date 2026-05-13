import pandas as pd
import psycopg2
from tqdm import tqdm
import json
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "cellsense",
    "user":     "postgres",
    "password": "7020"   # ← change this
}

# Paths — update if your folder is different
PATH_404    = r"C:\Users\Rishi Agrawal\Documents\CellSense\404.csv"
PATH_405    = r"C:\Users\Rishi Agrawal\Documents\CellSense\405.csv"
PATH_MNC    = r"C:\Users\Rishi Agrawal\Documents\CellSense\MCC-MNC India.csv"
PATH_GEOJSON= r"C:\Users\Rishi Agrawal\Documents\CellSense\states_india.geojson"

BATCH_SIZE  = 2000

# ─── STEP 1: Load MNC operator mapping ────────────────────
def load_operator_map():
    df = pd.read_csv(PATH_MNC)
    df.columns = df.columns.str.strip()
    df['mnc'] = df['mnc'].astype(int)
    df['mcc'] = df['mcc'].astype(int)

    op_map = {}
    for _, row in df.iterrows():
        key = (int(row['mcc']), int(row['mnc']))
        op_name = str(row['operator'])

        # Normalize operator names
        if 'jio' in op_name.lower() or 'reliance' in op_name.lower():
            op_map[key] = 'Jio'
        elif 'airtel' in op_name.lower():
            op_map[key] = 'Airtel'
        elif 'bsnl' in op_name.lower():
            op_map[key] = 'BSNL'
        elif 'vi' in op_name.lower() or 'vodafone' in op_name.lower() or 'idea' in op_name.lower():
            op_map[key] = 'Vi'
        else:
            op_map[key] = op_name.strip()

    print(f"Loaded {len(op_map)} MNC mappings")
    return op_map

# ─── STEP 2: Ingest tower CSV files ───────────────────────
def ingest_towers(conn, op_map):
    cur = conn.cursor()

    INSERT_SQL = """
        INSERT INTO towers (
            cell_id, operator, mcc, mnc, radio_type,
            latitude, longitude, geom,
            avg_signal_dbm, sample_count, range_m, last_seen
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s, %s, %s, %s
        )
        ON CONFLICT DO NOTHING;
    """

    total_inserted = 0

    for filepath, label in [(PATH_404, "MCC 404"), (PATH_405, "MCC 405")]:
        print(f"\nReading {label}...")
        df = pd.read_csv(filepath, low_memory=False)
        print(f"  Rows loaded: {len(df):,}")

        # Drop missing coordinates
        df = df.dropna(subset=['lat', 'long'])

        # Filter valid India coordinates
        df = df[
            (df['lat'] >= 6.0)  & (df['lat'] <= 37.0) &
            (df['long'] >= 68.0) & (df['long'] <= 98.0)
        ]
        print(f"  Valid coordinate rows: {len(df):,}")

        # Map operators
        df['operator'] = df.apply(
            lambda r: op_map.get((int(r['mcc']), int(r['mnc'])), 'Unknown')[:49], axis=1
        )

        # Convert timestamps
        df['updated'] = pd.to_datetime(df['updated'], unit='s', errors='coerce')

        batch = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc=f"Inserting {label}"):
            signal   = int(row['avgsignal']) if pd.notna(row['avgsignal']) and row['avgsignal'] != 0 else None
            last_seen= row['updated'].date() if pd.notna(row['updated']) else None
            samples  = int(row['sample'])    if pd.notna(row['sample'])   else None
            rng      = int(row['range'])     if pd.notna(row['range'])    else None

            batch.append((
                int(row['cid']),
                row['operator'],
                int(row['mcc']),
                int(row['mnc']),
                str(row['radio']),
                float(row['lat']),
                float(row['long']),
                float(row['long']),  # ST_MakePoint(lng, lat)
                float(row['lat']),
                signal,
                samples,
                rng,
                last_seen
            ))

            if len(batch) >= BATCH_SIZE:
                cur.executemany(INSERT_SQL, batch)
                conn.commit()
                total_inserted += len(batch)
                batch = []

        if batch:
            cur.executemany(INSERT_SQL, batch)
            conn.commit()
            total_inserted += len(batch)

    cur.close()
    print(f"\nTotal towers inserted: {total_inserted:,}")

# ─── STEP 3: Load GeoJSON into districts table ────────────
def ingest_geojson(conn):
    print("\nLoading states GeoJSON into districts table...")
    cur = conn.cursor()

    with open(PATH_GEOJSON) as f:
        gj = json.load(f)

    INSERT_SQL = """
        INSERT INTO districts (district_name, state_name, geom)
        VALUES (%s, %s, ST_Multi(ST_GeomFromGeoJSON(%s))::geography)
        ON CONFLICT DO NOTHING;
    """

    count = 0
    for feature in gj['features']:
        name = feature['properties'].get('st_nm', 'Unknown')
        geom_str = json.dumps(feature['geometry'])
        cur.execute(INSERT_SQL, (name, name, geom_str))
        count += 1

    conn.commit()
    cur.close()
    print(f"Inserted {count} states into districts table")

# ─── MAIN ──────────────────────────────────────────────────
def main():
    print("Connecting to CellSense DB...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("Connected.\n")

    op_map = load_operator_map()
    ingest_towers(conn, op_map)
    ingest_geojson(conn)

    conn.close()
    print("\nPhase 1 complete.")

if __name__ == "__main__":
    main()
