#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-linkcheck.py — Rastreador dinámico de enlaces rotos.

Recorre el proyecto de forma local (vía HTTP) para asegurar que ninguna 
ruta devuelve error 404, validando la integración real de Nginx y WordPress.
"""

import sys
import urllib.request
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        # Extraer URLs de anclas, estilos e imágenes
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and value:
                    self.links.append(value)
        elif tag == "link":
            for attr, value in attrs:
                if attr == "href" and value:
                    self.links.append(value)
        elif tag == "img":
            for attr, value in attrs:
                if attr == "src" and value:
                    self.links.append(value)

def main():
    # Por defecto, probamos el entorno de integración local
    base_url = "http://localhost"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')

    # Cola de URLs por visitar: lista de tuplas (url_destino, url_origen_donde_se_encontro)
    to_visit = [(base_url, "Punto de entrada (Manual)")]
    visited = set()
    broken_links = []
    
    print(f"🚀 [Merci LinkCheck] Iniciando rastreo profundo en: {base_url}")
    
    while to_visit:
        current_url, source_url = to_visit.pop(0)
        
        # Limpiar fragmentos (#) para no procesar anclas internas de la misma página como URLs distintas
        clean_url = urlparse(current_url)._replace(fragment="").geturl()
        
        if clean_url in visited or clean_url.startswith(('mailto:', 'tel:', 'javascript:')):
            continue
            
        visited.add(clean_url)
        
        try:
            # Fingimos ser el Bot de Merci para evitar bloqueos
            req = urllib.request.Request(clean_url, headers={'User-Agent': 'Merci-Bot/1.0'})
            with urllib.request.urlopen(req) as response:
                # Solo parseamos HTML en busca de nuevos enlaces. Ignoramos binarios o CSS
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    html = response.read().decode('utf-8', errors='ignore')
                    parser = LinkParser()
                    parser.feed(html)
                    
                    for link in parser.links:
                        full_url = urljoin(clean_url, link)
                        parsed_full = urlparse(full_url)
                        parsed_base = urlparse(base_url)
                        
                        # Regla estricta: Solo encolar y rastrear enlaces internos del mismo dominio
                        if parsed_full.netloc == parsed_base.netloc:
                            to_visit.append((full_url, clean_url))
                            
        except urllib.error.HTTPError as e:
            broken_links.append((clean_url, source_url, str(e.code)))
            print(f"❌ Roto: {clean_url} (HTTP {e.code})\n   ↳ Encontrado en: {source_url}\n")
        except urllib.error.URLError as e:
            broken_links.append((clean_url, source_url, str(e.reason)))
            print(f"❌ Error conexión: {clean_url}\n   ↳ {e.reason}\n")
        except Exception as e:
            broken_links.append((clean_url, source_url, str(e)))
            print(f"❌ Error inesperado: {clean_url} ({e})\n")
            
    print("--- Resumen del Rastreo ---")
    print(f"🔗 URLs únicas validadas: {len(visited)}")
    
    if broken_links:
        print(f"⚠️  Se encontraron {len(broken_links)} enlaces rotos.")
        sys.exit(1)
    else:
        print("✅ Estado: Perfecto. Arquitectura unificada sin enlaces rotos.")
        sys.exit(0)

if __name__ == "__main__":
    main()