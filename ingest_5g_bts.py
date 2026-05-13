import pandas as pd
import psycopg2

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "cellsense",
    "user":     "postgres",
    "password": "7020"
}

PATH_5G = r"C:\Users\Rishi Agrawal\Documents\CellSense\RS_Session_265_AU_1136_1.csv"

# State name normalization — govt names vs our GeoJSON names
STATE_MAP = {
    'Andaman and Nicobar Islands':                    'Andaman & Nicobar Island',
    'Dadra and Nagar Haveli and Daman and Diu':       'Dadra & Nagar Haveli',
    'Jammu and Kashmir':                              'Jammu & Kashmir',
    'Jammu & Kashmir':                                'Jammu & Kashmir',
    'Laddakh':                                        'Ladakh',
    'Tamilnadu':                                      'Tamil Nadu',
    'Delhi':                                          'NCT of Delhi',
    'Chattisgarh':                                    'Chhattisgarh',
    'Total':                                          'SKIP',
}


def main():
    df = pd.read_csv(PATH_5G)
    df.columns = ['sl_no', 'state', 'district', 'bts_installed', 'bts_fiberized']
    df['bts_installed']  = pd.to_numeric(df['bts_installed'],  errors='coerce').fillna(0).astype(int)
    df['bts_fiberized']  = pd.to_numeric(df['bts_fiberized'],  errors='coerce').fillna(0).astype(int)
    df['state'] = df['state'].str.strip()
    df = df[df['state'] != 'Total']


    # Aggregate to state level (our districts table = states)
    state_agg = df.groupby('state').agg(
        towers_5g=('bts_installed', 'sum'),
        towers_5g_fiberized=('bts_fiberized', 'sum')
    ).reset_index()

    # Normalize state names
    state_agg['state_mapped'] = state_agg['state'].apply(
        lambda x: STATE_MAP.get(x, x)
    )

    print("State-level 5G aggregation:")
    print(state_agg[['state_mapped', 'towers_5g', 'towers_5g_fiberized']].to_string())

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    updated = 0
    not_found = []

    for _, row in state_agg.iterrows():
        if row['state_mapped'] == 'SKIP':
            continue
        
        cur.execute("""
            UPDATE districts
            SET towers_5g = %s,
                towers_5g_fiberized = %s
            WHERE district_name = %s
        """, (int(row['towers_5g']), int(row['towers_5g_fiberized']), row['state_mapped']))

        if cur.rowcount == 0:
            not_found.append(row['state_mapped'])
        else:
            updated += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nUpdated: {updated} states")
    if not_found:
        print(f"Not matched: {not_found}")

if __name__ == "__main__":
    main()
