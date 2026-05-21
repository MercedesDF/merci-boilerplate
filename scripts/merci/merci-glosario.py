#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-glosario.py — Compilador de Glosario Autónomo (Data-Driven).

Busca términos técnicos no definidos en las bitácoras del proyecto,
delega a un modelo local (Ollama) su definición en formato JSON estructurado,
mantiene un registro maestro (JSON SSOT) y compila un Markdown estático ordenado.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GLOSSARY_JSON = REPO_ROOT / 'laboratorio' / 'biblioteca' / 'glosario-tecnico.json'
GLOSSARY_MD = REPO_ROOT / 'laboratorio' / 'biblioteca' / 'glosario-tecnico.md'
PROMPT_FILE = REPO_ROOT / 'laboratorio' / 'prompts' / 'prompt-glosario.md'
BITACORA_DIR = REPO_ROOT / 'laboratorio'

MODEL = 'qwen2.5-coder'
MAX_TERMS_PER_RUN = 3

def load_glossary_state():
    """Carga el estado maestro del glosario desde el JSON."""
    if GLOSSARY_JSON.exists():
        with open(GLOSSARY_JSON, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"terminos": {}, "ignorados": []}
    return {"terminos": {}, "ignorados": []}

def save_glossary_state(data):
    """Guarda el estado maestro modificado en el JSON."""
    with open(GLOSSARY_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_valid_term(term):
    if len(set(term.replace('-', ''))) == 1:
        return False
    date_markers = ['YYYY', 'AAAA', 'MM', 'DD', 'YYYY-MM', 'AAAA-MM', 'AAAA-MM-DD']
    if any(marker in term for marker in date_markers):
        return False
    return True

def extract_terms_from_bitacoras():
    """Retorna { 'Termino': { 'archivo.md': ['L123', ...] } } para facilitar el guardado en JSON."""
    terms_dict = {}
    
    pattern_acronym = re.compile(r'\b[A-Z][A-Z0-9]{2,7}\b') 
    pattern_specific = re.compile(r'\b(DevSecOps|Zero-[A-Z][a-z]+|Shift-[A-Z][a-z]+)\b')
    
    ignore_words = {
        "HTML", "CSS", "JSON", "XML", "YAML", "HTTPS", "HTTP", "TODO", "FIXME", 
        "XXX", "ERROR", "WARN", "PHP", "URL", "CLI", "API", "OS", "PDF", "SEO",
        "SSL", "TLS", "UI", "UX", "VPN", "WP", "ABSPATH", "ACPI", "ID", "SSH",
        "ALL", "ANY", "AWS", "DOM", "SSG", "APLICA", "NOTA", "INFO", "DEBUG",
        "TRACE", "FATAL", "FAIL", "PASS", "TRUE", "FALSE", "NULL", "NONE",
        "ESTE", "ESTA", "ESTO", "PARA", "COMO", "PERO", "SIEMPRE", "NUNCA"
    }
    
    for filepath in BITACORA_DIR.glob('bitacora*.md'):
        if not filepath.exists(): continue
        fname = filepath.name
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if line.strip().startswith('```'): continue
                
                matches = pattern_acronym.findall(line) + pattern_specific.findall(line)
                for m in set(matches):
                    if m not in ignore_words and is_valid_term(m):
                        if m not in terms_dict:
                            terms_dict[m] = {}
                        if fname not in terms_dict[m]:
                            terms_dict[m][fname] = []
                        line_ref = f"L{i}"
                        if line_ref not in terms_dict[m][fname]:
                            terms_dict[m][fname].append(line_ref)
    return terms_dict

def generate_with_ollama(system_prompt, user_prompt):
    """Llama a la API de Ollama exigiendo estricto formato JSON."""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": MODEL,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "format": "json", # Garantiza respuesta JSON
        "options": {
            "temperature": 0.1
        }
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return json.loads(result.get("response", "{}"))
    except Exception as e:
        raise Exception(f"Error procesando Ollama (JSON): {e}")

def compile_markdown(state_data):
    """Compila el JSON maestro hacia un archivo Markdown (Artefacto Build-Time)."""
    md = "# Glosario Técnico DevSecOps & Arquitectura\n\n"
    md += "Este glosario contiene términos y expresiones informáticas de nivel intermedio y avanzado, extraídos del análisis de las bitácoras del proyecto.\n\n"
    md += "## Índice Alfabético\n\n"
    
    terminos = state_data.get("terminos", {})
    
    if not terminos:
        md += "*Aún no se han consolidado términos técnicos en el glosario. El Agente Autónomo está a la espera de procesar la próxima remesa de la bitácora.*\n\n"
    else:
        # Orden alfabético forzado (Case-Insensitive)
        for term_name in sorted(terminos.keys(), key=lambda x: x.lower()):
            t = terminos[term_name]
            md += f"### {term_name}\n"
            md += f"**Inglés:** {t.get('ingles', term_name)}\n"
            md += f"**Español:** {t.get('espanol', term_name)}\n\n"
            md += f"**Definición:** {t.get('definicion', '')}\n\n"
            
            apariciones = t.get("apariciones", {})
            if apariciones:
                md += "**Apariciones en Bitácoras:**\n"
                for fname in sorted(apariciones.keys()):
                    # Ordenar las líneas (L1, L2, L10) numéricamente
                    lines_sorted = sorted(apariciones[fname], key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
                    md += f"- `{fname}`: {', '.join(lines_sorted)}\n"
                
            md += "\n---\n"
        
    with open(GLOSSARY_MD, 'w', encoding='utf-8') as f:
        f.write(md)

def main():
    use_ai = "--ai" in sys.argv
    state = load_glossary_state()
    
    if not use_ai:
        # MODO COMPILACIÓN: Ultra rápido para el pipeline CI/CD (merci total)
        print("⚡ [Merci Glosario] Modo Compilación. Construyendo Markdown desde JSON...")
        compile_markdown(state)
        sys.exit(0)

    # MODO INTELIGENCIA: Escaneo de términos y llamada a Ollama
    print("🤖 [Merci Glosario] Iniciando agente autónomo (Modo IA)...")
    if not PROMPT_FILE.exists():
        print(f"❌ Error: No se encontró el prompt en {PROMPT_FILE}")
        sys.exit(1)

    terminos_existentes = {k.lower() for k in state.get("terminos", {}).keys()}
    terminos_ignorados = {k.lower() for k in state.get("ignorados", [])}
    
    extracted = extract_terms_from_bitacoras()
    
    # Filtrar términos que ya están resueltos (ya sea en el glosario o en la lista de ignorados)
    new_terms = [t for t in extracted.keys() if t.lower() not in terminos_existentes and t.lower() not in terminos_ignorados]
    
    if not new_terms:
        print("✅ [Merci Glosario] No se detectaron términos nuevos.")
        sys.exit(0)
        
    target_terms = sorted(new_terms)[:MAX_TERMS_PER_RUN]
    
    print(f"🔍 [Merci Glosario] Quedan {len(new_terms)} términos en el backlog.")
    print(f"🧠 Consultando a {MODEL} (JSON API) para el lote: {target_terms}...")
    
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
        
    user_prompt = f"Define los siguientes términos DevSecOps:\n{', '.join(target_terms)}"
    
    try:
        response_data = generate_with_ollama(system_prompt, user_prompt)
        
        # Procesar la respuesta JSON de Ollama
        returned_terms = response_data.get("terminos", [])
        procesados = []
        
        for t in returned_terms:
            term_name = t.get("nombre")
            if term_name and term_name in target_terms:
                procesados.append(term_name)
                # Inyectar las apariciones que extrajimos previamente
                t["apariciones"] = extracted.get(term_name, {})
                # Guardar en el estado maestro
                state["terminos"][term_name] = t
                
        # Los términos que le pasamos a Ollama pero que Ollama ignoró
        # (porque no son DevSecOps) van a la lista de ignorados
        for t in target_terms:
            if t not in procesados:
                if "ignorados" not in state: state["ignorados"] = []
                state["ignorados"].append(t)
                
        # Guardar y compilar
        save_glossary_state(state)
        compile_markdown(state)
        
        print(f"✅ [Merci Glosario] Extracción y compilación JSON completada con éxito.")
            
    except Exception as e:
        print(f"⚠️ [Merci Glosario] Error: {e}")
        print("  La ejecución del glosario se omitirá, pero el pipeline puede continuar.")
        sys.exit(0)

if __name__ == "__main__":
    main()
