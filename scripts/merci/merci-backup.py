#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-backup.py — Herramienta de copias de seguridad locales.
Empaqueta el proyecto en un archivo ZIP excluyendo carpetas pesadas o de entorno.
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKUP_DIR = REPO_ROOT / "backups"

# QUÉ HACE: Define un conjunto (set) de carpetas que serán ignoradas durante la compresión.
# POR QUÉ: Evita respaldar dependencias recreables (.venv), control de versiones (.git) 
# o archivos crudos pesados (.assets-raw, evidencias) y artefactos compilados (descargas).
EXCLUDE_DIRS = {'.git', '.venv', '__pycache__', 'backups', '.assets-raw', 'evidencias', 'descargas'}

def create_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"merci_backup_{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_filename
    
    print(f"📦 [Merci Backup] Iniciando copia de seguridad local...")
    print(f"  Destino: {backup_path.relative_to(REPO_ROOT)}")
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(REPO_ROOT):
            # Modificamos la lista 'dirs' in-place para que os.walk ignore las carpetas excluidas
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                zipf.write(file_path, file_path.relative_to(REPO_ROOT))
                
    print(f"  ✅ Backup completado con éxito. Tamaño: {backup_path.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    create_backup()