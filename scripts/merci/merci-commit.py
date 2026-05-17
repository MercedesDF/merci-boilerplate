#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-commit.py — Automatización de commits impulsados por la bitácora.

Extrae la última entrada cronológica de la bitácora y la utiliza 
para redactar y ejecutar un commit atómico estructurado.
"""

import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Definición de rutas absolutas basadas en la ubicación del script
REPO_ROOT = Path(__file__).resolve().parents[2]

# QUÉ HACE: Autodescubre dinámicamente cualquier bitácora de épica.
# POR QUÉ: Zero Maintenance. Permite crear nuevas épicas sin modificar el código en Python.
def obtener_bitacoras_activas():
    """Busca dinámicamente todas las bitácoras de épicas en el laboratorio."""
    return list((REPO_ROOT / "laboratorio").glob("bitacora-merci-boilerplate-epic-*.md"))

def check_repo_changes():
    """Verifica si hay algún cambio en el repositorio (staged, unstaged o untracked)."""
    result = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True)
    return len(result.stdout.strip()) > 0

def obtener_bitacora_activa():
    """Devuelve la bitácora que ha sido modificada físicamente más recientemente."""
    activas = [b for b in obtener_bitacoras_activas() if b.exists()]
    if not activas:
        return None
    # Compara la fecha de modificación (st_mtime) y devuelve la más reciente
    return max(activas, key=lambda p: p.stat().st_mtime)

def check_bitacora_updated(bitacora_path):
    """
    Verifica si la bitácora ha sido modificada desde el último commit.
    Devuelve True si hay cambios, False si no.
    """
    # `git diff --quiet` devuelve 0 si no hay cambios, 1 si los hay.
    # Usamos `HEAD` para comparar contra el último commit.
    try:
        # Usamos 'git status --porcelain' que es más robusto para scripting.
        # Devuelve una línea si el archivo está modificado, es nuevo, etc.
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", str(bitacora_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip()) > 0
    except FileNotFoundError:
        # Git no está instalado, el script principal ya lo gestionará.
        return True
    except Exception:
        # En caso de un repo vacío sin commits (sin HEAD), git diff falla.
        # En ese caso, asumimos que hay cambios (es el primer commit).
        return True

def parse_latest_entry(content: str):
    """Analiza el texto de la bitácora y extrae los datos de la última entrada."""
    try:
        # Dividimos el texto para quedarnos solo con lo que hay debajo del registro
        _, registro = content.split("## Registro cronológico", 1)
    except ValueError:
        print("[Merci Error] No se encontró la cabecera '## Registro cronológico'.")
        sys.exit(1)

    # RegEx (Regular Expressions - Expresiones Regulares) para capturar el primer bloque:
    # Busca "### YYYY-MM-DD — Título" y captura todo hasta el siguiente "###" o el final.
    pattern = r"###\s+(\d{4}-\d{2}-\d{2})\s+—\s+([^\n]+)\n(.*?)(?=###\s+\d{4}-\d{2}-\d{2}|$)"
    match = re.search(pattern, registro, re.DOTALL)

    if not match:
        print("[Merci Error] No se detectaron entradas válidas en el registro.")
        sys.exit(1)

    date, title, body = match.groups()
    
    # RegEx adicionales para extraer bloques específicos dentro del cuerpo
    context_match = re.search(r"\*\*Contexto:\*\*\s*(.*?)(?=\*\*Hecho:\*\*|\*\*Detalle)", body, re.DOTALL)
    hecho_match = re.search(r"\*\*Hecho:\*\*\s*(.*?)(?=\*\*Detalle|\*\*Motivo)", body, re.DOTALL)

    context = context_match.group(1).strip() if context_match else "Sin contexto explícito."
    hecho = hecho_match.group(1).strip() if hecho_match else "Sin hechos documentados."

    return title.strip(), context, hecho

def main():
    print("Merci revisa el estado técnico...")
    
    # 0. ¿Hay algo que comitear realmente?
    if not check_repo_changes():
        print("\n[Merci Info] El repositorio está limpio. No hay archivos modificados para comitear.")
        sys.exit(0)

    bitacora_path = obtener_bitacora_activa()
    if not bitacora_path:
        print("[Merci Error] No se ha encontrado ninguna bitácora activa en el laboratorio.")
        sys.exit(1)

    # 1. Verificación de seguridad: ¿Se ha actualizado la bitácora?
    if not check_bitacora_updated(bitacora_path):
        # Usamos códigos de color ANSI para la alerta. \033[93m es amarillo. \033[0m lo resetea.
        print("\n\033[93m[Merci Alerta] La bitácora no ha sido actualizada desde el último commit.\033[0m")
        print("Se han detectado archivos modificados, pero falta la justificación técnica.")
        respuesta = input("¿Deseas registrar esto como un parche menor/manual sin bitácora? (s/N): ")
        if respuesta.lower().strip() != 's':
            print("\n[Merci Info] Operación cancelada. Por favor, actualiza la bitácora antes de continuar.")
            sys.exit(0)
            
        custom_subject = input("\nIntroduce el título corto del commit (ej. chore: limpieza de archivos): ").strip()
        if not custom_subject:
            print("[Merci Error] Título vacío. Cancelando operación.")
            sys.exit(1)
            
        commit_subject = custom_subject
        commit_body = "Mantenimiento o parche menor sin entrada en bitácora."
    else:
        content = bitacora_path.read_text(encoding="utf-8")
        title, context, hecho = parse_latest_entry(content)

        # QUÉ HACE: Actualiza automáticamente la fecha de revisión al final del documento.
        # POR QUÉ: Elimina la carga cognitiva de mantener este dato manualmente en cada sesión.
        today = datetime.now().strftime("%Y-%m-%d")
        updated_content = re.sub(r"\*Última revisión de la bitácora:.*?\*", f"*Última revisión de la bitácora: {today}.*", content)
        if updated_content != content:
            bitacora_path.write_text(updated_content, encoding="utf-8")

        # Formateo del mensaje para Git
        commit_subject = title
        commit_body = f"Contexto:\n{context}\n\nHecho:\n{hecho}"

    try:
        # 2. Añadir todos los archivos modificados/nuevos al stage (incluyendo la bitácora)
        print("[Merci Git] Añadiendo archivos al stage (git add .)...")
        subprocess.run(["git", "add", "."], cwd=REPO_ROOT, check=True)

        # 3. Ejecutar el commit con dos banderas -m (sujeto y cuerpo)
        print(f"[Merci Commit] Ejecutando: '{commit_subject}'")
        subprocess.run(["git", "commit", "-m", commit_subject, "-m", commit_body], check=True)
        
        print("\n[Merci Éxito] Commit atómico finalizado correctamente.")
        
    except subprocess.CalledProcessError as e:
        # Shift-Left: Captura de errores si Git falla (ej. si pre-commit lo bloquea)
        print(f"\n[Merci Error] La ejecución de Git ha fallado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()