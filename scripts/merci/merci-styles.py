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
BIN_DIR = REPO_ROOT / "scripts" / "merci" / "bin"
SASS_DIR = BIN_DIR / "dart-sass"
SASS_BIN = SASS_DIR / "sass"

SCSS_INPUT = REPO_ROOT / "src" / "scss" / "main.scss"
CSS_OUTPUT = REPO_ROOT / "public" / "css" / "main.css"

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
    print("⚙️  [Merci Styles] Compilando hojas de estilo...")
    # Aseguramos que la estructura de carpetas de destino (public/css) exista antes de escribir.
    CSS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Ejecutamos SASS forzando compresión máxima y desactivando mapas de origen para optimizar el peso final (Core Web Vitals).
    cmd = [str(SASS_BIN), str(SCSS_INPUT), str(CSS_OUTPUT), "--style=compressed", "--no-source-map"]
    subprocess.run(cmd, check=True)
    print("✅ [Merci Styles] CSS compilado exitosamente en public/css/main.css")

if __name__ == "__main__":
    install_sass()
    compile_sass()