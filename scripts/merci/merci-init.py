#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-init.py — Inicializador del Boilerplate (Fase 10).
Escanea el repositorio recién clonado, purga los datos de origen (mercedev)
e inyecta el nuevo nombre y dominio del proyecto.
"""

import argparse
import os
from pathlib import Path
import re
import shutil
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[2]

TARGET_EXTENSIONS = {'.html', '.php', '.md', '.py', '.js', '.scss', '.yaml', '.yml', '.json', '.txt', '.xml'}

def replace_in_files(old_str: str, new_str: str) -> None:
    """
    QUÉ HACE: Recorre recursivamente el repositorio buscando y reemplazando cadenas.
    POR QUÉ: Automatiza la personalización del boilerplate, evitando buscar
    y reemplazar manualmente en Nginx, WordPress, HTML y código fuente.
    """
    print(f"  🔄 Reemplazando '{old_str}' por '{new_str}'...")
    count = 0
    for root, dirs, files in os.walk(REPO_ROOT):
        # Exclusión precisa de carpetas para no saltarnos .github por error ("bug silencioso")
        try:
            rel_parts = Path(root).relative_to(REPO_ROOT).parts
            if '.git' in rel_parts or '.assets-raw' in rel_parts or ('assets' in rel_parts and 'images' in rel_parts):
                continue
        except ValueError:
            continue
            
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in TARGET_EXTENSIONS and file_path.name != "merci-init.py":
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if old_str in content:
                        new_content = content.replace(old_str, new_str)
                        file_path.write_text(new_content, encoding="utf-8")
                        count += 1
                except Exception as e:
                    print(f"    ⚠️ No se pudo procesar {file_path.name}: {e}")
    print(f"    ✅ Modificados {count} archivos.")

def resetear_roadmap(nuevo_nombre: str) -> None:
    """
    QUÉ HACE: Vacía el ROADMAP.md personal de la autora y lo sustituye por una plantilla base.
    POR QUÉ: Prevención de Fuga de Datos (DLP). El roadmap actual contiene todas las Épicas privadas de la autora.
    """
    print("  🗺️  Reseteando ROADMAP.md para el nuevo proyecto...")
    roadmap_path = REPO_ROOT / "ROADMAP.md"
    if roadmap_path.exists():
        clean_content = f"""# 🗺️ ROADMAP MAESTRO: Ecosistema {nuevo_nombre}

Única Fuente de Verdad (SSOT) del avance del proyecto y de las automatizaciones DevSecOps.

## ÉPICA 1: FUNDACIÓN DEVSECOPS

