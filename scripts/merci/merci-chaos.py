#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-chaos.py — Agente de Chaos Engineering (Epic 2 Fase 4).
Objetivo: Simular una mutación o sabotaje en el código fuente utilizando IA,
ejecutar la auditoría para verificar que el sistema lo detecta, y finalmente 
auto-restaurar el entorno (Rollback).
"""

import os
import sys
import subprocess
import random
import re
import json
from pathlib import Path
try:
    from litellm import completion
    import litellm
    litellm.telemetry = False
    litellm.suppress_debug_info = True
except ImportError:
    print("ℹ️ [Merci Chaos] LiteLLM no está instalado. Saliendo.")
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO_ROOT / "laboratorio" / "prompts" / "prompt-chaos.md"

def extract_json_array(text: str) -> list:
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return []

def main():
    print("\n🐒 [Merci Chaos] Iniciando experimento de Chaos Engineering...")
    
    status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True)
    if status.stdout.strip():
        print("  🛑 [Seguridad] Tienes cambios sin guardar en Git. Ejecuta 'merci total' primero.")
        print("     El Chaos Monkey necesita un entorno inmaculado para hacer el Rollback seguro.")
        sys.exit(1)

    if not PROMPT_PATH.exists():
        print("  ❌ [Merci Error] Falta el prompt del Chaos Monkey.")
        sys.exit(1)

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    objetivos = [REPO_ROOT / "public" / "index.html", REPO_ROOT / "scripts" / "merci" / "merci-publish.py"]
    target_file = random.choice([f for f in objetivos if f.exists()])
    print(f"  🎯 Objetivo fijado: {target_file.relative_to(REPO_ROOT)}")

    original_content = target_file.read_text(encoding="utf-8")
    prompt = f"Código objetivo (fragmento inicial):\n{original_content[:2000]}"

    print("  🧠 Solicitando táctica de sabotaje a IA Local (qwen2.5-coder)...")
    try:
        respuesta = completion(model="ollama/qwen2.5-coder", api_base="http://localhost:11434", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], temperature=0.7, timeout=120)
        sabotajes = extract_json_array(respuesta.choices[0].message.content)
    except Exception as e_local:
        print(f"  ❌ [Merci Error] Falló el motor local: {e_local}"); sys.exit(1)

    if not sabotajes or not sabotajes[0].get("buscar") or sabotajes[0].get("buscar") not in original_content:
        print("  ℹ️ [Merci Info] La IA falló en apuntar al código exacto. Abortando.")
        if sabotajes and sabotajes[0].get("buscar"):
            print(f"     [Debug] La IA intentó buscar:\n{sabotajes[0].get('buscar')}")
        sys.exit(0)

    print(f"  😈 Mutando el archivo (Inyectando vulnerabilidad)...")
    print(f"     [Táctica] Reemplazó: {sabotajes[0]['buscar']}")
    print(f"     [Táctica] Por:       {sabotajes[0]['reemplazar']}")
    target_file.write_text(original_content.replace(sabotajes[0]["buscar"], sabotajes[0]["reemplazar"], 1), encoding="utf-8")

    try:
        print("\n  🛡️ Lanzando Auditoría DevSecOps para medir defensas...")
        env_aislado = os.environ.copy()
        env_aislado["MERCI_SKIP_AI"] = "1"
        resultado = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "merci" / "merci-audit.py")], cwd=REPO_ROOT, capture_output=True, text=True, env=env_aislado)
        
        salida = resultado.stdout.strip()
        # Un WARN también es una detección exitosa del linter, aunque no rompa la compilación
        if resultado.returncode != 0 or "WARN" in salida or "ERROR" in salida: print(f"\n  ✅ [ÉXITO DEL CAOS] El sistema detectó la anomalía.\n\n{salida}")
        else: print(f"\n  ❌ [VULNERABILIDAD] El escudo falló. El código malicioso pasó indetectado.\n\n{salida}")
    finally:
        print("\n  ⏪ Ejecutando Auto-Healing (Rollback)...")
        subprocess.run(["git", "restore", str(target_file)], cwd=REPO_ROOT)
        print(f"  ✨ {target_file.name} restaurado. Tu proyecto está a salvo.")

if __name__ == "__main__": main()