#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-recorder.py — Utilidad de captura de pantalla para el Laboratorio.

Este script automatiza la grabación de la sesión de desarrollo durante 
un tiempo determinado (30 minutos por defecto).
"""

import subprocess
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Configuración de rutas
REPO_ROOT = Path(__file__).resolve().parents
OUTPUT_DIR = REPO_ROOT / "laboratorio" / "evidencias"
DURATION_SECS = 1800  # 30 minutos

def record_session(duration: int):
    """Ejecuta la captura de pantalla usando FFmpeg."""
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{timestamp}_evidencia-sesion.mp4"
    target_path = OUTPUT_DIR / filename

    print(f"[Merci Recorder] Iniciando captura de {duration // 60} min y {duration % 60} seg...")
    print(f"[Merci Recorder] Destino: {target_path}")

    # Comando FFmpeg para Linux (Ubuntu/X11)
    # -f x11grab: Captura del servidor gráfico X11
    # -s 1920x1080: Resolución (ajustar según monitor si es necesario)
    # -i :0.0: Pantalla principal
    # -t: Duración en segundos
    # -c:v libx264: Códec de vídeo H.264
    # -preset ultrafast: Menor carga de CPU (Central Processing Unit)
    # -crf 28: Calidad constante balanceada (18-28 es lo ideal)
    
    command = [
        "ffmpeg",
        "-f", "x11grab",
        "-video_size", "1920x1080",
        "-i", ":0.0",
        "-nostdin", # Evita que FFmpeg intente leer de la entrada estándar
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        str(target_path)
    ]

    try:
        subprocess.run(command, check=True)
        print(f"\n[Merci Recorder] Captura finalizada con éxito.")
    except FileNotFoundError:
        print("Error: FFmpeg no está instalado en el sistema.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error durante la grabación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grabador de sesiones Merci.")
    parser.add_argument(
        "--duration", 
        type=int, 
        default=DURATION_SECS, 
        help="Duración de la grabación en segundos (por defecto: 1800)."
    )
    args = parser.parse_args()
    
    record_session(args.duration)