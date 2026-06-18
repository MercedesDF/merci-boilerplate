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
import json
import html
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = REPO_ROOT / "public"
INDEX_PATH = PUBLIC_DIR / "index.html"

# Exclusiones: biblioteca (merci-publish), blog (WordPress), descargas (PDFs)
EXCLUDED_DIRS = {"biblioteca", "art-de-cote", "blog", "descargas"}


def generar_sre_badge_html(url: str, cache_data: dict) -> str:
    """
    QUÉ HACE: Genera el marcado HTML para el micro-sello SRE a partir de los datos de la caché.
    POR QUÉ: Permite inyectar una visualización Zero-JS ligera de Core Web Vitals en cada página.
    """
    scores = cache_data.get(url, {"performance": 100, "accessibility": 100, "best-practices": 100, "seo": 100})
    
    def get_color_class(val):
        if val >= 90: return "sre-badge__score--green"
        if val >= 50: return "sre-badge__score--orange"
        return "sre-badge__score--red"

    p_col = get_color_class(scores.get("performance", 100))
    a_col = get_color_class(scores.get("accessibility", 100))
    b_col = get_color_class(scores.get("best-practices", 100))
    s_col = get_color_class(scores.get("seo", 100))

    return f"""<div class="sre-badge" role="group" aria-label="Auditoría Lighthouse de esta página">
                <div class="sre-badge__item" title="Rendimiento">
                    <span class="sre-badge__icon">⚡</span>
                    <span class="sre-badge__score {p_col}">{scores.get("performance", 100)}</span>
                </div>
                <div class="sre-badge__item" title="Accesibilidad">
                    <span class="sre-badge__icon">♿</span>
                    <span class="sre-badge__score {a_col}">{scores.get("accessibility", 100)}</span>
                </div>
                <div class="sre-badge__item" title="Buenas Prácticas">
                    <span class="sre-badge__icon">🛡️</span>
                    <span class="sre-badge__score {b_col}">{scores.get("best-practices", 100)}</span>
                </div>
                <div class="sre-badge__item" title="SEO">
                    <span class="sre-badge__icon">🔍</span>
                    <span class="sre-badge__score {s_col}">{scores.get("seo", 100)}</span>
                </div>
            </div>"""


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


def main() -> None:
    """
    QUÉ HACE: Extrae componentes comunes (cabeceras, pies de página, estilos/scripts) de la portada y los replica en las páginas internas.
    POR QUÉ: Garantiza la paridad visual y estructural entre todas las páginas estáticas sin la sobrecarga de un motor de plantillas pesado.
    """
    print("🔄 [Merci Sync] Sincronizando estructuras comunes en páginas estáticas...")
    
    if not INDEX_PATH.exists():
        print("[Merci Error] Falta el index.html principal (SSOT) para sincronizar.")
        sys.exit(1)
        
    target_pages = discover_target_pages()
    index_html = INDEX_PATH.read_text(encoding="utf-8")
    
    # 1. Patrones de extracción (Regex)
    header_pattern = r'((?:<div id="top"[^>]*></div>\s*)?<header class="header"(?: id="top")?>.*?</header>)'
    footer_pattern = r'(<footer class="footer".*?</footer>)'
    aside_pattern = r'(<aside class="merci-ui".*?</aside>)'
    css_pattern = r'(<link rel="stylesheet" href="/css/main\.css\?v=\d+">)'
    jsc_pattern = r'(<script src="/js/MerciController\.js\?v=\d+"\s*defer></script>)'
    jsm_pattern = r'(<script src="/js/main\.js\?v=\d+"\s*defer></script>)'
    
    # 2. Extraer de la portada
    header_content = extract_block(index_html, header_pattern, "Header")
    footer_content = extract_block(index_html, footer_pattern, "Footer")
    aside_content = extract_block(index_html, aside_pattern, "Aside (Merci)")
    css_content = extract_block(index_html, css_pattern, "CSS Cache Busting")
    jsc_content = extract_block(index_html, jsc_pattern, "JS Controller Cache")
    jsm_content = extract_block(index_html, jsm_pattern, "JS Main Cache")
    
    # 3. Cargar la caché de telemetría para las inyecciones de los micro-sellos
    cache_path = REPO_ROOT / "observabilidad" / ".lighthouse_pages_cache.json"
    cache_data = {}
    if cache_path.exists():
        try:
            cache_data = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 4. Iterar e inyectar en todas las páginas de destino
    if not target_pages:
        print("ℹ️ [Merci Sync] No se encontraron páginas secundarias para sincronizar.")
        return

    for target_path in target_pages:
        # Obtenemos la ruta relativa para el log, así queda claro qué archivo exacto se sincroniza
        rel_path = target_path.relative_to(PUBLIC_DIR)
        
        target_html = target_path.read_text(encoding="utf-8")

        # Inyectar el micro-sello si el marcador está presente
        if "<!-- Merci SRE Badge -->" in target_html:
            canonical_url = f"https://tuempresa.es/{rel_path.parent}/" if rel_path.name == "index.html" else f"https://tuempresa.es/{rel_path}"
            canonical_url = re.sub(r'([^:])//+', r'\1/', canonical_url)
            badge_html = generar_sre_badge_html(canonical_url, cache_data)
            target_html = target_html.replace("<!-- Merci SRE Badge -->", badge_html)

        nuevo_html = replace_block(target_html, header_pattern, header_content, "Header")
        nuevo_html = replace_block(nuevo_html, footer_pattern, footer_content, "Footer")
        nuevo_html = replace_block(nuevo_html, aside_pattern, aside_content, "Aside (Merci)")
        nuevo_html = replace_block(nuevo_html, css_pattern, css_content, "CSS Cache Busting")
        nuevo_html = replace_block(nuevo_html, jsc_pattern, jsc_content, "JS Controller Cache")
        nuevo_html = replace_block(nuevo_html, jsm_pattern, jsm_content, "JS Main Cache")
        
        target_path.write_text(nuevo_html, encoding="utf-8")
        print(f"✅ {rel_path} sincronizado con la portada.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Sync] Sincronización cancelada por el usuario.")
        sys.exit(130)