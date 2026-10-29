from __future__ import annotations

import hmac
import hashlib
import json
from pathlib import Path
from typing import Any
from etl_historico import ejecutar_etl


def anonimizar_sip(sip: str | None, clave_secreta: str) -> str | None:
    # Ofuscamos el SIP con HMAC-SHA256 y truncamos a 16 caracteres
    if not sip or not isinstance(sip, str):
        return None
    
    clave_bytes = clave_secreta.encode("utf-8")
    sip_bytes = sip.strip().encode("utf-8")
    hash_obj = hmac.new(clave_bytes, sip_bytes, hashlib.sha256)
    
    return hash_obj.hexdigest()[:16]


def agrupar_edad(edad: Any) -> str | None:
    # Transformamos la edad exacta en un rango decenal
    try:
        edad_int = int(edad)
        if edad_int < 0:
            return None
    except (TypeError, ValueError):
        return None
    
    min_rango = (edad_int // 10) * 10
    max_rango = min_rango + 9
    
    return f"[{min_rango}-{max_rango}]"


def anonimizar_documentos(documentos: list[dict[str, Any]], clave_secreta: str) -> list[dict[str, Any]]:
    # Recorremos y aplicamos las reglas de anonimización a cada documento
    documentos_anonimizados = []
    
    for doc in documentos:
        doc_anonimo = doc.copy()
        
        # Ofuscamos el SIP
        if "sip_paciente" in doc_anonimo:
            doc_anonimo["sip_paciente"] = anonimizar_sip(doc_anonimo["sip_paciente"], clave_secreta)
            
        # Agrupamos la edad
        if "edad" in doc_anonimo:
            doc_anonimo["edad"] = agrupar_edad(doc_anonimo["edad"])
            
        # Sustituimos campos de nombre por un identificador secuencial único
        nombre_encontrado = False
        for campo_nombre in ("nombre", "nombre_paciente"):
            if campo_nombre in doc_anonimo:
                doc_anonimo[campo_nombre] = f"PACIENTE-ANON-{contador_paciente:05d}"
                nombre_encontrado = True
        
        # Incrementamos el contador solo si se ha enmascarado un nombre en este registro
        if nombre_encontrado:
            contador_paciente += 1

        
        documentos_anonimizados.append(doc_anonimo)
        
    return documentos_anonimizados


def guardar_en_json(documentos: list[dict[str, Any]], ruta_salida: Path) -> None:
    # Guardamos los documentos anonimizados en un archivo JSON local
    if not documentos:
        print("⚠️ No hay documentos para guardar.")
        return

    try:
        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(documentos, f, ensure_ascii=False, indent=4)
            
        print(f"💾 ¡{len(documentos)} documentos guardados con éxito en '{ruta_salida.name}'!")
        
    except Exception as e:
        print(f"❌ Error al guardar el archivo JSON: {e}")


def main() -> None:
    # Configuración y ejecución principal del proceso
    CLAVE_SECRETA_PRUEBA = "mi_clave_secreta_super_segura_urgencias"
    
    raiz = Path(__file__).resolve().parent.parent
    ruta_csv = raiz / "data" / "admisiones_historico.csv"
    ruta_json = raiz / "data" / "partes_clinicos.json"
    ruta_salida_json = raiz / "data" / "historico_anonimizado.json"
    
    try:
        print("🚀 Iniciando proceso de anonimización...")
        print("📂 Ejecutando ETL original...")
        documentos = ejecutar_etl(ruta_csv, ruta_json)
        
        print("🔒 Aplicando reglas de anonimización...")
        documentos_seguros = anonimizar_documentos(documentos, CLAVE_SECRETA_PRUEBA)
        
        print("💾 Guardando resultados...")
        guardar_en_json(documentos_seguros, ruta_salida_json)
        
        print("✨ ¡Proceso finalizado con éxito!")
                
    except Exception as e:
        print(f"❌ Error crítico: {e}")


if __name__ == "__main__":
    main()