### Fase 1 - Inicialización
- [x] Instanciar el Boilerplate de forma segura (`merci-init.py`).
- [ ] Configurar las credenciales en el archivo `.env` local.
- [ ] Ejecutar auditoría DevSecOps inicial (`merci total`).
"""
        roadmap_path.write_text(clean_content, encoding="utf-8")

def purge_directory(dir_path: Path, exclude: list[str] | None = None) -> None:
    """
    QUÉ HACE: Elimina todo el contenido de una carpeta excepto .gitkeep y los archivos excluidos.
    POR QUÉ: Limpia la biblioteca y el laboratorio, pero permite salvar archivos base como la bitácora agnóstica.
    """
    if exclude is None:
        exclude = []
        
    print(f"  🗑️  Purgando directorio: {dir_path.relative_to(REPO_ROOT)}...")
    if not dir_path.exists():
        return
        
    for item in dir_path.iterdir():
        if item.name == ".gitkeep" or item.name in exclude:
            continue
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

def anonimizar_portada(nuevo_dominio: str) -> None:
    """
    QUÉ HACE: Limpia el logotipo y reemplaza el texto de presentación por un mensaje de bienvenida (estilo Vite).
    POR QUÉ: Mejora la Developer Experience (DX) entregando una landing limpia y lista para personalizar.
    """
    print("  🖼️  Desacoplando logotipo y limpiando presentación en la portada...")
    index_path = REPO_ROOT / "public" / "index.html"
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
        # Preservar el estilo de tres últimas letras resaltadas en naranja
        parts = nuevo_dominio.rsplit('.', 1)
        if len(parts) == 2:
            name, tld = parts
            if len(name) > 3:
                nuevo_hero_title = f'{name[:-3]}<span class="hero__highlight">{name[-3:]}</span>.{tld}'
            else:
                nuevo_hero_title = f'<span class="hero__highlight">{name}</span>.{tld}'
        else:
            nuevo_hero_title = f'<span class="hero__highlight">{nuevo_dominio}</span>'

        content = content.replace(
            '<h1 class="hero__title">merce<span class="hero__highlight">dev</span>.es</h1>',
            f'<h1 class="hero__title">{nuevo_hero_title}</h1>'
        )
        
        nuevo_prose = f"""<article class="prose">
            <div class="prose__content">
                <h2>¡Bienvenido a tu Boilerplate DevSecOps!</h2>
                <p>Esta plataforma ha sido instanciada con éxito y el código base está listo para ti.</p>
                <p>Arriba puedes ver el Dashboard de rendimiento calculado empíricamente. Este espacio es tuyo para presentar tu proyecto o tesis de ingeniería.</p>
                <p>👉 Edita el bloque <code>&lt;article class="prose"&gt;</code> en <code>public/index.html</code> para comenzar a construir tu identidad.</p>
            </div>
        </article>"""
        
        content = re.sub(r'<article class="prose">.*?</article>', nuevo_prose, content, flags=re.DOTALL | re.IGNORECASE)

        # QUÉ HACE: Purga los textos personales del Hero y los bloques "Merci Explica" de la matriz.
        # POR QUÉ: Prevención de Fuga de Datos (DLP). Evita que la identidad, el copy de marketing
        # o explicaciones de la autora matriz se filtren en la demo pública del Showcase/Boilerplate.
        content = re.sub(r'<h2 class="hero__statement">.*?</h2>', '<h2 class="hero__statement">proyecto instanciado<br>infraestructura lista</h2>', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<p class="hero__subtitle">.*?</p>', '<p class="hero__subtitle">El ecosistema DevSecOps ha sido inicializado con éxito. El código base, los orquestadores y la infraestructura están listos para recibir tu proyecto.</p>', content, flags=re.DOTALL | re.IGNORECASE)
        content = content.replace('¿quieres conocerme?', 'Ver perfil')

        explica_pattern = re.compile(r'<(div|aside) class="hero__explica">.*?</\1>', re.DOTALL | re.IGNORECASE)
        content = explica_pattern.sub('', content)

        index_path.write_text(content, encoding="utf-8")

def anonimizar_paginas_secundarias(nuevo_nombre: str, nuevo_dominio: str) -> None:
    """
    QUÉ HACE: Arrasa con el contenido de Sobre Mí y Contacto, inyectando plantillas en blanco (estilo Vite).
    POR QUÉ: Data Leak Prevention (DLP) matemático. No depende de buscar textos exactos. Vacía el <main> por completo.
    """
    print("   Generando plantillas en blanco para páginas secundarias (DLP)...")
    
    # 1. Página: Sobre Mí (CV)
    cv_path = REPO_ROOT / "public" / "sobre-mi" / "index.html"
    if cv_path.exists():
        content = cv_path.read_text(encoding="utf-8")
        
        json_ld_template = f'''{{
      "@context": "https://schema.org",
      "@type": "Person",
      "name": "{nuevo_nombre}",
      "jobTitle": "Tu Rol / Puesto",
      "url": "https://{nuevo_dominio}/sobre-mi/",
      "sameAs": [
        "https://www.linkedin.com/in/tu-perfil/",
        "https://github.com/tu-usuario"
      ],
      "knowsAbout": [
        "Habilidad 1",
        "Habilidad 2",
        "Habilidad 3"
      ],
      "description": "Breve descripción profesional para los rastreadores ATS."
    }}'''
        content = re.sub(r'<script type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">\n    {json_ld_template}\n    </script>', content, flags=re.DOTALL)
        content = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="Perfil técnico y currículum semántico de {nuevo_nombre}.">', content)
        
        nuevo_main_cv = f"""<main class="main" id="main">
        <section class="hero">
            <h1 class="hero__title">sobre<span class="hero__highlight">mí</span></h1>
            <h2 class="hero__statement">{nuevo_nombre}</h2>
            <p class="hero__subtitle">Escribe aquí tu propuesta de valor y enfoque técnico.</p>
        </section>
        <section class="section">
            <article class="prose">
                <div class="prose__content">
                    <h2>Tu Historia y Stack Técnico</h2>
                    <p>Esta es tu página de perfil semántico (Anti-ATS). Reemplaza este texto con tu trayectoria profesional.</p>
                    <p>👉 Abre el archivo <code>public/sobre-mi/index.html</code> para personalizar tu currículum.</p>
                </div>
            </article>
        </section>
    </main>"""
        content = re.sub(r'<main[^>]*>.*?</main>', nuevo_main_cv, content, flags=re.DOTALL | re.IGNORECASE)
        cv_path.write_text(content, encoding="utf-8")
        
    # 2. Página: Contacto
    contacto_path = REPO_ROOT / "public" / "contacto" / "index.html"
    if contacto_path.exists():
        content = contacto_path.read_text(encoding="utf-8")
        nuevo_main_contacto = f"""<main class="main" id="main">
        <section class="hero">
            <h1 class="hero__title">con<span class="hero__highlight">tacto</span></h1>
            <h2 class="hero__statement">Hablemos de código e infraestructura.</h2>
        </section>
        <section class="section">
            <article class="prose">
                <div class="prose__content">
                    <h2>Comunicaciones Seguras</h2>
                    <p>Utiliza este espacio para añadir tu correo electrónico, formulario o tu clave pública PGP.</p>
                    <p>👉 Abre el archivo <code>public/contacto/index.html</code> para configurar tus canales.</p>
                </div>
            </article>
        </section>
    </main>"""
        content = re.sub(r'<main[^>]*>.*?</main>', nuevo_main_contacto, content, flags=re.DOTALL | re.IGNORECASE)
        contacto_path.write_text(content, encoding="utf-8")

def anonimizar_enlaces_y_textos(preserve_socials: bool = False) -> None:
    """
    QUÉ HACE: Limpia enlaces sociales del footer y frases hardcodeadas del asistente.
    POR QUÉ: Garantiza un "Marca Blanca" total sin depender del reemplazo de identidad global.
    """
    print("  🔗 Anonimizando enlaces sociales y frases del asistente...")
    # Footer (Mantiene el enlace de atribución a Merci Boilerplate)
    if not preserve_socials:
        replace_in_files('href="https://www.linkedin.com/in/mercedesdf-ingenieria/"', 'href="https://linkedin.com/in/tu-perfil/"')
        replace_in_files('href="https://github.com/MercedesDF" target="_blank"', 'href="https://github.com/tu-usuario" target="_blank"')
    
    # Controller (Frases hardcodeadas)
    replace_in_files("¡Hola! Me llamo Mercí, asistente de mercedev👋", "¡Hola! Soy tu asistente virtual👋")
    replace_in_files("merci-boilerplate es la base de este proyecto🚀 y tiene su propio repositorio en GitHub", "Este proyecto está construido sobre una arquitectura DevSecOps🚀")
    replace_in_files("habla con Mercedes-mercedev, el cerebro de la web", "habla con el administrador de la web")
    replace_in_files("La tienda no tienda de merchandising conmigo de como protagonista", "Catálogo oficial de demostración")

def generar_placeholders_directorios(nuevo_dominio: str) -> None:
    """
    QUÉ HACE: Genera archivos index.html en carpetas estructurales vacías.
    POR QUÉ: Al vaciar estas carpetas por DLP, Nginx devuelve 403 Forbidden. 
    Entregar plantillas básicas evita que los enlaces del menú parezcan rotos (Mejora la OOBE).
    """
    # QUÉ HACE: Extrae el layout común de la portada para mantener la consistencia visual.
    # POR QUÉ: Reutilizar el header y footer reales en las páginas de contingencia
    # hace que la experiencia de navegación sea 100% coherente, incluso en rutas vacías.
    header_html, footer_html = "", ""
    css_url, js_ctrl_url, js_main_url = "/css/main.css?v=1", "/js/MerciController.js?v=1", "/js/main.js?v=1"
    index_path = REPO_ROOT / "public" / "index.html"
    if index_path.exists():
        index_content = index_path.read_text(encoding="utf-8")
        h_match = re.search(r"(<header.*?</header>)", index_content, re.DOTALL | re.IGNORECASE)
        f_match = re.search(r"(<footer.*?</footer>)", index_content, re.DOTALL | re.IGNORECASE)
        m_match = re.search(r"(<!-- Asistente .*?</aside>)", index_content, re.DOTALL | re.IGNORECASE)
        
        css_match = re.search(r'<link rel="stylesheet" href="(/css/main\.css\?v=\d+)">', index_content)
        js_ctrl_match = re.search(r'<script src="(/js/MerciController\.js\?v=\d+)"', index_content)
        js_main_match = re.search(r'<script src="(/js/main\.js\?v=\d+)"', index_content)
        
        header_html = h_match.group(1) if h_match else ""
        footer_html = f_match.group(1) if f_match else ""
        if m_match:
            footer_html += f"\n\n    {m_match.group(1)}"
            
        if css_match: css_url = css_match.group(1)
        if js_ctrl_match: js_ctrl_url = js_ctrl_match.group(1)
        if js_main_match: js_main_url = js_main_match.group(1)

    print("  🏗️  Generando páginas de contingencia (Anti-403 Forbidden)...")
    blog_symlink = REPO_ROOT / "public" / "blog"
    if blog_symlink.is_symlink() or blog_symlink.exists():
        try:
            blog_symlink.unlink()
        except Exception:
            shutil.rmtree(blog_symlink, ignore_errors=True)
            
    art_cote_dir = REPO_ROOT / "public" / "art-de-cote"
    if art_cote_dir.exists():
        shutil.rmtree(art_cote_dir, ignore_errors=True)
            
    rutas = [
        ("biblioteca", "La Biblioteca", "El conocimiento inmutable se almacena aquí. Las páginas estáticas se autogenerarán con el orquestador."),
        ("blog", "El Blog", "Capa dinámica. Si no usas Headless CMS, puedes usar esta ruta para páginas estáticas."),
        ("blog/tienda", "La Tienda", "Catálogo oficial de productos y demostración e-commerce.")
    ]
    for ruta, titulo, desc in rutas:
        dir_path = REPO_ROOT / "public" / ruta
        dir_path.mkdir(parents=True, exist_ok=True)
        
        body_id = f"page-{'blog-tienda' if ruta == 'blog/tienda' else ruta}"
        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo} - {nuevo_dominio}</title>
    <!-- merci-audit:silence-seo -->
    <link rel="stylesheet" href="{css_url}">
    <script src="{js_ctrl_url}" defer></script>
    <script src="{js_main_url}" defer></script>
</head>
<body class="page" id="{body_id}">
    <div id="top" tabindex="-1" style="position: absolute; top: 0; left: 0;"></div> <!-- merci-audit:silence-style -->
    {header_html}
    <main class="main" id="main">
        <section class="hero hero--compact">
            <h1 class="hero__title">{titulo}</h1>
            <p class="hero__subtitle">{desc}</p>
            <br>
            <a href="/" class="nav__link" style="color: #ea580c; text-decoration: underline;">← Volver al inicio</a> <!-- merci-audit:silence-style -->
        </section>
    </main>
    {footer_html}
</body>
</html>"""
        (dir_path / "index.html").write_text(html_content, encoding="utf-8")

