#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-backup.py — Herramienta de copias de seguridad locales.

Empaqueta el proyecto en un archivo ZIP excluyendo carpetas pesadas o de entorno.
"""

import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKUP_DIR = REPO_ROOT / "backups"

# Define un conjunto de rutas absolutas que serán ignoradas.
# Usar rutas exactas evita que se respalde la instalación pesada de WordPress (public/blog)
# sin excluir por error nuestros archivos Markdown en el laboratorio o en la raíz.
EXCLUDE_PATHS = {
    REPO_ROOT / ".git",
    REPO_ROOT / ".venv",
    REPO_ROOT / "backups",
    REPO_ROOT / ".assets-raw",
    REPO_ROOT / "laboratorio" / "evidencias",
    REPO_ROOT / "auditorias-pagespeed.web.dev",
    REPO_ROOT / "public" / "descargas",
    REPO_ROOT / "public" / "blog",
    REPO_ROOT / "public" / "tienda",
    REPO_ROOT / ".privado",
    REPO_ROOT / "scripts" / "merci" / "bin"
}


def create_backup(verbose: bool = False) -> None:
    """
    QUÉ HACE: Crea una copia de seguridad en formato ZIP de los archivos del repositorio, excluyendo directorios pesados e innecesarios.
    POR QUÉ: Resguarda el estado del código fuente y documentación local en backups rápidos sin contaminar la instalación ni versionar dependencias externas.
    """
    BACKUP_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"merci_backup_{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_filename
    
    print("📦 [Merci Backup] Iniciando copia de seguridad local...")
    print(f"  Destino: {backup_path.relative_to(REPO_ROOT)}")
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(REPO_ROOT):
            # Modificamos la lista 'dirs' in-place comprobando la ruta absoluta
            # Ignoramos también cualquier subcarpeta __pycache__ genérica
            dirs[:] = [d for d in dirs if (Path(root) / d) not in EXCLUDE_PATHS and d != "__pycache__"]
            
            for file in files:
                file_path = Path(root) / file
                zipf.write(file_path, file_path.relative_to(REPO_ROOT))
                
                # Imprime la ruta relativa del archivo si el modo detallado está activo.
                if verbose:
                    print(f"    ➕ Añadiendo: {file_path.relative_to(REPO_ROOT)}")
                
    print(f"  ✅ Backup completado con éxito. Tamaño: {backup_path.stat().st_size / (1024*1024):.2f} MB")


if __name__ == "__main__":
    try:
        # Comprobamos si el usuario solicitó el modo detallado
        is_verbose = "--verbose" in sys.argv or "-v" in sys.argv
        create_backup(verbose=is_verbose)
    except KeyboardInterrupt:
        print("\n🛑 [Merci Backup] Proceso interrumpido por el usuario.")
        sys.exit(130)