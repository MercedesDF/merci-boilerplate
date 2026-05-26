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
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parents[2]
GLOSSARY_JSON = REPO_ROOT / 'laboratorio' / 'biblioteca' / 'glosario-tecnico.json'
GLOSSARY_MD = REPO_ROOT / 'biblioteca' / 'glosario-tecnico.md'
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
            except json.JSONDecodeError as e:
                print(f"\n❌ [Merci Error] El archivo JSON del glosario está corrupto: {e}")
                print("  🛑 El orquestador se ha detenido (Fail-Fast) para evitar la pérdida de datos y sobreescritura.")
                sys.exit(1)
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
    """Retorna terms_dict y context_dict con la frase donde apareció para ayudar al usuario."""
    terms_dict = {}
    context_dict = {}
    
    # Acrónimos y opcionalmente la siguiente palabra unida por guión (ej. AI-Changelog)
    pattern_acronym = re.compile(r'\b[A-Z][A-Z0-9]{1,9}(?:-[a-zA-Z0-9]+)?\b') 
    pattern_specific = re.compile(r'\b(DevSecOps|Zero-[A-Z][a-z]+|Shift-[A-Z][a-z]+)\b')
    
    ignore_words = {
        "HTML", "CSS", "JSON", "XML", "YAML", "HTTPS", "HTTP", "TODO", "FIXME", 
        "XXX", "ERROR", "WARN", "PHP", "URL", "CLI", "API", "OS", "PDF", "SEO",
        "UI", "UX", "VPN", "WP", "ABSPATH", "ACPI", "ID", "SSH",
        "ALL", "ANY", "AWS","APLICA", "NOTA", "INFO", "DEBUG",
        "TRACE", "FATAL", "FAIL", "PASS", "TRUE", "FALSE", "NULL", "NONE",
        "ESTE", "ESTA", "ESTO", "PARA", "COMO", "PERO", "SIEMPRE", "NUNCA"
    }
    
    archivos_objetivo = []
    
    # 1. Bitácoras (El flujo actual)
    archivos_objetivo.extend(BITACORA_DIR.rglob('bitacora*.md'))
    
    # 2. Toda la documentación técnica pública
    archivos_objetivo.extend((REPO_ROOT / "docs").rglob("*.md"))
    
    # 3. Manuales Operativos Maestros
    manuales = [
        REPO_ROOT / "instrucciones.md",
        REPO_ROOT / "README.md"
    ]
    archivos_objetivo.extend([m for m in manuales if m.exists()])
    
    for filepath in archivos_objetivo:
        if not filepath.exists(): continue
        fname = filepath.name
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if line.strip().startswith('```'): continue
                
                matches_acronym = list(pattern_acronym.finditer(line))
                matches_specific = list(pattern_specific.finditer(line))
                
                for match_obj in matches_acronym + matches_specific:
                    m = match_obj.group(0)
                    if m not in ignore_words and is_valid_term(m):
                        if m not in terms_dict:
                            terms_dict[m] = {}
                            # 5 palabras antes, el término, 5 palabras después
                            before = line[:match_obj.start()].split()[-5:]
                            after = line[match_obj.end():].split()[:5]
                            context_dict[m] = f"...{' '.join(before)} {m} {' '.join(after)}..."
                        if fname not in terms_dict[m]:
                            # Solo guardamos la primera aparición (línea) por archivo para no saturar el glosario
                            terms_dict[m][fname] = [f"L{i}"]
    return terms_dict, context_dict

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
            "temperature": 0.4
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
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    md = "---\n"
    md += "titulo: \"Glosario Técnico\"\n"
    md += "descripcion: \"Diccionario Data-Driven compilado automáticamente por el Agente Glosario.\"\n"
    md += "tema: \"DevSecOps y Gobernanza\"\n"
    md += "estado: \"publicado\"\n"
    md += f"alt_portada: \"Diccionario técnico automatizado {fecha_hoy}\"\n"
    md += f"fecha: \"{fecha_hoy}\"\n"
    md += "---\n\n"
    
    terminos = state_data.get("terminos", {})
    
    # Extraemos la fecha exacta de la última mutación del JSON matriz para control de versiones offline
    fecha_actualizacion = datetime.fromtimestamp(GLOSSARY_JSON.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if GLOSSARY_JSON.exists() else fecha_hoy
    
    md += "# Glosario Técnico DevSecOps & Arquitectura\n\n"
    md += "> **Estado del Documento:** Glosario vivo y autónomo. Un agente rastrea continuamente las bitácoras para extraer y definir nueva terminología DevSecOps.\n"
    md += f"> **Versión de control:** {len(terminos)} términos consolidados (Última actualización de datos: {fecha_actualizacion}).\n\n"
    md += "## Índice Alfabético\n\n"
    
    if not terminos:
        md += "*Aún no se han consolidado términos técnicos en el glosario. El Agente Autónomo está a la espera de procesar la próxima remesa de la bitácora.*\n\n"
    else:
        # Orden alfabético forzado (Case-Insensitive)
        for term_name in sorted(terminos.keys(), key=lambda x: x.lower()):
            t = terminos[term_name]
            md += f"### {term_name}\n"
            md += f"**Inglés:** {t.get('ingles', term_name)} | **Español:** {t.get('espanol', term_name)}\n\n"
            
            if "merci_explica" in t and t["merci_explica"]:
                md += f"**Definición:** {t.get('definicion', '')}\n\n"
                md += f"💡 **Merci Explica:** *{t['merci_explica']}*\n\n"
            else:
                md += f"**Definición:** {t.get('definicion', '')}\n\n"
            
            apariciones = t.get("apariciones", {})
            if apariciones:
                md += "**Apariciones en Bitácoras:**\n"
                for fname in sorted(apariciones.keys()):
                    # Ordenar las líneas (L1, L2, L10) numéricamente
                    lines_sorted = sorted(apariciones[fname], key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
                    md += f"- {fname}: {', '.join(lines_sorted)}\n"
                
            md += "\n---\n"
        
    with open(GLOSSARY_MD, 'w', encoding='utf-8') as f:
        f.write(md)

def main():
    use_ai = "--ai" in sys.argv
    state = load_glossary_state()
    
    # --- INICIO SINCRONIZACIÓN AUTOMÁTICA DE APARICIONES ---
    # Extraemos el estado actual de las bitácoras para ambos modos
    extracted, contexts = extract_terms_from_bitacoras()
    terminos_existentes = {k.lower() for k in state.get("terminos", {}).keys()}
    terminos_ignorados = {k.lower() for k in state.get("ignorados", [])}
    
    # Si un término ya existe, actualizamos sus líneas/archivos en tiempo real (Auto-Healing)
    modificado = False
    for term_key, term_data in state.get("terminos", {}).items():
        matched_ext = next((k for k in extracted.keys() if k.lower() == term_key.lower()), None)
        nuevas_apariciones = extracted[matched_ext] if matched_ext else {}
        if term_data.get("apariciones") != nuevas_apariciones:
            term_data["apariciones"] = nuevas_apariciones
            modificado = True
            
    if modificado:
        save_glossary_state(state)
    # --- FIN SINCRONIZACIÓN ---
    
    # Filtrar términos que ya están resueltos (ya sea en el glosario o en la lista de ignorados)
    new_terms = [t for t in extracted.keys() if t.lower() not in terminos_existentes and t.lower() not in terminos_ignorados]
    
    if not use_ai:
        # MODO COMPILACIÓN: Ultra rápido para el pipeline CI/CD (merci total)
        print("⚡ [Merci Glosario] Modo Compilación. Construyendo Markdown desde JSON...")
        
        if new_terms:
            print(f"  ⚠️ [Info] Tienes {len(new_terms)} término(s) nuevo(s) en la bitácora sin definir.")
            print(f"            Ejecuta 'merci glosario --ai' para revisarlos.")
            
        compile_markdown(state)
        sys.exit(0)

    # MODO INTELIGENCIA: Escaneo de términos y llamada a Ollama
    print("🤖 [Merci Glosario] Iniciando agente autónomo (Modo IA)...")
    if not PROMPT_FILE.exists():
        print(f"❌ Error: No se encontró el prompt en {PROMPT_FILE}")
        sys.exit(1)

    if not new_terms:
        print("✅ [Merci Glosario] No se detectaron términos nuevos. Actualizando cuadernillo y saliendo.")
        compile_markdown(state)
        sys.exit(0)
        
    print(f"🔍 [Merci Glosario] Quedan {len(new_terms)} términos en el backlog.")
    
    target_terms = []
    ignorados_en_sesion = []
    interrumpido = False
    san_pedro_count = 0
    
    # Triage Interactivo: El humano decide qué términos se envían al modelo local
    print("🤖 Modo Triage Activo. Clasifica los términos para el siguiente lote:")
    for term in sorted(new_terms):
        if len(target_terms) >= MAX_TERMS_PER_RUN:
            break
            
        resp = None
        while True:
            try:
                snippet = contexts.get(term, "")
                resp = input(f"❓ ¿Procesar '{term}'? (Visto en: \"{snippet}\")\n  [S=Sí / n=No / i=Ignorar]: ").strip().lower()
                if resp in ['s', '', 'n', 'i']:
                    break
                print("  ❌ Opción no válida. Por favor, responde con 's', 'n' o 'i'.")
            except KeyboardInterrupt:
                print("\n🛑 [Merci Glosario] Triage interrumpido por la usuaria. Guardando el progreso actual...")
                interrumpido = True
                break
                
        if interrumpido:
            break
        
        if resp == 's' or resp == '':
            target_terms.append(term)
        elif resp == 'i':
            ignorados_en_sesion.append(term)
        elif resp == 'n':
            if "rechazos" not in state: state["rechazos"] = {}
            state["rechazos"][term] = state["rechazos"].get(term, 0) + 1
            
            if state["rechazos"][term] >= 3:
                print(f"  🐓 [San Pedro] '{term}' negado 3 veces. Enviado a la lista negra definitivamente.")
                ignorados_en_sesion.append(term)
                san_pedro_count += 1
                del state["rechazos"][term]
            else:
                print(f"  ⏭️ '{term}' saltado por ahora ({state['rechazos'][term]}/3 avisos).")
            save_glossary_state(state)
            
    if ignorados_en_sesion:
        if "ignorados" not in state: state["ignorados"] = []
        state["ignorados"].extend(ignorados_en_sesion)
        save_glossary_state(state) # Guardamos los nuevos ignorados inmediatamente
        
    if interrumpido:
        if san_pedro_count > 0:
            print(f"\n  🐓 [San Pedro] Resumen: {san_pedro_count} término(s) bloqueado(s) definitivamente en esta sesión.")
        print("✅ [Merci Glosario] Actualizando cuadernillo y cerrando limpiamente.")
        compile_markdown(state)
        sys.exit(130)
        
    if not target_terms:
        if san_pedro_count > 0:
            print(f"\n  🐓 [San Pedro] Resumen: {san_pedro_count} término(s) bloqueado(s) definitivamente en esta sesión.")
        print("✅ [Merci Glosario] Ningún término para procesar. Actualizando cuadernillo y saliendo.")
        compile_markdown(state)
        sys.exit(0)
        
    print(f"🧠 Consultando a {MODEL} (JSON API) para el lote: {target_terms}...")
    
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
        
    # QUÉ HACE: Solo transfiere los datos puros.
    # POR QUÉ: Delega el 100% del comportamiento de la IA al archivo externo prompt-glosario.md (Separation of Concerns).
    user_prompt = f"Términos a definir ({len(target_terms)} en total):\n{', '.join(target_terms)}"
    
    try:
        response_data = generate_with_ollama(system_prompt, user_prompt)
        
        # Procesar la respuesta JSON de Ollama
        returned_terms = response_data.get("terminos", [])
        procesados = []
        
        if isinstance(returned_terms, dict):
            if "nombre" in returned_terms:
                returned_terms = [returned_terms]
            else:
                returned_terms = list(returned_terms.values())
                
        for t in returned_terms:
            if not isinstance(t, dict): continue
            raw_term_name = t.get("nombre")
            if not raw_term_name: continue
            
            # Búsqueda tolerante (case-insensitive) para evitar blacklisting accidental
            matched_target = next((target for target in target_terms if target.lower() == raw_term_name.lower()), None)
            
            if matched_target:
                procesados.append(matched_target)
                t["nombre"] = matched_target # Normalizar el nombre para evitar duplicados visuales
                t["apariciones"] = extracted.get(matched_target, {})
                state["terminos"][matched_target] = t
                
                # Feedback visual inmaculado en consola (DX)
                print(f"\n  ✨ [Término Consolidado]: {matched_target}")
                print(f"     🇪🇸 Español: {t.get('espanol', '')}")
                print(f"     🇬🇧 Inglés:  {t.get('ingles', '')}")
                print(f"     📖 Definición: {t.get('definicion', '')}")
                if t.get('merci_explica'):
                    print(f"     💡 Merci Explica: {t.get('merci_explica')}")
                
        # Fallback DevSecOps: Si la IA omite términos, NO los metemos en la lista negra oculta.
        # El usuario ha dicho explícitamente que los quiere (Triage: 'S').
        omitidos = [t for t in target_terms if t not in procesados]
        if omitidos:
            print(f"\n  ⚠️ [Merci Glosario] La IA desobedeció y omitió los siguientes términos: {', '.join(omitidos)}")
            print(f"     (Se mantendrán en tu cola para el próximo intento)")
            print(f"     [Depuración] JSON crudo devuelto por la IA: {json.dumps(response_data, ensure_ascii=False)}")
                
        # Guardar y compilar
        save_glossary_state(state)
        compile_markdown(state)
        
        if san_pedro_count > 0:
            print(f"\n  🐓 [San Pedro] Resumen: {san_pedro_count} término(s) bloqueado(s) definitivamente en esta sesión.")
            
        print(f"✅ [Merci Glosario] Extracción y compilación JSON completada con éxito.")
            
    except Exception as e:
        print(f"⚠️ [Merci Glosario] Error: {e}")
        print("  La ejecución del glosario se omitirá, pero el pipeline puede continuar.")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Glosario] Operación cancelada abruptamente. Saliendo limpiamente.")
        sys.exit(130)
