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
from pathlib import Path

try:
    from litellm import completion
    import litellm
    litellm.telemetry = False  # Telemetría desactivada por DevSecOps
except ImportError:
    print("ℹ️ [Merci Librarian] LiteLLM no está instalado. Omitiendo agente bibliotecario.")
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTES_DIR = REPO_ROOT / "laboratorio" / "notas_rapidas"
PROCESADAS_DIR = NOTES_DIR / "_procesadas"
LAB_DIR = REPO_ROOT / "laboratorio"
PROMPT_PATH = REPO_ROOT / "laboratorio" / "prompts" / "prompt-bibliotecario.md"

def get_system_prompt() -> str:
    """Extrae el rol innegociable y las reglas editoriales del Agente."""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8", errors="replace")
    print("❌ [Merci Error] Falta el archivo rector: prompt-bibliotecario.md")
    sys.exit(1)

def clean_markdown(text: str) -> str:
    """
    QUÉ HACE: Elimina los delimitadores de bloque de código (```markdown) que la IA 
    suele inyectar alrededor de sus respuestas.
    POR QUÉ: Garantiza que el archivo resultante tenga el YAML Frontmatter en la primera línea.
    """
    text = text.strip()
    if text.startswith("```markdown"):
        text = text[11:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
        
    if text.endswith("```"):
        text = text[:-3].strip()
        
    return text

def process_note(note_path: Path):
    print(f"\n🤖 [Merci Librarian] Analizando nota cruda: {note_path.name}")
    
    print("  ¿Qué tipo de conocimiento contiene esta nota?")
    print("  [1] Cuadernillo (Táctico - Biblioteca) [Defecto]")
    print("  [2] Compendio (Estratégico - Biblioteca)")
    print("  [3] Art de Coté (Experimento / Descartado - SSG Estático)")
    opcion = input("  👉 Elige una opción [1]: ").strip()
    
    tipo_doc = "cuadernillo"
    prefijo = "cuadernillo-borrador"
    destino_dir = LAB_DIR
    instrucciones_extra = ""

    if opcion == "2":
        tipo_doc = "compendio"
        prefijo = "compendio-borrador"
        instrucciones_extra = "ATENCIÓN: Estás redactando un COMPENDIO estratégico de alto nivel. Agrupa los conceptos con visión arquitectónica en lugar de centrarte en un solo bug."
    elif opcion == "3":
        prefijo = "art-de-cote-borrador"
        destino_dir = LAB_DIR / "art-de-cote"
        destino_dir.mkdir(parents=True, exist_ok=True)
        instrucciones_extra = "ATENCIÓN: Estás redactando un ART DE COTÉ. Enfatiza el valor del código descartado o el experimento realizado para que quede como registro."
    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    note_content = note_path.read_text(encoding="utf-8", errors="replace")
    prompt = f"La fecha actual es {fecha_hoy}. {instrucciones_extra}\n\nTransforma las siguientes notas en bruto en un documento estructurado:\n\n{note_content}"
    
    # Inyectamos el tipo de documento dinámicamente en el molde mental (System Prompt)
    system_prompt = get_system_prompt().replace('tipo: "cuadernillo"', f'tipo: "{tipo_doc}"')
    
    try:
        respuesta = completion(
            model="ollama/phi3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            api_base="http://localhost:11434",
            max_tokens=1500
        )
        
        md_final = clean_markdown(respuesta.choices[0].message.content)
        output_path = destino_dir / f"{prefijo}-{note_path.stem}.md"
        output_path.write_text(md_final, encoding="utf-8")
        
        print(f"  ✅ [Éxito] Cuadernillo generado: {output_path.relative_to(REPO_ROOT)}")
        
        # QUÉ HACE: Mueve el original a `_procesadas`.
        # POR QUÉ: Seguridad DLP. Nunca destruimos la información base por si la IA alucina.
        note_path.rename(PROCESADAS_DIR / note_path.name)
        
    except Exception as e:
        print(f"  ❌ [Merci Error] Fallo al consultar la IA: {e}")

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