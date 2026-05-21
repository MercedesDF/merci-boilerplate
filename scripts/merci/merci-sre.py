#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-sre.py — Agente de Observabilidad y Métricas (Fase 4).
Expone el estado del ecosistema DevSecOps en el puerto 8001 para Prometheus.
"""

import time
import re
import json
from pathlib import Path
from prometheus_client import start_http_server, Gauge

REPO_ROOT = Path(__file__).resolve().parents[2]

# Declaración de métricas (Gauges: valores que pueden subir y bajar)
ROADMAP_TASKS = Gauge('merci_roadmap_tareas_total', 'Tareas del Roadmap', ['estado'])
DOCS_INCUBACION = Gauge('merci_documentos_incubacion_total', 'Borradores en incubación')
DOCS_PROMOCION = Gauge('merci_documentos_promocion_total', 'Documentos listos para promover (borrador)')
DOCS_BIBLIOTECA = Gauge('merci_documentos_biblioteca_total', 'Documentos publicados en biblioteca')
DOCS_ART_DE_COTE = Gauge('merci_documentos_art_de_cote_total', 'Documentos publicados en art-de-cote')
DOCS_BLOG = Gauge('merci_documentos_blog_total', 'Documentos publicados en blog')
LINKEDIN_QUEUE = Gauge('merci_linkedin_queue_total', 'Publicaciones en cola para LinkedIn')
DOCUMENT_DRIFT = Gauge('merci_document_drift_total', 'Archivos con deriva documental')
PIPELINE_DURATION = Gauge('merci_pipeline_duration_seconds', 'Tiempo de ejecución de merci-total.py')
PIPELINE_SCRIPT_DURATION = Gauge('merci_pipeline_script_duration_seconds', 'Tiempo de ejecución por script', ['script'])
GLOSARIO_TERMS = Gauge('merci_glosario_terminos_total', 'Número total de términos definidos en el glosario JSON')
CHAOS_EVENTS = Gauge('merci_chaos_events_total', 'Resultados de los simulacros del Chaos Monkey', ['resultado'])
AI_FALLBACKS = Gauge('merci_ai_fallbacks_total', 'Respuestas de IA en modo contingencia (Fallback)')
AUDIT_ERRORS = Gauge('merci_audit_errors_total', 'Errores bloqueantes detectados por el linter')
AUDIT_WARNS = Gauge('merci_audit_warnings_total', 'Advertencias detectadas por el linter')

def actualizar_metricas_pipeline():
    """Lectura de JSON (Deriva y Duración). Se refrescan periódicamente (cada 10s)."""
    drift_path = REPO_ROOT / "observabilidad" / ".drift_report.json"
    if drift_path.exists():
        try:
            data = json.loads(drift_path.read_text(encoding="utf-8"))
            DOCUMENT_DRIFT.set(len(data))
        except Exception:
            pass

    duration_path = REPO_ROOT / "observabilidad" / ".pipeline_duration.json"
    if duration_path.exists():
        try:
            data = json.loads(duration_path.read_text(encoding="utf-8"))
            PIPELINE_DURATION.set(data.get("duration_seconds", 0.0))
            
            # Exponer desglose por script
            breakdown = data.get("breakdown", {})
            for script_name, s_duration in breakdown.items():
                PIPELINE_SCRIPT_DURATION.labels(script=script_name).set(s_duration)
                
        except Exception:
            pass

def actualizar_metricas_chaos():
    """Lectura del log privado de resiliencia (Chaos Engineering)."""
    chaos_path = REPO_ROOT / ".privado" / "chaos-audit.json"
    if chaos_path.exists():
        try:
            data = json.loads(chaos_path.read_text(encoding="utf-8"))
            detectados = sum(1 for item in data if item.get("defensa_exitosa", False))
            indetectados = len(data) - detectados
            CHAOS_EVENTS.labels(resultado="detectado").set(detectados)
            CHAOS_EVENTS.labels(resultado="indetectado").set(indetectados)
        except Exception:
            pass

def actualizar_metricas_ia_y_auditoria():
    """Lectura de fallbacks del Lóbulo Frontal y reportes del Auditor."""
    brain_path = REPO_ROOT / "public" / "js" / "brain_data.json"
    if brain_path.exists():
        try:
            data = json.loads(brain_path.read_text(encoding="utf-8"))
            fallbacks = sum(1 for v in data.values() if str(v).startswith("[Fallback]"))
            AI_FALLBACKS.set(fallbacks)
        except Exception:
            pass
            
    audit_path = REPO_ROOT / "observabilidad" / ".audit_report.json"
    if audit_path.exists():
        try:
            data = json.loads(audit_path.read_text(encoding="utf-8"))
            AUDIT_ERRORS.set(data.get("errors", 0))
            AUDIT_WARNS.set(data.get("warnings", 0))
        except Exception:
            pass

def actualizar_estado_documental():
    """Lectura de Markdown y YAML Frontmatter. Se refresca cada segundo para feedback instantáneo."""
    # 0. Glosario JSON
    glosario_json_path = REPO_ROOT / "laboratorio" / "biblioteca" / "glosario-tecnico.json"
    if glosario_json_path.exists():
        try:
            data = json.loads(glosario_json_path.read_text(encoding="utf-8"))
            GLOSARIO_TERMS.set(len(data.get("terminos", {})))
        except Exception:
            pass
            
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

    # 3. Contar documentos en producción (biblioteca, art-de-cote, blog)
    biblioteca_dir = REPO_ROOT / "biblioteca"
    if biblioteca_dir.exists():
        DOCS_BIBLIOTECA.set(len(list(biblioteca_dir.glob("*.md"))))
        
    art_de_cote_dir = REPO_ROOT / "art-de-cote"
    if art_de_cote_dir.exists():
        DOCS_ART_DE_COTE.set(len(list(art_de_cote_dir.glob("*.md"))))
        
    blog_dir = REPO_ROOT / "blog"
    if blog_dir.exists():
        DOCS_BLOG.set(len(list(blog_dir.glob("*.md"))))

    # 4. Contar publicaciones en cola para LinkedIn
    directorios_sociales = [REPO_ROOT / "blog", REPO_ROOT / "art-de-cote", REPO_ROOT / "biblioteca"]
    en_cola_social = 0
    for dir_path in directorios_sociales:
        if dir_path.exists():
            for md_file in dir_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8", errors="ignore")
                    match = re.match(r"^\s*---\r?\n(.*?)\n---", content, re.DOTALL)
                    if match:
                        yaml_block = match.group(1)
                        # Solo contamos si está publicado y en cola
                        if re.search(r'^estado:\s*["\']publicado["\']', yaml_block, re.MULTILINE | re.IGNORECASE) and \
                           re.search(r'^estado_social:\s*["\'](en_cola|aprobado)["\']', yaml_block, re.MULTILINE | re.IGNORECASE):
                            en_cola_social += 1
                except Exception:
                    pass
    LINKEDIN_QUEUE.set(en_cola_social)

def main():
    puerto = 8001
    print(f"👁️  [Merci SRE] Iniciando Agente de Observabilidad en el puerto {puerto}...")
    start_http_server(puerto, addr="0.0.0.0")
    
    while True:
        # QUÉ HACE: Muestreo continuo "hiper-rápido" (1s) para todas las métricas.
        actualizar_estado_documental()
        actualizar_metricas_pipeline()
        actualizar_metricas_chaos()
        actualizar_metricas_ia_y_auditoria()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👁️  [Merci SRE] Agente de Observabilidad detenido por el usuario. ¡Hasta la vista!")