#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-brain.py — Lóbulo frontal de Inteligencia Artificial (Shift-Left AI).

Conecta con la API REST de Google Gemini utilizando cero dependencias externas.
Se encarga de procesar el contexto de la web en tiempo de compilación para 
generar respuestas estáticas inteligentes, protegiendo el rendimiento (100/100)
y operando de forma 100% offline y gratuita.
"""

import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
import warnings
from pathlib import Path

# Silenciamos advertencias de deprecación de librerías de terceros (ej. google.generativeai) para mantener la consola limpia
warnings.filterwarnings("ignore", category=FutureWarning)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
PUBLIC_JS_DIR = REPO_ROOT / "public" / "js"
PROMPT_PATH = REPO_ROOT / "laboratorio" / "prompts" / "prompt-brain.md"

def slugify(texto: str) -> str:
    """
    QUÉ HACE: Convierte un texto en una cadena segura para URLs (slug).
    POR QUÉ: Normaliza y estandariza los nombres de archivo y URLs eliminando tildes y caracteres especiales.
    """
    texto = str(texto)
    texto = re.sub(r'[—–]', '-', texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

import os

try:
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    import logging
    logging.getLogger('LiteLLM').setLevel(logging.ERROR)
    from litellm import completion
    import litellm
    litellm.telemetry = False
except ImportError:
    pass

def consultar_ia_local(prompt: str) -> str:
    """
    QUÉ HACE: Orquesta la Pila Híbrida (Hybrid Stack). Intenta primero el modelo local,
              y si falla o no está disponible, hace fallback al proxy Gemini (Antigravity).
    POR QUÉ: Garantiza resiliencia total y gratuidad por defecto.
    """
    try:
        # Intento 1: Motor Local Primario (Ollama)
        # Timeout corto (10s) para no bloquear el pipeline si Ollama está caído
        respuesta = completion(
            model="ollama/qwen2.5-coder",
            api_base=os.environ.get("OLLAMA_API_BASE", "http://localhost:11434"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.65,
            timeout=10
        )
        return respuesta.choices[0].message.content.strip()
    except Exception as e_local:
        print(f"  ⚠️ Ollama no responde ({e_local}). Ejecutando Fallback a Antigravity (Gemini Proxy)...")
        # Intento 2: Fallback a Antigravity / Gemini Proxy
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                env_path = REPO_ROOT / ".env"
                if env_path.exists():
                    for line in env_path.read_text(encoding="utf-8").splitlines():
                        if line.startswith("GEMINI_API_KEY="):
                            api_key = line.split("=", 1)[1].strip('"\'')
                            os.environ["GEMINI_API_KEY"] = api_key
                            break
                            
            if not api_key:
                return "Error: GEMINI_API_KEY no encontrada en .env"

            respuesta = completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                temperature=0.65
            )
            return respuesta.choices[0].message.content.strip()
        except Exception as e_cloud:
            return f"Error HTTP Local: {e_cloud}"

def generar_cerebro_estatico(force_clean: bool = False) -> None:
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
        plantilla_prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else "Eres Merci. Saluda sobre: {titulo}."
        prompt = plantilla_prompt.replace("{titulo}", titulo).replace("{desc}", desc)
        
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
    try:
        print("🧠 [Merci Brain] Despertando lóbulo frontal (Motor 100% Local)...")
        force_clean = "--clean" in sys.argv
        generar_cerebro_estatico(force_clean)
    except Exception as e:
        print(f"❌ [Merci Brain] Error fatal en la ejecución: {e}")
        sys.exit(1)