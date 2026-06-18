#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-commit.py — Automatización de commits impulsados por la bitácora.

Extrae la última entrada cronológica de la bitácora y la utiliza 
para redactar y ejecutar un commit atómico estructurado.
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Rutas base y enrutamiento dinámico
REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_DIR = Path(os.getcwd()).resolve()
IS_EXTERNAL = TARGET_DIR != REPO_ROOT

def obtener_bitacoras_activas() -> list[Path]:
    """
    QUÉ HACE: Busca y devuelve todas las bitácoras de épicas en el laboratorio.
    POR QUÉ: Permite autodescubrir bitácoras dinámicamente sin mantenimiento manual de rutas.
    """
    return list((REPO_ROOT / "laboratorio").glob("bitacora-tuempresa-epic-*.md"))

def check_repo_changes(target_dir: Path) -> bool:
    """
    QUÉ HACE: Comprueba si existen cambios pendientes de confirmar en el repositorio Git.
    POR QUÉ: Evita intentar crear commits vacíos o innecesarios, capturando de forma segura fallos de entorno.
    """
    try:
        result = subprocess.run(["git", "status", "--porcelain"], cwd=target_dir, capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False

def obtener_bitacora_activa() -> Path | None:
    """
    QUÉ HACE: Encuentra y devuelve el archivo de bitácora modificado más recientemente.
    POR QUÉ: Determina de forma autónoma cuál es el frente de trabajo activo y de dónde extraer metadatos.
    """
    activas = [b for b in obtener_bitacoras_activas() if b.exists()]
    if not activas:
        return None
    # Compara la fecha de modificación (st_mtime) y devuelve la más reciente
    return max(activas, key=lambda p: p.stat().st_mtime)

def check_bitacora_updated(bitacora_path: Path) -> bool:
    """
    QUÉ HACE: Comprueba si la bitácora activa tiene cambios pendientes de registrar en Git.
    POR QUÉ: Valida que la ingeniera haya justificado técnicamente el trabajo antes del commit.
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

def parse_latest_entry(content: str) -> tuple[str, str, str]:
    """
    QUÉ HACE: Extrae el título, contexto y hechos de la última entrada de la bitácora.
    POR QUÉ: Automatiza la estructuración del mensaje de commit basándose en la documentación de laboratorio.
    """
    try:
        # Dividimos el texto para quedarnos solo con lo que hay debajo del registro
        _, registro = content.split("## Registro cronológico", 1)
    except ValueError:
        print("[Merci Error] No se encontró la cabecera '## Registro cronológico'.")
        sys.exit(1)

    # RegEx (Regular Expressions - Expresiones Regulares) para capturar el primer bloque:
    # Busca "### YYYY-MM-DD — Título" y captura todo hasta el siguiente "###" o el final.
    # Se hace tolerante a guion corto (-), medio (–) y largo (—) para robustez.
    pattern = r"###\s+(\d{4}-\d{2}-\d{2}(?:\s\d{2}:\d{2})?)\s+[-—–]\s+([^\n]+)\n(.*?)(?=###\s+\d{4}-\d{2}-\d{2}(?:\s\d{2}:\d{2})?|$)"
    match = re.search(pattern, registro, re.DOTALL)

    if not match:
        print("[Merci Error] No se detectaron entradas válidas en el registro.")
        sys.exit(1)

    date, title, body = match.groups()
    
    # RegEx adicionales para extraer bloques específicos dentro del cuerpo
    # Hacemos la búsqueda tolerante a los "átomos" opcionales como (Desafío) o (Maniobra)
    context_match = re.search(r"\*\*Contexto(?:[^\*]*):\*\*\s*(.*?)(?=\*\*Hecho(?:[^\*]*):\*\*|\*\*Detalle(?:[^\*]*):\*\*|\*\*Motivo(?:[^\*]*):\*\*|$)", body, re.DOTALL)
    hecho_match = re.search(r"\*\*Hecho(?:[^\*]*):\*\*\s*(.*?)(?=\*\*Detalle(?:[^\*]*):\*\*|\*\*Motivo(?:[^\*]*):\*\*|\*\*Siguiente(?:[^\*]*):\*\*|$)", body, re.DOTALL)

    context = context_match.group(1).strip() if context_match else "Sin contexto explícito."
    hecho = hecho_match.group(1).strip() if hecho_match else "Sin hechos documentados."

    return title.strip(), context, hecho

def main() -> None:
    """
    QUÉ HACE: Orquesta el proceso de commit atómico automatizado guiado por la bitácora.
    POR QUÉ: Estructura los mensajes de Git conforme al estándar de documentación y bloquea si hay inconsistencias.
    """
    print("Merci revisa el estado técnico...")
    
    # 0. ¿Hay algo que comitear realmente?
    if not check_repo_changes(TARGET_DIR):
        print("\n[Merci Info] El repositorio está limpio. No hay archivos modificados para comitear.")
        sys.exit(0)

    # MODO EXTERNO: Si estamos en la carpeta de un cliente, omitimos la bitácora matriz
    if IS_EXTERNAL:
        print(f"\n🌍 [Modo Externo] Operando en repositorio ajeno a la matriz: {TARGET_DIR.name}")
        commit_subject = input("\nIntroduce el título corto del commit (ej. fix: parche en cliente): ").strip()
        if not commit_subject:
            print("[Merci Error] Título vacío. Cancelando operación.")
            sys.exit(1)
            
        commit_body = input("Introduce una descripción detallada (opcional, presiona Enter para omitir): ").strip()
        
    # MODO MATRIZ: Leemos la bitácora de la épica
    else:
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
                # QUÉ HACE: Emite un código de salida 1 en lugar de 0 al cancelar.
                # POR QUÉ: Activa el patrón Fail-Fast del orquestador supremo (merci-completo), 
                # bloqueando el despliegue a producción de código no comiteado.
                print("\n[Merci Error] Operación cancelada por el usuario. El pipeline se detendrá aquí.")
                sys.exit(1)
                
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
        subprocess.run(["git", "add", "."], cwd=TARGET_DIR, check=True)

        # 3. Ejecutar el commit con dos banderas -m (sujeto y cuerpo)
        print(f"[Merci Commit] Ejecutando: '{commit_subject}'")
        if commit_body:
            subprocess.run(["git", "commit", "-m", commit_subject, "-m", commit_body], cwd=TARGET_DIR, check=True)
        else:
            subprocess.run(["git", "commit", "-m", commit_subject], cwd=TARGET_DIR, check=True)
        
        print("\n[Merci Éxito] Commit atómico finalizado correctamente.")
        
    except subprocess.CalledProcessError as e:
        # Shift-Left: Captura de errores si Git falla (ej. si pre-commit lo bloquea)
        print(f"\n[Merci Error] La ejecución de Git ha fallado: {e}")
        sys.exit(1)
    except Exception as e:
        # Control genérico de excepciones
        print(f"\n[Merci Error] Error inesperado en el proceso de commit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Commit] Operación cancelada por la usuaria. Saliendo limpiamente.")
        sys.exit(130)