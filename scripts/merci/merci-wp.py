#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-wp.py — Publicador Headless para WordPress.

Lee un documento Markdown local, extrae su categoría (tema) del YAML,
lo convierte a HTML y lo publica directamente en WordPress vía API REST,
manteniendo la seguridad de las credenciales mediante .env.
"""

import sys
import re
import json
import base64
import shutil
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError
from pathlib import Path

try:
    import markdown
except ImportError:
    print("🛡️ [Merci Error] Falta la librería 'markdown'. Ejecuta: pip install markdown")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"
WP_DIRS = [
    REPO_ROOT / "blog",
    REPO_ROOT / "art-de-cote"
]

def cargar_credenciales():
    """
    QUÉ HACE: Lector nativo de variables de entorno.
    POR QUÉ: Evita la dependencia de 'python-dotenv'. Mantiene Shift-Left Security.
    """
    if not ENV_FILE.exists():
        print("❌ [Merci WP] Error: No se encontró el archivo .env seguro.")
        print("Crea un archivo .env en la raíz con WP_URL, WP_USER y WP_APP_PASSWORD.")
        sys.exit(1)
        
    credenciales = {}
    content = ENV_FILE.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, val = line.split("=", 1)
            credenciales[key.strip()] = val.strip().strip('"\'')
            
    return credenciales

def obtener_id_categoria(wp_url, auth_b64, nombre_categoria):
    """
    QUÉ HACE: Busca el ID numérico de una categoría en WordPress por su nombre.
    POR QUÉ: La API REST de WP exige IDs numéricos para asignar categorías, no cadenas de texto.
    """
    query = urllib.parse.quote(nombre_categoria)
    endpoint = f"{wp_url}/wp-json/wp/v2/categories?search={query}"
    
    req = urllib.request.Request(endpoint, method="GET")
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("User-Agent", "Merci-Headless/1.0")

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

def publicar_en_wordpress(filepath: str, creds: dict):
    target_path = Path(filepath).resolve()
    
    if not target_path.exists():
        print(f"  ❌ Error: No se encontró el archivo '{target_path.name}'.")
        return False
        
    wp_url = creds.get("WP_URL", "").rstrip("/")
    wp_user = creds.get("WP_USER", "")
    wp_password = creds.get("WP_APP_PASSWORD", "")
    
    # 1. Preparar Autenticación Basic Auth (Shift-Left Security)
    auth_str = f"{wp_user}:{wp_password}"
    auth_b64 = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    # 2. Extraer metadatos YAML y contenido
    content = target_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
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
    wp_id = meta.get("wp_id", "")
    
    # 3. Conversión de estados y formateo HTML
    wp_status = "publish" if estado == "publicado" else "draft"
    print(f"  📖 Procesando: {titulo} (Estado WP: {wp_status})")
    
    html_content = markdown.markdown(md_body, extensions=['fenced_code'])
    
    # 4. Construir Payload (JSON) resolviendo la categoría
    payload = {
        "title": titulo,
        "content": html_content,
        "status": wp_status
    }
    
    if tema:
        print(f"  🔍 Buscando ID para la categoría: '{tema}'...")
        cat_id = obtener_id_categoria(wp_url, auth_b64, tema)
        if cat_id:
            payload["categories"] = [cat_id]
            print(f"  🏷️  Categoría vinculada (ID: {cat_id})")
        else:
            print(f"  ⚠️ La categoría '{tema}' no existe en WP. Quedará sin categorizar.")

    data = json.dumps(payload).encode("utf-8")
    
    # 5. Disparar a la API REST de WordPress
    # QUÉ HACE: Si existe un wp_id, cambia el endpoint para actualizar. Si no, crea uno nuevo.
    if wp_id:
        endpoint = f"{wp_url}/wp-json/wp/v2/posts/{wp_id}"
        print(f"  🔄 Actualizando post existente (ID WP: {wp_id})...")
    else:
        endpoint = f"{wp_url}/wp-json/wp/v2/posts"
        print("  📡 Creando nuevo post en WordPress...")
        
    req = urllib.request.Request(endpoint, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("User-Agent", "Merci-Headless/1.0")
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            link = res_data.get("link", "URL desconocida")
            nuevo_id = res_data.get("id")
            print(f"  ✅ ¡Éxito! Post transferido correctamente.")
            print(f"  🔗 Enlace de WP: {link}")
            
            # QUÉ HACE: Inyecta el ID devuelto por WordPress en el YAML del archivo local.
            # POR QUÉ: Convierte el Markdown en la Única Fuente de Verdad (SSOT) sincronizada.
            if not wp_id and nuevo_id:
                nuevo_yaml = yaml_raw.strip() + f'\nwp_id: "{nuevo_id}"'
                nuevo_contenido = content.replace(yaml_raw, nuevo_yaml, 1)
                target_path.write_text(nuevo_contenido, encoding="utf-8")
                print(f"  💾 ID de WordPress ({nuevo_id}) guardado en el Markdown local.")
                
            # QUÉ HACE: Expulsa físicamente el archivo origen hacia el entorno de incubación si es borrador.
            # POR QUÉ: Paridad de flujos. Mantiene las carpetas dinámicas raíz exclusivas para contenido en producción.
            if estado != "publicado" and not target_path.is_relative_to(REPO_ROOT / "laboratorio"):
                rel_path = target_path.relative_to(REPO_ROOT)
                destino_lab = REPO_ROOT / "laboratorio" / rel_path
                destino_lab.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target_path), str(destino_lab))
                print(f"  🔙 Expulsando (Estado: {estado}): Moviendo '{target_path.name}' de vuelta a laboratorio/{rel_path.parent.name}/")
            
    except HTTPError as e:
        error_info = e.read().decode("utf-8")
        print(f"  ❌ Error HTTP {e.code}: {e.reason}")
        print(f"  Detalle: {error_info}")
    except URLError as e:
        print(f"  ❌ Error de conexión: {e.reason}. ¿Está el entorno dinámico encendido?")
        return False
        
    return True

if __name__ == "__main__":
    print("🚀 [Merci WP] Iniciando conexión Headless con WordPress...")
    creds = cargar_credenciales()
    
    if not creds.get("WP_URL") or not creds.get("WP_USER") or not creds.get("WP_APP_PASSWORD"):
        print("❌ [Merci WP] Error: Faltan credenciales completas en tu archivo .env.")
        sys.exit(1)
        
    # QUÉ HACE: Si se pasa un argumento, procesa ese archivo o carpeta. Si no, sincroniza masivamente.
    # POR QUÉ: Permite sincronizaciones atómicas globales (SSOT) evitando la deriva de configuración.
    if len(sys.argv) > 1:
        target = Path(sys.argv[1]).resolve()
        if target.is_dir():
            for md_file in target.rglob("*.md"):
                publicar_en_wordpress(str(md_file), creds)
        else:
            publicar_en_wordpress(str(target), creds)
    else:
        print("🔄 Sincronización masiva de carpetas dinámicas detectada...")
        for wp_dir in WP_DIRS:
            if wp_dir.exists():
                print(f"\n📂 Escaneando directorio: {wp_dir.name}/")
                for md_file in wp_dir.rglob("*.md"):
                    publicar_en_wordpress(str(md_file), creds)
            else:
                print(f"\n⚠️  Directorio no encontrado: {wp_dir.name}/. Omitiendo.")
                
    print("\n✅ [Merci WP] Sincronización finalizada.")