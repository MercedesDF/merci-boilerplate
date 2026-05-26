#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-shop.py — Orquestador Headless para WooCommerce (Mock E-commerce).
Lee los archivos Markdown de laboratorio/tienda/ y los sincroniza
con la API REST de WooCommerce usando autenticación segura.
"""

import os
import sys
import json
import argparse
import base64
import urllib.request
import urllib.error
from pathlib import Path
import re
import shutil

try:
    import markdown
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]
TIENDA_DIR = REPO_ROOT / "tienda"
ENV_PATH = REPO_ROOT / ".env"

def cargar_credenciales() -> tuple[str, str]:
    """
    QUÉ HACE: Lee el .env local y genera el token de Autenticación Básica.
    POR QUÉ: Evita tener credenciales hardcodeadas (quemadas) en el código,
    respetando el principio Zero Trust y la seguridad Shift-Left.
    """
    env_vars = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip().strip("'\"")
            
    wp_url = (os.environ.get("WP_URL") or env_vars.get("WP_URL", "")).rstrip("/")
    wp_user = os.environ.get("WP_USER") or env_vars.get("WP_USER", "")
    wp_pass = os.environ.get("WP_APP_PASSWORD") or env_vars.get("WP_APP_PASSWORD", "")
    
    if not wp_url or not wp_user or not wp_pass:
        print("  ℹ️ [Merci Info] Faltan credenciales completas en el .env. Omitiendo tienda.")
        sys.exit(0)
        
    credenciales = f"{wp_user}:{wp_pass}"
    auth_b64 = base64.b64encode(credenciales.encode("utf-8")).decode("utf-8")
    return wp_url, f"Basic {auth_b64}"

def realizar_peticion_wc(url: str, auth_header: str, method: str = "GET", data: dict | None = None) -> dict | None:
    """
    QUÉ HACE: Ejecuta peticiones HTTP a la API REST de WooCommerce (v3).
    POR QUÉ: Usa X-Authorization para eludir la ceguera de proxy de Varnish/Nginx
    y un User-Agent corporativo para evitar bloqueos por WAF.
    """
    headers = {
        "Authorization": auth_header,
        "X-Authorization": auth_header,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Merci-Boilerplate-Agent/1.0"
    }
    
    payload = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  ❌ Error HTTP {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"  ❌ Error de conexión: {e}")
        return None

def obtener_producto_por_slug(wc_endpoint: str, auth_header: str, slug: str):
    """Busca si el producto ya existe en WooCommerce mediante su slug."""
    url = f"{wc_endpoint}?slug={slug}"
    try:
        respuesta = realizar_peticion_wc(url, auth_header)
        if respuesta and len(respuesta) > 0:
            return respuesta[0].get("id")
    except Exception:
        pass
    return None

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)
    verbose = args.verbose

    print("🛒 [Merci Shop] Iniciando Orquestador Headless de WooCommerce...")
    
    wp_url, auth_header = cargar_credenciales()
    wc_endpoint = f"{wp_url}/wp-json/wc/v3/products"
    
    if verbose: print(f"  🔗 Conectando a WooCommerce en: {wp_url}")
    
    # Health Check: Intentamos traer solo 1 producto para validar credenciales
    respuesta = realizar_peticion_wc(f"{wc_endpoint}?per_page=1", auth_header)
    
    if respuesta is not None:
        if verbose: print("  ✅ Conexión exitosa. Autenticación verificada.")
    else:
        print("  ℹ️ [Merci Info] El endpoint de WooCommerce es inaccesible (entorno no configurado). Omitiendo.")
        sys.exit(0)
        
    # Aseguramos que la estantería del catálogo exista para futuros pasos
    TIENDA_DIR.mkdir(parents=True, exist_ok=True)
    
    domain_root = wp_url.removesuffix('/blog')
    productos_procesados = 0
    
    if verbose: print("  📦 Sincronizando catálogo desde Markdowns...")
    for md_file in TIENDA_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        match = re.search(r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)(.*)", content, flags=re.DOTALL | re.MULTILINE)
        if not match:
            continue
            
        yaml_raw, md_body = match.groups()
        meta = {}
        for line in yaml_raw.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip().strip('"\'')
                
        slug = md_file.stem
        producto_id = obtener_producto_por_slug(wc_endpoint, auth_header, slug)
        nombre = meta.get("nombre", md_file.stem)

        if meta.get("estado", "borrador").lower() != "publicado":
            if producto_id:
                if verbose: print(f"  🗑️ Despublicando producto (Kill-Switch): {nombre}")
                realizar_peticion_wc(f"{wc_endpoint}/{producto_id}?force=true", auth_header, method="DELETE")
                
            destino_incubacion = REPO_ROOT / "laboratorio" / "incubacion" / md_file.name
            destino_incubacion.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(md_file), str(destino_incubacion))
            if verbose: print(f"  ↩️ Devuelto a incubación: {md_file.name}")
            continue
            
        precio = meta.get("precio", "0.00")
        imagen = meta.get("imagen", "")
        
        if "markdown" in sys.modules:
            html_desc = markdown.markdown(md_body.strip(), extensions=['fenced_code'])
        else:
            html_desc = md_body.strip()
        
        payload = {
            "name": nombre,
            "slug": slug,
            "type": "simple",
            "regular_price": precio,
            "description": html_desc,
            "short_description": meta.get("descripcion_corta", ""),
            "status": "publish"
        }
        
        if imagen:
            payload["images"] = [{"src": f"{domain_root}/assets/images/{imagen}"}]
            
        if producto_id:
            if verbose: print(f"  🔄 Actualizando producto: {nombre} (ID: {producto_id})")
            realizar_peticion_wc(f"{wc_endpoint}/{producto_id}", auth_header, method="PUT", data=payload)
        else:
            if verbose: print(f"  ✨ Creando nuevo producto: {nombre}")
            realizar_peticion_wc(wc_endpoint, auth_header, method="POST", data=payload)
            
        productos_procesados += 1
        
    print(f"✅ [Merci Shop] Sincronización finalizada. {productos_procesados} producto(s) procesado(s).")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Merci Shop] Interrumpido por el usuario.")
        sys.exit(130)