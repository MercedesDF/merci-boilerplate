#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-init.py — Inicializador del Boilerplate (Fase 10).
Escanea el repositorio recién clonado, purga los datos de origen (mercedev)
e inyecta el nuevo nombre y dominio del proyecto.
"""

import os
import sys
import shutil
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TARGET_EXTENSIONS = {'.html', '.php', '.md', '.py', '.js', '.scss', '.yaml', '.yml'}

def replace_in_files(old_str: str, new_str: str):
    """
    QUÉ HACE: Recorre recursivamente el repositorio buscando y reemplazando cadenas.
    POR QUÉ: Automatiza la personalización del boilerplate, evitando buscar
    y reemplazar manualmente en Nginx, WordPress, HTML y código fuente.
    """
    print(f"  🔄 Reemplazando '{old_str}' por '{new_str}'...")
    count = 0
    for root, dirs, files in os.walk(REPO_ROOT):
        # Excluimos la carpeta .git, los binarios y el propio script
        if '.git' in root or '.assets-raw' in root or 'assets/images' in root:
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

def purge_directory(dir_path: Path, exclude: list = None):
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

def anonimizar_cv(nuevo_nombre: str, nuevo_dominio: str):
    """
    QUÉ HACE: Vacía los datos personales y el JSON-LD de la página sobre-mi.
    POR QUÉ: Data Leak Prevention (DLP). Transforma el currículum de la autora en una plantilla "Anti-ATS" genérica.
    """
    print("  🕵️‍♂️  Anonimizando el CV Semántico (Data Leak Prevention)...")
    cv_path = REPO_ROOT / "public" / "sobre-mi" / "index.html"
    if not cv_path.exists():
        return
        
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
    
    # 1. Purgar y reinyectar JSON-LD
    content = re.sub(r'<script type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">\n    {json_ld_template}\n    </script>', content, flags=re.DOTALL)
    
    # 2. Limpiar Meta Descripcion
    content = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="Perfil técnico y currículum semántico de {nuevo_nombre}.">', content)
    
    # 3. Anonimizar Hero (Textos)
    content = re.sub(r'<h1 class="hero__title">.*?</h1>', r'<h1 class="hero__title">Escribe aquí tu<br>declaración de intenciones.</h1>', content, flags=re.DOTALL)
    content = re.sub(r'<p class="hero__subtitle">.*?</p>', r'<p class="hero__subtitle">Resume aquí tu propuesta de valor, tu enfoque técnico y la madurez que aportas a los proyectos. Sustituye este texto por un resumen de los problemas que resuelves.</p>', content, flags=re.DOTALL)
    
    # 4. Anonimizar el stack de ejemplo en el cuerpo
    content = re.sub(r'<em>DevSecOps, Gobernanza LLM, Python, SSG</em>', r'<em>Stack Tecnológico 1, Habilidad 2, Framework 3</em>', content)
    
    cv_path.write_text(content, encoding="utf-8")

def configure_ai_module(include_ai: bool):
    """Configura la Marca Blanca del asistente o ejecuta su amputación quirúrgica."""
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

def main():
    print("🚀 [Merci Init] Preparación de nuevo proyecto a partir del Boilerplate.")
    print("⚠️  ADVERTENCIA DE SEGURIDAD: Este script es DESTRUCTIVO.")
    print("Destruirá la biblioteca actual y reemplazará todas las referencias de mercedev.es")
    print("Solo debes ejecutar esto cuando hayas CLONADO este repo para un proyecto NUEVO.\n")
    
    confirm = input("¿Estás segura de querer formatear este código base? Escribe 'DESTRUIR' para continuar: ")
    if confirm != "DESTRUIR":
        print("Operación cancelada. El repositorio está a salvo.")
        sys.exit(0)
        
    nuevo_dominio = input("Introduce el nuevo dominio (ej. midominio.com): ").strip()
    nuevo_nombre = input("Introduce el nombre del proyecto (ej. Mi Empresa): ").strip()
    incluir_ia = input("\n🤖 ¿Deseas incluir el módulo de Inteligencia Artificial (Shift-Left AI) en tu proyecto? [Y/n]: ").strip().lower() != 'n'
    
    if not nuevo_dominio or not nuevo_nombre:
        print("❌ Error: Los datos no pueden estar vacíos.")
        sys.exit(1)

    # 1. Reemplazo de identidad
    replace_in_files("mercedev.es", nuevo_dominio)
    replace_in_files("mercedev", nuevo_nombre.lower().replace(" ", ""))
    replace_in_files("Mercedes", nuevo_nombre)
    
    anonimizar_cv(nuevo_nombre, nuevo_dominio)
    configure_ai_module(incluir_ia)

    # 2. Purga de datos históricos
    purge_directory(REPO_ROOT / "biblioteca")
    purge_directory(REPO_ROOT / "laboratorio", exclude=["bitacora-merci-boilerplate.md"])
    purge_directory(REPO_ROOT / "blog")
    purge_directory(REPO_ROOT / "art-de-cote")
    purge_directory(REPO_ROOT / "public" / "biblioteca")
    purge_directory(REPO_ROOT / "public" / "descargas")
    purge_directory(REPO_ROOT / "public" / "art-de-cote")
    
    # QUÉ HACE: Purga incondicional de la base de conocimientos estática de la IA.
    # POR QUÉ: DLP (Data Leak Prevention). Garantiza que la IA nazca con amnesia, sin arrastrar las respuestas cacheadas de la autora.
    (REPO_ROOT / "public" / "js" / "brain_data.json").unlink(missing_ok=True)
    
    # QUÉ HACE: Elimina el flujo de despliegue automático a producción.
    # POR QUÉ: Prevención de acoplamiento. El Boilerplate es agnóstico y no debe heredar rutinas de CD con rutas hardcodeadas de la matriz.
    (REPO_ROOT / ".github" / "workflows" / "deploy.yml").unlink(missing_ok=True)

    # QUÉ HACE: Reconstruye las carpetas estructurales (Matriz y Laboratorio).
    # POR QUÉ: Recrearlas vacías garantiza que no haya fugas de datos (borradores antiguos)
    # pero asegura que el andamiaje del Headless CMS esté listo para el nuevo usuario.
    for dir_name in ["blog", "art-de-cote"]:
        for base in ["laboratorio", ""]:
            dir_path = REPO_ROOT / base / dir_name if base else REPO_ROOT / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            (dir_path / ".gitkeep").touch(exist_ok=True)

    # QUÉ HACE: Purga el material multimedia personal del autor original.
    # POR QUÉ: Evita engordar el Boilerplate con fotos propias, pero preserva 
    # los iconos estructurales de la UI (logos y el avatar del asistente Merci).
    purge_directory(REPO_ROOT / ".assets-raw")
    
    imagenes_a_conservar = ["favicon.ico", "favicon.png", "logo.webp", "logo.png"]
    if incluir_ia:
        imagenes_a_conservar.append("Merci-en-la-nube.webp")
    purge_directory(REPO_ROOT / "assets" / "images", exclude=imagenes_a_conservar)
    
    # Purga selectiva de manuales operativos exclusivos de la matriz
    print("  🗑️  Purgando manuales SOP exclusivos del proyecto matriz...")
    docs_matriz = REPO_ROOT / "docs" / "matriz"
    if docs_matriz.exists():
        shutil.rmtree(docs_matriz)
    
    # 3. Intercambio Documental (Los Gemelos)
    print("  📄 Intercambiando documentación matriz por documentación agnóstica...")
    
    # Borramos la identidad documental del autor original
    (REPO_ROOT / "README.md").unlink(missing_ok=True)
    (REPO_ROOT / "instrucciones.md").unlink(missing_ok=True)
    
    # Ascendemos los archivos gemelos a oficiales
    readme_merci = REPO_ROOT / "README-merci.md"
    if readme_merci.exists():
        readme_merci.rename(REPO_ROOT / "README.md")
        
    instrucciones_merci = REPO_ROOT / "instrucciones-merci.md"
    if instrucciones_merci.exists():
        instrucciones_merci.rename(REPO_ROOT / "instrucciones.md")

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

    print("\n🎉 ¡Inicialización completada! Bienvenido a tu nuevo proyecto.")

if __name__ == "__main__":
    main()