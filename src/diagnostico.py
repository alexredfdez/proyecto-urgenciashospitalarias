#Archivo para el diagnóstico y limpieza de datos, no se utiliza porque
#el archivo etl_historico.py ya realiza esta tarea

from pathlib import Path
import pandas as pd

#Rutas de los archivos
RAIZ = Path(__file__).resolve().parent.parent
RUTA_CSV = RAIZ / "data" / "admisiones_historico.csv"
RUTA_JSON = RAIZ / "data" / "partes_clinicos.json"

#Dataframe que guarda los datos en bruto del csv
df_adm = pd.read_csv(RUTA_CSV)

#Dataframe que guarda los datos en bruto del json
df_partes = pd.read_json(RUTA_JSON)

#Identificar los ids duplicados
repetidos_csv = df_adm["id_episodio"].duplicated().sum()
print("IDs repetidos en el CSV:", repetidos_csv)
repetidos_json = df_partes["id_episodio"].duplicated().sum()
print("IDs repetidos en el JSON:", repetidos_json)

#Identificar si hay filas completas duplicadas
#Solo se miran las filas en el csv ya que en el json no hay ids duplicados
filas_identicas = df_adm.duplicated().sum()
print("Filas totalmente idénticas en el CSV:", filas_identicas)

#Eliminar los duplicados y guardarlos en un df nuevo
df_adm_sin_duplicados = df_adm.drop_duplicates()
print("Filas antes:", len(df_adm))
print("Filas después:", len(df_adm_sin_duplicados))

#Comparar que ids aparecen sólo en uno de los dos archivos
ids_csv = set(df_adm_sin_duplicados["id_episodio"])
ids_json = set(df_partes["id_episodio"])

print("En ambos ficheros:", len(ids_csv & ids_json))
print("Solo en el CSV:", len(ids_csv - ids_json))
print("Solo en el JSON:", len(ids_json - ids_csv))