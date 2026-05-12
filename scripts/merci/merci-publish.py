#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-publish.py — Orquestador maestro de publicación (Fase 7.1).
Transforma documentos Markdown de la biblioteca en páginas HTML estáticas.
"""

import argparse
import re
import sys
import shutil
import unicodedata
import html
import json
from pathlib import Path

try:
    import markdown
except ImportError:
    print("ℹ️ [Merci Info] Falta la librería 'markdown' (pip install markdown). Omitiendo compilación SSG estática.")
    sys.exit(0)

try:
    from weasyprint import HTML
except ImportError:
    HTML = None
    print("ℹ️ [Merci Info] Falta la librería 'weasyprint' (pip install weasyprint). No se generarán PDFs.")

REPO_ROOT = Path(__file__).resolve().parents[2]
BIBLIOTECA_DIR = REPO_ROOT / "biblioteca"
ART_DE_COTE_DIR = REPO_ROOT / "art-de-cote"
PUBLIC_BIBLIOTECA = REPO_ROOT / "public" / "biblioteca"
PUBLIC_ART_DE_COTE = REPO_ROOT / "public" / "art-de-cote"
PUBLIC_DESCARGAS = REPO_ROOT / "public" / "descargas"

def slugify(texto: str) -> str:
    """
    QUÉ HACE: Convierte un texto (ej. título) en una cadena segura para URLs (slug).
    POR QUÉ: Permite al autor nombrar sus archivos .md libremente en el sistema local, 
    asegurando que las URLs públicas sean siempre limpias, sin acentos ni espacios.
    """
    texto = str(texto)
    # Normaliza eliminando acentos (ej. á -> a, ñ -> n)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    # Elimina caracteres que no sean alfanuméricos, espacios o guiones
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    # Reemplaza múltiples espacios o guiones por un solo guion
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

def limpiar_directorio_salida():
    """
    QUÉ HACE: Purga exclusivamente los archivos .html y .pdf generados en ejecuciones anteriores.
    POR QUÉ: Implementa un patrón 'Clean Build' automático. Previene la acumulación de archivos 'zombis' 
    si un documento Markdown origen es renombrado o eliminado de la biblioteca.
    """
    print("🧹 [Merci Publish] Limpiando compilaciones anteriores (Clean Build)...")
    for directorio in [PUBLIC_BIBLIOTECA, PUBLIC_ART_DE_COTE, PUBLIC_DESCARGAS]:
        if not directorio.exists():
            continue
        for item in directorio.iterdir():
            if item.is_file() and item.suffix in {'.html', '.pdf'}:
                try:
                    item.unlink()
                except OSError as e:
                    print(f"  ⚠️ No se pudo borrar {item.name}: {e}")

def procesar_archivo(filepath: Path, header_html: str, footer_html: str, css_v: int, js_c_v: int, js_m_v: int):
    content = filepath.read_text(encoding="utf-8")
    
    # 1. Extraer YAML Frontmatter y Cuerpo del Markdown
    match = re.search(r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)(.*)", content, flags=re.DOTALL | re.MULTILINE)
    if not match:
        print(f"  ❌ Error: No se encontró YAML Frontmatter válido en {filepath.name}")
        return False
        
    yaml_raw, md_body = match.groups()
    
    # 2. Parsear metadatos manualmente (Cero dependencias extra para YAML simple)
    meta = {}
    for line in yaml_raw.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip().strip('"\'')
            
    titulo = meta.get("titulo", "Documento sin título")
    tipo = meta.get("tipo", "proyecto")
    descripcion = meta.get("descripcion", f"Documento técnico: {titulo}")
    tema = meta.get("tema", "Estantería General")
    estado = meta.get("estado", "borrador").lower()
    alt_portada = meta.get("alt_portada", "")
    fase = meta.get("fase", "")
    
    titulo_html = html.escape(titulo)
    descripcion_html = html.escape(descripcion)

    # QUÉ HACE: Genera los nombres de salida basándose en el título del YAML, no en el archivo.
    # POR QUÉ: Desacopla el sistema de archivos del routing web (Auto-nombrado).
    out_filename = slugify(titulo) + ".html"
    out_pdf_filename = slugify(titulo) + ".pdf"
    
    is_art = "art-de-cote" in filepath.parts
    out_base_dir = PUBLIC_ART_DE_COTE if is_art else PUBLIC_BIBLIOTECA
    base_url_path = "/art-de-cote/" if is_art else "/biblioteca/"
    back_text = "← Volver a Art de Coté" if is_art else "← Volver a la Biblioteca"
    
    html_target = out_base_dir / out_filename
    pdf_target = PUBLIC_DESCARGAS / out_pdf_filename

    # [REGLA DE NEGOCIO]: Máquina de estados (Kill-Switch). Aisla o destruye borradores en producción.
    if estado != "publicado":
        if html_target.exists() or pdf_target.exists():
            print(f"  🗑️  Despublicando (Estado: {estado}): Eliminando artefactos de {filepath.name}")
            if html_target.exists(): html_target.unlink()
            if pdf_target.exists(): pdf_target.unlink()
            
        # QUÉ HACE: Expulsa físicamente el archivo origen hacia el entorno de incubación.
        # POR QUÉ: Principio de segregación de entornos. La biblioteca no admite borradores.
        rel_path = filepath.relative_to(REPO_ROOT)
        destino_laboratorio = REPO_ROOT / "laboratorio" / rel_path
        destino_laboratorio.parent.mkdir(parents=True, exist_ok=True)
        print(f"  🔙 Expulsando (Estado: {estado}): Moviendo '{filepath.name}' de vuelta al laboratorio.")
        try:
            shutil.move(str(filepath), str(destino_laboratorio))
        except Exception as e:
            print(f"  ❌ Error al reubicar {filepath.name}: {e}")
            
        return False
        
    # [QA ACCESIBILIDAD]: WAI-ARIA estricto. Bloquea si falta la descripción visual de la portada.
    if not alt_portada:
        print(f"  ❌ Error: Falta el atributo 'alt_portada' obligatorio en {filepath.name}")
        return False
    
    canonical_url = f"https://merci-boilerplate.es{base_url_path}{out_filename}"

    # QUÉ HACE: Pre-procesador de multimedia. Busca sintaxis de imagen que apunte a un vídeo.
    # POR QUÉ: Markdown nativo no soporta la etiqueta <video>. Usamos expresiones regulares para transformar 
    # ![alt](video.mp4) en un reproductor HTML5 accesible y creamos un texto de respaldo para el PDF.
    md_body = re.sub(
        r'!\[(.*?)\]\((.*?\.(?:mp4|webm|ogg))\)',
        r'<video controls width="100%" preload="metadata" aria-label="\1" class="multimedia-video"><source src="\2">Tu navegador no soporta video.</video><div class="video-fallback">[Vídeo: \1] <em>(Disponible en la versión web)</em></div>',
        md_body,
        flags=re.IGNORECASE
    )

    # 3. Convertir Markdown a HTML (Soportando bloques de código)
    # QUÉ HACE: Bloque try-except para atrapar errores de sintaxis en el conversor Markdown
    # POR QUÉ: Evita el colapso total del pipeline si un solo documento contiene caracteres o sintaxis corrupta.
    try:
        html_content = markdown.markdown(md_body, extensions=['fenced_code'])
    except Exception as e:
        print(f"  ❌ Error al compilar Markdown en {filepath.name}: {e}")
        return False
    
    # 4. Generar PDF con WeasyPrint (Maquetación específica para impresión)
    out_pdf_path = PUBLIC_DESCARGAS / out_pdf_filename
    PUBLIC_DESCARGAS.mkdir(parents=True, exist_ok=True)
    
    fase_pdf_text = f" | Fase {fase}" if fase else ""
    
    pdf_html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{titulo_html}</title>
    <style>
        @page {{ size: A4; margin: 2.5cm; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #334155; }}
        .portada {{ text-align: center; page-break-after: always; padding-top: 30%; }}
        .portada h1 {{ font-size: 2.5em; color: #ea580c; margin-bottom: 0.2em; }}
        .portada p {{ font-size: 1.2em; color: #64748b; }}
        h2 {{ color: #ea580c; margin-top: 2em; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.5em; }}
        pre {{ background: #f1f5f9; padding: 1em; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; font-size: 0.9em; }}
        code {{ font-family: monospace; background: #f1f5f9; padding: 0.2em 0.4em; border-radius: 3px; font-size: 0.9em; }}
        img {{ max-width: 100%; height: auto; border-radius: 4px; }}
        video.multimedia-video {{ display: none !important; }} /* Los vídeos no se pueden imprimir en papel */
        div.video-fallback {{ display: block !important; padding: 1rem; background: #f8fafc; border: 1px dashed #cbd5e1; text-align: center; color: #64748b; font-size: 0.9em; margin-bottom: 1.5rem; }}
    </style>
</head>
<body>
    <div class="portada">
        <h1>{titulo_html}</h1>
        <p>{tipo.capitalize()} | Vol. {meta.get('volumen', 1)}</p>
        <p><strong>merci-boilerplate.es</strong> — {meta.get('fecha', '')}{fase_pdf_text}</p>
    </div>
    <div class="contenido">
        {html_content}
    </div>
</body>
</html>"""

    # QUÉ HACE: Renderiza el PDF inyectando el base_url hacia la carpeta public/.
    # POR QUÉ: Sin el base_url, WeasyPrint no puede resolver rutas absolutas como /assets/images/... 
    # y las imágenes del Markdown aparecerían rotas o invisibles en el PDF descargable.
    # CONTROL DE ERRORES: WeasyPrint es propenso a fallar si las imágenes anidadas están corruptas.
    if HTML:
        try:
            HTML(string=pdf_html_content, base_url=str(REPO_ROOT / "public")).write_pdf(out_pdf_path)
        except Exception as e:
            print(f"  ❌ Error crítico al generar PDF para {filepath.name}. Comprueba las imágenes: {e}")
            # Continuamos con el proceso aunque falle el PDF para no dejar a la web sin HTML
            pass

    # 5. Generar el HTML final inyectando las clases BEM estructurales
    # QUÉ HACE: Asigna la clase CSS BEM dinámicamente basándose en el atributo 'tipo'.
    # POR QUÉ: Respeta la decisión del autor en el YAML Frontmatter, aplicando degradación elegante.
    clase_css = "card--booklet" if tipo.lower() == "cuadernillo" else "card--book"
    
    html_final = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo_html} — merci-boilerplate.es</title>
    <meta name="description" content="{descripcion_html}">
    <link rel="canonical" href="{canonical_url}">
    <link rel="stylesheet" href="/css/main.css?v={css_v}">
    <script src="/js/MerciController.js?v={js_c_v}" defer></script>
    <script src="/js/main.js?v={js_m_v}" defer></script>
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": {json.dumps(titulo)},
      "description": {json.dumps(descripcion)},
      "url": {json.dumps(canonical_url)}
    }}
    </script>
