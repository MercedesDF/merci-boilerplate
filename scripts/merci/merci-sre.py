#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-sre.py — Agente de Observabilidad y Métricas (Fase 4).
Expone el estado del ecosistema DevSecOps en el puerto 8001 para Prometheus.
"""

import time
import re
from pathlib import Path
from prometheus_client import start_http_server, Gauge

REPO_ROOT = Path(__file__).resolve().parents[2]

# Declaración de métricas (Gauges: valores que pueden subir y bajar)
ROADMAP_TASKS = Gauge('merci_roadmap_tareas_total', 'Tareas del Roadmap', ['estado'])
DOCS_INCUBACION = Gauge('merci_documentos_incubacion_total', 'Borradores en incubación')
DOCS_PROMOCION = Gauge('merci_documentos_promocion_total', 'Documentos listos para promover (borrador)')
DOCS_BIBLIOTECA = Gauge('merci_documentos_biblioteca_total', 'Documentos publicados en biblioteca')

def actualizar_metricas():
    # 1. Analizar tareas del Roadmap
    roadmap_path = REPO_ROOT / "ROADMAP.md"
    if roadmap_path.exists():
        content = roadmap_path.read_text(encoding="utf-8")
        pendientes = len(re.findall(r'- \[\s*\] ', content))
        completadas = len(re.findall(r'- \[\s*[xX]\s*\] ', content))
        ROADMAP_TASKS.labels(estado="pendiente").set(pendientes)
        ROADMAP_TASKS.labels(estado="completada").set(completadas)

    # 2. Contar documentos por estado (incubación y promoción) mediante YAML Frontmatter
    laboratorio_dir = REPO_ROOT / "laboratorio"
    if laboratorio_dir.exists():
        en_incubacion = 0
        borradores = 0
        for md_file in laboratorio_dir.rglob("*.md"):
            # Excluir bitácoras para evitar falsos positivos
            if md_file.name.startswith("bitacora"):
                continue
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                match = re.match(r"^\s*---\r?\n(.*?)\n---", content, re.DOTALL)
                if match:
                    if re.search(r'^estado:\s*["\']incubacion["\']', match.group(1), re.MULTILINE | re.IGNORECASE):
                        en_incubacion += 1
                    elif re.search(r'^estado:\s*["\']borrador["\']', match.group(1), re.MULTILINE | re.IGNORECASE):
                        borradores += 1
            except Exception:
                pass
        DOCS_INCUBACION.set(en_incubacion)
        DOCS_PROMOCION.set(borradores)

    # 3. Contar documentos en la biblioteca pública
    biblioteca_dir = REPO_ROOT / "biblioteca"
    if biblioteca_dir.exists():
        DOCS_BIBLIOTECA.set(len(list(biblioteca_dir.glob("*.md"))))

def main():
    puerto = 8001
    print(f"👁️  [Merci SRE] Iniciando Agente de Observabilidad en el puerto {puerto}...")
    start_http_server(puerto, addr="0.0.0.0")
    while True:
        actualizar_metricas()
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👁️  [Merci SRE] Agente de Observabilidad detenido por el usuario. ¡Hasta la vista!")