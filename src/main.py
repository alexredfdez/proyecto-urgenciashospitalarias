import descargar_archivos as df
from pathlib import Path
from etl_historico import ejecutar_etl
import analytics_mongo as mongo
def ejecutar_etl_historico():
    raiz = Path(__file__).resolve().parent.parent
    documentos = ejecutar_etl(
        raiz / "data" / "admisiones_historico.csv",
        raiz / "data" / "partes_clinicos.json"
    )

    print(f"\nEpisodios preparados: {len(documentos)}")

    mongo.cargar_en_mongo(documentos)
    print("Carga en MongoDB completada")
def mostrarMenu():
    while True:
        print("SISTEMA DE URGENCIAS HOSPITALARIAS")
        print("-"*50)
        print("1. Ejecutar ETL histórico")
        print("0. Salir")
        opcion = input("Selecciona una opción: ").strip()
        if opcion == "1":
            try:
                ejecutar_etl_historico
            except Exception as error:
                print(f"Error durante la ejecución del ETL: {error}")
        elif opcion == "0":
            print("Saliendo")
            break
        else:
            print("Esta opción no es válida. Selecciona una")
if __name__ == "__main__":
    mostrarMenu()

    
