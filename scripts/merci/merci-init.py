#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-init.py — Inicializador del Boilerplate (Fase 10).
Escanea el repositorio recién clonado, purga los datos de origen (mercedev)
e inyecta el nuevo nombre y dominio del proyecto.
"""

import os
import sys
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
            import shutil
            shutil.rmtree(item)

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
    
    if not nuevo_dominio or not nuevo_nombre:
        print("❌ Error: Los datos no pueden estar vacíos.")
        sys.exit(1)

    # 1. Reemplazo de identidad
    replace_in_files("mercedev.es", nuevo_dominio)
    replace_in_files("mercedev", nuevo_nombre.lower().replace(" ", ""))
    replace_in_files("Mercedes", nuevo_nombre)

    # 2. Purga de datos históricos
    purge_directory(REPO_ROOT / "biblioteca")
    purge_directory(REPO_ROOT / "laboratorio", exclude=["bitacora-merci-boilerplate.md"])
    purge_directory(REPO_ROOT / "blog")
    purge_directory(REPO_ROOT / "art-de-cote")
    purge_directory(REPO_ROOT / "public" / "biblioteca")
    purge_directory(REPO_ROOT / "public" / "descargas")
    purge_directory(REPO_ROOT / "public" / "art-de-cote")
    
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
    purge_directory(REPO_ROOT / "assets" / "images", exclude=["favicon.ico", "favicon.svg", "favicon.png", "logo.svg", "logo.webp", "logo.png", "merci-avatar.webp", "merci-avatar.png"])
    
    # Purga selectiva de manuales operativos exclusivos de la matriz
    print("  🗑️  Purgando manuales SOP exclusivos del proyecto matriz...")
    docs_matriz = REPO_ROOT / "docs" / "matriz"
    if docs_matriz.exists():
        import shutil
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