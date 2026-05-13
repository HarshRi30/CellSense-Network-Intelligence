# ◈ CellSense — India Network Intelligence Platform

> Know your network. Know your coverage.

CellSense is a full-stack network intelligence platform that helps users find the best mobile operator at any location in India, while giving telecom operators and regulators a data-driven view of coverage gaps across all 36 states.

Built on 2.5 million real tower records, a physics-based signal propagation model, and a machine learning speed predictor trained on 228,000 TRAI speed test samples — CellSense is not a demo project. It is a working product.

---

## Aim & Vision

India has 4 active mobile operators — Jio, Airtel, Vi, and BSNL — serving 1.4 billion people across vastly different geographies. A user in Mumbai and a user in Arunachal Pradesh experience entirely different network realities. Yet every SIM purchase, every plan decision, is made without any location-specific intelligence.

CellSense solves this at two levels:

**For consumers (B2C):** Enter any address, landmark, or city in India. CellSense queries a PostGIS spatial database of 2.5M towers, runs the Okumura-Hata signal propagation model across all nearby towers, and returns a ranked list of operators with estimated signal strength, radio type, frequency band, and predicted download speed — in under a second.

**For operators and regulators (B2B):** A coverage gap dashboard ranks all 36 Indian states by tower density relative to geographic area. It shows operator-wise tower counts, 5G rollout progress (from real 2024 government data), and identifies the most underserved regions — the kind of analysis TRAI and DoT run before spectrum auctions and tower subsidy programs.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL + PostGIS |
| Data Processing | Python, Pandas, GeoPandas |
| Signal Model | Okumura-Hata (physics-based propagation) |
| ML Model | XGBoost (speed prediction) |
| Backend API | FastAPI |
| Frontend | React + Leaflet.js + Recharts |
| Deployment | GitHub + Azure (planned) |

---

## Project Structure

```
CellSense/
├── main.py                  # FastAPI entry point
├── signal_engine.py         # Okumura-Hata signal model + ML inference
├── train_speed_model.py     # XGBoost speed prediction training
├── ingest_towers.py         # Tower data ingestion
├── ingest_5g_bts.py         # Government 5G BTS data ingestion
├── tag_tower_states.py      # Spatial state tagging for towers
├── db/
│   └── connection.py
├── models/
│   └── schemas.py
├── routers/
│   ├── network_selector.py  # POST /api/best-network
│   ├── coverage_gap.py      # GET /api/coverage-gap
│   └── route_analysis.py   # POST /api/route-analysis
└── frontend/                # React + Leaflet UI
```

---

## Data Sources & Setup Instructions

### 1. Tower Location Data

**Important:** OpenCelliD does not provide a dedicated India dataset on their downloads page. India (MCC 404 and MCC 405) is completely absent from their country-specific exports list. Direct MCC download URLs (`mcc404.csv.gz`, `mcc405.csv.gz`) return `FILE_NOT_FOUND` errors on the free tier. The full worldwide dataset download was also attempted but returned zero India records.

**Workaround used:** A community-maintained India-specific mirror on Kaggle, sourced from OpenCelliD and uploaded on April 25, 2023.
- Search **"Mobile Network Coverage India"** on https://www.kaggle.com (by sachinxshrivastav)
- Direct link: https://www.kaggle.com/datasets/sachinxshrivastav/mobile-network-coverage-india
- Download and extract — you will get `404.csv`, `405.csv`, `MCC-MNC India.csv`, `states_india.geojson`
- Place `404.csv` and `405.csv` inside the `data/` folder
- Place `states_india.geojson` in the root `CellSense/` directory
- Run: `python ingest_towers.py`
- Run: `python tag_tower_states.py`

### 2. Speed Test Data — TRAI MySpeed
- Go to: https://data.gov.in/catalog/myspeed-crowdsourced-mobile-data-speeds
- Select Operator + Licensed Service Area (Maharashtra) + Year 2024
- Download separately for Jio, Airtel, and Vi (BSNL data is unavailable)
- Rename files to `trai_jio.csv`, `trai_airtel.csv`, `trai_vi.csv` and place in root directory
- Run: `python train_speed_model.py`