</head>
<body class="page">
    <div id="top" tabindex="-1" style="position: absolute; top: 0; left: 0;"></div>
    {header_html}
    <main class="main--padded section" id="main">
        <article class="card {clase_css}">
            <a href="{base_url_path}" class="card__back-link">{back_text}</a>
            <header>
                <h1 class="home-card__title--highlight">{titulo_html}</h1>
                <a href="/descargas/{out_pdf_filename}" class="card__download" download>📄 Descargar Edición PDF</a>
            </header>
            <div class="card__content">
                {html_content}
            </div>
        </article>
    </main>
    {footer_html}
</body>
</html>"""

    # 5. Escribir el documento final en el núcleo estático
    out_path = out_base_dir / out_filename
    out_base_dir.mkdir(parents=True, exist_ok=True)
    
    # CONTROL DE ERRORES: Escritura final en disco (riesgo de permisos I/O)
    try:
        out_path.write_text(html_final, encoding="utf-8")
        print(f"  ✅ Publicado con éxito: public{base_url_path}{out_filename}")
    except IOError as e:
        print(f"  ❌ Error de permisos al guardar el HTML {out_filename}: {e}")
        return False
    
    # Devolvemos los metadatos para construir el índice
    return {
        "titulo": titulo,
        "descripcion": descripcion,
        "url": f"{base_url_path}{out_filename}",
        "tipo": tipo,
        "fecha": meta.get("fecha", "1970-01-01"),
        "tema": tema,
        "fase": fase
    }

def generar_indice(publicaciones, out_path, title, meta_desc, hero_subtitle, canonical_url, header_html, footer_html, css_v: int, js_c_v: int, js_m_v: int):
    print(f"📖 Generando índice temático para {title}...")
    title_html = html.escape(title)
    meta_desc_html = html.escape(meta_desc)
    
    # Agrupar publicaciones por tema (Estanterías)
    estanterias = {}
    for pub in publicaciones:
        tema_original = pub["tema"]
        tema = tema_original.casefold()  # normalización robusta: evita que una may. convierta el tema en dos diferentes.
        if tema not in estanterias:
            estanterias[tema] = []

        estanterias[tema].append(pub)
        
    secciones_html = ""
    enlaces_indice_html = ""
    
    # Ordenar temas alfabéticamente y procesar sus publicaciones
    for tema in sorted(estanterias.keys()):
        # QUÉ HACE: Genera un ID válido para el ancla (ej. 'devsecops-y-gobernanza')
        tema_slug = slugify(tema)
        
        # QUÉ HACE: Ordena los artículos: Primero los "Compendios" (True), luego por fecha del más nuevo al más antiguo.
        # POR QUÉ: Otorga un trato preferente (arriba de la lista) a los documentos de alto nivel 
        # para que el usuario encuentre la visión global antes de descender a los cuadernillos tácticos.
        pubs_tema = sorted(estanterias[tema], key=lambda x: (x["tipo"].lower() == "compendio", x["fecha"]), reverse=True)
        
        # Construimos el contenedor principal de la estantería (con diseño de columnas responsivo)
        enlaces_indice_html += f'                <li class="library-nav__item">\n'
        # QUÉ HACE: Delega el color a la clase SASS .indice__tema para permitir pseudo-clases interactivas (:visited).
        enlaces_indice_html += f'                    <a href="#{tema_slug}" class="library-nav__theme-title" aria-label="Explorar estantería: {tema}">{tema}</a>\n'
        enlaces_indice_html += f'                    <ul class="library-nav__article-list">\n'
        
        cards_html = ""
        for pub in pubs_tema:
            # QUÉ HACE: Genera un ID válido para la tarjeta del artículo.
            pub_slug = slugify(pub["titulo"])
            
            # QUÉ HACE: Inyecta cada artículo como un ancla interna apuntando a su tarjeta resumen.
            # POR QUÉ: Retiene al usuario en la página índice para que pueda leer la descripción antes de entrar.
            enlaces_indice_html += f'                        <li class="library-nav__article-item">\n'
            # QUÉ HACE: Diferencia el texto accesible (aria-label) para evitar penalización por enlaces con mismo texto y distinto destino.
            enlaces_indice_html += f'                            <a href="#{pub_slug}" class="library-nav__article-link" aria-label="Ir al resumen de: {pub["titulo"]}">{pub["titulo"]}</a>\n'
            enlaces_indice_html += f'                        </li>\n'
            
            clase_css = "card--booklet" if pub["tipo"].lower() == "cuadernillo" else "card--book"
            badge = pub["tipo"].capitalize()
            fase_badge = f" &middot; Fase {pub['fase']}" if pub.get("fase") else ""
            
            cards_html += f"""
                <article class="card {clase_css}" id="{pub_slug}">
                    <header>
                        <span class="card__meta">{pub["fecha"]} — {badge}{fase_badge}</span>
                        <h2 class="card__title"><a href="{pub["url"]}" aria-label="Leer artículo completo: {pub["titulo"]}">{pub["titulo"]}</a></h2>
                    </header>
                    <div class="card__content">
                        <p>{pub["descripcion"]}</p>
                    </div>
                </article>"""
                
        # Cerramos la lista de artículos y el elemento principal de la estantería
        enlaces_indice_html += f'                    </ul>\n                </li>\n'
                
        # QUÉ HACE: Inyecta el ID para el ancla, 'scroll-margin-top' y un contenedor flex para alinear el botón "Volver arriba" a la derecha.
        # POR QUÉ: Mejora la navegación permitiendo al usuario saltar de vuelta al Mega-Menú inmediatamente después de explorar una estantería.
        secciones_html += f"""
        <section class="library-section" id="{tema_slug}">
            <div class="library-section__header">
                <h2 class="library-section__title home-card__title--highlight"><a href="#{tema_slug}" aria-label="Ver sección: {tema}">{tema}</a></h2>
                <a href="#top" class="library-section__back-link">↑ Volver arriba</a>
            </div>
            <div class="home-grid">
                {cards_html}
            </div>
        </section>"""
                
    html_final = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_html} — merci-boilerplate.es</title>
    <meta name="description" content="{meta_desc_html}">
    <link rel="canonical" href="{canonical_url}">
    <link rel="stylesheet" href="/css/main.css?v={css_v}">
    <script src="/js/MerciController.js?v={js_c_v}" defer></script>
    <script src="/js/main.js?v={js_m_v}" defer></script>
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "CollectionPage",
      "name": {json.dumps(title + " - merci-boilerplate.es")},
      "description": {json.dumps(meta_desc)},
      "url": {json.dumps(canonical_url)}
    }}
    </script>
</head>
<body class="page">
    <div id="top" tabindex="-1" style="position: absolute; top: 0; left: 0;"></div>
    {header_html}
    <main class="main" id="main">
        <!-- QUÉ HACE: Sección Hero unificada con el resto del ecosistema -->
        <section class="hero">
            <h1 class="hero__title">{title_html}</h1>
            <p class="hero__subtitle">{meta_desc_html}</p>
        </section>
        
        <!-- QUÉ HACE: Índice Curado (Table of Contents) autogenerado -->
        <!-- POR QUÉ: Mejora la UX permitiendo navegación intra-página sin scroll excesivo. -->
        <nav class="library-nav" aria-label="Índice de estanterías">
            <h2 class="library-nav__title">Estanterías Temáticas</h2>
            <ul class="library-nav__list">
{enlaces_indice_html}            </ul>
        </nav>
        
        {secciones_html}
    </main>
    {footer_html}
</body>
</html>"""

    out_path.write_text(html_final, encoding="utf-8")
    print(f"  ✅ Índice generado con éxito: {out_path.relative_to(REPO_ROOT)}")

