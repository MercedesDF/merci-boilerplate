#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-styles.py — Compilador SASS Standalone.
Descarga Dart Sass si no existe y compila src/scss/main.scss a public/css/main.css.
"""

import os
import sys
import urllib.request
import tarfile
import subprocess
from pathlib import Path

# 1. CONFIGURACIÓN DE RUTAS DINÁMICAS
# Resolutor dinámico de rutas absolutas. Permite que el script funcione
# correctamente independientemente de la carpeta desde donde se invoque.
REPO_ROOT = Path(__file__).resolve().parents[2]
_args = [arg for arg in sys.argv[1:] if arg not in ("-v", "--verbose")]
TARGET_DIR = Path(_args[0]).resolve() if _args else Path(os.getcwd()).resolve()
IS_EXTERNAL = TARGET_DIR != REPO_ROOT

BIN_DIR = REPO_ROOT / "scripts" / "merci" / "bin"
SASS_DIR = BIN_DIR / "dart-sass"
SASS_BIN = SASS_DIR / "sass"

# Motor de deducción de contexto para compilación:
if not IS_EXTERNAL:
    SCSS_INPUT = REPO_ROOT / "src" / "scss" / "main.scss"
    CSS_OUTPUT = REPO_ROOT / "public" / "css" / "main.css"
else:
    # Modo Externo: Buscar un archivo de entrada válido (main.scss o style.scss)
    entradas = list(TARGET_DIR.rglob("main.scss")) + list(TARGET_DIR.rglob("style.scss"))
    # Filtramos archivos que estén dentro de carpetas ocultas o dependencias
    entradas = [f for f in entradas if not any(p.startswith(".") or p == "node_modules" for p in f.parts)]
    
    if entradas:
        SCSS_INPUT = entradas[0]
        # Salida In-Place: Mismo nombre, extensión .css al lado del original
        CSS_OUTPUT = SCSS_INPUT.with_suffix(".css")
    else:
        print(f"❌ [Merci Styles] No se encontró 'main.scss' ni 'style.scss' en {TARGET_DIR.name}")
        sys.exit(1)

# URL oficial de Dart Sass para Linux x64
SASS_URL = "https://github.com/sass/dart-sass/releases/download/1.72.0/dart-sass-1.72.0-linux-x64.tar.gz"

def install_sass():
    # Si el binario ya existe, saltamos la instalación para agilizar la compilación.
    if SASS_BIN.exists():
        return
        
    print("📥 [Merci Styles] Descargando compilador Dart Sass (0 dependencias NPM)...")
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    tar_path = BIN_DIR / "dart-sass.tar.gz"
    
    try:
        # Descarga e instalación autónoma. Mantiene la máquina anfitriona limpia
        # al no requerir ecosistemas pesados como Node.js o NPM (Regla de 0 dependencias).
        urllib.request.urlretrieve(SASS_URL, tar_path)
        print("📦 [Merci Styles] Extrayendo binarios locales...")
        with tarfile.open(tar_path) as tar:
            tar.extractall(path=BIN_DIR)
        tar_path.unlink()
        # Otorgamos permisos de ejecución (chmod +x) al binario extraído para poder invocarlo.
        SASS_BIN.chmod(0o755)
    except Exception as e:
        print(f"❌ Error al instalar Dart Sass: {e}", file=sys.stderr)
        sys.exit(1)

def compile_sass():
    try:
        rel_in = SCSS_INPUT.relative_to(TARGET_DIR)
        rel_out = CSS_OUTPUT.relative_to(TARGET_DIR)
    except ValueError:
        rel_in, rel_out = SCSS_INPUT.name, CSS_OUTPUT.name
        
    print(f"⚙️  [Merci Styles] Compilando hojas de estilo{' (Modo Externo)' if IS_EXTERNAL else ''}...")
    print(f"   Entrada: {rel_in}")
    # Aseguramos que la estructura de carpetas de destino (public/css) exista antes de escribir.
    CSS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Ejecutamos SASS forzando compresión máxima y desactivando mapas de origen para optimizar el peso final (Core Web Vitals).
    cmd = [str(SASS_BIN), str(SCSS_INPUT), str(CSS_OUTPUT), "--style=compressed", "--no-source-map"]
    subprocess.run(cmd, check=True)
    print(f"✅ [Merci Styles] CSS compilado exitosamente en {rel_out}")

if __name__ == "__main__":
    install_sass()
    compile_sass()