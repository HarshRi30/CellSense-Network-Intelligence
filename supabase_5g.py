import psycopg2
import pandas as pd

CLOUD_DB = "postgresql://postgres:CellSense2026@db.qjhpatciiitdwputpqjk.supabase.co:5432/postgres"
CSV_5G = r"C:\Users\Rishi Agrawal\Documents\CellSense\RS_Session_265_AU_1136_1.csv"

STATE_MAP = {
    'Andaman and Nicobar Islands': 'Andaman & Nicobar Island',
    'Jammu and Kashmir':           'Jammu & Kashmir',
    'Jammu & Kashmir':             'Jammu & Kashmir',
    'Laddakh':                     'Ladakh',
    'Tamilnadu':                   'Tamil Nadu',
    'Delhi':                       'NCT of Delhi',
    'Chattisgarh':                 'Chhattisgarh',
    'Total':                       'SKIP',
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

conn = psycopg2.connect(CLOUD_DB)
cur  = conn.cursor()

updated = 0
for _, row in state_agg.iterrows():
    if row['state_mapped'] == 'SKIP':
        continue
    cur.execute("""
        UPDATE districts SET towers_5g = %s, towers_5g_fiberized = %s
        WHERE district_name = %s
    """, (int(row['towers_5g']), int(row['towers_5g_fiberized']), row['state_mapped']))
    if cur.rowcount > 0:
        updated += 1

conn.commit()
cur.close()
conn.close()
print(f"Done. Updated {updated} states.")