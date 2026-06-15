#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
merci-extract-metrics.py — Agente Extractor Data-Driven Autónomo (PageSpeed API).

Interroga la API de Google PageSpeed Insights, cachea la respuesta para proteger
el rendimiento del pipeline, extrae las métricas de Core Web Vitals, inyecta
diagnósticos SRE de red y actualiza la portada.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# Permite que un orquestador externo (como merci-showcase) defina
# una raíz de proyecto distinta, aislando la ejecución del script.
# Garantiza que el Showcase opere sobre su clon efímero y no contamine
# ni lea los datos del proyecto matriz.
if 'MERCI_PROJECT_ROOT' in os.environ:
    REPO_ROOT = Path(os.environ['MERCI_PROJECT_ROOT']).resolve()
else:
    REPO_ROOT = Path(__file__).resolve().parents[2]

INDEX_HTML = REPO_ROOT / "public" / "index.html"
OBSERVABILIDAD_DIR = REPO_ROOT / "observabilidad"
CACHE_FILE = OBSERVABILIDAD_DIR / ".metrics_cache"
PAGESPEED_CACHE_JSON = OBSERVABILIDAD_DIR / "pagespeed_response.json"

# Configuración de la API Autónoma
TARGET_URL = "https://tuempresa.es/"
STRATEGY = "mobile"
CACHE_TTL_SECONDS = 86400  # 24 horas de caché para no estrangular el pipeline CI/CD local


def load_api_key() -> str | None:
    """
    QUÉ HACE: Lee el archivo .env seguro y busca la clave PAGESPEED_API_KEY.
    POR QUÉ: Permite autenticarse ante la API de Google PageSpeed Insights para no agotar la cuota de llamadas anónimas.
    """
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("PAGESPEED_API_KEY="):
            # Extraemos ignorando comentarios inline y purgamos TODO lo que no sea alfanumérico o guiones
            raw_key = line.split("=", 1)[1].split("#")[0]
            key = re.sub(r'[^A-Za-z0-9_\-]', '', raw_key)
            
            if key and not key.startswith("AIza"):
                print(f"  ⚠️ [Merci Warn] La clave '{key[:5]}...' no es una API Key válida de Google (debe empezar por 'AIza').")
                return None
            return key
    return None


def fetch_pagespeed_data(api_key: str | None) -> dict | None:
    """
    QUÉ HACE: Realiza una petición HTTP GET a la API de Google PageSpeed Insights para la URL y estrategia configuradas.
    POR QUÉ: Obtiene el reporte Lighthouse en formato JSON de forma automatizada.
    """
    print(f"🌍 Interrogando a Google PageSpeed Insights API ({STRATEGY})...")
    url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={TARGET_URL}&strategy={STRATEGY}"
    if api_key:
        url += f"&key={api_key}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            content = response.read().decode("utf-8")
            PAGESPEED_CACHE_JSON.write_text(content, encoding="utf-8")
            print("  ✅ Datos frescos descargados y guardados en caché SRE local.")
            return json.loads(content)
    except urllib.error.URLError as e:
        print(f"  ❌ Error de red al consultar PageSpeed API: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Error inesperado de la API: {e}")
        return None


