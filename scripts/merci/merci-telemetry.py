#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-telemetry.py — Inyector dinámico de telemetría del proyecto.

Calcula métricas vivas del repositorio (commits, agentes, líneas de doc)
y las inyecta en las páginas estáticas (Portada y Sobre Mí) para que 
los dashboards reflejen el estado real del ecosistema.
"""

import re
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "public" / "index.html"
SOBRE_MI_HTML = REPO_ROOT / "public" / "sobre-mi" / "index.html"

def get_git_commits() -> str:
    try:
        result = subprocess.run(["git", "rev-list", "--count", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        return "N/D"

def get_active_days() -> str:
    try:
        # Extrae fechas únicas de commits para contar solo los días de trabajo real
        result = subprocess.run("git log --format='%cd' --date=short | sort -u | wc -l", cwd=REPO_ROOT, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        return "N/D"

def get_agent_count() -> str:
    agentes = list((REPO_ROOT / "scripts" / "merci").glob("*.py"))
    # Restamos __init__.py si llegara a existir para que sea exacto
    return str(len([a for a in agentes if a.name != "__init__.py"]))

def get_doc_lines() -> str:
    total_lines = 0
    for md_file in REPO_ROOT.rglob("*.md"):
        if any(part in {".venv", "node_modules", ".git"} for part in md_file.parts):
            continue
        try:
            total_lines += sum(1 for _ in open(md_file, 'r', encoding='utf-8', errors='ignore'))
        except Exception:
            pass
    # Formatear con separador de miles estilo europeo (ej. 15.420)
    return f"{total_lines:,}".replace(",", ".")

def get_latest_release() -> str:
    readme_merci = REPO_ROOT / "README-merci.md"
    if readme_merci.exists():
        content = readme_merci.read_text(encoding="utf-8")
        match = re.search(r"# Merci Boilerplate (v\d+\.\d+\.\d+)", content)
        if match:
            return match.group(1)
    return "v1.0.0"

def inject_metrics(html_path: Path, metrics: dict):
    if not html_path.exists():
        return

    html = html_path.read_text(encoding="utf-8")
    for key, value in metrics.items():
        if value == "N/D": continue
        # Búsqueda tolerante en orden inverso: Primero el span del valor y luego el de la etiqueta.
        pattern = rf'(<span class="hero__metric-value">)[^<]+(</span>\s*<span class="hero__metric-label">[^<]*?{key}[^<]*?</span>)'
        html = re.sub(pattern, rf'\g<1>{value}\g<2>', html, flags=re.IGNORECASE)
        
    html_path.write_text(html, encoding="utf-8")

def main():
    print("📈 [Merci Telemetry] Calculando métricas de ingeniería del proyecto...")
    metrics = {"Commit": get_git_commits(), "Agente": get_agent_count(), "Línea": get_doc_lines(), "Release": get_latest_release(), "Versión": get_latest_release(), "Día": get_active_days()}
    inject_metrics(INDEX_HTML, metrics)
    inject_metrics(SOBRE_MI_HTML, metrics)

if __name__ == "__main__":
    main()