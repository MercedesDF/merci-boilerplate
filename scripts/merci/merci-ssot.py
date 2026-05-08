#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-ssot.py — Agente Sync SSOT (Fase 3).

Verifica que la última entrada de la bitácora esté reflejada en el Roadmap.
Si detecta tareas hechas que no están marcadas con [x], avisa al usuario.
"""
import sys
from pathlib import Path

try:
    from litellm import completion
    import litellm
    litellm.telemetry = False
except ImportError:
    print("ℹ️ [Merci SSOT] LiteLLM no instalado. Omitiendo agente.")
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parents[2]
BITACORA_PATH = REPO_ROOT / "laboratorio" / "bitacora-merci-boilerplate-orquestacion-ia.md"
ROADMAP_PATH = REPO_ROOT / "laboratorio" / "ROADMAP-AI-ORQUESTACION-SELF-HEALING-SYSTEM.md"

def obtener_ultima_entrada() -> str:
    """Extrae solo el texto de la última entrada cronológica."""
    if not BITACORA_PATH.exists(): return ""
    contenido = BITACORA_PATH.read_text(encoding="utf-8")
    partes = contenido.split("### ")
    if len(partes) > 1:
        return "### " + partes[1].split("### ")[0].strip()
    return ""

def main():
    if not ROADMAP_PATH.exists():
        print("❌ [Merci Error] No se encuentra el Roadmap.")
        sys.exit(1)
        
    ultima_bitacora = obtener_ultima_entrada()
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    
    print("🤖 [Merci SSOT] Cruzando datos semánticos entre Bitácora y Roadmap...")
    
    prompt = f"""
Eres un auditor DevSecOps encargado de mantener la Única Fuente de Verdad (SSOT).
Compara la última acción realizada con el Roadmap del proyecto.

ÚLTIMA ACCIÓN (Bitácora):
{ultima_bitacora}

ROADMAP:
{roadmap}

TAREA: ¿Hay alguna tarea descrita como completada en la Bitácora que todavía tenga una casilla vacía '- [ ]' en el Roadmap?
Si TODO está sincronizado, responde EXACTAMENTE: "✅ SSOT Sincronizado: No hay deriva documental."
Si falta marcar alguna casilla, responde con una advertencia indicando qué línea exacta debe marcarse con '[x]'.
Sé extremadamente breve y directo.
"""
    
    try:
        respuesta = completion(
            model="ollama/phi3",
            messages=[
                {"role": "system", "content": "Eres un auditor estricto. Respuestas cortas."},
                {"role": "user", "content": prompt}
            ],
            api_base="http://localhost:11434",
            max_tokens=250
        )
        resultado = respuesta.choices[0].message.content.strip()
        print(f"\n{resultado}\n")
    except Exception as e:
        print(f"❌ [Merci SSOT] Fallo al consultar Ollama: {e}")
        
if __name__ == "__main__":
    main()