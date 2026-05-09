#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-ssot.py — Agente Sync SSOT (Fase 3).

Objetivo: Analiza las últimas entradas de la bitácora activa y verifica si el 
ROADMAP-AI-ORQUESTACION-SELF-HEALING-SYSTEM.md necesita ser actualizado 
(marcar tareas como completadas [x] o deprecadas). Si detecta deriva documental, 
auto-sana el archivo del Roadmap reescribiéndolo automáticamente.
"""

import sys
from pathlib import Path
import warnings
import json
import urllib.request
import re

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from litellm import completion
    import litellm
    litellm.telemetry = False
    litellm.suppress_debug_info = True
except ImportError:
    print("ℹ️ [Merci SSOT] LiteLLM no está instalado. Omitiendo agente SSOT.")
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
ROADMAP_PATH = REPO_ROOT / "laboratorio" / "ROADMAP-AI-ORQUESTACION-SELF-HEALING-SYSTEM.md"
BITACORA_PATH = REPO_ROOT / "laboratorio" / "bitacora-merci-boilerplate-orquestacion-ia.md"

def cargar_api_key():
    if not ENV_PATH.exists():
        return None
    for linea in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if linea.startswith("GEMINI_API_KEY="):
            return linea.split("=", 1)[1].strip().strip('"\'')
    return None

def auto_descubrir_modelo(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            validos = [m["name"].split("/")[-1] for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", []) and "gemini" in m.get("name", "").lower()]
            for familia in ["1.5-flash", "1.5-pro"]:
                for v in validos:
                    if familia in v: return v
            return "gemini-1.5-flash"
    except Exception:
        return "gemini-1.5-flash"

def clean_markdown(text: str) -> str:
    """Limpia el código de salida de la IA para que sea Markdown puro."""
    # Buscar el inicio real del Markdown y amputar la basura conversacional
    inicio_md = text.find("# 🗺️ ROADMAP")
    if inicio_md == -1:
        inicio_md = text.find("# ")
    if inicio_md != -1:
        text = text[inicio_md:]
        
    text = text.strip()
    if text.startswith("```markdown"):
        text = text[11:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip() + "\n"

def main():
    print("\n🤖 [Merci SSOT] Analizando deriva documental entre Bitácora y Roadmap...")
    
    if not ROADMAP_PATH.exists() or not BITACORA_PATH.exists():
        print("  ❌ [Merci Error] No se encuentra el Roadmap o la Bitácora de IA.")
        return

    roadmap_content = ROADMAP_PATH.read_text(encoding="utf-8")
    bitacora_full = BITACORA_PATH.read_text(encoding="utf-8")
    
    # Extraer solo las últimas 2 entradas de la bitácora para ser precisos y evitar diluir el prompt
    entradas = re.split(r'(?=### \d{4}-\d{2}-\d{2})', bitacora_full)
    bitacora_reciente = "".join(entradas[1:3]) if len(entradas) > 1 else bitacora_full[:2000]

    # QUÉ HACE: Amputa matemáticamente todo el texto de la bitácora excepto el bloque "Hecho".
    # POR QUÉ: Previene la alucinación inercial. Si la IA no lee el bloque "Siguiente paso", es imposible que asuma tareas futuras como completadas.
    hechos = re.findall(r'\*\*Hecho:\*\*(.*?)(?=\*\*Detalle técnico:|\*\*Motivo / criterio:|\*\*Siguiente paso o deuda:|### |$)', bitacora_reciente, re.DOTALL)
    bitacora_filtrada = "\n".join([h.strip() for h in hechos]) if hechos else "No hay acciones registradas."

    system_prompt = """Eres el Agente SSOT de un ecosistema DevSecOps.
Tu misión es actualizar el ROADMAP basándote en los últimos avances de la BITÁCORA.

INSTRUCCIONES DE RAZONAMIENTO PREVIO (Piensa paso a paso):
1. Analiza los "Hechos" extraídos de la Bitácora.
2. Busca qué tareas pendientes `- [ ]` del Roadmap se corresponden con esos hechos (algo descartado o relegado a cloud también se considera completado).
3. Escribe en texto plano qué tareas vas a actualizar de `[ ]` a `[x]`. Si no hay evidencia en "Hecho", no marques nada nuevo. Si se menciona un círculo rojo en la bitácora, añade 🔴.
4. Si NO hay coincidencias, declara explícitamente la palabra clave "SIN_CAMBIOS" y detente por completo.

