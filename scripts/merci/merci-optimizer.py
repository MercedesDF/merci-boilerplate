#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-optimizer.py — Automatización de optimización de activos (Fase 3.4 / Épica 7).

Escanea `.assets-raw/` en busca de imágenes originales (PNG, JPG) y vídeos (MP4, MOV)
y genera versiones optimizadas (WebP para imágenes, WebM/MP4 para vídeos) en `assets/`.
"""

import sys
import os
import subprocess
from pathlib import Path

# Intentar cargar la biblioteca Pillow para imágenes de forma condicional (evita fallos si no se usa)
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    print("   La biblioteca Pillow no está disponible. Se omitirá la optimización de imágenes.")
    HAS_PILLOW = False

# --- Configuración de rutas y parámetros ---
# Enrutamiento dinámico: Usa la ruta pasada por terminal o el directorio actual (pwd).
# Ignora los flags de verbosidad (-v, --verbose).
_args = [arg for arg in sys.argv[1:] if arg not in ("-v", "--verbose")]
_target_path = Path(_args[0]).resolve() if _args else Path(os.getcwd()).resolve()

# Motor de deducción de contexto:
if _target_path.name == ".assets-raw":
    # Caso 1: Se apunta directamente a la carpeta cruda
    SOURCE_DIR = _target_path
    REPO_ROOT = _target_path.parent
    IS_EXTERNAL = False
elif (_target_path / ".assets-raw").is_dir():
    # Caso 2: Se apunta a la raíz de un proyecto Merci (contiene .assets-raw)
    REPO_ROOT = _target_path
    SOURCE_DIR = REPO_ROOT / ".assets-raw"
    IS_EXTERNAL = False
else:
    # Caso 3: Carpeta genérica externa (se escanea directamente)
    REPO_ROOT = _target_path
    SOURCE_DIR = _target_path
    IS_EXTERNAL = True

DEST_IMAGES_DIR = REPO_ROOT / "assets/images"
DEST_VIDEOS_DIR = REPO_ROOT / "assets/videos"

# Tamaños de imágenes responsivas
TARGET_WIDTHS = [1920, 1280, 800, 400, 160, 80]
WEBP_QUALITY = 80  # Calidad de conversión a WebP (0-100)

def optimize_images(verbose=False):
    """
    Busca imágenes en el directorio fuente, las convierte a formato WebP
    en varios tamaños responsivos y las guarda en el destino de producción.
    """
    if not HAS_PILLOW:
        return

    print(f"🔎 Escaneando {SOURCE_DIR} en busca de imágenes...")
    
    if not IS_EXTERNAL:
        DEST_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    image_files = list(SOURCE_DIR.rglob("*.png")) + \
                  list(SOURCE_DIR.rglob("*.jpg")) + \
                  list(SOURCE_DIR.rglob("*.jpeg"))

    if not image_files:
        print("✅ No se encontraron nuevas imágenes para optimizar.")
        return

    for image_path in image_files:
        # Caché Incremental: Evita reprocesar si la imagen WebP base ya existe y es más reciente
        target_dir = image_path.parent if IS_EXTERNAL else DEST_IMAGES_DIR
        base_output = target_dir / f"{image_path.stem}.webp"
        if base_output.exists() and int(base_output.stat().st_mtime) >= int(image_path.stat().st_mtime):
            if verbose:
                print(f"   ⏭️ Saltando (Caché): {image_path.name}")
            continue

        try:
            with Image.open(image_path) as img:
                if verbose:
                    print(f"⚙️  Procesando: {image_path.name}")
                
                # Preservar el canal alfa para imágenes con transparencia
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGBA')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Escudo de rendimiento para el logotipo principal
                if "logo" in image_path.name.lower() and img.width > 526:
                    aspect_ratio = img.height / img.width
                    img = img.resize((526, int(526 * aspect_ratio)), Image.Resampling.LANCZOS)

                # Escudo de rendimiento para avatares específicos de la interfaz de usuario
                if "Merci-en-la-nube" in image_path.name and img.width > 160:
                    aspect_ratio = img.height / img.width
                    img = img.resize((160, int(160 * aspect_ratio)), Image.Resampling.LANCZOS)

                # Guardar el archivo WebP optimizado con calidad predefinida
                img.save(base_output, "WEBP", quality=WEBP_QUALITY)
                if verbose:
                    print(f"   ✨ Generado base: {base_output.name}")

                # En modo externo, omitimos la generación masiva de resoluciones responsivas
                if IS_EXTERNAL:
                    if not verbose:
                        print(f"  ✅ Optimizada in-place: {image_path.name}")
                    continue

                for width in TARGET_WIDTHS:
                    if width >= img.width:
                        continue

                    # Calcular proporción y redimensionar imagen
                    aspect_ratio = img.height / img.width
                    new_height = int(width * aspect_ratio)
                    resized_img = img.resize((width, new_height), Image.Resampling.LANCZOS)
                    
                    output_filename = f"{image_path.stem}-{width}w.webp"
                    output_path = target_dir / output_filename
                    
                    resized_img.save(output_path, "WEBP", quality=WEBP_QUALITY)
                    if verbose:
                        print(f"   ✨ Generado: {output_path.name}")
                        
                if not verbose:
                    print(f"  ✅ Optimizada: {image_path.name}")

        except Exception as e:
            print(f"❌ Error procesando imagen {image_path.name}: {e}", file=sys.stderr)

def optimize_videos(verbose=False):
    """
    Busca vídeos en el directorio fuente, los comprime a formatos optimizados
    para la web (WebM y MP4) utilizando FFmpeg de forma desatendida.
    """
    print(f"\n🔎 Escaneando {SOURCE_DIR} en busca de vídeos...")
    if not IS_EXTERNAL:
        DEST_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    video_files = list(SOURCE_DIR.rglob("*.mp4")) + \
                  list(SOURCE_DIR.rglob("*.mov")) + \
                  list(SOURCE_DIR.rglob("*.avi")) + \
                  list(SOURCE_DIR.rglob("*.webm"))

    if not video_files:
        print("✅ No se encontraron nuevos vídeos para optimizar.")
        return

    # Verificar si FFmpeg está disponible en la variable de entorno PATH
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠️ [Merci Warning] FFmpeg no está disponible en el sistema. Omitiendo optimización de vídeos.")
        return

    for video_path in video_files:
        # Definir los archivos de salida optimizados
        target_dir = video_path.parent if IS_EXTERNAL else DEST_VIDEOS_DIR
        output_webm = target_dir / f"{video_path.stem}.webm"
        output_mp4 = target_dir / f"{video_path.stem}.mp4"

        # Verificar si ya existe una versión optimizada actualizada (Caché Incremental)
        needs_webm = not output_webm.exists() or int(output_webm.stat().st_mtime) < int(video_path.stat().st_mtime)
        needs_mp4 = not output_mp4.exists() or int(output_mp4.stat().st_mtime) < int(video_path.stat().st_mtime)

        if not needs_webm and not needs_mp4:
            if verbose:
                print(f"   ⏭️ Saltando (Caché): {video_path.name}")
            continue

        print(f"⚙️  Procesando vídeo: {video_path.name}")

        # Compresión a formato libre WebM (Codec VP9, calidad CRF 36 para balance peso/rendimiento)
        # Implementación del patrón "Video-as-GIF": Se elimina la pista de audio (-an)
        # y se reducen los fotogramas a 15 fps (-r 15) para reducir drásticamente el peso
        # permitiendo que el vídeo se comporte visualmente como un GIF ligero.
        if needs_webm:
            if verbose:
                print(f"   🎥 Codificando WebM (VP9) en modo Video-as-GIF...")
            cmd_webm = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-c:v", "libvpx-vp9", "-crf", "36", "-b:v", "0",
                "-r", "15", "-an", "-nostdin", str(output_webm)
            ]
            try:
                subprocess.run(cmd_webm, capture_output=True, check=True)
                if verbose:
                    print(f"   ✨ Generado: {output_webm.name}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error al codificar WebM para {video_path.name}: {e.stderr.decode().strip()}", file=sys.stderr)

        # Compresión a formato MP4 de respaldo (Codec H.264 compatible, calidad CRF 30)
        # Al igual que en WebM, amputamos el audio y bajamos a 15 fps para el patrón "Video-as-GIF".
        if needs_mp4:
            if verbose:
                print(f"   🎥 Codificando MP4 (H.264) en modo Video-as-GIF...")
            cmd_mp4 = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-c:v", "libx264", "-crf", "30", "-preset", "fast",
                "-r", "15", "-an", "-nostdin", str(output_mp4)
            ]
            try:
                subprocess.run(cmd_mp4, capture_output=True, check=True)
                if verbose:
                    print(f"   ✨ Generado: {output_mp4.name}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error al codificar MP4 para {video_path.name}: {e.stderr.decode().strip()}", file=sys.stderr)

        if not verbose:
            print(f"  ✅ Vídeo optimizado: {video_path.name}")

def main():
    """Lógica principal de control de ejecución del orquestador."""
    is_verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    if HAS_PILLOW:
        optimize_images(is_verbose)
    
    optimize_videos(is_verbose)
    print("\n[Merci Optimizer] Proceso completado con éxito.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Optimizer] Proceso interrumpido por la usuaria. Saliendo limpiamente.")
        sys.exit(130)