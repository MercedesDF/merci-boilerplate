#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-optimizer.py — Automatización de optimización de imágenes (Fase 3.4).

Escanea `.assets-raw/` en busca de imágenes originales (PNG, JPG) y genera
versiones WebP responsivas y optimizadas en `assets/`.
"""

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ℹ️ [Merci Info] La librería Pillow no está instalada (pip install Pillow). Omitiendo optimización de imágenes.")
    sys.exit(0)

# --- Configuración ---
REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO_ROOT / ".assets-raw"
DEST_DIR = REPO_ROOT / "assets/images"

# Tamaños objetivo en píxeles de ancho. El alto se calculará manteniendo la proporción.
TARGET_WIDTHS = [1920, 1280, 800, 400]
WEBP_QUALITY = 80  # Calidad del 0 al 100. 80 es un buen equilibrio.

def optimize_images(verbose=False):
    """
    Busca imágenes en el directorio fuente, las convierte a WebP en varios
    tamaños y las guarda en el directorio de destino.
    """
    print(f"🔎 Escaneando {SOURCE_DIR} en busca de imágenes...")
    
    # Asegurarse de que el directorio de destino exista
    DEST_DIR.mkdir(exist_ok=True)

    image_files = list(SOURCE_DIR.glob("*.png")) + \
                  list(SOURCE_DIR.glob("*.jpg")) + \
                  list(SOURCE_DIR.glob("*.jpeg"))

    if not image_files:
        print("✅ No se encontraron nuevas imágenes para optimizar.")
        return

    for image_path in image_files:
        # Caché Incremental: Evita reprocesar si la imagen WebP base ya existe y es más reciente
        base_output = DEST_DIR / f"{image_path.stem}.webp"
        if base_output.exists() and int(base_output.stat().st_mtime) >= int(image_path.stat().st_mtime):
            if verbose:
                print(f"   ⏭️ Saltando (Caché): {image_path.name}")
            continue

        try:
            with Image.open(image_path) as img:
                if verbose:
                    print(f"⚙️  Procesando: {image_path.name}")
                
                # Preservar transparencia (canal Alpha) al convertir a WebP
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Siempre generar una versión base optimizada al tamaño original
                img.save(base_output, "WEBP", quality=WEBP_QUALITY)
                if verbose:
                    print(f"   ✨ Generado base: {base_output.name}")

                for width in TARGET_WIDTHS:
                    # Solo generar tamaños más pequeños que el original
                    if width >= img.width:
                        continue

                    # Calcular el nuevo alto manteniendo la proporción
                    aspect_ratio = img.height / img.width
                    new_height = int(width * aspect_ratio)
                    
                    resized_img = img.resize((width, new_height), Image.Resampling.LANCZOS)
                    
                    # Construir el nombre del archivo de salida
                    output_filename = f"{image_path.stem}-{width}w.webp"
                    output_path = DEST_DIR / output_filename
                    
                    resized_img.save(output_path, "WEBP", quality=WEBP_QUALITY)
                    if verbose:
                        print(f"   ✨ Generado: {output_path.name}")
                        
                if not verbose:
                    print(f"  ✅ Optimizada: {image_path.name}")

        except Exception as e:
            print(f"❌ Error procesando {image_path.name}: {e}", file=sys.stderr)

if __name__ == "__main__":
    is_verbose = "--verbose" in sys.argv or "-v" in sys.argv
    optimize_images(is_verbose)
    print("\n[Merci Optimizer] Proceso completado.")