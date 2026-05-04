#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-sync-pages.py — Sincronizador de estructuras comunes estáticas.

Extrae el <header>, <footer> y el asistente <aside> de la portada (SSOT)
y los inyecta en páginas estáticas secundarias (como contacto/index.html)
para mantener la paridad estructural en todo el ecosistema SSG sin duplicar código.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = REPO_ROOT / "public"
INDEX_PATH = PUBLIC_DIR / "index.html"

# Exclusiones: biblioteca (merci-publish), blog (WordPress), descargas (PDFs)
EXCLUDED_DIRS = {"biblioteca", "blog", "descargas"}

def discover_target_pages() -> list[Path]:
    """
    QUÉ HACE: Autodescubre páginas HTML estáticas ignorando la portada y las rutas autogeneradas/dinámicas.
    POR QUÉ: Automatización real. Si añades una nueva carpeta en public/ en el futuro, se sincronizará mágicamente.
    """
    pages = []
    for html_file in PUBLIC_DIR.rglob("*.html"):
        if html_file == INDEX_PATH:
            continue
        if not any(excluded in html_file.parts for excluded in EXCLUDED_DIRS):
            pages.append(html_file)
    return pages

def extract_block(html: str, regex_pattern: str, block_name: str) -> str:
    """
    QUÉ HACE: Extrae un bloque HTML usando expresiones regulares.
    POR QUÉ: Permite capturar la estructura exacta de la portada sin librerías externas.
    """
    match = re.search(regex_pattern, html, re.DOTALL)
    if not match:
        print(f"[Merci Error] No se pudo extraer el bloque {block_name} de la portada.")
        sys.exit(1)
    return match.group(1)

def replace_block(html: str, regex_pattern: str, new_content: str, block_name: str) -> str:
    """
    QUÉ HACE: Reemplaza un bloque HTML destino con el contenido nuevo.
    POR QUÉ: Actualiza la página secundaria manteniendo intacto su contenido único (<main>).
    """
    if not re.search(regex_pattern, html, re.DOTALL):
        print(f"[Merci Error] No se encontró el bloque {block_name} en la página destino.")
        sys.exit(1)
    # Usamos una función lambda para evitar que re.sub interprete barras invertidas erróneas.
    return re.sub(regex_pattern, lambda m: new_content, html, flags=re.DOTALL)

def main():
    print("🔄 [Merci Sync] Sincronizando estructuras comunes en páginas estáticas...")
    
    if not INDEX_PATH.exists():
        print("[Merci Error] Falta el index.html principal (SSOT) para sincronizar.")
        sys.exit(1)
        
    target_pages = discover_target_pages()
    index_html = INDEX_PATH.read_text(encoding="utf-8")
    
    # 1. Patrones de extracción (Regex)
    header_pattern = r'(<header class="header">.*?</header>)'
    footer_pattern = r'(<footer class="footer".*?</footer>)'
    aside_pattern = r'(<aside class="merci-ui".*?</aside>)'
    
    # 2. Extraer de la portada
    header_content = extract_block(index_html, header_pattern, "Header")
    footer_content = extract_block(index_html, footer_pattern, "Footer")
    aside_content = extract_block(index_html, aside_pattern, "Aside (Merci)")
    
    # 3. Iterar e inyectar en todas las páginas de destino
    if not target_pages:
        print("ℹ️ [Merci Sync] No se encontraron páginas secundarias para sincronizar.")
        return

    for target_path in target_pages:
        # Obtenemos el nombre de la carpeta contenedora para el log, o el nombre del archivo si está en la raíz
        page_name = target_path.parent.name if target_path.parent.name != "public" else target_path.name
        
        target_html = target_path.read_text(encoding="utf-8")
        nuevo_html = replace_block(target_html, header_pattern, header_content, "Header")
        nuevo_html = replace_block(nuevo_html, footer_pattern, footer_content, "Footer")
        nuevo_html = replace_block(nuevo_html, aside_pattern, aside_content, "Aside (Merci)")
        
        target_path.write_text(nuevo_html, encoding="utf-8")
        print(f"✅ {page_name.capitalize()} sincronizado con la portada.")

if __name__ == "__main__":
    main()