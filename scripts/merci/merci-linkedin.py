#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-linkedin.py — Motor de automatización social (Fase 8.3).
Arquitectura OIDC (Three-legged OAuth) con 0 dependencias externas.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.parse
import unicodedata
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"
TOKEN_PATH = REPO_ROOT / ".linkedin_token.json" # Aquí guardaremos la llave

def slugify(texto: str) -> str:
    """Convierte un texto en una cadena segura para URLs (slug)."""
    texto = str(texto)
    texto = re.sub(r'[—–]', '-', texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

# =========================================================================
# 1. EL MICRO-SERVIDOR LOCAL (El atrapa-códigos)
# =========================================================================

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """
    QUÉ HACE: Crea un servidor web efímero que solo sabe responder a la ruta /callback.
    POR QUÉ: LinkedIn redirigirá tu navegador aquí después de que apruebes los permisos.
    Necesitamos atrapar el código que viene en la URL (?code=XYZ).
    """
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/callback':
            query = urllib.parse.parse_qs(parsed_path.query)
            
            if 'code' in query:
                # Guardamos el código secreto en el servidor padre
                self.server.auth_code = query['code'][0]
                
                # Le respondemos a tu navegador para que sepas que funcionó
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                html = """
                <html><body style="font-family: sans-serif; text-align: center; padding: 50px;"> # merci-audit:silence-style
                    <h1 style="color: #ea580c;">¡Autenticación capturada!</h1> # merci-audit:silence-style
                    <p>Merci ya tiene el código. Puedes cerrar esta pestaña y volver a la terminal.</p>
                </body></html>
                """
                self.wfile.write(html.encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Error: No se recibio ningun codigo.")

    # Silenciamos los logs del servidor para no ensuciar la terminal
    def log_message(self, format, *args):
        pass

# =========================================================================
# 2. EL FLUJO OAUTH (El Canje)
# =========================================================================

def obtener_credenciales():
    """Extrae las credenciales del .env de forma segura."""
    if not ENV_PATH.exists():
        print("❌ Error: No se encontró el archivo .env seguro.")
        sys.exit(1)
        
    env_data = {}
    for linea in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.startswith("#"):
            clave, valor = linea.split("=", 1)
            env_data[clave.strip()] = valor.strip().strip('"').strip("'")
            
    return env_data.get("LINKEDIN_CLIENT_ID"), env_data.get("LINKEDIN_CLIENT_SECRET"), env_data.get("LINKEDIN_REDIRECT_URI")

def autenticar_linkedin():
    print("🚀 [Merci LinkedIn] Iniciando flujo OIDC seguro...")
    client_id, client_secret, redirect_uri = obtener_credenciales()
    
    if not client_id or not client_secret:
        print("❌ Error: Faltan las credenciales LINKEDIN_CLIENT_ID o SECRET en el .env.")
        return

    # PASO 1: Generar la URL de permiso (Scopes: perfil básico y publicar)
    scopes = "openid profile w_member_social"
    auth_params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes
    })
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{auth_params}"

    # PASO 2: Levantar el servidor y abrir el navegador
    print("🌐 Levantando servidor local en el puerto 8000 para atrapar el código...")
    server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
    server.auth_code = None
    
    print("👉 Abriendo navegador... Por favor, aprueba la solicitud en LinkedIn.")
    webbrowser.open(auth_url)
    
    # El script se "pausa" aquí hasta que recibe 1 sola petición web
    server.handle_request() 
    
    if not server.auth_code:
        print("❌ Falló la captura del código de autorización.")
        return
        
    print("✅ Código atrapado con éxito. Canjeando por el Access Token...")
    
    # PASO 3: Canjear el código por las llaves maestras
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": server.auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }).encode('utf-8')
    
    req = urllib.request.Request(token_url, data=token_data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    with urllib.request.urlopen(req) as response:
        token_json = json.loads(response.read().decode('utf-8'))
        TOKEN_PATH.write_text(json.dumps(token_json, indent=4))
        print("🔐 ¡ÉXITO! Access Token guardado de forma segura en .linkedin_token.json")
        print("Ya estamos listos para automatizar publicaciones.")

# =========================================================================
# 3. EL PUBLICADOR (El Lector de Markdown)
# =========================================================================

def obtener_urn_usuario(access_token):
    """Obtiene el ID único (URN) de tu perfil en LinkedIn."""
    url = "https://api.linkedin.com/v2/userinfo"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return f"urn:li:person:{data['sub']}"
    except Exception as e:
        print(f"❌ Error al obtener identidad de LinkedIn: {e}")
        return None

def publicar_texto_linkedin(access_token, author_urn, texto):
    """Envía el POST a la API de LinkedIn para publicar un texto plano."""
    url = "https://api.linkedin.com/v2/ugcPosts"
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": texto.strip()},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    })
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res.get("id") # Retorna el ID único del post en LinkedIn
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("  ⚠️ [Merci Warn] Token expirado (HTTP 401). Borrando .linkedin_token.json para forzar re-autenticación.")
            TOKEN_PATH.unlink(missing_ok=True)
        print(f"❌ Error API LinkedIn: {e.read().decode('utf-8')}")
        return None

def procesar_linkedin(modo_auto=False):
    print(f"🚀 [Merci LinkedIn] {'Modo Automático (Cron)' if modo_auto else 'Modo Revisión Interactiva'}...")
    
    token_data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    access_token = token_data.get("access_token")
    author_urn = obtener_urn_usuario(access_token)
    
    if not author_urn: return

    # Añadimos la biblioteca para poder promocionar también Cuadernillos y Compendios estáticos
    directorios = [REPO_ROOT / "blog", REPO_ROOT / "art-de-cote", REPO_ROOT / "biblioteca"]
    yaml_pattern = re.compile(r"^\s*---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
    
    en_cola = []
    aprobados = []
    for dir_path in directorios:
        if not dir_path.exists(): continue
        
        for archivo in dir_path.rglob("*.md"):
            content = archivo.read_text(encoding="utf-8")
            match = yaml_pattern.search(content)
            if not match: continue
            
            yaml_block = match.group(1)
            estado = re.search(r'^estado:\s*["\']?([^"\'\n]+)["\']?', yaml_block, re.MULTILINE)
            
            linkedin_id = re.search(r'^linkedin_id:', yaml_block, re.MULTILINE)
            
            # NUEVA LÓGICA: Leer el texto de LinkedIn desde un comentario HTML en el cuerpo del Markdown
            linkedin_text_match = re.search(r'<!--\s*linkedin:\s*(.*?)\s*-->', content, re.DOTALL | re.IGNORECASE)
            
            estado_social = re.search(r'^estado_social:\s*["\']?([^"\'\n]+)["\']?', yaml_block, re.MULTILINE)
            fecha = re.search(r'^fecha:\s*["\']?([^"\'\n]+)["\']?', yaml_block, re.MULTILINE)
            
            if estado and estado.group(1) == "publicado" and estado_social and linkedin_text_match and not linkedin_id:
                val_estado_social = estado_social.group(1)
                fecha_val = fecha.group(1) if fecha else "9999-99-99"
                
                texto_post_base = linkedin_text_match.group(1).strip()
                
                # INYECCIÓN DINÁMICA DE URL: Si no hay link, lo calculamos y añadimos
                if "http" not in texto_post_base:
                    tema_match = re.search(r'^tema:\s*["\']?([^"\'\n]+)["\']?', yaml_block, re.MULTILINE)
                    tema_val = tema_match.group(1).lower() if tema_match else ""
                    if "blog" in tema_val:
                        enlace = f"https://merci-boilerplate.es/blog/{archivo.stem}/"
                    else:
                        titulo_match = re.search(r'^titulo:\s*["\']?([^"\'\n]+)["\']?', yaml_block, re.MULTILINE)
                        titulo_val = titulo_match.group(1) if titulo_match else archivo.stem
                        slug = slugify(titulo_val)
                        base_path = "/art-de-cote/" if "art" in tema_val else "/biblioteca/"
                        enlace = f"https://merci-boilerplate.es{base_path}{slug}.html"
                    texto_post_final = f"{texto_post_base}\n\n🔗 Lee el artículo completo aquí:\n{enlace}"
                else:
                    texto_post_final = texto_post_base

                datos_post = {
                    "archivo": archivo,
                    "fecha": fecha_val,
                    "texto_post": texto_post_final,
                    "yaml_block": yaml_block,
                    "content": content
                }
                
                if val_estado_social == "en_cola":
                    en_cola.append(datos_post)
                elif val_estado_social == "aprobado":
                    aprobados.append(datos_post)

    if modo_auto:
        if not aprobados:
            print("  🤷‍♀️ Ningún post 'aprobado' en la cola para emitir hoy.")
            return
            
        aprobados.sort(key=lambda x: x["fecha"])
        post_objetivo = aprobados[0]
        archivo = post_objetivo["archivo"]
        texto_post = post_objetivo["texto_post"]
        yaml_block = post_objetivo["yaml_block"]
        content = post_objetivo["content"]

        print(f"\n  📝 Emitiendo post más antiguo aprobado: {archivo.name} ({post_objetivo['fecha']})")
        
        post_id = publicar_texto_linkedin(access_token, author_urn, texto_post)
        if post_id:
            nuevo_yaml = re.sub(r'^estado_social:\s*["\']?aprobado["\']?', 'estado_social: "publicado_linkedin"', yaml_block, flags=re.MULTILINE)
            nuevo_yaml += f'\nlinkedin_id: "{post_id}"'
            nuevo_contenido = content.replace(yaml_block, nuevo_yaml)
            archivo.write_text(nuevo_contenido, encoding="utf-8")
            print(f"  ✅ ¡Éxito! Post publicado automáticamente.")
    else:
        
        aprobados_hoy = 0
        en_cola.sort(key=lambda x: x["fecha"])
        
        while True:
            if not en_cola:
                print("\n  🎉 Ya no hay más posts pendientes de revisión en la cola.")
                break
                
            print(f"\n  📊 Estado del Buffer: {len(en_cola)} pendientes de revisión | {len(aprobados)} listos para emisión automática.")
            print("\n  📄 Posts pendientes de revisión:")
            for i, post in enumerate(en_cola, 1):
                print(f"    [{i}] {post['fecha']} — {post['archivo'].name}")
                
            opcion = input("\n  👉 Elige el número del post a revisar (0 para salir): ").strip()
            
            if opcion == '0' or not opcion:
                break
                
            try:
                idx = int(opcion) - 1
                if idx < 0 or idx >= len(en_cola):
                    print("  ❌ Selección inválida.")
                    continue
                post = en_cola[idx]
            except ValueError:
                print("  ❌ Entrada inválida. Introduce un número.")
                continue

            archivo = post["archivo"]
            texto_post = post["texto_post"]
            yaml_block = post["yaml_block"]
            content = post["content"]
            
            print(f"\n  📝 Revisando: {archivo.name} ({post['fecha']})")
            print(f"  💬 Previsualización:\n{texto_post}\n")
            
            confirmacion = input("  👉 ¿Aprobar este post y moverlo a la cola automática de emisión? (s/N): ").strip().lower()
            if confirmacion == 's':
                nuevo_yaml = re.sub(r'^estado_social:\s*["\']?en_cola["\']?', 'estado_social: "aprobado"', yaml_block, flags=re.MULTILINE)
                nuevo_contenido = content.replace(yaml_block, nuevo_yaml)
                archivo.write_text(nuevo_contenido, encoding="utf-8")
                print(f"  ✅ Post movido a 'aprobado' (en tránsito).")
                aprobados_hoy += 1
                en_cola.pop(idx)
                aprobados.append(post)
            else:
                print("  ⏭️ Omitido. Dejado en la cola.")
                
        if aprobados_hoy > 0:
            print(f"\n  🎉 Has aprobado {aprobados_hoy} post(s). Una tarea Cron los irá publicando poco a poco.")

if __name__ == "__main__":
    modo_auto = "--auto" in sys.argv or "--cron" in sys.argv
    if not TOKEN_PATH.exists():
        autenticar_linkedin()
    else:
        procesar_linkedin(modo_auto)