#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-assets-watcher.py — Agente local de WebP Automation (Fase 2).

Observa en segundo plano la carpeta `.assets-raw/`. Si detecta nuevas
imágenes o modificaciones, dispara automáticamente el orquestador 
`merci-optimizer.py`.
"""

import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_RAW_DIR = REPO_ROOT / ".assets-raw"
OPTIMIZER_SCRIPT = REPO_ROOT / "scripts" / "merci" / "merci-optimizer.py"


def get_assets_state() -> dict[Path, float]:
    """
    QUÉ HACE: Crea un diccionario con la ruta de cada imagen/vídeo en .assets-raw y su última fecha de modificación.
    POR QUÉ: Permite detectar de forma reactiva si se agregan nuevos archivos multimedia o se actualizan los existentes.
    """
    if not ASSETS_RAW_DIR.exists():
        return {}
    
    valid_extensions = {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff",  # Formatos de imagen
        ".mp4", ".mov", ".avi", ".webm"                     # Formatos de vídeo
    }
    return {
        path: path.stat().st_mtime
        for path in ASSETS_RAW_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in valid_extensions
    }


def main() -> None:
    """
    QUÉ HACE: Ejecuta un bucle continuo de sondeo (polling) observando la carpeta .assets-raw y disparando el optimizador ante cualquier cambio.
    POR QUÉ: Automatiza la conversión desatendida a formatos óptimos (como WebP), cumpliendo la política de rendimiento Mobile-First.
    """
    print("🤖 [Merci Brain] Iniciando Agente Vigilante de Assets (WebP Automation)...")
    print(f"    👀 Observando: {ASSETS_RAW_DIR.relative_to(REPO_ROOT)}")
    print("    (Pulsa Ctrl+C para detener)")
    
    last_state = get_assets_state()
    while True:
        time.sleep(2)  # Intervalo de sondeo (2s previene errores con archivos a medio copiar)
        current_state = get_assets_state()

        if current_state != last_state:
            print("\n📸 [Merci Brain] Movimiento detectado en .assets-raw/. Despertando optimizador...")
            subprocess.run([sys.executable, str(OPTIMIZER_SCRIPT)])
            last_state = current_state


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Brain] Vigilancia de assets detenida.")
        sys.exit(130)