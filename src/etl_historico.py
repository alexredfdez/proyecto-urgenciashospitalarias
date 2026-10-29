"""
esto es para la limpieza del historico de urgencias csv
el resultado de ``limpiar_datos`` está preparado para insertarse como
documentos en MongoDB
"""
# comando de docker para iniciarlo (desde la raiz del proyecto): docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import analytics_mongo as mongo


VALORES_NULOS = {
    "",
    "N/D",
    "S/D",
    "NULL",
    "NONE",
    "NAN",
    "ERROR",
    "PENDIENTE",
}


def extraer_datos(ruta_csv: str | Path, ruta_json: str | Path) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    # recibe 2 rutas, lee los archivos, comprueba los datos y los dvuelve
    admisiones = pd.read_csv(ruta_csv)
    with Path(ruta_json).open(encoding="utf-8") as fichero:
        partes = json.load(fichero)
    if not isinstance(partes, list):
        raise ValueError("El JSON clínico debe contener una lista de partes")
    return admisiones, partes


def _limpiar_fechas(serie: pd.Series) -> pd.Series:
    # limpia una columna de fechas. primero convierte a texto, comprueba si es nulo o no y si es lo convierte a NaN, luego convierte a fecha. elimina zona horaria y lo devuelve
    valores = serie.astype("string").str.strip()
    valores = valores.mask(valores.str.upper().isin(VALORES_NULOS))
    fechas = pd.to_datetime(
        valores, format="mixed", dayfirst=True, utc=True, errors="coerce"
    )
    return fechas.dt.tz_localize(None)


def _limpiar_texto(serie: pd.Series) -> pd.Series:
    # convierte los valores a texto y los nulos devuelve NaN. tambien sustituye varios espacios en solo uno
    valores = serie.astype("string").str.strip()
    valores = valores.mask(valores.str.upper().isin(VALORES_NULOS))
    return valores.str.replace(r"\s+", " ", regex=True).str.lower()


def _limpiar_frecuencia(serie: pd.Series) -> pd.Series:
    # limpia frecuencias cardiacas pasandolas a numero y solo devuelve si el numero es mayor de 30 y menor de 220
    frecuencia = pd.to_numeric(serie, errors="coerce")
    return frecuencia.where(frecuencia.between(30, 220))


def limpiar_datos(admisiones: pd.DataFrame, partes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # limpia los datos, elimina los duplicado y los cruza mediante id_episodio
    # comprueba columans obligatorias
    requeridas_csv = {"id_episodio", "timestamp_llegada", "timestamp_alta"}
    faltantes = requeridas_csv - set(admisiones.columns)
    # si falta alguna columna lanza un error
    if faltantes:
        raise ValueError(f"Faltan columnas obligatorias en el CSV: {sorted(faltantes)}")
    # elimina duplicado del csv
    df_admisiones = admisiones.drop_duplicates("id_episodio", keep="first").copy()
    # elimina duplicados del json
    df_partes = pd.DataFrame(partes).drop_duplicates("id_episodio", keep="first").copy()
    # limpia fechas del csv
    for columna in ("timestamp_llegada", "timestamp_alta"):
        df_admisiones[columna] = _limpiar_fechas(df_admisiones[columna])
    #limpia textos del csv
    for columna in ("motivo_consulta", "destino_alta", "tension_arterial"):
        if columna in df_admisiones:
            df_admisiones[columna] = _limpiar_texto(df_admisiones[columna])
    # limpia la frecuencia del csv
    if "frecuencia_cardiaca" in df_admisiones:
        df_admisiones["frecuencia_cardiaca"] = _limpiar_frecuencia(
            df_admisiones["frecuencia_cardiaca"]
        )
    # comprueba que el bloque existe en el JSON
    if "triaje_manchester" in df_partes:
        # extrae cada categoria 
        # lambda aplica la funcion a todos los valores de la columna
        df_partes["categoria_patologia"] = df_partes["triaje_manchester"].map(
            lambda valor: valor.get("categoria_patologia") if isinstance(valor, dict) else None
        )
        df_partes["nivel_manchester"] = df_partes["triaje_manchester"].map(
            lambda valor: valor.get("nivel") if isinstance(valor, dict) else None
        )
        df_partes["tiempo_max_espera_min"] = df_partes["triaje_manchester"].map(
            lambda valor: valor.get("tiempo_max_espera_min") if isinstance(valor, dict) else None
        )
    # extrae la frecuencia cardiaca del triaje y la limpia
    if "constantes" in df_partes:
        df_partes["frecuencia_cardiaca_triaje"] = df_partes["constantes"].map(
            lambda valor: valor.get("frecuencia_cardiaca_triaje") if isinstance(valor, dict) else None
        )
        df_partes["frecuencia_cardiaca_triaje"] = _limpiar_frecuencia(
            df_partes["frecuencia_cardiaca_triaje"]
        )
    
    # cruza el csv con el json usando el campo id_episidio (si aparece en ambos)
    df = df_admisiones.merge(
        df_partes,
        on="id_episodio",
        how="inner",
        suffixes=("", "_parte"),
        validate="one_to_one",
    )
    # si existe alguna columna repetida, la elimina
    df = df.drop(columns=["sip_paciente_parte"], errors="ignore")
    # lo convierte en documentos para luego usarlo en Mongo (records genera una lista de objetos y loads convierte el json en diccionarios)
    return json.loads(df.to_json(orient="records", date_format="iso"))


def ejecutar_etl(ruta_csv: str | Path, ruta_json: str | Path) -> list[dict[str, Any]]:
    # extrae los datos y ejecuta limpiar_datos para mergearlos y limpiarlos
    admisiones, partes = extraer_datos(ruta_csv, ruta_json)
    return limpiar_datos(admisiones, partes)


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent
    documentos = ejecutar_etl(
        raiz / "data" / "admisiones_historico.csv",
        raiz / "data" / "partes_clinicos.json",
    )
    print(f"Episodios listos para MongoDB: {len(documentos)}")
    mongo.cargar_en_mongo(documentos)
    print("Carga en MongoDB completada")
    
