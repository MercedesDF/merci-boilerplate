#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-hardening.py — Agente de Hardening Continuo (Fase 4).

Objetivo: Traduce las políticas de 'docs/checklist-hardening.md' a comprobaciones
ejecutables. Audita la postura de seguridad de la infraestructura y el repositorio.
"""

import os
import sys
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_PATH = REPO_ROOT / "docs" / "checklist-hardening.md"

def check_env_permissions():
    """Verifica que el archivo de variables de entorno tenga permisos seguros (600)."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists() or os.name == 'nt':
        return True
        
    st_mode = os.stat(env_file).st_mode
    permisos_octales = oct(st_mode)[-3:]
    
    if permisos_octales != "600":
        print(f"  ❌ [Hardening] Vulnerabilidad: El archivo .env tiene permisos '{permisos_octales}'.")
        print(f"     💡 Corrección: Ejecuta 'chmod 600 .env' para evitar exposición de credenciales.")
        return False
    return True

def check_dlp_gitignore():
    """Verifica que el .gitignore contenga las reglas de prevención de fugas de datos."""
    gitignore = REPO_ROOT / ".gitignore"
    if not gitignore.exists():
        print("  ❌ [Hardening] Vulnerabilidad: No se encontró el archivo .gitignore.")
        return False
        
    content = gitignore.read_text(encoding="utf-8")
    reglas_criticas = [".env", ".privado/", "docs/matriz/", ".linkedin_token.json"]
    
    seguro = True
    for regla in reglas_criticas:
        if regla not in content:
            print(f"  ❌ [Hardening] Fuga de Datos: Falta la regla DLP '{regla}' en el .gitignore.")
            seguro = False
    return seguro

def check_mixed_content():
    """Busca enlaces HTTP (no seguros) en los HTML generados, excluyendo dominios de desarrollo y esquemas."""
    public_dir = REPO_ROOT / "public"
    if not public_dir.exists():
        return True
        
    seguro = True
    for html_file in public_dir.rglob("*.html"):
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        # Busca 'http://' pero perdona dominios locales y esquemas XML/W3C
        matches = re.findall(r'href="http://(?!localhost|www\.w3\.org|schema\.org)[^"]+"', content)
        if matches:
            print(f"  ❌ [Hardening] Mixed Content en {html_file.relative_to(REPO_ROOT)}: {matches[0]}")
            seguro = False
    return seguro

def check_rogue_configs():
    """Asegura que no haya archivos de configuración de producción colados en el repo."""
    rogue_files = ["wp-config.php", "docker-compose.override.yml"]
    seguro = True
    for rf in rogue_files:
        if (REPO_ROOT / rf).exists():
            print(f"  ❌ [Hardening] Exposición Crítica: Archivo '{rf}' detectado en el código fuente.")
            seguro = False
    return seguro

def main():
    print("\n🛡️  [Merci Hardening] Auditando infraestructura y políticas de seguridad...")
    
    if not CHECKLIST_PATH.exists():
        print("  ⚠️ [Merci Warn] No se encontró el checklist de hardening base.")
        
    passed = True
    if not check_env_permissions(): passed = False
    if not check_dlp_gitignore(): passed = False
    if not check_mixed_content(): passed = False
    if not check_rogue_configs(): passed = False
    
    if passed:
        print("  ✅ [Éxito] Ecosistema blindado. Políticas de Hardening cumplidas al 100%.")
        sys.exit(0)
    else:
        print("  🛑 [Merci Error] La auditoría de seguridad ha fallado. Revisa las vulnerabilidades detectadas.")
        sys.exit(1)

if __name__ == "__main__":
    main()