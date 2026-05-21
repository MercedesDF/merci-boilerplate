#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-librarian.py — Agente Bibliotecario (Fase 3).

Objetivo: Escanea la carpeta `laboratorio/notas_rapidas/`, aplica el prompt 
editorial a través del modelo de IA local (Ollama) y genera cuadernillos 
Markdown estructurados en el directorio de incubación (`laboratorio/`).
"""

import os
import sys
from datetime import datetime
import json
import urllib.request
from pathlib import Path
import warnings
import re
import subprocess

# Silenciamos advertencias de deprecación de librerías de terceros (ej. google.generativeai) para mantener la consola limpia
warnings.filterwarnings("ignore", category=FutureWarning)

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTES_DIR = REPO_ROOT / "laboratorio" / "notas_rapidas"
PROCESADAS_DIR = NOTES_DIR / "_procesadas"
LAB_DIR = REPO_ROOT / "laboratorio"
PROMPT_PATH = REPO_ROOT / "laboratorio" / "prompts" / "prompt-bibliotecario.md"
ENV_PATH = REPO_ROOT / ".env"

def consultar_ia_local(prompt, system_prompt):
    """Realiza una petición POST nativa a la API local de Ollama."""
    # QUÉ HACE: Envía el prompt y el molde mental (system) al endpoint de la API local de Ollama sin librerías externas.
    # POR QUÉ: Erradica la dependencia de LiteLLM y la nube, consolidando la arquitectura 100% local.
    try:
        local_url = "http://localhost:11434/api/generate"
        local_payload = {
            "model": "qwen2.5-coder",
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_ctx": 4096
            }
        }
        local_req = urllib.request.Request(local_url, data=json.dumps(local_payload).encode("utf-8"), method="POST")
        local_req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(local_req, timeout=600) as local_response:
            local_data = json.loads(local_response.read().decode("utf-8"))
            return local_data["response"].strip()
    except Exception as e_local:
        return f"Error HTTP Local: {e_local}"

def get_bitacora_context(nota_cruda: str) -> str:
    """Extrae palabras clave de la nota y filtra entradas relevantes de la bitácora (RAG Optimizado)."""
    bitacoras = [LAB_DIR / "bitacora-merci-boilerplate-orquestacion-ia.md", LAB_DIR / "bitacora-merci-boilerplate.md"]
    contexto = ""
    palabras_clave = [p.lower() for p in re.findall(r'\b[a-zA-Z]{5,}\b', nota_cruda)]

    for bitacora in bitacoras:
        if bitacora.exists():
            texto = bitacora.read_text(encoding="utf-8", errors="replace")
            entradas = re.split(r'(?=### \d{4}-\d{2}-\d{2}(?:\s\d{2}:\d{2})?)', texto)
            relevantes = []
            for entrada in entradas:
                if not entrada.strip(): continue
                if any(kw in entrada.lower() for kw in palabras_clave):
                    relevantes.append(entrada.strip())
                    if len(relevantes) >= 2: break # Solo las 2 más relevantes por archivo
            if relevantes:
                contexto += f"\n--- Entradas relevantes de {bitacora.name} ---\n" + "\n\n".join(relevantes) + "\n"
    return contexto[:3000] # Límite estricto de seguridad para modelos locales

def get_system_prompt() -> str:
    """Extrae el rol innegociable y las reglas editoriales del Agente."""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8", errors="replace")
    print("❌ [Merci Error] Falta el archivo rector: prompt-bibliotecario.md")
    sys.exit(1)

def clean_markdown(text: str) -> str:
    """
    QUÉ HACE: Elimina texto conversacional previo ("Here is the output:") y delimitadores.
    POR QUÉ: Garantiza que el archivo comience estrictamente por el YAML Frontmatter (---).
    """
    # 1. Buscar el inicio real del YAML Frontmatter y amputar la basura conversacional
    inicio_yaml = text.find("---\n")
    if inicio_yaml != -1:
        text = text[inicio_yaml:]
    
    # 2. Limpiar cierres de bloque de código al final
    text = text.strip()
    if text.endswith("```"):
        text = text[:-3].strip()
        
    return text

def process_note(note_path: Path):
    print(f"\n🤖 [Merci Librarian] Analizando nota cruda: {note_path.name}")
    
    print("  ¿Qué tipo de conocimiento contiene esta nota?")
    print("  [1] Cuadernillo (Táctico - Biblioteca) [Defecto]")
    print("  [2] Compendio (Estratégico - Biblioteca)")
    print("  [3] Art de Coté (Experimento / Descartado - SSG Estático)")
    print("  [4] Solo Post Marketing (Blog/LinkedIn - Sin documento técnico)")
    opcion = input("  👉 Elige una opción [1]: ").strip()
    
    if opcion == "4":
        print("\n  🚀 Transfiriendo la nota cruda directamente al Agente Blogger...")
        subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "merci" / "merci-blogger.py"), str(note_path)])
        return

    tipo_doc = "cuadernillo"
    prefijo = "cuadernillo"
    # QUÉ HACE: Centraliza la salida de todos los documentos en una única bandeja de entrada.
    # POR QUÉ: Separa los documentos recién creados por la IA de los borradores maduros listos para promoción.
    destino_dir = LAB_DIR / "incubacion"
    destino_dir.mkdir(parents=True, exist_ok=True)
    instrucciones_extra = ""
    plantilla_path = REPO_ROOT / "docs" / "plantilla-cuadernillo.md"

    if opcion == "2":
        tipo_doc = "compendio"
        prefijo = "compendio"
        instrucciones_extra = "ATENCIÓN: Estás redactando un COMPENDIO estratégico de alto nivel. Agrupa los conceptos con visión arquitectónica en lugar de centrarte en un solo bug."
        plantilla_path = REPO_ROOT / "docs" / "plantilla-proyecto.md"
    elif opcion == "3":
        prefijo = "art-de-cote"
        instrucciones_extra = "ATENCIÓN: Estás redactando un ART DE COTÉ. Enfatiza el valor del código descartado o el experimento realizado para que quede como registro."
        plantilla_path = REPO_ROOT / "docs" / "plantilla-art-de-cote.md"

    if plantilla_path.exists():
        plantilla_content = plantilla_path.read_text(encoding="utf-8", errors="replace")
        instrucciones_extra += f"\n\nREGLA ESTRICTA DE FORMATO: Tu respuesta DEBE ser un calco exacto de la siguiente plantilla. Debes rellenar los valores del YAML Frontmatter y seguir la estructura de cabeceras mostrada a continuación:\n\n{plantilla_content}\n"

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    note_content = note_path.read_text(encoding="utf-8", errors="replace")
    bitacora_context = get_bitacora_context(note_content)
    prompt = f"La fecha actual es {fecha_hoy}. {instrucciones_extra}\n\nREGLA DE IDIOMA INNEGOCIABLE: Todo el texto generado DEBE estar redactado exclusivamente en Castellano (Español de España). Queda estrictamente prohibido el uso del inglés.\n\nREGLA DE ESTRUCTURACIÓN (Zero-Hallucination): Tu objetivo principal es DAR FORMATO a la 'NOTA CRUDA' encajándola en la plantilla solicitada. NO inventes código, NO inventes soluciones técnicas ni comandos que no estén explícitamente en la nota o en la bitácora. Limítate a estructurar la información en los '3 átomos'.\n\n--- NOTA CRUDA (TEMA PRINCIPAL) ---\n{note_content}\n\n--- CONTEXTO DE LA BITÁCORA (MATERIAL DE APOYO SECUNDARIO) ---\n{bitacora_context}"
    
    # Inyectamos el tipo de documento dinámicamente en el molde mental (System Prompt)
    system_prompt = get_system_prompt().replace('tipo: "cuadernillo"', f'tipo: "{tipo_doc}"')
    
    print(f"  🧠 [Merci Librarian] Solicitando redacción a Ollama local (qwen2.5-coder)...")
    respuesta = consultar_ia_local(prompt, system_prompt)
    
    if respuesta.startswith("Error HTTP Local"):
        print(f"  ❌ [Merci Error] Fallo total de IA Local: {respuesta}")
        return
            
    try:
        md_final = clean_markdown(respuesta)
        output_path = destino_dir / f"{prefijo}-{note_path.stem}.md"
        output_path.write_text(md_final, encoding="utf-8")
        
        print(f"  ✅ [Éxito] Cuadernillo generado: {output_path.relative_to(REPO_ROOT)}")
        
        # QUÉ HACE: Mueve el original a `_procesadas`.
        # POR QUÉ: Seguridad DLP. Nunca destruimos la información base por si la IA alucina.
        note_path.rename(PROCESADAS_DIR / note_path.name)
        
        # BARRERA DE ENCADENAMIENTO (Agent Chaining)
        crear_blog = input(f"\n  👉 ¿Quieres que el Blogger redacte un post promocionando este {tipo_doc}? (s/N): ").strip().lower() == 's'
        if crear_blog:
            print("\n  🚀 Pasando el testigo al Agente Blogger...")
            subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "merci" / "merci-blogger.py"), str(output_path)])

    except Exception as e:
        print(f"  ❌ [Merci Error] Fallo procesando la respuesta de la IA: {e}")

if __name__ == "__main__":
    # Creamos los directorios si es la primera ejecución
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESADAS_DIR.mkdir(parents=True, exist_ok=True)
    
    notas = [p for p in NOTES_DIR.glob("*") if p.is_file() and p.suffix in {".txt", ".md"}]
    if not notas:
        print("ℹ️ [Merci Librarian] Estantería vacía. No hay notas nuevas en /notas_rapidas/")
        sys.exit(0)
        
    for nota in notas:
        process_note(nota)