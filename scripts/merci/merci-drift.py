#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-drift.py — Detector de Deriva Documental (Document Drift).

Objetivo: Compara la presencia de los scripts del ecosistema frente a sus 
manuales operacionales específicos. Si un script no está documentado en 
sus correspondientes archivos, genera una advertencia y guarda un reporte.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts" / "merci"
DRIFT_REPORT_PATH = REPO_ROOT / "observabilidad" / ".drift_report.json"

# Mapeo de validación contextual por categorías de scripts
SCRIPT_MAPPINGS = {
    # Core DevSecOps (Deben estar en README.md e instrucciones.md)
    "merci-total.py": ["README.md", "instrucciones.md"],
    "merci-completo.py": ["README.md", "instrucciones.md"],
    "merci-init.py": ["README.md", "instrucciones.md"],
    "merci-commit.py": ["README.md", "instrucciones.md"],
    "merci-audit.py": ["README.md", "instrucciones.md"],
    "merci-release.py": ["README.md", "instrucciones.md"],
    
    # Compilación y SASS (Deben estar en instrucciones.md)
    "merci-styles.py": ["instrucciones.md"],
    "merci-watcher.py": ["instrucciones.md"],
    
    # Publicación y Contenidos (Deben estar en instrucciones.md y en su SOP específico)
    "merci-publish.py": ["instrucciones.md", "docs/flujo-publicacion-sop.md"],
    "merci-promote.py": ["instrucciones.md", "docs/flujo-publicacion-sop.md"],
    "merci-wp.py": ["instrucciones.md", "docs/integracion-wordpress.md"],
    "merci-shop.py": ["instrucciones.md", "docs/integracion-wordpress.md"],
    
    # SRE y Telemetría (Deben estar en instrucciones.md)
    "merci-sre.py": ["instrucciones.md"],
    "merci-telemetry.py": ["instrucciones.md"],
    "merci-extract-metrics.py": ["instrucciones.md"],
    
    # Seguridad y Robustez (Deben estar en instrucciones.md y en su SOP específico)
    "merci-hardening.py": ["instrucciones.md", "docs/checklist-hardening.md"],
    "merci-chaos.py": ["instrucciones.md"],
    "merci-auto-fix.py": ["instrucciones.md"],
    
    # IA y Gobernanza (Deben estar en instrucciones.md)
    "merci-brain.py": ["instrucciones.md"],
    "merci-ssot.py": ["instrucciones.md"],
    "merci-librarian.py": ["instrucciones.md"],
    "merci-drift.py": ["instrucciones.md"],
    "merci-glosario.py": ["instrucciones.md"],
    "merci-blogger.py": ["instrucciones.md"],
    "merci-queue.py": ["instrucciones.md"],
    "merci-linkedin.py": ["instrucciones.md"],
    
    # Copias de Seguridad (Deben estar en instrucciones.md)
    "merci-backup.py": ["instrucciones.md"],
    
    # Indexación y Sitemap (Deben estar en instrucciones.md)
    "merci-sitemap.py": ["instrucciones.md"],
    "merci-linkcheck.py": ["instrucciones.md"],
    
    # Watchers de multimedia (Deben estar en instrucciones.md)
    "merci-assets-watcher.py": ["instrucciones.md"],
    "merci-optimizer.py": ["instrucciones.md"],
    
    # Despliegue (Deben estar en instrucciones.md y en su Playbook específico)
    "merci-deploy.py": ["instrucciones.md", "docs/deployment-playbook.md"],
}

def main() -> None:
    """
    QUÉ HACE: Realiza una auditoría estática de presencia semántica cruzando scripts con sus manuales.
    POR QUÉ: Garantiza que no exista deriva documental (Document Drift) y que todo script esté documentado.
    """
    print("🕵️‍♂️  [Merci Drift] Analizando presencia semántica de scripts en manuales...")

    # Caché de lectura de archivos para optimizar tiempos de I/O
    file_contents = {}
    def get_file_content(rel_path: str) -> str:
        if rel_path not in file_contents:
            p = REPO_ROOT / rel_path
            file_contents[rel_path] = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
        return file_contents[rel_path]

    archivos_en_deriva = []
    
    if SCRIPTS_DIR.exists():
        for s in SCRIPTS_DIR.glob("*.py"):
            if s.name == "__init__.py":
                continue
            motivos = []
            
            # Buscar manuales asignados o aplicar fallback a instrucciones.md
            required_docs = SCRIPT_MAPPINGS.get(s.name, ["instrucciones.md"])
            faltantes = []
            for doc in required_docs:
                content = get_file_content(doc)
                if s.name not in content:
                    faltantes.append(doc)
            
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
    try:
        main()
    except Exception as e:
        print(f"❌ [Merci Drift] Error fatal inesperado: {e}")
        sys.exit(1)