def main(): # type: ignore
    print("🚀 [Merci Publish] Iniciando orquestador de publicación...")
    
    # 0. Limpieza previa (Evitar archivos zombis)
    limpiar_directorio_salida()
    
    # QUÉ HACE: Implementa "Cache Busting" dinámico usando la fecha de modificación del archivo.
    # POR QUÉ: Obliga a los navegadores móviles a descargar la última versión de los assets.
    css_path = REPO_ROOT / "public/css/main.css"
    js_controller_path = REPO_ROOT / "public/js/MerciController.js"
    js_main_path = REPO_ROOT / "public/js/main.js"
    css_version = int(css_path.stat().st_mtime) if css_path.exists() else '11'
    js_controller_version = int(js_controller_path.stat().st_mtime) if js_controller_path.exists() else '11'
    js_main_version = int(js_main_path.stat().st_mtime) if js_main_path.exists() else '11'

    # 0. Extraer Header y Footer dinámicamente de la portada (Single Source of Truth)
    header_html, footer_html = "", ""
    index_path = REPO_ROOT / "public" / "index.html"
    if index_path.exists():
        index_content = index_path.read_text(encoding="utf-8")
        
        # QUÉ HACE: Autoinyecta las nuevas versiones en el index.html (Single Source of Truth)
        # POR QUÉ: Automatiza el Cache Busting. Las páginas satélite lo heredarán a través de merci-sync-pages.py.
        index_content = re.sub(r'(href="/css/main\.css\?v=)\d+', rf'\g<1>{css_version}', index_content)
        index_content = re.sub(r'(src="/js/MerciController\.js\?v=)\d+', rf'\g<1>{js_controller_version}', index_content)
        index_content = re.sub(r'(src="/js/main\.js\?v=)\d+', rf'\g<1>{js_main_version}', index_content)
        index_path.write_text(index_content, encoding="utf-8")

        h_match = re.search(r"(<header.*?</header>)", index_content, re.DOTALL | re.IGNORECASE)
        f_match = re.search(r"(<footer.*?</footer>)", index_content, re.DOTALL | re.IGNORECASE)
        m_match = re.search(r"(<!-- Asistente Virtual -->.*?</aside>)", index_content, re.DOTALL | re.IGNORECASE)
        header_html = h_match.group(1) if h_match else ""
        footer_html = f_match.group(1) if f_match else ""
        
        # QUÉ HACE: Añade el bloque de Merci al footer extraído para inyectarlo en todas las páginas generadas
        if m_match:
            footer_html += f"\n\n    {m_match.group(1)}"

    publicaciones_bib = []
    publicaciones_art = []

    # QUÉ HACE: Lee recursivamente todos los archivos .md en la biblioteca y sus subcarpetas.
    # POR QUÉ: Permite al autor organizar los archivos fuente en subdirectorios temáticos 
    # sin alterar la estructura plana de URLs de salida (/biblioteca/archivo.html).
    if BIBLIOTECA_DIR.exists():
        for md_file in BIBLIOTECA_DIR.rglob("*.md"):
            meta = procesar_archivo(md_file, header_html, footer_html, css_version, js_controller_version, js_main_version)
            if meta:
                publicaciones_bib.append(meta)
                
    if ART_DE_COTE_DIR.exists():
        for md_file in ART_DE_COTE_DIR.rglob("*.md"):
            meta = procesar_archivo(md_file, header_html, footer_html, css_version, js_controller_version, js_main_version)
            if meta:
                publicaciones_art.append(meta)
                
    if publicaciones_bib:
        PUBLIC_BIBLIOTECA.mkdir(parents=True, exist_ok=True)
        generar_indice(publicaciones_bib, PUBLIC_BIBLIOTECA / "index.html", "La Biblioteca", "Índice de publicaciones técnicas y proyectos de la Biblioteca.", "Documentación técnica, proyectos DevSecOps y arquitectura de software. El activo de conocimiento central del ecosistema.", "https://merci-boilerplate.es/biblioteca/", header_html, footer_html, css_version, js_controller_version, js_main_version)
        
    if publicaciones_art:
        PUBLIC_ART_DE_COTE.mkdir(parents=True, exist_ok=True)
        generar_indice(publicaciones_art, PUBLIC_ART_DE_COTE / "index.html", "Art de Coté", "Índice de scripts experimentales, andamiajes y código colateral.", "Scripts, flujos de automatización y código experimental preservado bajo la filosofía Zero Waste (Cero Desperdicio).", "https://merci-boilerplate.es/art-de-cote/", header_html, footer_html, css_version, js_controller_version, js_main_version)
            
    print("🚀 [Merci Publish] Pipeline de conversión finalizado.")

if __name__ == "__main__":
    main()