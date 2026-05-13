import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import os

BASE = r"C:\Users\Rishi Agrawal\Documents\CellSense"
DATA = BASE + r"\data"

FILES = {
    'Jio':    BASE + r"\trai_jio.csv",
    'Airtel': BASE + r"\trai_airtel.csv",
    'Vi':     BASE + r"\trai_vi.csv",
}

# ─── LOAD & COMBINE ───────────────────────────────────────
dfs = []
for op, path in FILES.items():
    df = pd.read_csv(path)
    df['operator_clean'] = op
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)
print(f"Total rows: {len(df):,}")
print(df['operator_clean'].value_counts())

# ─── FILTER DOWNLOAD ONLY ─────────────────────────────────
df = df[df['download'] == 'download'].copy()
print(f"\nDownload rows only: {len(df):,}")

# ─── FEATURE ENGINEERING ──────────────────────────────────
# Convert speed from kbps to Mbps
df['speed_mbps'] = df['speed_kbps'] / 1000

# Drop extreme outliers (top 1% and bottom 1%)
low  = df['speed_mbps'].quantile(0.01)
high = df['speed_mbps'].quantile(0.99)
df   = df[(df['speed_mbps'] >= low) & (df['speed_mbps'] <= high)]
print(f"After outlier removal: {len(df):,}")

# Drop missing signal strength
df = df.dropna(subset=['signal_strength', 'speed_mbps'])

# Encode technology
tech_map = {'2G': 0, '3G': 1, '4G': 2, '5G': 3}
df['tech_encoded'] = df['technology'].map(tech_map).fillna(2)

# Encode operator
op_map = {'Jio': 0, 'Airtel': 1, 'Vi': 2, 'BSNL': 3}
df['op_encoded'] = df['operator_clean'].map(op_map).fillna(0)

# Signal strength as absolute value (it's negative dBm)
df['signal_strength'] = pd.to_numeric(df['signal_strength'], errors='coerce')
df['signal_abs'] = df['signal_strength'].abs()

print(f"\nSpeed distribution (Mbps):")
print(df['speed_mbps'].describe().round(2))

# ─── FEATURES & TARGET ────────────────────────────────────
FEATURES = ['signal_abs', 'tech_encoded', 'op_encoded']
TARGET   = 'speed_mbps'

X = df[FEATURES]
y = df[TARGET]

# ─── TRAIN / TEST SPLIT ───────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"\nTrain: {len(X_train):,} | Test: {len(X_test):,}")

# ─── TRAIN XGBOOST ────────────────────────────────────────
print("\nTraining XGBoost model...")
model = XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# ─── EVALUATE ─────────────────────────────────────────────
y_pred = model.predict(X_test)
mae    = mean_absolute_error(y_test, y_pred)
r2     = r2_score(y_test, y_pred)

print(f"\nModel Performance:")
print(f"  MAE : {mae:.2f} Mbps")
print(f"  R²  : {r2:.4f}")

# ─── SAVE MODEL ───────────────────────────────────────────
model_path = BASE + r"\models\speed_model.pkl"
os.makedirs(BASE + r"\models", exist_ok=True)
joblib.dump(model, model_path)
print(f"\nModel saved to: {model_path}")

# ─── QUICK TEST ───────────────────────────────────────────
print("\nSample predictions:")
test_cases = [
    {"signal_abs": 70,  "tech_encoded": 2, "op_encoded": 0, "label": "Jio 4G good signal"},
    {"signal_abs": 95,  "tech_encoded": 2, "op_encoded": 1, "label": "Airtel 4G weak signal"},
    {"signal_abs": 60,  "tech_encoded": 3, "op_encoded": 0, "label": "Jio 5G excellent signal"},
    {"signal_abs": 105, "tech_encoded": 1, "op_encoded": 2, "label": "Vi 3G poor signal"},
]
for t in test_cases:
    features = [[t['signal_abs'], t['tech_encoded'], t['op_encoded']]]
    pred = model.predict(features)[0]
    print(f"  {t['label']:35} → {pred:.1f} Mbps")