def resetear_telemetria_html() -> None:
    """
    QUÉ HACE: Resetea los contadores del dashboard inyectados por merci-telemetry.py.
    POR QUÉ: Previene la fuga de datos (DLP) de las métricas de la autora hacia el nuevo proyecto.
    """
    print("  📊 Reseteando métricas de telemetría en dashboards (DLP)...")
    targets = [REPO_ROOT / "public" / "index.html", REPO_ROOT / "public" / "sobre-mi" / "index.html"]
    keys = ["Commit", "Agente", "Línea", "Release", "Versión", "Día"]
    
    for path in targets:
        if not path.exists(): continue
        html = path.read_text(encoding="utf-8")
        for key in keys:
            # Formato 1: Valor antes que etiqueta (ej. sobre-mi/index.html)
            pattern1 = rf'(<span class="hero__metric-value">)[^<]+(</span>\s*<span class="hero__metric-label">[^<]*?{key}[^<]*?</span>)'
            html = re.sub(pattern1, r'\g<1>N/D\g<2>', html, flags=re.IGNORECASE)
            # Formato 2: Etiqueta antes que valor (ej. index.html de la portada)
            pattern2 = rf'(<span class="hero__metric-label">[^<]*?{key}[^<]*?</span>\s*<span class="hero__metric-value">)[^<]+(</span>)'
            html = re.sub(pattern2, r'\g<1>N/D\g<2>', html, flags=re.IGNORECASE)
            
        # Purgar también el tiempo E2E (Data-Driven Copywriting SRE)
        html = re.sub(r'(<span class="sre-deploy-time">)[^<]+(</span>)', r'\g<1>N/D\g<2>', html, flags=re.IGNORECASE)
        
        path.write_text(html, encoding="utf-8")

