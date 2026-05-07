#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-extract-metrics.py — Lector de reportes PDF de PageSpeed Insights.
Busca el PDF más reciente en la carpeta de auditorías, extrae las métricas
de Core Web Vitals y actualiza la portada (index.html) automáticamente.
"""

import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("ℹ️ [Merci Info] Falta la librería 'pypdf'. Instálala con el comando:")
    print("   pip install pypdf")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Buscamos la carpeta con el nombre correcto de la herramienta, y caemos al typo original por si acaso
AUDITORIAS_DIR = REPO_ROOT / "auditorias-pagespeed.web.dev"
if not AUDITORIAS_DIR.exists():
    AUDITORIAS_DIR = REPO_ROOT / "auditorias-pagespedd.web.dev"
INDEX_HTML = REPO_ROOT / "public" / "index.html"

def extract_metrics_from_pdf(pdf_path: Path):
    print(f"📄 Leyendo PDF: {pdf_path.name}")
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
        
    if not text.strip():
        print("  🛑 ¡ALTO! El PDF no contiene texto seleccionable (parece ser una imagen).")
        print("  💡 Usa la función nativa de tu navegador: Ctrl+P (o Cmd+P) -> 'Guardar como PDF'.")
        print("  ❌ No uses extensiones de captura de pantalla (ScreenCapture), ya que generan fotos, no texto.")
        return {"FCP": "N/D", "LCP": "N/D", "INP": "N/D", "CLS": "N/D", "TBT": "N/D", "SI": "N/D"}
    
    # QUÉ HACE: Patrones flexibles para encontrar las métricas tolerando los saltos 
    # de línea irregulares típicos de la extracción de texto en PDFs.
    # POR QUÉ: Incluye soporte para reportes generados en Español e Inglés, y captura números decimales.
    num_time = r'((?:<|>)?\s*\d+[.,]?\d*\s*(?:m\s*s|ms|s))'
    num_unitless = r'((?:<|>)?\s*\d+[.,]?\d*)'
    
    patrones_adelante = {
        "FCP": r'(?:First\s*Contentful\s*Paint|Primer.*?contenido|FCP)(?:\s*\([^)]+\))?\s*[:\-]?\s*' + num_time,
        "LCP": r'(?:Largest\s*Contentful\s*Paint|Despliegue.*?extenso|LCP)(?:\s*\([^)]+\))?\s*[:\-]?\s*' + num_time,
        "INP": r'(?:Interaction\s*to\s*Next\s*Paint|Interacci[óo]n.*?pint|INP)(?:\s*\([^)]+\))?\s*[:\-]?\s*' + num_time,
        "CLS": r'(?:Cum\s*ulative\s*Layout\s*Shift|Cumulative\s*Layout\s*Shift|Cambio.*?dise[ñn]o|CLS)(?:\s*\([^)]+\))?\s*[:\-]?\s*' + num_unitless,
        "TBT": r'(?:T\s*otal\s*Blocking\s*T\s*im\s*e|Total\s*Blocking\s*Time|Tiempo.*?bloqueo|TBT)(?:\s*\([^)]+\))?\s*[:\-]?\s*' + num_time,
        "SI": r'(?:Speed\s*Index|Índice.*?velocidad|SI)(?:\s*\([^)]+\))?\s*[:\-]?\s*' + num_time
    }
    
    patrones_atras = {
        "FCP": num_time + r'\s*[:\-]?\s*(?:First\s*Contentful\s*Paint|Primer.*?contenido|FCP)',
        "LCP": num_time + r'\s*[:\-]?\s*(?:Largest\s*Contentful\s*Paint|Despliegue.*?extenso|LCP)',
        "INP": num_time + r'\s*[:\-]?\s*(?:Interaction\s*to\s*Next\s*Paint|Interacci[óo]n.*?pint|INP)',
        "CLS": num_unitless + r'\s*[:\-]?\s*(?:Cum\s*ulative\s*Layout\s*Shift|Cumulative\s*Layout\s*Shift|Cambio.*?dise[ñn]o|CLS)',
        "TBT": num_time + r'\s*[:\-]?\s*(?:T\s*otal\s*Blocking\s*T\s*im\s*e|Total\s*Blocking\s*Time|Tiempo.*?bloqueo|TBT)',
        "SI": num_time + r'\s*[:\-]?\s*(?:Speed\s*Index|Índice.*?velocidad|SI)'
    }
    
    metrics = {}
    for key in patrones_adelante.keys():
        match = re.search(patrones_adelante[key], text, re.IGNORECASE | re.DOTALL)
        if not match:
            match = re.search(patrones_atras[key], text, re.IGNORECASE | re.DOTALL)
            
        if match:
            raw_val = match.group(1).strip()
            # Limpiamos los espacios erráticos generados por el PDF (ej. "0 m s" -> "0ms" -> "0 ms")
            clean_val = re.sub(r'\s+', '', raw_val)
            if clean_val.endswith('ms'):
                clean_val = clean_val[:-2] + ' ms'
            elif clean_val.endswith('s'):
                clean_val = clean_val[:-1] + ' s'
            metrics[key] = clean_val
        else:
            metrics[key] = "N/D"
            print(f"  ⚠️ No se pudo extraer la métrica {key}.")
            
    if metrics.get("INP") == "N/D":
        print("  ℹ️ Info: Es normal que INP sea N/D si el sitio es nuevo (PageSpeed necesita 28 días de datos de usuarios reales).")
        
    # DEBUG: Guardamos el texto bruto en un archivo para auditarlo cómodamente
    if any(v == "N/D" for v in metrics.values()) and text.strip():
        debug_file = AUDITORIAS_DIR / "debug_pdf_text.txt"
        debug_file.write_text(text, encoding="utf-8")
        print(f"\n  🐛 [DEBUG] Algunas métricas fallaron. He guardado el texto bruto del PDF en:")
        print(f"     -> {debug_file}")
        print("     Si estás segura de que los números SÍ están en el PDF, abre ese archivo de texto y pégame cómo los ha formateado Google para ajustar el script.")
            
    return metrics

def update_index_html(metrics: dict):
    if not INDEX_HTML.exists():
        print(f"❌ No se encontró el archivo: {INDEX_HTML}")
        return
        
    print("🔄 Actualizando el Dashboard en public/index.html...")
    html = INDEX_HTML.read_text(encoding="utf-8")
    
    for key, value in metrics.items():
        if value == "N/D":
            continue
            
        # QUÉ HACE: Busca exactamente la métrica en el HTML basándose en su clase BEM
        # y reemplaza el contenido del span de valor, preservando la estructura del HTML.
        pattern = rf'(<span class="hero__metric-label">{key}</span>\s*<span class="hero__metric-value">)[^<]+(</span>)'
        html = re.sub(pattern, rf'\g<1>{value}\g<2>', html)
        print(f"  ✅ {key} actualizado a -> {value}")
            
    INDEX_HTML.write_text(html, encoding="utf-8")
    print("✨ Portada actualizada con éxito.")

def main():
    print("🚀 Iniciando extracción de métricas DevSecOps...")
    if not AUDITORIAS_DIR.exists() or not AUDITORIAS_DIR.is_dir():
        print(f"❌ Error: No existe la carpeta '{AUDITORIAS_DIR.name}' en la raíz del proyecto.")
        sys.exit(1)
        
    pdfs = list(AUDITORIAS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"❌ Error: No se encontraron archivos PDF en '{AUDITORIAS_DIR.name}'.")
        sys.exit(1)
        
    # Obtener el archivo más reciente basándose en su fecha de modificación
    latest_pdf = max(pdfs, key=lambda p: p.stat().st_mtime)
    metrics = extract_metrics_from_pdf(latest_pdf)
    
    print("\n📊 Resultados extraídos:")
    for k, v in metrics.items():
        print(f"  - {k}: {v}")
        
    print()
    update_index_html(metrics)

if __name__ == "__main__":
    main()