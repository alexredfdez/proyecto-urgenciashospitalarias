import time
import requests
from triage_redis import verificar_conexion, encolar_paciente

API_URL = "http://10.201.59.248:28000/api/v1/urgencias/novedades"

def main():
    print("Iniciando worker de urgencias...")
    
    verificar_conexion()
    
    print(f"Escuchando novedades en {API_URL}...")
    print("-" * 40)

    try:
        while True:
            try:
                respuesta = requests.get(API_URL, timeout=5)

                if respuesta.status_code == 200:
                    datos = respuesta.json()

                    nuevos = datos.get('total_nuevos', 0)
                    altas = datos.get('total_altas', 0)

                    print(f"[{time.strftime('%H:%M:%S')}] OK - Novedades: {nuevos} ingresos | {altas} altas.")
                    
                    if nuevos > 0:
                        for paciente in datos["nuevos_ingresos"]:
                            sip = paciente["datos_admision"]["sip_paciente"]
                            nivel = paciente["datos_triaje"]["nivel_manchester"]
                            print(f" -> Nuevo ingreso: SIP {sip} | Nivel: {nivel}")
                            
                            encolar_paciente(paciente)

                    if altas > 0:
                        for alta in datos["pacientes_alta"]:
                            id_ep = alta["id_episodio"]
                            destino = alta["destino_alta"]
                            print(f" <- ALTA: Episodio {id_ep} | Destino: {destino}")
                    
                    asignar_boxes()

                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Error en la API: {respuesta.status_code}")  
            
            except requests.exceptions.RequestException as e:
                print(f"[{time.strftime('%H:%M:%S')}] Error de conexión: {e}")

            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nWorker de urgencias detenido manualmente. Cerrando...")

if __name__ == "__main__":
    main()