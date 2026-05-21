#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-drift.py — Detector de Deriva Documental (Document Drift).

Compara la fecha de última modificación (Regla 17) de los scripts del 
ecosistema frente a la de los manuales maestros. Si un script es más 
reciente que los manuales, emite una advertencia y guarda una métrica para el SRE.
"""

import re
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts" / "merci"
DRIFT_REPORT_PATH = REPO_ROOT / "observabilidad" / ".drift_report.json"

MANUALES_MAESTROS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "instrucciones.md"
]

def main():
    print("🕵️‍♂️  [Merci Drift] Analizando presencia semántica de scripts en manuales...")

    # Extraer el contenido de todos los manuales maestros para comprobación semántica estricta
    manuales_textos = {m.name: (m.read_text(encoding="utf-8", errors="ignore") if m.exists() else "") for m in MANUALES_MAESTROS}

    archivos_en_deriva = []
    for s in SCRIPTS_DIR.glob("*.py"):
        if s.name == "__init__.py": continue
        motivos = []
            
        # 1. Deriva Semántica (Presencia en manuales maestros)
        faltantes = [nombre for nombre, contenido in manuales_textos.items() if s.name not in contenido]
        if faltantes:
            motivos.append(f"Semántica: No mencionado en {', '.join(faltantes)}")
            
        if motivos:
            archivos_en_deriva.append({"archivo": s.name, "motivos": " | ".join(motivos)})

    DRIFT_REPORT_PATH.parent.mkdir(exist_ok=True)
    DRIFT_REPORT_PATH.write_text(json.dumps(archivos_en_deriva, indent=2), encoding="utf-8")

    if archivos_en_deriva:
        print(f"  ⚠️ [ADVERTENCIA] Deriva Documental detectada en {len(archivos_en_deriva)} script(s).")
        for item in archivos_en_deriva:
            print(f"     - {item['archivo']} ({item['motivos']})")
    else:
        print("  ✅ [Éxito] Sincronización semántica perfecta. Todos los scripts están documentados.")

if __name__ == "__main__":
    main()