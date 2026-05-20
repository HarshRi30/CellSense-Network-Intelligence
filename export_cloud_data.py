import psycopg2
import psycopg2.extras
import csv
import os

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "cellsense",
    "user":     "postgres",
    "password": "7020"
}

BASE = r"C:\Users\Rishi Agrawal\Documents\CellSense"
OUTPUT = BASE + r"\data\towers_cloud.csv"

# Top 15 states by population + relevance
TARGET_STATES = [
    'Uttar Pradesh', 'Maharashtra', 'Bihar', 'West Bengal',
    'Madhya Pradesh', 'Rajasthan', 'Tamil Nadu', 'Karnataka',
    'Gujarat', 'Andhra Pradesh', 'Odisha', 'Telangana',
    'Kerala', 'Jharkhand', 'NCT of Delhi'
]

# Active operators only, LTE + NR radio (4G + 5G focus)
QUERY = """
    SELECT 
        tower_id, operator, radio_type, frequency_band,
        latitude, longitude, avg_signal_dbm, sample_count,
        range_m, state_circle
    FROM towers
    WHERE operator IN ('Jio', 'Airtel', 'Vi', 'BSNL')
    AND radio_type IN ('LTE', 'NR', 'UMTS')
    AND state_circle = ANY(%s)
    AND latitude IS NOT NULL
    AND longitude IS NOT NULL
    ORDER BY sample_count DESC NULLS LAST
    LIMIT 500000
"""

def main():
    print("Connecting to DB...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    print("Exporting trimmed tower dataset...")
    cur.execute(QUERY, (TARGET_STATES,))
    rows = cur.fetchall()
    print(f"Rows fetched: {len(rows):,}")

    os.makedirs(BASE + r"\data", exist_ok=True)
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'tower_id', 'operator', 'radio_type', 'frequency_band',
            'latitude', 'longitude', 'avg_signal_dbm', 'sample_count',
            'range_m', 'state_circle'
        ])
        writer.writerows(rows)

    cur.close()
    conn.close()

    size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
    print(f"Exported to: {OUTPUT}")
    print(f"File size: {size_mb:.1f} MB")
    print("Done.")

if __name__ == "__main__":
    main()
