import joblib
import numpy as np

MODEL_PATH = r"C:\Users\Rishi Agrawal\Documents\CellSense\models\speed_model.pkl"
speed_model = joblib.load(MODEL_PATH)

TECH_MAP = {'GSM': 0, 'UMTS': 1, 'LTE': 2, 'NR': 3}
OP_MAP   = {'Jio': 0, 'Airtel': 1, 'Vi': 2, 'BSNL': 3}
import math
import psycopg2
import psycopg2.extras

# ─── DB CONFIG ────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "cellsense",
    "user":     "postgres",
    "password": "7020"
}

# ─── CONSTANTS ────────────────────────────────────────────
# Typical transmit power per radio type (dBm)
TX_POWER = {
    "LTE":  43,
    "NR":   46,
    "UMTS": 43,
    "GSM":  45,
}

# Default frequency (MHz) per radio type if band unknown
DEFAULT_FREQ = {
    "LTE":  1800,
    "NR":   3500,
    "UMTS": 2100,
    "GSM":  900,
}

# Signal quality thresholds (dBm)
SIGNAL_QUALITY = {
    "Excellent": (-1,   -70),
    "Good":      (-70,  -85),
    "Fair":      (-85,  -100),
    "Poor":      (-100, -110),
    "No Signal": (-110, -200),
}

ACTIVE_OPERATORS = ['Jio', 'Airtel', 'Vi', 'BSNL']

# ─── HAVERSINE DISTANCE ───────────────────────────────────
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ─── OKUMURA-HATA PATH LOSS ───────────────────────────────
def okumura_hata_loss(distance_km, frequency_mhz, hb=30, hm=1.5):
    """
    Urban path loss in dB.
    distance_km  : tower to receiver distance
    frequency_mhz: carrier frequency
    hb           : base station antenna height (m)
    hm           : mobile device height (m)
    """
    if distance_km < 0.01:
        distance_km = 0.01  # min 10 metres to avoid log(0)

    a_hm = ((1.1 * math.log10(frequency_mhz) - 0.7) * hm
            - (1.56 * math.log10(frequency_mhz) - 0.8))

    L = (69.55
         + 26.16 * math.log10(frequency_mhz)
         - 13.82 * math.log10(hb)
         - a_hm
         + (44.9 - 6.55 * math.log10(hb)) * math.log10(distance_km))
    return L

# ─── SIGNAL QUALITY LABEL ─────────────────────────────────
def signal_quality(dbm):
    for label, (high, low) in SIGNAL_QUALITY.items():
        if dbm <= high and dbm > low:
            return label
    return "No Signal"

# ─── MAIN FUNCTION: SCORE OPERATORS AT A LOCATION ─────────
def get_best_network(lat, lng, radius_m=5000, indoor=False):
    """
    Given lat/lng, returns ranked operators with signal estimates.
    indoor: adds 15dB penetration loss for indoor scenario
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # PostGIS radius query — get all active towers nearby
    cur.execute("""
        SELECT 
            tower_id, operator, radio_type, frequency_band,
            latitude, longitude, avg_signal_dbm, sample_count
        FROM towers
        WHERE ST_DWithin(
            geom,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s
        )
        AND operator = ANY(%s)
    """, (lng, lat, radius_m, ACTIVE_OPERATORS))

    towers = cur.fetchall()
    cur.close()
    conn.close()

    if not towers:
        return {"error": "No towers found within radius", "towers_checked": 0}

    # Score each operator — keep best signal tower per operator
    scores = {}

    for t in towers:
        op          = t['operator']
        radio       = t['radio_type'] or 'LTE'
        freq        = t['frequency_band'] or DEFAULT_FREQ.get(radio, 1800)
        tx          = TX_POWER.get(radio, 43)
        dist_km = haversine_km(lat, lng, float(t['latitude']), float(t['longitude']))

        path_loss   = okumura_hata_loss(dist_km, freq)
        signal_dbm  = tx - path_loss

        # Indoor penalty
        if indoor:
            signal_dbm -= 15

        # Use crowd-sourced signal if available and model is weaker
        if t['avg_signal_dbm'] and t['sample_count'] and t['sample_count'] > 5:
            crowd_signal = float(t['avg_signal_dbm'])
            # Weighted blend: 60% model, 40% crowd-sourced
            signal_dbm = 0.6 * signal_dbm + 0.4 * crowd_signal

        if op not in scores or signal_dbm > scores[op]['signal_dbm']:
            scores[op] = {
                'operator':      op,
                'signal_dbm':    round(signal_dbm, 1),
                'radio_type':    radio,
                'frequency_mhz': freq,
                'distance_km':   round(dist_km, 3),
                'tower_id':      t['tower_id'],
                'quality':       signal_quality(signal_dbm),
                'predicted_speed_mbps': round(float(speed_model.predict([[
                    abs(signal_dbm),
                    TECH_MAP.get(radio, 2),
                    OP_MAP.get(op, 0)
                ]])[0]), 1)
            }

    # Sort by signal strength
    ranked = sorted(scores.values(), key=lambda x: x['signal_dbm'], reverse=True)

    return {
        "lat":            lat,
        "lng":            lng,
        "radius_m":       radius_m,
        "indoor":         indoor,
        "towers_checked": len(towers),
        "ranked_operators": ranked,
        "recommendation": ranked[0]['operator'] if ranked else "No coverage"
    }

# ─── TEST ─────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    print("Testing CellSense Signal Engine...")
    print("Location: Nagpur city centre\n")

    result = get_best_network(lat=21.1458, lng=79.0882)

    print(f"Towers checked : {result['towers_checked']}")
    print(f"Recommendation : {result['recommendation']}")
    print("\nRanked Operators:")
    for r in result['ranked_operators']:
        print(f"  {r['operator']:8} | {r['signal_dbm']:7} dBm | {r['quality']:10} | {r['radio_type']} | {r['distance_km']} km | {r.get('predicted_speed_mbps', 'N/A')} Mbps")
        
    print("\n--- Indoor scenario ---")
    result_indoor = get_best_network(lat=21.1458, lng=79.0882, indoor=True)
    for r in result_indoor['ranked_operators']:
        print(f"  {r['operator']:8} | {r['signal_dbm']:7} dBm | {r['quality']:10}")
