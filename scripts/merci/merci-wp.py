#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-wp.py — Publicador Headless para WordPress.

Lee un documento Markdown local, extrae su categoría (tema) del YAML,
lo convierte a HTML y lo publica directamente en WordPress vía API REST,
manteniendo la seguridad de las credenciales mediante .env.
"""

import base64
import html
import json
import os
import re
import shutil
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

try:
    import markdown
except ImportError:
    print("ℹ️ [Merci Info] Falta la librería 'markdown' (pip install markdown). Omitiendo sincronización Headless.")
    sys.exit(0)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"
WP_DIRS = [
    REPO_ROOT / "blog"
]
SYNC_CACHE_PATH = REPO_ROOT / "observabilidad" / ".wp_sync.json"

def slugify(texto: str) -> str:
    """
    QUÉ HACE: Convierte un texto en una cadena segura para URLs (slug) sin caracteres especiales.
    POR QUÉ: Garantiza que el slug generado sea idéntico al del SSG para evitar enlaces rotos.
    """
    texto = str(texto)
    texto = re.sub(r'[—–]', '-', texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

def cargar_credenciales() -> dict[str, str]:
    """
    QUÉ HACE: Lee el archivo .env de forma local y devuelve las variables de entorno de WordPress.
    POR QUÉ: Evita quemar secretos en código duro y cumple el principio de Zero Trust.
    """
    credenciales = {}
    if ENV_FILE.exists():
        content = ENV_FILE.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                key, val = line.split("=", 1)
                credenciales[key.strip()] = val.strip().strip('"\'')
                
    # Prioridad a las variables inyectadas por el SO (vital para merci-deploy.py)
    if os.environ.get("WP_URL"): credenciales["WP_URL"] = os.environ.get("WP_URL")
    if os.environ.get("WP_USER"): credenciales["WP_USER"] = os.environ.get("WP_USER")
    if os.environ.get("WP_APP_PASSWORD"): credenciales["WP_APP_PASSWORD"] = os.environ.get("WP_APP_PASSWORD")
            
    return credenciales

def obtener_id_categoria(wp_url: str, auth_b64: str, nombre_categoria: str) -> int | None:
    """
    QUÉ HACE: Consulta la API de WordPress para buscar el ID de una categoría a partir de su nombre.
    POR QUÉ: WordPress exige IDs numéricos al clasificar posts, abstrayendo esta consulta del Markdown.
    """
    query = urllib.parse.quote(nombre_categoria)
    endpoint = f"{wp_url}/wp-json/wp/v2/categories?search={query}"
    
    req = urllib.request.Request(endpoint, method="GET")
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("X-Authorization", f"Basic {auth_b64}")
    req.add_header("User-Agent", "Merci-Boilerplate-Agent/1.0")

    try:
        with urllib.request.urlopen(req) as response:
            categorias = json.loads(response.read().decode("utf-8"))
            for cat in categorias:
                if cat.get("name", "").lower() == nombre_categoria.lower():
                    return cat.get("id")
    except Exception as e:
        print(f"  ⚠️ No se pudo resolver la categoría '{nombre_categoria}': {e}")
        
    return None

def obtener_id_por_slug(wp_url: str, auth_b64: str, slug: str) -> int | None:
    """
    QUÉ HACE: Consulta si existe algún artículo en WordPress con el slug indicado y devuelve su ID.
    POR QUÉ: Permite saber si actualizar un post existente o crear uno nuevo.
    """
    endpoint = f"{wp_url}/wp-json/wp/v2/posts?slug={slug}"
    req = urllib.request.Request(endpoint, method="GET")
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("X-Authorization", f"Basic {auth_b64}")
    req.add_header("User-Agent", "Merci-Boilerplate-Agent/1.0")
    
    try:
        with urllib.request.urlopen(req) as response:
            posts = json.loads(response.read().decode("utf-8"))
            if posts and len(posts) > 0:
                return posts[0].get("id")
    except Exception:
        pass
    return None

def publicar_en_wordpress(filepath: str, creds: dict[str, str], sync_cache: dict[str, int], verbose: bool = False) -> bool:
    """
    QUÉ HACE: Convierte un archivo Markdown a HTML y lo envía a WordPress vía API REST.
    POR QUÉ: Automatiza la publicación Headless centralizada desde control de versiones.
    """
    target_path = Path(filepath).resolve()
    
    if not target_path.exists():
        print(f"  ❌ Error: No se encontró el archivo '{target_path.name}'.")
        return False
        
    file_key = str(target_path.relative_to(REPO_ROOT))
    md_mtime = int(target_path.stat().st_mtime)
    if file_key in sync_cache and sync_cache[file_key] >= md_mtime and "--force" not in sys.argv:
        return True

    wp_url = creds.get("WP_URL", "").rstrip("/")
    wp_user = creds.get("WP_USER", "")
    wp_password = creds.get("WP_APP_PASSWORD", "")
    
    auth_str = f"{wp_user}:{wp_password}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    content = target_path.read_text(encoding="utf-8")
    match = re.search(r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)(.*)", content, flags=re.DOTALL | re.MULTILINE)
    if not match:
        print(f"  ❌ Error: El archivo {target_path.name} no tiene un YAML Frontmatter válido.")
        return False
        
    yaml_raw, md_body = match.groups()
    
    meta = {}
    for line in yaml_raw.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip().strip('"\'')
            
    titulo = meta.get("titulo", "Borrador desde Terminal")
    estado = meta.get("estado", "draft").lower()
    tema = meta.get("tema", "")
    
    wp_status = "publish" if estado == "publicado" else "draft"
    if verbose:
        print(f"  📖 Procesando: {titulo} (Estado WP: {wp_status})")
    
    html_content = markdown.markdown(md_body, extensions=['fenced_code'])
    
    payload = {
        "title": titulo,
        "slug": target_path.stem,
        "content": html_content,
        "status": wp_status,
        "excerpt": meta.get("descripcion", "")
    }
    
    if tema:
        if verbose: print(f"  🔍 Buscando ID para la categoría: '{tema}'...")
        cat_id = obtener_id_categoria(wp_url, auth_b64, tema)
        if cat_id:
            payload["categories"] = [cat_id]
            if verbose: print(f"  🏷️  Categoría vinculada (ID: {cat_id})")
        else:
            print(f"  ⚠️ La categoría '{tema}' no existe en WP. Quedará sin categorizar.")
            print(f"     👉 Solución: Entra en {wp_url}/wp-admin/edit-tags.php?taxonomy=category")
            print(f"     crea la categoría '{tema}' y vuelve a ejecutar este comando para enlazarla.")

    data = json.dumps(payload).encode("utf-8")
    
    entorno_id = obtener_id_por_slug(wp_url, auth_b64, target_path.stem)
    if entorno_id:
        endpoint = f"{wp_url}/wp-json/wp/v2/posts/{entorno_id}"
        if verbose: print(f"  🔄 Actualizando post existente (ID remoto: {entorno_id})...")
    else:
        endpoint = f"{wp_url}/wp-json/wp/v2/posts"
        if verbose: print("  📡 Creando nuevo post en WordPress...")
        
    req = urllib.request.Request(endpoint, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("X-Authorization", f"Basic {auth_b64}")
    req.add_header("User-Agent", "Merci-Boilerplate-Agent/1.0")

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            link = res_data.get("link", "URL desconocida")
            
            if verbose:
                print(f"  ✅ ¡Éxito! Post transferido correctamente.")
                print(f"  🔗 Enlace de WP: {link}")
            
            if estado != "publicado" and not target_path.is_relative_to(REPO_ROOT / "laboratorio"):
                destino_lab = REPO_ROOT / "laboratorio" / "incubacion" / target_path.name
                destino_lab.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target_path), str(destino_lab))
                if verbose: print(f"  🔙 Expulsando (Estado: {estado}): Moviendo '{target_path.name}' de vuelta a laboratorio/incubacion/")
            
            sync_cache[file_key] = md_mtime
            
    except HTTPError as e:
        error_info = e.read().decode("utf-8")
        print(f"  ❌ Error HTTP {e.code}: {e.reason}")
        print(f"  Detalle: {error_info}")
    except URLError as e:
        print(f"  ❌ Error de conexión: {e.reason}. ¿Está el entorno dinámico encendido?")
        return False
        
    return True

if __name__ == "__main__":
    try:
        is_verbose = "--verbose" in sys.argv or "-v" in sys.argv
        args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
        
        print("🚀 [Merci WP] Iniciando conexión Headless con WordPress...")
        creds = cargar_credenciales()
        
        if not creds.get("WP_URL") or not creds.get("WP_USER") or not creds.get("WP_APP_PASSWORD"):
            print("  ℹ️ [Merci Info] Faltan credenciales completas en tu archivo .env. Omitiendo sincronización.")
            sys.exit(0)
            
        sync_cache = {}
        if SYNC_CACHE_PATH.exists():
            try:
                sync_cache = json.loads(SYNC_CACHE_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        entorno_activo = creds.get("WP_URL", "")
        if sync_cache.get("_entorno") != entorno_activo:
            if is_verbose: print(f"🔄 [Merci WP] Entorno cambiado a '{entorno_activo}'. Invalidando caché de sincronización...")
            sync_cache = {"_entorno": entorno_activo}
        else:
            sync_cache.setdefault("_entorno", entorno_activo)

        publicaciones_procesadas = 0
        if len(args) > 0:
            target = Path(args[0]).resolve()
            if target.is_dir():
                for md_file in target.rglob("*.md"):
                    if publicar_en_wordpress(str(md_file), creds, sync_cache, is_verbose):
                        publicaciones_procesadas += 1
            else:
                if publicar_en_wordpress(str(target), creds, sync_cache, is_verbose):
                    publicaciones_procesadas += 1
        else:
            if is_verbose:
                print("🔄 Sincronización masiva de carpetas dinámicas detectada...")
            for wp_dir in WP_DIRS:
                if wp_dir.exists():
                    if is_verbose: print(f"\n📂 Escaneando directorio: {wp_dir.name}/")
                    for md_file in wp_dir.rglob("*.md"):
                        if publicar_en_wordpress(str(md_file), creds, sync_cache, is_verbose):
                            publicaciones_procesadas += 1
                else:
                    if is_verbose: print(f"\n⚠️  Directorio no encontrado: {wp_dir.name}/. Omitiendo.")
                    
        sync_cache["_entorno"] = entorno_activo
        SYNC_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SYNC_CACHE_PATH.write_text(json.dumps(sync_cache, indent=2), encoding="utf-8")

        print(f"✅ [Merci WP] Sincronización finalizada. {publicaciones_procesadas} publicacion(es) procesada(s).")
    except KeyboardInterrupt:
        print("\n🛑 [Merci WP] Sincronización interrumpida por la usuaria. Saliendo limpiamente.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ [Merci WP] Error fatal inesperado: {e}")
        sys.exit(1)