#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-total.py — Orquestador maestro del ecosistema Merci.

Ejecuta en secuencia lógica todos los scripts de compilación, 
optimización y auditoría del proyecto. Excluye scripts interactivos 
(merci-commit) o de vigilancia continua (merci-watch).
"""

import subprocess
import time
import json
import sys
import os
from pathlib import Path

# Definimos la ruta base donde residen los scripts
SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]

# Pipeline de ejecución secuencial. El orden es estricto por arquitectura:
# --- FASE DE CONSTRUCCIÓN (BUILD) ---
# 1. Optimizador: Prepara las imágenes WebP necesarias.
# 2. Styles: Compila el SASS final a main.css.
# 3. Glosario AI: Compila el diccionario técnico a Markdown antes del SSG.
# 4. Publish: SSG que compila la Biblioteca desde Markdown a HTML/PDF.
# 5. WP Headless: Sincroniza los markdowns locales dinámicos hacia WordPress.
# 6. Shop Headless: Sincroniza los productos mock a WooCommerce.
# 7. Sync Pages: Propaga el header/footer maestro a las páginas secundarias.
# 8. Extract Metrics: Inyecta las estadísticas de PageSpeed en home.
# 9. Telemetry: Inyecta métricas de repositorio en la portada y sobre-mí.
# 10. Brain: Genera el JSON estático con respuestas contextuales de IA.
# --- FASE DE QA (QUALITY ASSURANCE) ---
# 11. Sitemap: Escanea todos los HTML finales generados y actualiza el mapa XML.
# 12. Drift: Detecta asimetrías de fechas entre manuales y código fuente.
# 13. Audit: Auditoría estricta de seguridad, SEO y sintaxis sobre el código final.
# 14. Hardening: Audita la postura de seguridad de la infraestructura y el repositorio.
# 15. Linkcheck: Rastreo dinámico de enlaces rotos sobre el HTML final compilado.

PIPELINE = [
    "merci-optimizer.py",
    "merci-styles.py",
    "merci-glosario.py",
    "merci-publish.py",
    "merci-wp.py",
    "merci-shop.py",
    "merci-sync-pages.py",
    "merci-extract-metrics.py",
    "merci-telemetry.py",
    "merci-brain.py",
    "merci-sitemap.py",
    "merci-drift.py",
    "merci-audit.py",
    "merci-hardening.py",
    "merci-linkcheck.py"
]

def main():
    start_time = time.time()
    print("🚀 [Merci Total] Iniciando orquestación del pipeline DevSecOps...\n")
    
    script_durations = {}
    
    for script in PIPELINE:
        script_path = SCRIPTS_DIR / script
        
        if not script_path.exists():
            print(f"❌ [Merci Total] Error: No se encuentra el script {script}")
            sys.exit(1)
            
        print(f"▶️ Ejecutando: {script} ...")
        script_start = time.time()
        try:
            # check=True garantiza el patrón "Fail-Fast": si un script falla, 
            # el orquestador aborta inmediatamente sin ejecutar los siguientes.
            subprocess.run([sys.executable, str(script_path)], check=True)
            script_end = time.time()
            script_durations[script] = script_end - script_start
            print()  # Separador visual entre bloques de ejecución
        except subprocess.CalledProcessError as e:
            print(f"\n❌ [Merci Total] Pipeline detenido. El proceso '{script}' reportó errores y bloqueó la ejecución.")
            sys.exit(e.returncode)
            
    end_time = time.time()
    duration = end_time - start_time
    
    obs_dir = REPO_ROOT / "observabilidad"
    obs_dir.mkdir(exist_ok=True)
    
    # Exportar tanto el total como el desglose SRE
    pipeline_data = {
        "duration_seconds": duration,
        "breakdown": script_durations
    }
    (obs_dir / ".pipeline_duration.json").write_text(json.dumps(pipeline_data, indent=2), encoding="utf-8")
    
    print(f"\n✅ [Merci Total] ¡Pipeline completado con éxito en {duration:.2f}s! Todo optimizado y auditado.")
    
    print("\n⏱️  Desglose de Tiempos de Ejecución:")
    print("-" * 40)
    for s_name, s_time in script_durations.items():
        print(f"  {s_name:<25} : {s_time:>5.2f}s")
    print("-" * 40)
    
    if not os.environ.get("MERCI_IS_COMPLETO"):
        print("\n💡 [Merci DX] Todo en verde. Si tu iteración ha finalizado, ejecuta 'merci completo' para sellar y subir a producción.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Total] Orquestación interrumpida por la usuaria. Saliendo limpiamente.")
        sys.exit(130)