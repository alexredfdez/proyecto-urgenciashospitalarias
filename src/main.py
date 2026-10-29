from __future__ import annotations

import descargar_archivos as df
from pathlib import Path
from etl_historico import ejecutar_etl
import analytics_mongo as mongo
from urgencias_worker import main as iniciarworker
from anonimizador import anonimizar_documentos  # Importamos la capa de anonimización

def ejecutar_etl_historico():
    # Clave secreta para el HMAC del SIP
    CLAVE_SECRETA = "mi_clave_secreta_super_segura_urgencias"
    
    raiz = Path(__file__).resolve().parent.parent
    documentos_brutos = ejecutar_etl(
        raiz / "data" / "admisiones_historico.csv",
        raiz / "data" / "partes_clinicos.json"
    )

    print(f"\nEpisodios extraídos (brutos): {len(documentos_brutos)}")

    # Aplicamos la capa de anonimización (GDPR / HIPAA)
    print("🔒 Aplicando anonimización y enmascaramiento de datos...")
    documentos = anonimizar_documentos(documentos_brutos, CLAVE_SECRETA)

    print(f"Episodios seguros listos para carga: {len(documentos)}")

    # Cargamos en MongoDB los documentos ya anonimizados
    mongo.cargar_en_mongo(documentos)
    print("✨ Carga en MongoDB completada con éxito.")

def mostrarMenu():
    while True:
        print("SISTEMA DE URGENCIAS HOSPITALARIAS")
        print("-"*50)
        print("1. Ejecutar ETL histórico")
        print("2. Triaje")
        print("\nSISTEMA DE URGENCIAS HOSPITALARIAS")
        print("-" * 50)
        print("1. Ejecutar ETL histórico y cargar en MongoDB")
        print("0. Salir")
        opcion = input("Selecciona una opción: ").strip()
        
        if opcion == "1":
            try:
                ejecutar_etl_historico()
                ejecutar_etl_historico()
            except Exception as error:
                print(f"Error durante la ejecución del ETL: {error}")
        elif opcion=="2":
            try:
                iniciarworker()
            except Exception as error:
                print(f"Error durante la ejecución del worker: {error}")
                print(f"❌ Error durante la ejecución del ETL: {error}")
        elif opcion == "0":
            print("Saliendo del sistema...")
            break
        else:
            print("⚠️ Esta opción no es válida. Selecciona una correcta.")

if __name__ == "__main__":
    mostrarMenu()