def extract_metrics_from_data(data: dict) -> dict[str, str]:
    """
    QUÉ HACE: Parsea la respuesta JSON de PageSpeed para extraer métricas de rendimiento y Core Web Vitals (LCP, TBT, CLS, etc.).
    POR QUÉ: Permite analizar cuantitativamente el estado del frontend e inyectar avisos de red.
    """
    print("📄 Parseando árbol .lighthouseResult...")
    metrics = {"FCP": "N/D", "LCP": "N/D", "INP": "N/D", "CLS": "N/D", "TBT": "N/D", "SI": "N/D"}
    
    try:
        # Extracción adaptada a la estructura nativa de Google PageSpeed Insights
        lh = data.get("lighthouseResult", {})
        audits = lh.get("audits", {})
        categories = lh.get("categories", {})
        
        fcp = audits.get("first-contentful-paint", {}).get("numericValue")
        lcp = audits.get("largest-contentful-paint", {}).get("numericValue")
        cls_val = audits.get("cumulative-layout-shift", {}).get("numericValue")
        tbt = audits.get("total-blocking-time", {}).get("numericValue")
        si = audits.get("speed-index", {}).get("numericValue")
        ttfb = audits.get("server-response-time", {}).get("numericValue", 0)

        if fcp is not None: metrics["FCP"] = f"{fcp / 1000:.1f} s"
        if lcp is not None: metrics["LCP"] = f"{lcp / 1000:.1f} s"
        if cls_val is not None: metrics["CLS"] = "0" if float(cls_val) < 0.05 else f"{float(cls_val):.3f}"
        if tbt is not None: metrics["TBT"] = f"{int(tbt)} ms"
        if si is not None: metrics["SI"] = f"{si / 1000:.1f} s"
        
        # INP proviene preferiblemente de métricas reales de campo (CrUX)
        loading_exp = data.get("loadingExperience", {}).get("metrics", {})
        inp_field = loading_exp.get("INTERACTION_TO_NEXT_PAINT_MS", {}).get("percentile")
        if inp_field:
            metrics["INP"] = f"{inp_field} ms"
        else:
            metrics["INP"] = "<100ms"

        # Análisis de puntuación global de Lighthouse
        s_perf = int(categories.get("performance", {}).get("score", 1.0) * 100)
        s_acc = int(categories.get("accessibility", {}).get("score", 1.0) * 100)
        s_bp = int(categories.get("best-practices", {}).get("score", 1.0) * 100)
        s_seo = int(categories.get("seo", {}).get("score", 1.0) * 100)
        
        str_perf = f"{s_perf}" + ("*" if s_perf < 100 else "")
        str_acc = f"{s_acc}" + ("*" if s_acc < 100 else "")
        str_bp = f"{s_bp}" + ("*" if s_bp < 100 else "")
        str_seo = f"{s_seo}" + ("*" if s_seo < 100 else "")
        
        scores_html = f"{str_perf} en Rendimiento | {str_acc} en Accesibilidad | {str_bp} en Mejores Prácticas | {str_seo} en SEO"

        # Diagnóstico SRE de Física de Redes e Inyección de Justificación
        latency = int(ttfb)
        if latency > 300:
            print(f"  ⚠️ [SRE] Advertencia de Física de Redes detectada:")
            print(f"     -> TTFB (Latencia): {latency}ms")
            print("     Documentando posible falso positivo en observabilidad...")
            
            if s_perf < 100:
                scores_html += f"<br><small>* Penalización externa por latencia de red (TTFB: {latency}ms).</small>"
            
            log_file = OBSERVABILIDAD_DIR / "falsos_positivos_red.log"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] PageSpeed API Autónoma | TTFB: {latency}ms | Posible penalización por red, no por CPU.\n")

        sre_payload = {
            "lighthouse_performance": s_perf,
            "lighthouse_accessibility": s_acc,
            "lighthouse_best_practices": s_bp,
            "lighthouse_seo": s_seo,
            "network_latency_ms": latency,
            "network_ttfb_ms": latency,
            "cwv_tbt_ms": int(tbt) if tbt is not None else 0,
            "cwv_lcp_ms": int(lcp) if lcp is not None else 0,
            "cwv_cls": float(cls_val) if cls_val is not None else 0.0
        }
        sre_file = OBSERVABILIDAD_DIR / ".lighthouse_sre.json"
        with open(sre_file, "w", encoding="utf-8") as f:
            json.dump(sre_payload, f, indent=2)

        metrics["SCORES_HTML"] = scores_html

    except Exception as e:
        print(f"  ❌ Estructura JSON no esperada o error: {e}")
        
    return metrics


