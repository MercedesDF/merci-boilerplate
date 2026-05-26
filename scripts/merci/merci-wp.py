#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-wp.py — Publicador Headless para WordPress.

Lee un documento Markdown local, extrae su categoría (tema) del YAML,
lo convierte a HTML y lo publica directamente en WordPress vía API REST,
manteniendo la seguridad de las credenciales mediante .env.
"""

import sys
import os
import re
import json
import base64
import shutil
import urllib.request
import urllib.parse
import unicodedata
import html
from urllib.error import URLError, HTTPError
from pathlib import Path

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
    QUÉ HACE: Convierte un texto en una cadena segura para URLs (slug) eliminando acentos y caracteres especiales.
    POR QUÉ: Desacopla el nombre físico del archivo local de la URI pública, asegurando enlaces limpios 
    y consistentes independientemente de cómo el autor nombre sus archivos en el sistema operativo.
    """
    texto = str(texto)
    texto = re.sub(r'[—–]', '-', texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

def cargar_credenciales():
    """
    QUÉ HACE: Lector nativo de variables de entorno.
    POR QUÉ: Evita la dependencia externa de 'python-dotenv', manteniendo el script ultraligero 
    (regla de 0 dependencias) y asegurando las credenciales localmente (Shift-Left Security).
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

def obtener_id_categoria(wp_url, auth_b64, nombre_categoria):
    """
    QUÉ HACE: Busca el ID numérico de una categoría en WordPress por su nombre.
    POR QUÉ: La API REST de WP exige identificadores numéricos, no cadenas de texto. Resolverlo dinámicamente 
    mantiene el archivo Markdown agnóstico a la base de datos final.
    """
    query = urllib.parse.quote(nombre_categoria)
    endpoint = f"{wp_url}/wp-json/wp/v2/categories?search={query}"
    
    # QUÉ HACE: Inyecta cabeceras 'X-Authorization' (gemela) y 'User-Agent' personalizado.
    # POR QUÉ: Evita la "Ceguera de Proxy" (proxies como Varnish purgan la cabecera estándar Authorization) 
    # y elude Cortafuegos (WAF) que bloquean peticiones automatizadas de librerías genéricas de Python.
    req = urllib.request.Request(endpoint, method="GET")
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("X-Authorization", f"Basic {auth_b64}")
    req.add_header("User-Agent", "Merci-Boilerplate-Agent/1.0")

    try:
        with urllib.request.urlopen(req) as response:
            categorias = json.loads(response.read().decode("utf-8"))
            for cat in categorias:
                # Coincidencia exacta (ignorando mayúsculas)
                if cat.get("name", "").lower() == nombre_categoria.lower():
                    return cat.get("id")
    except Exception as e:
        print(f"  ⚠️ No se pudo resolver la categoría '{nombre_categoria}': {e}")
        
    return None

def obtener_id_por_slug(wp_url, auth_b64, slug):
    """
    QUÉ HACE: Interroga a la API para saber si ya existe un artículo publicado con el slug indicado.
    POR QUÉ: Sustituye el uso de 'wp_id' fijos locales, logrando Paridad Dev/Prod absoluta al permitir 
    sincronizar el mismo archivo Markdown en distintos servidores (Local o Nube) sin colisiones de base de datos.
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

def publicar_en_wordpress(filepath: str, creds: dict, sync_cache: dict, verbose: bool = False):
    """
    QUÉ HACE: Lee un archivo Markdown, extrae su contenido y metadatos, y lo sincroniza
    con la base de datos de WordPress correspondiente según el entorno activo.
    POR QUÉ: Centraliza la lógica de publicación Headless, aislando al usuario del panel
    de administración de WP y permitiendo gobernar el CMS puramente desde archivos planos
    controlados por Git (GitOps).
    """
    target_path = Path(filepath).resolve()
    
    if not target_path.exists():
        print(f"  ❌ Error: No se encontró el archivo '{target_path.name}'.")
        return False
        
    # Caché Incremental: Evita llamadas de red si el archivo no ha sido modificado localmente
    file_key = str(target_path.relative_to(REPO_ROOT))
    # Usamos int() para evitar pérdida de precisión de microsegundos al serializar en JSON
    md_mtime = int(target_path.stat().st_mtime)
    if file_key in sync_cache and sync_cache[file_key] >= md_mtime and "--force" not in sys.argv:
        return True

    wp_url = creds.get("WP_URL", "").rstrip("/")
    wp_user = creds.get("WP_USER", "")
    wp_password = creds.get("WP_APP_PASSWORD", "")
    
    # 1. Preparar Autenticación Basic Auth (Shift-Left Security)
    auth_str = f"{wp_user}:{wp_password}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    # 2. Extraer metadatos YAML y contenido
    content = target_path.read_text(encoding="utf-8")
    match = re.search(r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)(.*)", content, flags=re.DOTALL | re.MULTILINE)
    if not match:
        print(f"  ❌ Error: El archivo {target_path.name} no tiene un YAML Frontmatter válido.")
        return False
        
    yaml_raw, md_body = match.groups()
    
    meta = {}
    # QUÉ HACE: Parsea el YAML de forma nativa sin librerías de terceros.
    # POR QUÉ: Mantiene la compatibilidad y velocidad del orquestador (0 dependencias externas).
    for line in yaml_raw.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip().strip('"\'')
            
    titulo = meta.get("titulo", "Borrador desde Terminal")
    estado = meta.get("estado", "draft").lower()
    tema = meta.get("tema", "")
    
    # 3. Conversión de estados y formateo HTML
    wp_status = "publish" if estado == "publicado" else "draft"
    if verbose:
        print(f"  📖 Procesando: {titulo} (Estado WP: {wp_status})")
    
    html_content = markdown.markdown(md_body, extensions=['fenced_code'])
    
    # 4. Construir Payload (JSON) resolviendo la categoría
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
            # QUÉ HACE: Provee la URL exacta y las instrucciones para resolver la falta de categoría.
            # POR QUÉ: Mejora la Developer Experience (DX) evitando que el usuario deba recordar rutas o buscar manuales.
            print(f"  ⚠️ La categoría '{tema}' no existe en WP. Quedará sin categorizar.")
            print(f"     👉 Solución: Entra en {wp_url}/wp-admin/edit-tags.php?taxonomy=category")
            print(f"     crea la categoría '{tema}' y vuelve a ejecutar este comando para enlazarla.")

    data = json.dumps(payload).encode("utf-8")
    
    # 5. Disparar a la API REST de WordPress (Resolución dinámica multi-entorno)
    entorno_id = obtener_id_por_slug(wp_url, auth_b64, target_path.stem)
    if entorno_id:
        endpoint = f"{wp_url}/wp-json/wp/v2/posts/{entorno_id}"
        if verbose: print(f"  🔄 Actualizando post existente (ID remoto: {entorno_id})...")
    else:
        endpoint = f"{wp_url}/wp-json/wp/v2/posts"
        if verbose: print("  📡 Creando nuevo post en WordPress...")
        
    # QUÉ HACE: Envío dual de credenciales y agente de usuario corporativo.
    # POR QUÉ: Asegura que el POST atraviese Varnish Cache y Nginx en servidores de alto rendimiento.
    req = urllib.request.Request(endpoint, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("X-Authorization", f"Basic {auth_b64}")
    req.add_header("User-Agent", "Merci-Boilerplate-Agent/1.0")

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            link = res_data.get("link", "URL desconocida")
            nuevo_id = res_data.get("id")
            
            if verbose:
                print(f"  ✅ ¡Éxito! Post transferido correctamente.")
                print(f"  🔗 Enlace de WP: {link}")
            
            # QUÉ HACE: Expulsa físicamente el archivo origen hacia el entorno de incubación si es borrador.
            # POR QUÉ: Paridad de flujos. Mantiene las carpetas dinámicas raíz exclusivas para contenido en producción.
            if estado != "publicado" and not target_path.is_relative_to(REPO_ROOT / "laboratorio"):
                destino_lab = REPO_ROOT / "laboratorio" / "incubacion" / target_path.name
                destino_lab.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target_path), str(destino_lab))
                if verbose: print(f"  🔙 Expulsando (Estado: {estado}): Moviendo '{target_path.name}' de vuelta a laboratorio/incubacion/")
            
            # Registrar sincronización exitosa en la caché
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

        # QUÉ HACE: Invalida la caché si el entorno destino (WP_URL) ha cambiado desde el último ciclo.
        # POR QUÉ: La caché registra mtime de archivos locales, no el destino al que se subieron.
        # Cambiar de local a producción sin invalidar la caché provoca que el script omita todos
        # los archivos silenciosamente (Cache Hit falso). Guardar el entorno activo como clave
        # centinela (_entorno) permite detectar y descartar la caché de forma automática.
        entorno_activo = creds.get("WP_URL", "")
        if sync_cache.get("_entorno") != entorno_activo:
            if is_verbose: print(f"🔄 [Merci WP] Entorno cambiado a '{entorno_activo}'. Invalidando caché de sincronización...")
            sync_cache = {"_entorno": entorno_activo}
        else:
            # Asegurar que la clave centinela está presente aunque la caché sea antigua
            sync_cache.setdefault("_entorno", entorno_activo)

        # QUÉ HACE: Si se pasa un argumento, procesa ese archivo o carpeta. Si no, sincroniza masivamente.
        # POR QUÉ: Permite sincronizaciones atómicas globales (SSOT) evitando la deriva de configuración.
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
                    
        # QUÉ HACE: Persiste la clave centinela junto con los registros de mtime.
        # POR QUÉ: Garantiza que en el próximo ciclo el script compare el entorno guardado
        # con el activo y descarte la caché si ha habido un cambio de entorno.
        sync_cache["_entorno"] = entorno_activo
        SYNC_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SYNC_CACHE_PATH.write_text(json.dumps(sync_cache, indent=2), encoding="utf-8")

        print(f"✅ [Merci WP] Sincronización finalizada. {publicaciones_procesadas} publicacion(es) procesada(s).")
    except KeyboardInterrupt:
        print("\n🛑 [Merci WP] Sincronización interrumpida por la usuaria.")
        sys.exit(130)