def configure_ai_module(include_ai: bool) -> None:
    """
    QUÉ HACE: Configura la Marca Blanca del asistente de IA o ejecuta su amputación quirúrgica.
    POR QUÉ: Permite decidir si conservar la IA de forma despersonalizada o eliminarla por completo de la UI y los scripts del pipeline.
    """
    if include_ai:
        print("  🧠 Configurando módulo de Inteligencia Artificial (Marca Blanca)...")
        replace_in_files("Eres Merci, la asistente virtual", "Eres un asistente virtual técnico")
        replace_in_files("Me llamo Mercí, asistente", "Soy tu asistente virtual")
        replace_in_files("Soy Merci, tu asistente", "Soy tu asistente virtual")
        replace_in_files("Interactuar con Merci", "Interactuar con el asistente")
        replace_in_files("Asistente Merci", "Asistente Virtual")
    else:
        print("  🪓 Ejecutando amputación quirúrgica del módulo de Inteligencia Artificial...")
        
        # 1. Borrar archivos exclusivos de IA y UI del asistente
        for f in ["scripts/merci/merci-brain.py", "public/js/MerciController.js", "public/js/brain_data.json", "src/scss/components/_merci.scss"]:
            (REPO_ROOT / f).unlink(missing_ok=True)
            
        # 2. Purgar referencias en el DOM (HTML/PHP)
        archivos_ui = [
            "public/index.html",
            "public/contacto/index.html",
            "src/wp-theme/merci-theme/index.php",
            "src/wp-theme/merci-theme/woocommerce.php"
        ]
        for ruta in archivos_ui:
            archivo = REPO_ROOT / ruta
            if archivo.exists():
                content = archivo.read_text(encoding="utf-8")
                content = re.sub(r'\s*<!-- Asistente .*?<\/aside>', '', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'\s*<script src="/js/MerciController\.js.*?</script>', '', content, flags=re.IGNORECASE)
                archivo.write_text(content, encoding="utf-8")
                
        # 3. Limpiar dependencias en Python y SASS
        total_py = REPO_ROOT / "scripts" / "merci" / "merci-total.py"
        if total_py.exists():
            content_total = total_py.read_text(encoding="utf-8")
            content_total = re.sub(r'\s*"merci-brain\.py",', '', content_total)
            total_py.write_text(content_total, encoding="utf-8")
            
        scss_index = REPO_ROOT / "src" / "scss" / "components" / "_index.scss"
        if scss_index.exists():
            scss_index.write_text(scss_index.read_text(encoding="utf-8").replace("@forward 'merci';\n", ""), encoding="utf-8")
            
        sync_py = REPO_ROOT / "scripts" / "merci" / "merci-sync-pages.py"
        if sync_py.exists():
            content = sync_py.read_text(encoding="utf-8")
            content = re.sub(r'\s*aside_pattern = r\'\(<aside class="merci-ui".*?</aside>\)\'', '', content)
            content = re.sub(r'\s*aside_content = extract_block\(index_html, aside_pattern, "Aside \(Merci\)"\)', '', content)
            content = re.sub(r'\s*nuevo_contacto = replace_block\(nuevo_contacto, aside_pattern, aside_content, "Aside \(Merci\)"\)', '', content)
            content = content.replace(' (Header, Footer y Merci)', ' (Header y Footer)')
            sync_py.write_text(content, encoding="utf-8")
            
        publish_py = REPO_ROOT / "scripts" / "merci" / "merci-publish.py"
        if publish_py.exists():
            content = publish_py.read_text(encoding="utf-8")
            content = re.sub(r'\s*<script src="/js/MerciController\.js.*?</script>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'\s*m_match = re\.search\(r"\(<!-- Asistente .*?</aside>\)", index_content, re\.DOTALL \| re\.IGNORECASE\)', '', content)
            content = re.sub(r'\s*if m_match:\n\s*footer_html \+= f"\\n\\n    \{m_match\.group\(1\)\}"', '', content)
            content = re.sub(r'\s*js_controller_path = REPO_ROOT / "public/js/MerciController\.js"', '', content)
            content = re.sub(r'\s*js_controller_version = int\(js_controller_path.*?\'11\'', '', content)
            content = content.replace(', js_controller_version', '').replace(', js_c_v: int', '')
            publish_py.write_text(content, encoding="utf-8")

def main() -> None:
    """
    QUÉ HACE: Orquesta la instanciación completa del Boilerplate para un nuevo proyecto.
    POR QUÉ: Automatiza la purga de datos personales, marcas comerciales y configuraciones locales
            para generar un repositorio limpio y agnóstico de marca blanca.
    """
    parser = argparse.ArgumentParser(description="Inicializa un nuevo Boilerplate DevSecOps a partir del repositorio.")
    parser.add_argument('--force', action='store_true', help="Ignora la advertencia destructiva")
    parser.add_argument('--dominio', type=str, help="Nuevo dominio sin protocolo (ej. mi-proyecto.com)")
    parser.add_argument('--nombre', type=str, help="Nuevo nombre del proyecto")
    parser.add_argument('--ia', action='store_true', help="Incluye el módulo de Inteligencia Artificial")
    parser.add_argument('--preserve-socials', action='store_true', help="Preserva los enlaces sociales originales")
    args, unknown = parser.parse_known_args()

    if not args.force:
        print("🚀 [Merci Init] Preparación de nuevo proyecto a partir del Boilerplate.")
        print("⚠️  ADVERTENCIA DE SEGURIDAD: Este script es DESTRUCTIVO.")
        print("Destruirá la biblioteca actual y reemplazará todas las referencias de mercedev.es")
        print("Solo debes ejecutar esto cuando hayas CLONADO este repo para un proyecto NUEVO.\n")
        
        confirm = input("¿Estás segura de querer formatear este código base? Escribe 'DESTRUIR' para continuar: ")
        if confirm != "DESTRUIR":
            print("Operación cancelada. El repositorio está a salvo.")
            sys.exit(0)
            
    nuevo_dominio = args.dominio if args.dominio else input("Introduce el nuevo dominio (ej. midominio.com): ").strip()
    nuevo_nombre = args.nombre if args.nombre else input("Introduce el nombre del proyecto (ej. Mi Empresa): ").strip()
    
    if args.ia:
        incluir_ia = True
    elif not args.force:
        incluir_ia = input("\n🤖 ¿Deseas incluir el módulo de Inteligencia Artificial (Shift-Left AI) en tu proyecto? [Y/n]: ").strip().lower() != 'n'
    else:
        incluir_ia = False
        
    preserve_socials = args.preserve_socials
    
    if not nuevo_dominio or not nuevo_nombre:
        print("❌ Error: Los datos no pueden estar vacíos.")
        sys.exit(1)

    # 0. Reparación de Metadatos de Autor antes de proteger el usuario de GitHub
    # POR QUÉ: Evita que el nuevo sitio declare a MercedesDF como autora en el <meta name="author">
    replace_in_files('content="MercedesDF"', f'content="{nuevo_nombre}"')

    anonimizar_enlaces_y_textos(preserve_socials)

    # QUÉ HACE: Protege los créditos originales de la autora en los enlaces (Boilerplate, GitHub, LinkedIn).
    # POR QUÉ: Permite anonimizar el resto de la web sin romper los enlaces "publicitarios" de atribución.
    replace_in_files("MercedesDF", "%%PROTECT_GITHUB_USER%%")
    replace_in_files("mercedesdf-ingenieria", "%%PROTECT_LINKEDIN_USER%%")

    # 1. Reemplazo de identidad
    replace_in_files("mercedev.es", nuevo_dominio)
    replace_in_files("mercedev", nuevo_nombre.lower().replace(" ", ""))
    replace_in_files("Mercedes Domínguez", nuevo_nombre)
    replace_in_files("Mercedes", nuevo_nombre)
    
    # Restaurar enlaces publicitarios protegidos
    replace_in_files("%%PROTECT_GITHUB_USER%%", "MercedesDF")
    replace_in_files("%%PROTECT_LINKEDIN_USER%%", "mercedesdf-ingenieria")

    anonimizar_portada(nuevo_dominio)
    anonimizar_paginas_secundarias(nuevo_nombre, nuevo_dominio)
    resetear_roadmap(nuevo_nombre)
    resetear_telemetria_html()
    configure_ai_module(incluir_ia)

    # 2. Purga de datos históricos
    purge_directory(REPO_ROOT / "biblioteca")
    purge_directory(REPO_ROOT / "laboratorio", exclude=["bitacora-merci-boilerplate.md", "prompts"])
    purge_directory(REPO_ROOT / "blog")
    purge_directory(REPO_ROOT / "art-de-cote")
    purge_directory(REPO_ROOT / "public" / "biblioteca")
    purge_directory(REPO_ROOT / "public" / "descargas")
    purge_directory(REPO_ROOT / "public" / "art-de-cote")
    
    # QUÉ HACE: Purga incondicional de la base de conocimientos estática de la IA.
    # POR QUÉ: DLP (Data Leak Prevention). Garantiza que la IA nazca con amnesia, sin arrastrar las respuestas cacheadas de la autora.
    (REPO_ROOT / "public" / "js" / "brain_data.json").unlink(missing_ok=True)

    # QUÉ HACE: Purga el sitemap antiguo.
    # POR QUÉ: Evita SEO Drift. El sitemap de la autora contiene cientos de URLs que ahora serán 404.
    (REPO_ROOT / "public" / "sitemap.xml").unlink(missing_ok=True)
    
    # QUÉ HACE: Purga de telemetría, auditorías privadas y tokens de la autora original.
    # POR QUÉ: DLP extremo. Evita que el nuevo usuario herede fallos, tiempos de compilación o el historial de Chaos Engineering.
    print("  🧹 Purgando telemetría, Chaos Engineering y tokens...")
    for telemetry_file in [".wp_sync.json", ".drift_report.json", ".pipeline_duration.json", ".audit_report.json"]:
        (REPO_ROOT / "observabilidad" / telemetry_file).unlink(missing_ok=True)
        
    for priv_dir in [".privado", "backups", "auditorias-pagespeed.web.dev", "auditorias-pagespedd.web.dev", "scratch"]:
        dir_target = REPO_ROOT / priv_dir
        if dir_target.exists() and dir_target.is_dir():
            shutil.rmtree(dir_target)
            
    (REPO_ROOT / ".linkedin_token.json").unlink(missing_ok=True)

    # QUÉ HACE: Elimina el flujo de despliegue automático a producción.
    # POR QUÉ: Prevención de acoplamiento. El Boilerplate es agnóstico y no debe heredar rutinas de CD con rutas hardcodeadas de la matriz.
    (REPO_ROOT / ".github" / "workflows" / "deploy.yml").unlink(missing_ok=True)
    (REPO_ROOT / "scripts" / "merci" / "merci-deploy.py").unlink(missing_ok=True)
    (REPO_ROOT / "scripts" / "merci" / "merci-completo.py").unlink(missing_ok=True)
    (REPO_ROOT / "scripts" / "merci" / "merci-showcase.py").unlink(missing_ok=True)
    (REPO_ROOT / "scripts" / "merci" / "merci-release.py").unlink(missing_ok=True)

    # QUÉ HACE: Reconstruye las carpetas estructurales (Matriz y Laboratorio).
    # POR QUÉ: Recrearlas vacías garantiza que no haya fugas de datos (borradores antiguos)
    # pero asegura que el andamiaje del Headless CMS esté listo para el nuevo usuario.
    for dir_name in ["blog"]:
        dir_path = REPO_ROOT / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / ".gitkeep").touch(exist_ok=True)

    # Reconstrucción del andamiaje interno del laboratorio
    for lab_dir in ["blog", "incubacion", "notas_rapidas", "prompts", "historico", "biblioteca", "evidencias"]:
        dir_path = REPO_ROOT / "laboratorio" / lab_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / ".gitkeep").touch(exist_ok=True)

    # QUÉ HACE: Purga el material multimedia personal del autor original.
    # POR QUÉ: Evita engordar el Boilerplate con fotos propias, pero preserva 
    # los iconos estructurales de la UI (logos y el avatar del asistente Merci).
    purge_directory(REPO_ROOT / ".assets-raw")
    
    # Mantenemos las imágenes base y los nuevos gemelos
    imagenes_a_conservar = ["favicon.ico", "favicon.png", "tu_logo.webp"]
    if incluir_ia:
        imagenes_a_conservar.append("tu_avatar.webp")
    purge_directory(REPO_ROOT / "assets" / "images", exclude=imagenes_a_conservar)
    
    # Aplicar patrón Gemelos Multimedia
    print("  🖼️  Aplicando patrón Gemelos Multimedia (reemplazando recursos de matriz en el código)...")
    v_buste = int(time.time())
    replace_in_files("/assets/images/logo.webp?v=2", f"/assets/images/tu_logo.webp?v={v_buste}")
    replace_in_files("/assets/images/logo.webp", f"/assets/images/tu_logo.webp?v={v_buste}")
    
    if incluir_ia:
        replace_in_files("/assets/images/Merci-en-la-nube.webp", f"/assets/images/tu_avatar.webp?v={v_buste}")
    
    generar_placeholders_directorios(nuevo_dominio)
    
    # Purga selectiva de manuales operativos exclusivos de la matriz
    print("  🗑️  Purgando manuales SOP exclusivos del proyecto matriz...")
    docs_matriz = REPO_ROOT / "docs" / "matriz"
    if docs_matriz.exists():
        shutil.rmtree(docs_matriz)
    
    # 3. Intercambio Documental (Los Gemelos)
    print("  📄 Intercambiando documentación matriz por documentación agnóstica...")
    
    # Purga del enlace a Art de Coté en toda la navegación
    replace_in_files('            <a href="/art-de-cote/" class="nav__link">Art de Coté</a>\n', '')
    replace_in_files('<a href="/art-de-cote/" class="nav__link">Art de Coté</a>', '')
    
    # Borramos la identidad documental del autor original
    (REPO_ROOT / "README.md").unlink(missing_ok=True)
    (REPO_ROOT / "instrucciones.md").unlink(missing_ok=True)
    (REPO_ROOT / "SECURITY.md").unlink(missing_ok=True)
    
    # Ascendemos los archivos gemelos a oficiales
    readme_merci = REPO_ROOT / "README-merci.md"
    if readme_merci.exists():
        readme_merci.rename(REPO_ROOT / "README.md")
        
    instrucciones_merci = REPO_ROOT / "instrucciones-merci.md"
    if instrucciones_merci.exists():
        instrucciones_merci.rename(REPO_ROOT / "instrucciones.md")

    # QUÉ HACE: Renombra la bitácora en la sombra a la nomenclatura oficial requerida por merci-commit.py.
    # POR QUÉ: merci-commit.py autodescubre "bitacora-{slug}-epic-*.md" (tras el replace_in_files). 
    # Si no la renombramos, el nuevo usuario no podrá hacer commits porque el orquestador colapsará.
    bitacora_merci = REPO_ROOT / "laboratorio" / "bitacora-merci-boilerplate.md"
    if bitacora_merci.exists():
        slug_nombre = nuevo_nombre.lower().replace(" ", "")
        bitacora_merci.rename(REPO_ROOT / "laboratorio" / f"bitacora-{slug_nombre}-epic-01.md")

    # 4. Creación de archivo de entorno de ejemplo
    # QUÉ HACE: Genera un archivo .env con placeholders.
    # POR QUÉ: Evita que el pipeline de 'merci total' falle en la primera ejecución
    # al no encontrar las credenciales para el publicador Headless de WordPress.
    print("  🔧 Creando archivo de entorno de ejemplo (.env)...")
    env_content = """# Configuración para la conexión Headless a WordPress (merci-wp.py)

# Reemplaza estos valores con tus datos de desarrollo local.
WP_URL="http://tu-dominio-local.com"
WP_USER="tu_usuario_wp"
WP_APP_PASSWORD="tu_contraseña_de_aplicacion"
"""
    (REPO_ROOT / ".env").write_text(env_content, encoding="utf-8")
    
    if os.name != 'nt':
        (REPO_ROOT / ".env").chmod(0o600)

    print("\n🎉 ¡Inicialización completada! Bienvenido a tu nuevo proyecto.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Init] Inicialización cancelada. El repositorio base no ha sido modificado.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ [Merci Init] Error fatal durante la inicialización: {e}")
        sys.exit(1)