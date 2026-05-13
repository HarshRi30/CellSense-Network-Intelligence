import psycopg2
import geopandas as gpd
import pandas as pd

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "cellsense",
    "user":     "postgres",
    "password": "7020"
}

BASE = r"C:\Users\Rishi Agrawal\Documents\CellSense"
PATH_GEOJSON = BASE + r"\states_india.geojson"

CHUNK = 50000

# ── Load states ──────────────────────────────────────────
print("Loading states GeoJSON...")
states = gpd.read_file(PATH_GEOJSON)[['st_nm', 'geometry']]
states = states.rename(columns={'st_nm': 'state_name'})
states = states.set_crs("EPSG:4326", allow_override=True)
print(f"  {len(states)} states loaded")

# ── Connect ───────────────────────────────────────────────
conn = psycopg2.connect(**DB_CONFIG)
cur  = conn.cursor()

# ── Get total tower count ─────────────────────────────────
cur.execute("SELECT COUNT(*) FROM towers")
total = cur.fetchone()[0]
print(f"Total towers to tag: {total:,}\n")

# ── Process in chunks ────────────────────────────────────
offset = 0
tagged = 0

while offset < total:
    cur.execute(
        "SELECT tower_id, longitude, latitude FROM towers ORDER BY tower_id LIMIT %s OFFSET %s",
        (CHUNK, offset)
    )
    rows = cur.fetchall()
    if not rows:
        break

    df = pd.DataFrame(rows, columns=['tower_id', 'lon', 'lat'])
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df['lon'], df['lat']),
        crs="EPSG:4326"
    )

    # Spatial join
    joined = gpd.sjoin(gdf, states, how='left', predicate='within')

    # Build update list
    updates = [
        (row['state_name'] if pd.notna(row['state_name']) else None, row['tower_id'])
        for _, row in joined[['tower_id', 'state_name']].iterrows()
    ]

    cur.executemany(
        "UPDATE towers SET state_circle = %s WHERE tower_id = %s",
        updates
    )
    conn.commit()

    offset += CHUNK
    tagged += len(rows)
    print(f"  Tagged {tagged:,} / {total:,} towers")

cur.close()
conn.close()
print("\nDone. All towers tagged.")
