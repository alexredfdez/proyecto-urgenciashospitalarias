from pymongo import MongoClient

mongourl = "mongodb://admin:admin@mongo:27017/?authSource=admin"
nombredatabase = "urgencias"
coleccion = "episodios_urgencias"

def conectar_mongo():
    cliente = MongoClient(mongourl)
    cliente.admin.command("ping")
    base_datos = cliente[nombredatabase]
    coleccion_mongo = base_datos[coleccion]
    return cliente, coleccion_mongo

def cargar_en_mongo(documentos):
    cliente, coleccion = conectar_mongo()
    try:
        # crea un índice único
        coleccion.create_index(
            "id_episodio",
            unique=True
        )
        # inserta los documentos obtenidos por parámetro en la base de datos
        for documento in documentos:
            coleccion.replace_one(
                {"id_episodio": documento["id_episodio"]},
                documento,
                upsert=True
            )
    finally:
        cliente.close()


