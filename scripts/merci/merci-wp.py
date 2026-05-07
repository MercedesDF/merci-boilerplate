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
import unicodedata
from urllib.error import URLError, HTTPError
from pathlib import Path

try:
    import markdown
except ImportError:
    print("ℹ️ [Merci Info] Falta la librería 'markdown' (pip install markdown). Omitiendo sincronización Headless.")
    sys.exit(0)

try:
    from weasyprint import HTML
except ImportError:
    HTML = None
    print("ℹ️ [Merci Info] Falta la librería 'weasyprint' (pip install weasyprint). No se generarán PDFs.")

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"
WP_DIRS = [
    REPO_ROOT / "blog"
]

def slugify(texto: str) -> str:
    """
    QUÉ HACE: Convierte un texto en una cadena segura para URLs (slug) eliminando acentos y caracteres especiales.
    POR QUÉ: Desacopla el nombre físico del archivo local de la URI pública, asegurando enlaces limpios 
    y consistentes independientemente de cómo el autor nombre sus archivos en el sistema operativo.
    """
    texto = str(texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

def cargar_credenciales():
    """
    QUÉ HACE: Lector nativo de variables de entorno.
    POR QUÉ: Evita la dependencia externa de 'python-dotenv', manteniendo el script ultraligero 
    (regla de 0 dependencias) y asegurando las credenciales localmente (Shift-Left Security).
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

def publicar_en_wordpress(filepath: str, creds: dict, verbose: bool = False):
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
            print(f"  ⚠️ La categoría '{tema}' no existe en WP. Quedará sin categorizar.")

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
            
            # 3.5 Generar PDF localmente (Paridad con Biblioteca)
            # QUÉ HACE: Genera el PDF utilizando el slug definitivo asignado por WordPress en su base de datos.
            # POR QUÉ: Asegura que el enlace dinámico ($post->post_name) de la web coincida matemáticamente con el archivo local.
            pdf_msg = ""
            wp_slug = res_data.get("slug")
            if wp_slug and estado == "publicado":
                out_pdf_filename = f"{wp_slug}.pdf"
                out_pdf_path = REPO_ROOT / "public" / "descargas" / out_pdf_filename
                out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                
                pdf_html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{titulo}</title>
    <style>
        @page {{ size: A4; margin: 2.5cm; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #334155; }}
        .portada {{ text-align: center; page-break-after: always; padding-top: 30%; }}
        .portada h1 {{ font-size: 2.5em; color: #ea580c; margin-bottom: 0.2em; }}
        .portada p {{ font-size: 1.2em; color: #64748b; }}
        h2 {{ color: #ea580c; margin-top: 2em; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.5em; }}
        pre {{ background: #f1f5f9; padding: 1em; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; font-size: 0.9em; }}
        code {{ font-family: monospace; background: #f1f5f9; padding: 0.2em 0.4em; border-radius: 3px; font-size: 0.9em; }}
        img {{ max-width: 100%; height: auto; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="portada">
        <h1>{titulo}</h1>
        <p>Art de Coté | Cuadernillo</p>
    </div>
    <div class="contenido">
        {html_content}
    </div>
</body>
</html>"""
                if HTML:
                    try:
                        HTML(string=pdf_html_content, base_url=str(REPO_ROOT / "public")).write_pdf(out_pdf_path)
                        if verbose: print(f"  📄 PDF generado con éxito: public/descargas/{out_pdf_filename}")
                        pdf_msg = " (+ PDF)"
                    except Exception as e:
                        print(f"  ❌ Error al generar PDF para {target_path.name}: {e}")
                    
            if not verbose and estado == "publicado":
                print(f"  ✅ Sincronizado en WP: {target_path.name}{pdf_msg}")

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
    is_verbose = "--verbose" in sys.argv or "-v" in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
    
    print("🚀 [Merci WP] Iniciando conexión Headless con WordPress...")
    creds = cargar_credenciales()
    
    if not creds.get("WP_URL") or not creds.get("WP_USER") or not creds.get("WP_APP_PASSWORD"):
        print("❌ [Merci WP] Error: Faltan credenciales completas en tu archivo .env.")
        sys.exit(1)
        
    # QUÉ HACE: Si se pasa un argumento, procesa ese archivo o carpeta. Si no, sincroniza masivamente.
    # POR QUÉ: Permite sincronizaciones atómicas globales (SSOT) evitando la deriva de configuración.
    if len(args) > 0:
        target = Path(args[0]).resolve()
        if target.is_dir():
            for md_file in target.rglob("*.md"):
                publicar_en_wordpress(str(md_file), creds, is_verbose)
        else:
            publicar_en_wordpress(str(target), creds, is_verbose)
    else:
        if is_verbose:
            print("🔄 Sincronización masiva de carpetas dinámicas detectada...")
        for wp_dir in WP_DIRS:
            if wp_dir.exists():
                if is_verbose: print(f"\n📂 Escaneando directorio: {wp_dir.name}/")
                for md_file in wp_dir.rglob("*.md"):
                    publicar_en_wordpress(str(md_file), creds, is_verbose)
            else:
                if is_verbose: print(f"\n⚠️  Directorio no encontrado: {wp_dir.name}/. Omitiendo.")
                
    print("\n✅ [Merci WP] Sincronización finalizada.")