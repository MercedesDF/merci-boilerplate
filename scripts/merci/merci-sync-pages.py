#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-sync-pages.py — Sincronizador de estructuras comunes estáticas.

Extrae el <header>, <footer> y el asistente <aside> de la portada (SSOT)
y los inyecta en páginas estáticas secundarias (como contacto/index.html)
para mantener la paridad estructural sin duplicar código.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = REPO_ROOT / "public" / "index.html"
CONTACTO_PATH = REPO_ROOT / "public" / "contacto" / "index.html"

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
    
    if not INDEX_PATH.exists() or not CONTACTO_PATH.exists():
        print("[Merci Error] Faltan archivos HTML estáticos para sincronizar.")
        sys.exit(1)
        
    index_html = INDEX_PATH.read_text(encoding="utf-8")
    contacto_html = CONTACTO_PATH.read_text(encoding="utf-8")
    
    # 1. Patrones de extracción (Regex)
    header_pattern = r'(<header class="header">.*?</header>)'
    footer_pattern = r'(<footer class="footer".*?</footer>)'
    aside_pattern = r'(<aside class="merci-ui".*?</aside>)'
    
    # 2. Extraer de la portada
    header_content = extract_block(index_html, header_pattern, "Header")
    footer_content = extract_block(index_html, footer_pattern, "Footer")
    aside_content = extract_block(index_html, aside_pattern, "Aside (Merci)")
    
    # 3. Inyectar en la página de contacto
    nuevo_contacto = replace_block(contacto_html, header_pattern, header_content, "Header")
    nuevo_contacto = replace_block(nuevo_contacto, footer_pattern, footer_content, "Footer")
    nuevo_contacto = replace_block(nuevo_contacto, aside_pattern, aside_content, "Aside (Merci)")

    # 4. Escribir los cambios de forma destructiva
    CONTACTO_PATH.write_text(nuevo_contacto, encoding="utf-8")
    print("✅ Contacto sincronizado con la portada (Header, Footer y Merci).")

if __name__ == "__main__":
    main()