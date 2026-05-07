#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-total.py — Orquestador maestro del ecosistema Merci.

Ejecuta en secuencia lógica todos los scripts de compilación, 
optimización y auditoría del proyecto. Excluye scripts interactivos 
(merci-commit) o de vigilancia continua (merci-watch).
"""

import subprocess
import sys
from pathlib import Path

# Definimos la ruta base donde residen los scripts
SCRIPTS_DIR = Path(__file__).resolve().parent

# Pipeline de ejecución secuencial. El orden es estricto por arquitectura:
# --- FASE DE CONSTRUCCIÓN (BUILD) ---
# 1. Optimizador: Prepara las imágenes WebP necesarias.
# 2. Styles: Compila el SASS final a main.css.
# 3. Publish: SSG que compila la Biblioteca desde Markdown a HTML/PDF.
# 4. WP Headless: Sincroniza los markdowns locales dinámicos hacia WordPress.
# 5. Sync Pages: Propaga el header/footer maestro a las páginas secundarias.
# 6. Extract Metrics: Inyecta las últimas estadísticas de PageSpeed Insight en home.
# --- FASE DE QA (QUALITY ASSURANCE) ---
# 7. Sitemap: Escanea todos los HTML finales generados y actualiza el mapa XML.
# 8. Audit: Auditoría estricta de seguridad, SEO y sintaxis sobre el código final.
# 9. Linkcheck: Rastreo dinámico de enlaces rotos sobre el HTML final compilado.

PIPELINE = [
    "merci-optimizer.py",
    "merci-styles.py",
    "merci-publish.py",
    "merci-wp.py",
    "merci-sync-pages.py",
    "merci-extract-metrics.py",
    "merci-brain.py",
    "merci-sitemap.py",
    "merci-audit.py",
    "merci-linkcheck.py"
]

def main():
    print("🚀 [Merci Total] Iniciando orquestación del pipeline DevSecOps...\n")
    
    for script in PIPELINE:
        script_path = SCRIPTS_DIR / script
        
        if not script_path.exists():
            print(f"❌ [Merci Total] Error: No se encuentra el script {script}")
            sys.exit(1)
            
        print(f"▶️ Ejecutando: {script} ...")
        try:
            # check=True garantiza el patrón "Fail-Fast": si un script falla, 
            # el orquestador aborta inmediatamente sin ejecutar los siguientes.
            subprocess.run([sys.executable, str(script_path)], check=True)
            print()  # Separador visual entre bloques de ejecución
        except subprocess.CalledProcessError as e:
            print(f"\n❌ [Merci Total] Pipeline detenido. El script {script} ha fallado.")
            sys.exit(e.returncode)
            
    print("\n✅ [Merci Total] ¡Pipeline completado con éxito! Todo optimizado y auditado.")

if __name__ == "__main__":
    main()