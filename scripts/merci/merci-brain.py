#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-brain.py — Lóbulo frontal de Inteligencia Artificial (Shift-Left AI).

Conecta con la API REST de Google Gemini utilizando cero dependencias externas.
Se encarga de procesar el contexto de la web en tiempo de compilación para 
generar respuestas estáticas inteligentes, protegiendo el rendimiento (100/100)
y operando de forma 100% offline y gratuita.
"""

import sys
import json
import re
import unicodedata
import urllib.request
import urllib.error
from pathlib import Path
import warnings

# Silenciamos advertencias de deprecación de librerías de terceros (ej. google.generativeai) para mantener la consola limpia
warnings.filterwarnings("ignore", category=FutureWarning)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
PUBLIC_JS_DIR = REPO_ROOT / "public" / "js"

def slugify(texto: str) -> str:
    """Convierte un texto en una cadena segura para URLs (slug)."""
    texto = str(texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

def consultar_ia_local(prompt):
    """Realiza una petición POST nativa a la API local de Ollama (qwen2.5-coder)."""
    # QUÉ HACE: Envía el prompt de generación de texto al endpoint de la API local de Ollama.
    # POR QUÉ: Aísla el proceso de la nube, garantizando cero latencia de red y privacidad total.
    try:
        local_url = "http://localhost:11434/api/generate"
        local_payload = {
            "model": "qwen2.5-coder",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.4}
        }
        local_req = urllib.request.Request(local_url, data=json.dumps(local_payload).encode("utf-8"), method="POST")
        local_req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(local_req, timeout=120) as local_response:
            local_data = json.loads(local_response.read().decode("utf-8"))
            return local_data["response"].strip()
    except Exception as e_local:
        return f"Error HTTP Local: {e_local}"

def generar_cerebro_estatico(force_clean=False):
    """
    QUÉ HACE: Escanea la biblioteca, pide saludos contextuales a Ollama local y los guarda en un JSON.
    POR QUÉ: Permite a Merci tener respuestas inteligentes en cada artículo sin consumir
    tiempo de red (0 ms latencia) ni depender de servicios externos de terceros.
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
    
    fallo_local = False
    
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
            
        # Circuit Breaker: Si el servidor local falló en esta ejecución, mantenemos/creamos el fallback en silencio
        if fallo_local:
            if url not in brain_data or brain_data[url].startswith("Error HTTP"):
                brain_data[url] = f"[Fallback] Bienvenido a la lectura de: {titulo}."
            continue
        
        print(f"  🧠 Pensando saludo para: {titulo}...")
        prompt = f"Eres un asistente virtual técnico de la web merci-boilerplate.es (Arquitectura DevSecOps). El usuario acaba de entrar a leer el artículo titulado '{titulo}' (Contexto: {desc}). Escribe un saludo directo, inteligente y con un sutil toque 'geek' o de ingeniería (una sola frase, máximo 15 palabras) dándole la bienvenida a este contenido concreto. No uses comillas."
        
        respuesta = consultar_ia_local(prompt)
        
        if respuesta.startswith("Error HTTP Local"):
            print(f"  ⚠️ Error de conexión con Ollama. Suspendiendo peticiones y aplicando contingencia...")
            fallo_local = True
            brain_data[url] = f"[Fallback] Bienvenido a la lectura de: {titulo}."
        else:
            brain_data[url] = respuesta.replace('"', '').strip()

    # Guardar el JSON (Base de conocimientos estática)
    PUBLIC_JS_DIR.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(brain_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ ¡Cerebro estático generado! Guardado en {output_json.relative_to(REPO_ROOT)}")
    
    # Reporte final de contingencias
    fallbacks_count = sum(1 for v in brain_data.values() if v.startswith("[Fallback]"))
    if fallbacks_count > 0:
        print(f"  ℹ️  Info: Quedan {fallbacks_count} artículos pendientes de IA por fallo de conexión local. Verifica Ollama.")

if __name__ == "__main__":
    print("🧠 [Merci Brain] Despertando lóbulo frontal (Motor 100% Local)...")
    force_clean = "--clean" in sys.argv
    
    generar_cerebro_estatico(force_clean)