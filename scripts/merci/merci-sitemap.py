#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-sitemap.py — Automatización del mantenimiento del sitemap.xml.

Escanea recursivamente la carpeta public/ y auto-descubre las nuevas páginas 
generadas, construyendo el sitemap.xml desde cero con URLs amigables 
(limpias) y prioridades dinámicas.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = REPO_ROOT / "public"
SITEMAP_PATH = PUBLIC_DIR / "sitemap.xml"
DOMAIN = "https://merci-boilerplate.es"

def generar_sitemap():
    print("🗺️ [Merci Sitemap] Escaneando páginas webs estáticas...")
    ahora = datetime.now().strftime("%Y-%m-%d")
    bloques_url = []

    # QUÉ HACE: Escanea recursivamente buscando todos los archivos .html
    # POR QUÉ: Auto-descubre las nuevas páginas sin intervención humana.
    for html_file in PUBLIC_DIR.rglob("*.html"):
        rel_path = html_file.relative_to(PUBLIC_DIR).as_posix()
        
        # QUÉ HACE: Limpia las extensiones para generar URLs amigables (Clean URLs).
        if rel_path == "index.html":
            url_path = ""
            prioridad = "1.0"
        elif rel_path.endswith("/index.html"):
            url_path = rel_path[:-10]
            prioridad = "0.8"
        elif rel_path.endswith(".html"):
            url_path = rel_path[:-5]
            prioridad = "0.7"
        else:
            continue

        full_url = f"{DOMAIN}/{url_path}"

        bloque = f"""   <url>
      <loc>{full_url}</loc>
      <lastmod>{ahora}</lastmod>
      <changefreq>weekly</changefreq>
      <priority>{prioridad}</priority>
   </url>"""
        bloques_url.append(bloque)

    # Ensambla y sobrescribe el documento XML final
    xml_final = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(bloques_url)}
</urlset>"""

    SITEMAP_PATH.write_text(xml_final, encoding="utf-8")
    print(f"  ✅ sitemap.xml regenerado con éxito ({len(bloques_url)} URLs auto-descubiertas).")

if __name__ == "__main__":
    try:
        generar_sitemap()
    except Exception as e:
        print(f"Error técnico en el sitemap: {e}", file=sys.stderr)
        sys.exit(1)