INSTRUCCIONES DE SALIDA:
- Si hubo avances: Imprime todo el código del Roadmap actualizado. DEBES REESCRIBIR EL ROADMAP ENTERO DE PRINCIPIO A FIN.
- Si NO hubo avances: NO escribas el Roadmap. Limítate a emitir tu razonamiento y la palabra clave "SIN_CAMBIOS"."""

    prompt = f"--- ESTADO ACTUAL DEL ROADMAP ---\n{roadmap_content}\n\n--- ÚLTIMOS HECHOS EXTRAÍDOS ---\n{bitacora_filtrada}"

    api_key = cargar_api_key()
    raw_response = None

    if api_key:
        modelo_activo = auto_descubrir_modelo(api_key)
        print(f"  🧠 Consultando a {modelo_activo} en la nube...")
        try:
            respuesta = completion(
                model=f"gemini/{modelo_activo}",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                api_key=api_key,
                temperature=0.0,
                max_tokens=4000,
                timeout=600
            )
            raw_response = respuesta.choices[0].message.content
        except Exception as e_cloud:
            print(f"  ⚠️ [Merci Warn] Falló Gemini ({e_cloud}). Intentando Fallback local con Ollama (qwen2.5-coder)...")
    else:
        print("  ⚠️ [Merci Warn] Falta GEMINI_API_KEY. Delegando directamente a IA Local (qwen2.5-coder)...")

    if not raw_response:
        # QUÉ HACE: Delega la tarea a Ollama localmente si no hay API Key o si la nube falla.
        # POR QUÉ: Garantiza la Degradación Elegante (Graceful Degradation) para que el agente siga operativo offline.
        try:
            respuesta = completion(
                model="ollama/qwen2.5-coder",
                api_base="http://localhost:11434",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=4000,
                timeout=600
            )
            raw_response = respuesta.choices[0].message.content
        except Exception as e_local:
            print(f"  ❌ [Merci Error] Falló el motor local de Ollama. Detalle: {e_local}")
            return

    try:
        if "SIN_CAMBIOS" in raw_response or "No hay tareas completadas" in raw_response:
            print("  ℹ️ [Merci Info] Sin avances en roadmap-ai. Ya está perfectamente sincronizado.")
            return

        nuevo_roadmap = clean_markdown(raw_response)
        
        # ESCUDO ANTI-ALUCINACIONES (Sanity Checks)
        if len(nuevo_roadmap) < len(roadmap_content) * 0.5:
            print("  ❌ [Merci Error] La IA devolvió un resumen en lugar del documento completo. Destrucción evitada.")
            return
        if "# " not in nuevo_roadmap:
            print("  ❌ [Merci Error] La IA no devolvió un formato Markdown válido. Destrucción evitada.")
            return
        
        if nuevo_roadmap.strip() != roadmap_content.strip():
            # Identificar qué fases han sido actualizadas comparando líneas
            old_lines = roadmap_content.strip().splitlines()
            new_lines = nuevo_roadmap.strip().splitlines()
            fases_modificadas = set()
            fase_actual = "Fase General"
            
            for i, new_line in enumerate(new_lines):
                if new_line.startswith("## "):
                    fase_actual = new_line.replace("##", "").strip()
                if i >= len(old_lines) or new_line != old_lines[i]:
                    fases_modificadas.add(fase_actual)
                    
            ROADMAP_PATH.write_text(nuevo_roadmap, encoding="utf-8")
            print("  ✅ [Éxito] Deriva documental sanada. Roadmap reescrito automáticamente.")
            if fases_modificadas:
                print(f"  🗺️  Avance registrado en: {', '.join(fases_modificadas)}")
        else:
            print("  ℹ️ [Merci Info] Sin avances en roadmap-ai. Ya está perfectamente sincronizado.")
            
    except Exception as e:
        print(f"  ❌ [Merci Error] Fallo procesando la respuesta de la IA: {e}")

if __name__ == "__main__":
    main()