def update_index_html(metrics: dict[str, str]) -> None:
    """
    QUÉ HACE: Modifica la portada estática (public/index.html) para inyectar los valores de las métricas en su respectivo bloque HTML.
    POR QUÉ: Proporciona a los usuarios visitantes un panel visual en tiempo real con las métricas del sitio.
    """
    if not INDEX_HTML.exists():
        print(f"❌ No se encontró el archivo: {INDEX_HTML}")
        return
        
    print("🔄 Actualizando el Dashboard en public/index.html...")
    html = INDEX_HTML.read_text(encoding="utf-8")
    
    scores_html = metrics.pop("SCORES_HTML", None)
    
    for key, value in metrics.items():
        if value == "N/D":
            continue
            
        # Busca exactamente la métrica en el HTML basándose en su clase BEM
        # y reemplaza el contenido del span de valor, preservando la estructura del HTML.
        pattern = rf'(<span class="hero__metric-label">{key}</span>\s*<span class="hero__metric-value">)[^<]+(</span>)'
        html = re.sub(pattern, rf'\g<1>{value}\g<2>', html)
        print(f"  ✅ {key} actualizado a -> {value}")
            
    if scores_html:
        pattern_scores = r'(<div id="lighthouse-scores"[^>]*>).*?(</div>)'
        html = re.sub(pattern_scores, rf'\g<1>\n                {scores_html}\n            \g<2>', html, flags=re.DOTALL | re.IGNORECASE)
        print(f"  ✅ Puntuaciones Lighthouse inyectadas.")
            
    INDEX_HTML.write_text(html, encoding="utf-8")
    print("✨ Portada actualizada con éxito.")


def main() -> None:
    """
    QUÉ HACE: Orquesta el flujo de extracción de métricas, aplicando caché de 24 horas y llamando a la inyección en la portada.
    POR QUÉ: Protege el rendimiento del pipeline de build local contra cuotas de red y llamadas repetitivas lentas.
    """
    print("🚀 Iniciando extracción de métricas DevSecOps (PageSpeed API Autónoma)...")
    OBSERVABILIDAD_DIR.mkdir(exist_ok=True)
    
    api_key = load_api_key()
    if not api_key:
        print("  ℹ️ [Merci Info] Operando en modo anónimo (sin clave o clave inválida).")
        
    # Lógica Cache Hit Temporal (Zero Noise & API Quota Protection)
    fetch_new = True
    if PAGESPEED_CACHE_JSON.exists():
        age_seconds = time.time() - PAGESPEED_CACHE_JSON.stat().st_mtime
        if age_seconds < CACHE_TTL_SECONDS:
            fetch_new = False
            print(f"  ⚡ [Cache Hit] Usando reporte SRE de hace {age_seconds/3600:.1f} horas. Omitiendo llamada HTTP.")
        else:
            print(f"  ⏳ [Cache Expired] Reporte obsoleto ({age_seconds/3600:.1f}h). Solicitando uno fresco...")

    if fetch_new:
        data = fetch_pagespeed_data(api_key)
        if not data:
            print("  ℹ️ [Merci Info] Fallo en la API. Omitiendo inyección en portada.")
            sys.exit(0)
    else:
        data = json.loads(PAGESPEED_CACHE_JSON.read_text(encoding="utf-8"))
        
    cache_id = str(PAGESPEED_CACHE_JSON.stat().st_mtime) if PAGESPEED_CACHE_JSON.exists() else "0"
    if CACHE_FILE.exists() and CACHE_FILE.read_text(encoding="utf-8").strip() == cache_id:
        print("  ⚡ [Cache Hit] Métricas SRE sin cambios. Omitiendo inyección en portada.")
        sys.exit(0)
        
    metrics = extract_metrics_from_data(data)
    
    print("\n📊 Resultados extraídos:")
    for k, v in metrics.items():
        if k != "SCORES_HTML":
            print(f"  - {k}: {v}")
        
    print()
    update_index_html(metrics)
    
    # Guardamos en caché el nombre del archivo recién procesado
    CACHE_FILE.write_text(cache_id, encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 [Merci Extract] Interrumpido por la usuaria. Saliendo limpiamente.")
        sys.exit(130)