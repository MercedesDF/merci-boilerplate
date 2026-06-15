#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-watcher.py — Vigilante de archivos SASS para compilación automática.

Este script monitoriza el directorio `src/scss/` en busca de cambios y
ejecuta automáticamente `merci-styles.py` cuando detecta una modificación.
"""

import subprocess
import sys
import time
from pathlib import Path

# --- Configuración ---
REPO_ROOT = Path(__file__).resolve().parents[2]
SCSS_DIR = REPO_ROOT / "src" / "scss"
STYLES_SCRIPT = REPO_ROOT / "scripts" / "merci" / "merci-styles.py"


def get_scss_state() -> dict[Path, float]:
    """
    QUÉ HACE: Crea un diccionario con la ruta de cada archivo .scss y su última fecha de modificación física.
    POR QUÉ: Permite determinar si ha habido cambios en el árbol de estilos de SASS comparando estados de tiempo.
    """
    return {
        path: path.stat().st_mtime
        for path in SCSS_DIR.rglob("*.scss")
    }


def main() -> None:
    """
    QUÉ HACE: Ejecuta un bucle continuo de sondeo (polling) para detectar modificaciones de SCSS y recompilar estilos automáticamente.
    POR QUÉ: Automatiza la compilación SASS local al editar estilos, mejorando la experiencia de desarrollo (DX).
    """
    print("🚀 [Merci Watcher] Iniciando vigilancia de archivos SASS...")
    print(f"    Directorio vigilado: {SCSS_DIR.relative_to(REPO_ROOT)}")
    print("    Pulsa Ctrl+C para detener.")
    
    last_state = get_scss_state()
    while True:
        time.sleep(1)  # Pausa para no consumir CPU innecesariamente
        current_state = get_scss_state()

        if current_state != last_state:
            print("\n🔄 [Merci Watcher] Cambios detectados. Recompilando estilos...")
            
            # Llamamos a nuestro script compilador
            subprocess.run([sys.executable, str(STYLES_SCRIPT)], check=True)
            
            print("✅ [Merci Watcher] Estilos compilados. Reanudando vigilancia...")
            last_state = current_state


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Watcher] Vigilancia detenida por el usuario.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ [Merci Watcher] Error inesperado: {e}", file=sys.stderr)
        sys.exit(1)