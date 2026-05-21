#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-auto-fix.py — Agente Autónomo de Reparación en CI/CD (Fase 2).

Objetivo: Escanear el repositorio en busca del primer error bloqueante 
reportado por `merci-audit.py` y solicitar a la API de contingencia en la 
nube (Gemini Flash) que genere un parche directo sobre el código fuente.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
import logging

try:
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    logging.getLogger('LiteLLM').setLevel(logging.ERROR)
    from litellm import completion
    import litellm
    litellm.telemetry = False  # Telemetría desactivada por DevSecOps
except ImportError:
    print("ℹ️ [Merci AI] LiteLLM no instalado. Omitiendo auto-fix.")
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parents[2]

def obtener_error_linter() -> dict | None:
    """Ejecuta el auditor maestro e intercepta el primer error encontrado."""
    audit_script = REPO_ROOT / "scripts" / "merci" / "merci-audit.py"
    resultado = subprocess.run([sys.executable, str(audit_script)], capture_output=True, text=True)
    
    for linea in resultado.stdout.splitlines():
        match = re.match(r"^ERROR (\w+) (.*?):(\d+): (.*)$", linea.strip())
        if match:
            return {
                "code": match.group(1),
                "file": match.group(2),
                "line": int(match.group(3)),
                "message": match.group(4)
            }
    return None

def aplicar_parche_ia(error: dict) -> bool:
    """Delega la reparación al modelo de contingencia (Hybrid Stack)."""
    file_path = REPO_ROOT / error["file"]
    if not file_path.exists():
        return False

    contenido_actual = file_path.read_text(encoding="utf-8")
    prompt = f"""Ejerce como un linter automatizado. Este archivo tiene un error:
Archivo: {error['file']}
Fallo: [{error['code']}] {error['message']} (Línea {error['line']})

Devuelve ÚNICAMENTE el código fuente completo con el error corregido.
NO uses bloques de markdown (ni ```python ni similares). Solo devuelve el código crudo para guardarlo directamente.

{contenido_actual}"""

    print(f"🤖 [Merci Brain Cloud] Solicitando parche a Gemini para {error['file']}...")
    try:
        respuesta = completion(
            model="gemini/gemini-1.5-flash",
            messages=[{"role": "user", "content": prompt}],
            api_key=os.environ.get("GEMINI_API_KEY")
        )
        nuevo_contenido = respuesta.choices.message.content.strip()
        
        # QUÉ HACE: Limpieza defensiva en caso de que la IA ignore la regla e inyecte Markdown.
        if nuevo_contenido.startswith("```"):
            nuevo_contenido = nuevo_contenido.split("\n", 1)[-1].rsplit("\n", 1)[0]
            
        file_path.write_text(nuevo_contenido, encoding="utf-8")
        print(f"✅ [Éxito] Archivo {error['file']} parcheado autónomamente.")
        return True
    except Exception as e:
        print(f"❌ [Merci Error] Fallo al generar parche en la nube: {e}")
        return False

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ [Merci AI] GEMINI_API_KEY no detectada. Cancelando Auto-Fix.")
        sys.exit(1)
        
    error_detectado = obtener_error_linter()
    if error_detectado:
        exito = aplicar_parche_ia(error_detectado)
        sys.exit(0 if exito else 1)
    else:
        print("✅ [Merci AI] Ningún error interceptado. Ecosistema limpio.")
        sys.exit(0)