### 3. 5G BTS Data — Government of India
- Go to: https://data.gov.in
- Search: **"5G BTS installed state district"**
- Download the Rajya Sabha session document CSV (district-wise 5G BTS counts, data up to June 2024)
- Place as `data/RS_Session_265_AU_1136_1.csv`
- Run: `python ingest_5g_bts.py`

---

## API Endpoints

```
POST /api/best-network
Body: { "lat": 21.1458, "lng": 79.0882, "radius_m": 5000, "indoor": false }
Returns: ranked operators with signal_dbm, quality, radio_type, predicted_speed_mbps

GET /api/coverage-gap?state=Maharashtra
Returns: tower counts, gap scores, 5G rollout data per state

POST /api/route-analysis
Body: { "waypoints": [[lat, lng], [lat, lng], ...] }
Returns: best operator per waypoint + overall route winner
```

Full interactive API docs at: `http://localhost:8000/docs`

---

## Obstacles Faced in Data Collection

Building CellSense exposed a fundamental problem with telecom data in India — it is fragmented, outdated, and largely inaccessible.

**OpenCelliD does not have India data:** Despite being the world's largest open cell tower database, OpenCelliD's country-specific downloads page does not list India at all. India (MCC 404 and 405) is absent from their 208-country export list. Direct MCC download links also return `FILE_NOT_FOUND`. The full worldwide CSV was downloaded as a fallback but contained zero India records — confirming that India tower data is either withheld or not available on the free tier. The only working source was a Kaggle community mirror.

**Kaggle mirror is ~3 years old:** The India-specific dataset on Kaggle was uploaded on April 25, 2023 — making it approximately 3 years old as of 2026. India's telecom infrastructure has changed significantly in this period. Jio completed its pan-India 5G rollout, new towers have been deployed in rural areas under BharatNet and USOF programs, and several operators have decommissioned legacy 2G/3G infrastructure. None of these changes are reflected in the current dataset.

**Dead operators in data:** The dataset includes towers from AIRCEL, Uninor, and DOLPHIN — operators that have shut down or merged since 2023. These records inflate tower counts and had to be explicitly filtered out in all analytics queries.

**No operator-published data:** None of India's four active operators (Jio, Airtel, Vi, BSNL) publish tower location data publicly. This is commercially sensitive information. The entire foundation of CellSense rests on crowd-sourced observations logged by Android devices — a proxy for real infrastructure, not the real thing.

**TRAI MySpeed fragmentation:** TRAI's speed test data requires manual selection of operator + state + year — one combination at a time. There is no bulk export for all-India, all-operator data. BSNL data was entirely unavailable for the selected state and period. This forced the ML model to train on only 3 of 4 operators (Jio, Airtel, Vi).

**5G data at state level only:** The government's 5G BTS dataset provides district-wise tower counts but no GPS coordinates. This means 5G coverage cannot be modeled spatially — only aggregated at the state level on the B2B dashboard.

**State tagging performance:** Assigning each of the 2.5M towers to its Indian state required a spatial join between tower coordinates and state polygon boundaries. A naive PostgreSQL `ST_Within` UPDATE query ran for over an hour without completing on a consumer laptop. The final solution used GeoPandas in Python with chunked processing of 50,000 rows at a time — completing in approximately 25 minutes.

**Missing states in GeoJSON:** The India states boundary file was missing Arunachal Pradesh, Dadra & Nagar Haveli, and Ladakh. These 3 states/UTs were excluded from state-level gap analysis.

---

## Future Prospects — What Updated Data Would Enable

The architecture of CellSense is designed to handle real-time and frequently updated data. The current dataset's age is a limitation of data availability, not system design.

**Resolving the OpenCelliD India gap:** If OpenCelliD adds India to its country-specific exports, or if a crowdsourcing campaign is run specifically for India (via apps like Network Cell Info), CellSense's ingestion pipeline can process and load fresh tower data with zero code changes.

**Real-time tower updates via OpenCelliD API:** The OpenCelliD API supports bounding-box queries that return live crowd-sourced tower observations. Automating this as a nightly ingestion job would keep the tower database current within weeks of any new tower deployment.

