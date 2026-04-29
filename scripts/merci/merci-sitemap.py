#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-sitemap.py — Automatización del mantenimiento del sitemap.xml.

Este script busca la etiqueta <lastmod> y la actualiza con la fecha actual
en formato AAAA-MM-DD para asegurar que los motores de búsqueda detecten
los cambios recientes en el núcleo estático.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

# Configuración de rutas relativas a la raíz del proyecto
REPO_ROOT = Path(__file__).resolve().parents[2]
SITEMAP_PATH = REPO_ROOT / "public" / "sitemap.xml"

def update_lastmod():
    """Actualiza la fecha de última modificación en el archivo sitemap.xml."""
    if not SITEMAP_PATH.exists():
        print(f"Error: No se encuentra el archivo en {SITEMAP_PATH}")
        sys.exit(1)

    # Obtener la fecha de hoy en formato ISO 8601 (AAAA-MM-DD)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Leer el contenido actual del archivo
    content = SITEMAP_PATH.read_text(encoding="utf-8")
    
    # Expresión regular para encontrar la etiqueta <lastmod> y su contenido
    # XML (Extensible Markup Language - Lenguaje de Marcado Extensible)
    pattern = r"<lastmod>.*?</lastmod>"
    replacement = f"<lastmod>{today}</lastmod>"
    
    # Realizar la sustitución
    new_content = re.sub(pattern, replacement, content)
    
    if content == new_content:
        print("✅ El sitemap ya está actualizado con la fecha de hoy.")
    else:
        # Escribir los cambios de vuelta al archivo
        SITEMAP_PATH.write_text(new_content, encoding="utf-8")
        print(f"✅ Sitemap actualizado: <lastmod> establecido en {today}")

if __name__ == "__main__":
    try:
        update_lastmod()
    except Exception as e:
        print(f"Error técnico en el sitemap: {e}", file=sys.stderr)
        sys.exit(1)