import pandas as pd
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CSV = RAIZ / "data" / "admisiones_historico.csv"
RUTA_JSON = RAIZ / "data" / "partes_clinicos.json"

# --- CSV ---
df_adm = pd.read_csv(RUTA_CSV)
print("=== CSV ===")
print("Filas, columnas:", df_adm.shape)
print(df_adm.dtypes)
print(df_adm.head())

# --- JSON ---
df_partes = pd.read_json(RUTA_JSON)
print("\n=== JSON ===")
print("Filas, columnas:", df_partes.shape)
print(df_partes.dtypes)
print(df_partes.head())