**Operator 5G rollout tracking:** As the government publishes quarterly 5G BTS data, each release can be ingested automatically. A time-series layer would allow CellSense to visualize 5G rollout velocity — which states are adding towers fastest and which are falling behind.

**TRAI MySpeed integration at scale:** If TRAI provides a bulk API or monthly full-India export, the speed prediction model could be retrained quarterly — capturing seasonal congestion patterns, new spectrum deployments, and the impact of 5G on 4G speeds in overlapping areas.

**District-level gap analysis:** The current gap analysis operates at state level. A district-level boundary file (available from the Survey of India) would enable gap scoring at district granularity — enabling TRAI, DoT, and USOF programs to target subsidies at the exact districts that need them most.

**Live congestion modeling:** With timestamped speed test data, a time-of-day congestion layer could be added — "Jio slows to 8 Mbps in this area between 8–10 PM." This would make CellSense genuinely useful for users making SIM purchase decisions in high-traffic urban areas.

**BSNL inclusion:** BSNL serves critical rural and government infrastructure. As TRAI MySpeed data for BSNL becomes available, the ML model can be retrained to include accurate BSNL speed predictions.

---

## Current Advantages

- **2.5 million real tower records** covering all 36 Indian states across 4 operators
- **Physics-based signal model** (Okumura-Hata) validated against crowd-sourced signal measurements — not a simple distance calculation
- **ML speed predictor** trained on 228,000 real TRAI speed test samples (R² = 0.63)
- **Sub-second API response** — PostGIS spatial index returns results for a 5km radius query across 2.5M towers in under 300ms
- **Dual value proposition** — B2C network selector and B2B coverage gap dashboard in one platform
- **Click-on-map** — users can click anywhere on the India map to instantly get network rankings
- **Indoor signal modeling** — 15dB penetration loss applied for indoor scenarios
- **Real 2024 5G data** — sourced from official government BTS deployment records, not estimates
- **Route analysis** — submit waypoints and get the best operator per segment of a commute or journey

---

## Current Drawbacks & Known Limitations

- **Data is ~3 years old** — tower database sourced from a Kaggle mirror of OpenCelliD uploaded April 2023. Towers deployed after early 2023 are absent.
- **OpenCelliD has no India-specific export** — India (MCC 404, 405) is not listed in OpenCelliD's country downloads. There is no official path to get updated India tower data from this source on the free tier.
- **Dead operator records in DB** — AIRCEL, Uninor, and DOLPHIN towers exist in the raw dataset despite these operators being defunct. Filtered in queries but present in raw tables.
- **No BSNL speed data** — TRAI MySpeed had no available BSNL data. BSNL speed predictions are less accurate than the other three operators.
- **GSM-dominant results** — OpenCelliD over-represents older GSM towers. LTE and NR towers may be underrepresented relative to actual deployment.
- **State-level 5G only** — 5G BTS data has district counts but no coordinates, so individual 5G tower locations cannot be shown on the map.
- **No live congestion data** — predicted speeds are based on signal strength and operator averages, not real-time network load.
- **Single-state speed training** — ML model trained on Maharashtra data only. Speed predictions may be less accurate for other states.
- **No authentication** — API has no rate limiting or API key middleware. Not production-safe without adding auth before public deployment.
- **3 states missing from gap analysis** — Arunachal Pradesh, Dadra & Nagar Haveli, and Ladakh were absent from the GeoJSON boundary file and excluded from coverage gap scoring.

---

## Running Locally

**Prerequisites:** PostgreSQL 15+ with PostGIS, Python 3.10+, Node.js 18+

```bash
# Install Python dependencies
pip install fastapi uvicorn psycopg2-binary pandas geopandas xgboost scikit-learn joblib tqdm shapely

# Start API server
python -m uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Backend: `http://localhost:8000`
API docs: `http://localhost:8000/docs`
Frontend: `http://localhost:5173`

---

## Built By

Rishi Agrawal — B.Tech CSE (Data Science), RCOEM Nagpur
GitHub: [HarshRi30](https://github.com/HarshRi30)
Contact: rishiagra30@gmail.com
