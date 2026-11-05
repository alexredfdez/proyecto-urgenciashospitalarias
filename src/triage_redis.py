import json
import time
import redis

# Conexión a Redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def inicializar_boxes():
    """Asegura que los 5 boxes existen en Redis al arrancar."""
    for i in range(1, 6):
        box_key = f"box:{i}"
        if not redis_client.exists(box_key):
            redis_client.hset(box_key, mapping={"estado": "libre", "id_episodio": "", "hora_entrada": ""})
    print("Boxes inicializados correctamente.")

def verificar_conexion():
    """Verifica la conexión con Redis e inicializa los boxes."""
    try:
        if redis_client.ping():
            print("Conexión a Redis: OK")
            inicializar_boxes()
    except redis.exceptions.ConnectionError:
        print("ERROR: No se pudo conectar a Redis. ¿Está levantado el contenedor?")

def encolar_paciente(paciente):
    """Calcula el score Earliest Deadline First y encola al paciente en Redis."""
    id_episodio = paciente['id_episodio']
    llegada = paciente['datos_admision']['timestamp_llegada']
    espera_min = paciente['datos_triaje']['tiempo_max_espera_min']
    
    # Algoritmo Earliest Deadline First: score = llegada + (espera * 60)
    score = llegada + (espera_min * 60)
    
    # Guardar los datos completos del paciente como JSON
    redis_client.set(f"paciente:{id_episodio}", json.dumps(paciente))
    
    # Añadir a la cola de espera ordenada por score
    redis_client.zadd("urgencias:cola_espera", {id_episodio: score})
    print(f"   [REDIS] Paciente {id_episodio} encolado con score {score}")

def asignar_boxes():
    """Busca boxes libres y asigna los pacientes con mayor prioridad (menor score)."""
    for i in range(1, 6):
        box_key = f"box:{i}"
        estado = redis_client.hget(box_key, "estado")
        
        if estado == "libre":
            # Extrae el paciente con menor score
            paciente_urgente = redis_client.zpopmin("urgencias:cola_espera", count=1)
            
            if paciente_urgente:
                id_episodio = paciente_urgente[0][0]
                redis_client.hset(box_key, mapping={
                    "estado": "ocupado", 
                    "id_episodio": id_episodio, 
                    "hora_entrada": time.time()
                })
                print(f"   [BOX] Paciente {id_episodio} asignado al {box_key}.")
            else:
                break

def procesar_alta_redis(id_episodio):
    """Libera el box del paciente, recupera sus datos y lo borra de Redis."""
    # 1. Buscar en qué box estaba y liberarlo
    for i in range(1, 6):
        box_key = f"box:{i}"
        if redis_client.hget(box_key, "id_episodio") == id_episodio:
            redis_client.hset(box_key, mapping={"estado": "libre", "id_episodio": "", "hora_entrada": ""})
            print(f"   [BOX] {box_key} liberado (paciente {id_episodio} dado de alta).")
            break
    
    # 2. Recuperar todos los datos clínicos del paciente
    datos_str = redis_client.get(f"paciente:{id_episodio}")
    
    if datos_str:
        datos_paciente = json.loads(datos_str)
        
        # 3. Borrar rastro de Redis (del String y de la cola)
        redis_client.delete(f"paciente:{id_episodio}")
        redis_client.zrem("urgencias:cola_espera", id_episodio)
        
        # Devolver los datos como diccionario
        return datos_paciente
        
    return None

if __name__ == "__main__":
    verificar_conexion()