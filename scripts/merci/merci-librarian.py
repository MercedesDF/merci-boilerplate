#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-librarian.py — Agente Bibliotecario (Fase 3).

Objetivo: Escanea la carpeta `laboratorio/notas_rapidas/`, aplica el prompt 
editorial a través del modelo de IA local (Ollama) y genera cuadernillos 
Markdown estructurados en el directorio de incubación (`laboratorio/`).
"""

import json
import os
import re
import subprocess
import sys
import warnings
from datetime import datetime
from pathlib import Path

# Silenciamos advertencias de deprecación de librerías de terceros (ej. google.generativeai) para mantener la consola limpia
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    import logging
    logging.getLogger('LiteLLM').setLevel(logging.ERROR)
    from litellm import completion
    import litellm
    litellm.telemetry = False
    litellm.suppress_debug_info = True
except ImportError:
    print("ℹ️ [Merci Librarian] LiteLLM no está instalado. Instalalo para usar el motor híbrido.")
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTES_DIR = REPO_ROOT / "laboratorio" / "notas_rapidas"
PROCESADAS_DIR = NOTES_DIR / "_procesadas"
LAB_DIR = REPO_ROOT / "laboratorio"
PROMPT_PATH = REPO_ROOT / "laboratorio" / "prompts" / "prompt-bibliotecario.md"
ENV_PATH = REPO_ROOT / ".env"

def consultar_ia_hibrida(prompt: str, system_prompt: str) -> str:
    """
    QUÉ HACE: Realiza una petición a Gemini Pro mediante LiteLLM, con fallback a Gemini Flash.
    POR QUÉ: Asegura la máxima capacidad analítica para cerrar la Épica.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.split("=", 1)[1].strip('"\'')
                os.environ["GEMINI_API_KEY"] = api_key
                break

    if not api_key:
        return "Error: GEMINI_API_KEY no detectada en el entorno ni en .env."

    try:
        respuesta = completion(
            model="gemini/gemini-1.5-pro-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            api_key=api_key,
            temperature=0.0,
            max_tokens=4000
        )
        return respuesta.choices[0].message.content.strip()
    except Exception as e_pro:
        print(f"  ⚠️ Gemini Pro no responde ({e_pro}). Ejecutando Fallback a Gemini Flash...")
        try:
            respuesta_flash = completion(
                model="gemini/gemini-2.5-flash",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                api_key=api_key,
                temperature=0.0,
                max_tokens=4000
            )
            return respuesta_flash.choices[0].message.content.strip()
        except Exception as e_flash:
            return f"Error HTTP Nube: Falló Pro y Flash. {e_flash}"

def get_bitacora_context(nota_cruda: str) -> str:
    """
    QUÉ HACE: Extrae palabras clave de la nota y filtra entradas relevantes de la bitácora (RAG Optimizado).
    POR QUÉ: Proporciona contexto histórico a la IA para evitar alucinaciones y mantener la trazabilidad.
    """
    bitacoras = list((REPO_ROOT / "laboratorio").glob("bitacora-tuempresa-epic-*.md"))
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
    """
    QUÉ HACE: Extrae el rol innegociable y las reglas editoriales del Agente.
    POR QUÉ: Carga la directiva del sistema desde el archivo de prompt para desacoplar el comportamiento del código.
    """
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

def process_note(note_path: Path) -> None:
    """
    QUÉ HACE: Analiza una nota cruda, pregunta por el tipo de documento y llama a la IA para darle formato.
    POR QUÉ: Automatiza la ingesta de borradores en la bandeja de entrada del laboratorio de forma interactiva.
    """
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
    
    print(f"  🧠 [Merci Librarian] Solicitando redacción a Antigravity (Gemini Pro)...")
    respuesta = consultar_ia_hibrida(prompt, system_prompt)
    
    if respuesta.startswith("Error"):
        print(f"  ❌ [Merci Error] Fallo total de IA Híbrida: {respuesta}")
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
    try:
        # Creamos los directorios si es la primera ejecución
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        PROCESADAS_DIR.mkdir(parents=True, exist_ok=True)
        
        notas = [p for p in NOTES_DIR.glob("*") if p.is_file() and p.suffix in {".txt", ".md"}]
        if not notas:
            print("ℹ️ [Merci Librarian] Estantería vacía. No hay notas nuevas en /notas_rapidas/")
            sys.exit(0)
            
        for nota in notas:
            process_note(nota)
    except Exception as e:
        print(f"❌ [Merci Librarian] Error fatal inesperado: {e}")
        sys.exit(1)