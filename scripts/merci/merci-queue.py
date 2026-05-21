#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-queue.py — Visor rápido de la cola social por terminal.

Escanea las carpetas de producción y muestra una lista formateada
con los artículos pendientes de revisar y los listos para emisión.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def main():
    print("📊 [Merci Queue] Escaneando la cola de publicación social...\n")
    
    directorios = [
        REPO_ROOT / "blog",
        REPO_ROOT / "biblioteca",
        REPO_ROOT / "art-de-cote"
    ]
    
    en_cola = []
    aprobados = []
    
    for dir_path in directorios:
        if not dir_path.exists():
            continue
            
        for archivo in dir_path.rglob("*.md"):
            content = archivo.read_text(encoding="utf-8", errors="ignore")
            # Extraemos el bloque YAML Frontmatter
            match = re.search(r"^\s*---\r?\n(.*?)\r?\n---", content, re.DOTALL)
            if not match:
                continue
                
            yaml_block = match.group(1)
            
            estado = re.search(r'^estado:\s*["\']?([^"\'\n]+)["\']?', yaml_block, re.MULTILINE)
            estado_social = re.search(r'^estado_social:\s*["\']?([^"\'\n]+)["\']?', yaml_block, re.MULTILINE)
            titulo = re.search(r'^titulo:\s*["\']?([^"\'\n]+)["\']?', yaml_block, re.MULTILINE)
            
            if estado and estado.group(1).lower() == "publicado" and estado_social:
                val_estado_social = estado_social.group(1).lower()
                val_titulo = titulo.group(1) if titulo else archivo.name
                
                if val_estado_social == "en_cola":
                    en_cola.append((val_titulo, archivo.relative_to(REPO_ROOT)))
                elif val_estado_social == "aprobado":
                    aprobados.append((val_titulo, archivo.relative_to(REPO_ROOT)))

    print("📋 PENDIENTES DE REVISIÓN (Falta tu aprobación manual)")
    print("-" * 60)
    if not en_cola:
        print("  Ningún artículo pendiente de revisión.")
    else:
        for titulo, ruta in en_cola:
            print(f"  🟡 {titulo}\n     └─ {ruta}")
            
    print("\n🚀 EN EL BUFFER SOCIAL (Listos para que el Cron los publique)")
    print("-" * 60)
    if not aprobados:
        print("  Ningún artículo en el buffer de emisión.")
    else:
        for titulo, ruta in aprobados:
            print(f"  🟢 {titulo}\n     └─ {ruta}")

    print(f"\n📈 Resumen: {len(en_cola)} por revisar | {len(aprobados)} en el buffer.\n")

if __name__ == "__main__":
    main()