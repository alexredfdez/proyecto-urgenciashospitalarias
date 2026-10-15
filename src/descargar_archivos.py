import requests
from pathlib import Path

URL_BASE = "http://10.201.59.248:8088"
CARPETA_DATA = Path("data")


def descargar_ficheros():
    CARPETA_DATA.mkdir(exist_ok=True)

    ficheros = [
        "admisiones_historico.csv",
        "partes_clinicos.json"
    ]

    for nombre in ficheros:
        url = f"{URL_BASE}/{nombre}"

        respuesta = requests.get(url, timeout=30)
        respuesta.raise_for_status()

        ruta = CARPETA_DATA / nombre
        ruta.write_bytes(respuesta.content)

        print(f"Descargado: {ruta}")


if __name__ == "__main__":
    descargar_ficheros()