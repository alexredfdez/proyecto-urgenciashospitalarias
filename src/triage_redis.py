import json
import time
import redis

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)


def inicializar_boxes():
    for i in range(1, 6):
        box_key = f"box_{i}"
        if not redis_client.exists(box_key):
            redis_client.hset(
                box_key,
                mapping={
                    "estado": "disponible",
                    "paciente": "",
                    "tiempo_ingreso": "",
                }
            )
    print("Boxes inicializados correctamente.")

def verificar_conexion():
    try: 
        if redis_client.ping():
            print("Conexion a Redis: OK")
            inicializar_boxes()
    except redis.ConnectionError:
        print("ERROR: No se pudo conectar a Redis. ¿Está levantado el contenedor?")

def encolar_paciente(paciente):
    id_episodio = paciente["id_episodio"]
    llegada = paciente["datos_adminsion"]["timestamp_llegada"]
    espera_min = paciente["datos_triaje"]["tiempo_max_espera_min"]

    score = llegada + (espera_min * 60)

    redis_client.set (f"paciente: {id_episodio}", json.dumps(paciente))

    redis_client.zadd("cola_pacientes", {id_episodio: score})
    print(f"  [REDIS] Paciente {id_episodio} encolado con score {score}.")

    def asignar_boxes():
        for i in range(1, 6):
            box_key = f"box_{i}"
            estado = redis_client.hget(box_key, "estado")

            if estado == "libre":
                paciente_urgente = redis_client.zpopmin(
                    "urgencias:cola_espera",
                    count=1
                )
                if paciente_urgente:
                    id_episodio = paciente_urgente[0][0]
                redis_client.hset(
                    box_key,
                    mapping={
                        "estado": "ocupado",
                        "id_episodio": id_episodio,
                        "hora_entrada": time.time()
                    }
                )
                print(f"   [BOX] Paciente {id_episodio} asignado al {box_key}.")
            else:
                break


if __name__ == "__main__":
    verificar_conexion()






