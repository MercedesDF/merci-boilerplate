#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-chaos.py — Agente de Chaos Engineering (Epic 2 Fase 4).

Objetivo: Simular una mutación o sabotaje en el código fuente utilizando IA,
ejecutar la auditoría para verificar que el sistema lo detecta, y finalmente 
auto-restaurar el entorno (Rollback).
"""

import json
import logging
import os
import random
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    logging.getLogger('LiteLLM').setLevel(logging.ERROR)
    import litellm
    from litellm import completion
    litellm.telemetry = False
    litellm.suppress_debug_info = True
except ImportError:
    print("ℹ️ [Merci Chaos] LiteLLM no está instalado. Saliendo.")
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO_ROOT / "laboratorio" / "prompts" / "prompt-chaos.md"
PRIVADO_DIR = REPO_ROOT / ".privado"
CHAOS_LOG_PATH = PRIVADO_DIR / "chaos-audit.json"


def extract_json_array(text: str) -> list:
    """
    QUÉ HACE: Busca y extrae un array JSON de un bloque de texto dado.
    POR QUÉ: Resuelve la deserialización cuando el LLM devuelve texto adicional alrededor del JSON.
    """
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        json_str = match.group(0)
        # Saneamiento: Los LLMs a veces escapan comillas simples (\'), lo cual es inválido en JSON
        json_str = json_str.replace("\\'", "'")
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    return []


def main() -> None:
    """
    QUÉ HACE: Orquesta un experimento de Chaos Engineering inyectando vulnerabilidades aleatorias en el código,
              verificando si el escudo linter las detecta, y aplicando un rollback seguro.
    POR QUÉ: Garantiza de forma empírica la resiliencia del sistema de integración y la fiabilidad de las auditorías.
    """
    print("\n🐒 [Merci Chaos] Iniciando experimento de Chaos Engineering...")
    
    status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True)
    
    # Filtramos la telemetría SRE y logs privados para no bloquear bucles de testing
    cambios_reales = [line for line in status.stdout.splitlines() if "observabilidad/" not in line and ".privado/" not in line]
    if cambios_reales:
        print("  🛑 [Seguridad] Tienes cambios sin guardar en Git. Ejecuta 'merci total' primero.")
        print("     El Chaos Monkey necesita un entorno inmaculado para hacer el Rollback seguro.")
        sys.exit(1)

    print("  🎲 Seleccionando táctica de caos aleatoria...")
    tactica = random.choice(["A", "B", "C"])
    
    if tactica == "A":
        print("  🏴‍☠️ [Táctica A] Sabotaje de Código (Mutación AST)")
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
            print(f"  ❌ [Merci Error] Falló el motor local: {e_local}")
            sys.exit(1)

        if not sabotajes or not sabotajes[0].get("buscar") or sabotajes[0].get("buscar") not in original_content:
            print("  ℹ️ [Merci Info] La IA falló en apuntar al código exacto. Abortando.")
            sys.exit(0)

        print("  😈 Mutando el archivo (Inyectando vulnerabilidad)...")
        print(f"     [Táctica] Reemplazó: {sabotajes[0]['buscar']}")
        print(f"     [Táctica] Por:       {sabotajes[0]['reemplazar']}")
        target_file.write_text(original_content.replace(sabotajes[0]["buscar"], sabotajes[0]["reemplazar"], 1), encoding="utf-8")
        inyeccion_texto = sabotajes[0]["reemplazar"]
        
    elif tactica == "B":
        print("  🔌 [Táctica B] Corte de Red a API Ollama")
        print("  😈 Simulando caída catastrófica del motor local asignando un puerto muerto...")
        os.environ["OLLAMA_API_BASE"] = "http://localhost:9999"
        target_file = REPO_ROOT / "scripts" / "merci" / "merci-brain.py"
        inyeccion_texto = "API Base = http://localhost:9999"
        
    elif tactica == "C":
        print("  👻 [Táctica C] Deriva Documental (Drift)")
        print("  😈 Inyectando script fantasma no documentado en el ecosistema...")
        target_file = REPO_ROOT / "scripts" / "merci" / "merci-fantasma-chaos.py"
        target_file.write_text("#!/usr/bin/env python3\nprint('Script fantasma')", encoding="utf-8")
        inyeccion_texto = "Script fantasma (merci-fantasma-chaos.py) inyectado"

    try:
        if tactica == "A":
            print("\n  🛡️ Lanzando Auditoría DevSecOps para medir defensas...")
            env_aislado = os.environ.copy()
            env_aislado["MERCI_SKIP_AI"] = "1"
            resultado = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "merci" / "merci-audit.py")], cwd=REPO_ROOT, capture_output=True, text=True, env=env_aislado)
            
            salida = resultado.stdout.strip()
            fue_detectado = False
            
            if resultado.returncode != 0 or "WARN" in salida or "ERROR" in salida: 
                print(f"\n  ✅ [ÉXITO DEL CAOS] El sistema detectó la anomalía.\n\n{salida}")
                fue_detectado = True
            else: 
                print(f"\n  ❌ [VULNERABILIDAD] El escudo falló. El código/archivo pasó indetectado.\n\n{salida}")

        elif tactica == "C":
            print("\n  🛡️ Lanzando Detector de Deriva Documental para medir defensas...")
            env_aislado = os.environ.copy()
            resultado = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "merci" / "merci-drift.py")], cwd=REPO_ROOT, capture_output=True, text=True, env=env_aislado)
            
            salida = resultado.stdout.strip()
            fue_detectado = False
            
            if resultado.returncode != 0 or "Deriva Documental" in salida: 
                print(f"\n  ✅ [ÉXITO DEL CAOS] El sistema detectó el script fantasma.\n\n{salida}")
                fue_detectado = True
            else: 
                print(f"\n  ❌ [VULNERABILIDAD] El escudo falló. El código/archivo pasó indetectado.\n\n{salida}")

        elif tactica == "B":
            print("\n  🛡️ Lanzando Motor de IA (merci-brain.py) para probar Fallback...")
            # Aquí forzamos --clean para asegurarnos de que intente llamar a la IA
            env_aislado = os.environ.copy()
            resultado = subprocess.run([sys.executable, str(target_file), "--clean"], cwd=REPO_ROOT, capture_output=True, text=True, env=env_aislado)
            
            salida = resultado.stdout.strip()
            fue_detectado = False
            
            if "Fallback a Antigravity" in salida and resultado.returncode == 0:
                print(f"\n  ✅ [ÉXITO DEL CAOS] El sistema detectó la caída local y aplicó Fallback a Gemini con éxito.\n\n{salida}")
                fue_detectado = True
            else:
                print(f"\n  ❌ [VULNERABILIDAD] El sistema falló o no aplicó el Fallback.\n\n{salida}")
            
        # --- REGISTRO DE AUDITORÍA PRIVADA ---
        PRIVADO_DIR.mkdir(exist_ok=True)
        logs_chaos = []
        if CHAOS_LOG_PATH.exists():
            try:
                logs_chaos = json.loads(CHAOS_LOG_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
                
        logs_chaos.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tactica": tactica,
            "objetivo": target_file.name,
            "inyeccion": inyeccion_texto,
            "defensa_exitosa": fue_detectado
        })
        CHAOS_LOG_PATH.write_text(json.dumps(logs_chaos, indent=2), encoding="utf-8")
        
    finally:
        print("\n  ⏪ Ejecutando Auto-Healing (Rollback)...")
        if tactica == "A":
            subprocess.run(["git", "restore", str(target_file)], cwd=REPO_ROOT)
        elif tactica == "B":
            # Eliminamos la variable de entorno para el proceso actual si persistiera (aunque subprocess usa copia)
            if "OLLAMA_API_BASE" in os.environ:
                del os.environ["OLLAMA_API_BASE"]
        elif tactica == "C":
            if target_file.exists():
                target_file.unlink()
                
        print(f"  ✨ Entorno restaurado. Tu proyecto está a salvo.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Chaos] Experimento cancelado por la usuaria.")
        sys.exit(130)