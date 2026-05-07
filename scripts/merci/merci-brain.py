#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-brain.py — Lóbulo frontal de Inteligencia Artificial (Shift-Left AI).

Conecta con la API REST de Google Gemini utilizando cero dependencias externas.
Se encarga de procesar el contexto de la web en tiempo de compilación para 
generar respuestas estáticas inteligentes, protegiendo el rendimiento (100/100)
y evitando la exposición de claves en el frontend.
"""

import sys
import json
import re
import unicodedata
import time
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
PUBLIC_JS_DIR = REPO_ROOT / "public" / "js"

def slugify(texto: str) -> str:
    """Convierte un texto en una cadena segura para URLs (slug)."""
    texto = str(texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

def cargar_api_key():
    """Lee la clave de Gemini desde el entorno local seguro."""
    if not ENV_PATH.exists():
        return None
    for linea in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if linea.startswith("GEMINI_API_KEY="):
            return linea.split("=", 1)[1].strip().strip('"\'')
    return None

def auto_descubrir_modelo(api_key):
    """
    QUÉ HACE: Interroga a Google para saber qué modelos exactos están disponibles.
    POR QUÉ: Resuelve los errores 404 por restricciones regionales (UE) o cambios 
    de alias en la API, buscando dinámicamente el modelo más rápido permitido.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            validos = [
                m["name"].split("/")[-1] for m in data.get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", [])
                and "gemini" in m.get("name", "").lower()
            ]
            # Búsqueda flexible por subcadena para atrapar sufijos (-001, -002) y garantizar cuota de 1500/día
            for familia in ["1.5-flash", "1.5-pro", "2.0-flash"]:
                for v in validos:
                    if familia in v: return v
            # Si no encuentra ninguna familia prioritaria, coge la última para evitar las experimentales recientes
            return validos[-1] if validos else "gemini-pro"
    except Exception:
        return "gemini-pro"

def consultar_gemini(prompt, api_key, modelo="gemini-pro"):
    """Realiza una petición POST nativa a la API de Gemini."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        # Ajustamos la temperatura para respuestas concisas y precisas
        "generationConfig": {"temperature": 0.4}
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        error_info = e.read().decode("utf-8")
        return f"Error HTTP {e.code}: {e.reason}\nDetalle de la API: {error_info}"
    except Exception as e:
        return f"Error de conexión sináptica: {e}"

def generar_cerebro_estatico(api_key, modelo, force_clean=False):
    """
    QUÉ HACE: Escanea la biblioteca, pide saludos contextuales a Gemini y los guarda en un JSON.
    POR QUÉ: Permite a Merci tener respuestas inteligentes en cada artículo sin consumir
    tiempo de red (0 ms latencia) ni exponer la clave API en el navegador.
    """
    print("\n📚 [Merci Brain] Iniciando escaneo de la Biblioteca...")
    biblioteca_dir = REPO_ROOT / "biblioteca"
    output_json = PUBLIC_JS_DIR / "brain_data.json"
    
    if not biblioteca_dir.exists():
        print("  ⚠️ La carpeta biblioteca no existe.")
        return

    if force_clean and output_json.exists():
        print("  🧹 [Clean Build] Borrando memoria anterior para forzar regeneración...")
        output_json.unlink()

    # QUÉ HACE: Lee el cerebro existente para no repetir peticiones válidas (Incremental Build).
    brain_data = {}
    if output_json.exists():
        try:
            brain_data = json.loads(output_json.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    cuota_agotada = False
    
    for md_file in biblioteca_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match: continue
            
        yaml_raw = match.group(1)
        meta = {}
        for line in yaml_raw.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip().strip('"\'')
                
        if meta.get("estado", "borrador").lower() != "publicado":
            continue
            
        titulo = meta.get("titulo", md_file.stem)
        desc = meta.get("descripcion", "")
        url = f"/biblioteca/{slugify(titulo)}.html"
        
        # Si ya existe una respuesta válida generada por IA, la conservamos y saltamos en silencio
        if url in brain_data and not brain_data[url].startswith("Error HTTP") and not brain_data[url].startswith("[Fallback]"):
            continue
            
        # Circuit Breaker: Si la cuota ya se agotó en esta ejecución, mantenemos/creamos el fallback en silencio
        if cuota_agotada:
            if url not in brain_data or brain_data[url].startswith("Error HTTP"):
                brain_data[url] = f"[Fallback] Bienvenido a la lectura de: {titulo}."
            continue
        
        print(f"  🧠 Pensando saludo para: {titulo}...")
        prompt = f"Eres un asistente virtual técnico de la web merci-boilerplate.es (Arquitectura DevSecOps). El usuario acaba de entrar a leer el artículo titulado '{titulo}' (Contexto: {desc}). Escribe un saludo directo, inteligente y con un sutil toque 'geek' o de ingeniería (una sola frase, máximo 15 palabras) dándole la bienvenida a este contenido concreto. No uses comillas."
        
        respuesta = consultar_gemini(prompt, api_key, modelo)
        
        # Degradación elegante con Circuit Breaker
        if respuesta.startswith("Error HTTP"):
            print(f"  ⚠️ Cuota de API agotada. Suspendiendo peticiones y aplicando contingencia...")
            cuota_agotada = True
            brain_data[url] = f"[Fallback] Bienvenido a la lectura de: {titulo}."
        else:
            brain_data[url] = respuesta.replace('"', '').strip()
            # Respetar el límite estricto de la API gratuita (5 RPM)
            print("  ⏳ Enfriando sinapsis (15s) para evitar bloqueos por cuota de red...")
            time.sleep(15)

    # Guardar el JSON (Base de conocimientos estática)
    PUBLIC_JS_DIR.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(brain_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ ¡Cerebro estático generado! Guardado en {output_json.relative_to(REPO_ROOT)}")
    
    # Reporte final de contingencias
    fallbacks_count = sum(1 for v in brain_data.values() if v.startswith("[Fallback]"))
    if fallbacks_count > 0:
        print(f"  ℹ️  Info: Quedan {fallbacks_count} artículos pendientes de IA por límite de cuota. Se reintentarán automáticamente en el próximo 'merci total'.")

if __name__ == "__main__":
    print("🧠 [Merci Brain] Despertando lóbulo frontal...")
    force_clean = "--clean" in sys.argv
    api_key = cargar_api_key()
    
    if not api_key:
        print("  ⚠️ WARN: GEMINI_API_KEY no encontrada en el archivo .env.")
        print("  ℹ️  El asistente Merci utilizará sus respuestas genéricas por defecto.")
        sys.exit(0)
        
    modelo_activo = auto_descubrir_modelo(api_key)
    print(f"  📡 Conectando a la red neuronal (Modelo auto-descubierto: {modelo_activo})...")
    
    generar_cerebro_estatico(api_key, modelo_activo, force_clean)