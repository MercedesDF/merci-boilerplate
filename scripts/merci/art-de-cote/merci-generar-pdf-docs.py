#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QUÉ HACE: Lee el manual Markdown de YAML Frontmatter y genera un PDF renderizado en la carpeta docs/.
POR QUÉ: Resuelve la necesidad de imprimir manuales estructurales internos sin obligar a la autora a procesarlos a través de la máquina de estados pública del SSG.
"""

import sys
from pathlib import Path

try:
    import markdown
    from weasyprint import HTML
except ImportError:
    print("❌ Error: Faltan las dependencias. Ejecuta 'pip install markdown weasyprint'")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"

def main():
    md_files = list(DOCS_DIR.glob("*.md"))
    if not md_files:
        print(f"❌ Error: No se encontraron archivos Markdown en {DOCS_DIR.relative_to(REPO_ROOT)}")
        sys.exit(1)

    print("📄 Archivos disponibles en docs/:")
    for i, filepath in enumerate(md_files, 1):
        print(f"  {i}. {filepath.name}")
        
    try:
        opcion = int(input("\n👉 Elige el número del archivo que quieres imprimir: "))
        if opcion < 1 or opcion > len(md_files):
            raise ValueError
    except ValueError:
        print("❌ Opción no válida. Operación abortada.")
        sys.exit(1)

    md_file = md_files[opcion - 1]
    pdf_file = md_file.with_suffix(".pdf")

    # Leer archivo y convertir Markdown a HTML crudo
    md_content = md_file.read_text(encoding="utf-8")
    html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])

    # Inyectar el CSS atómico basado en los estándares visuales de merci-boilerplate.es
    html_string = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Manual de Ciclo de Vida y Tipos YAML</title>
        <style>
            @page {{ size: A4; margin: 2.5cm; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; line-height: 1.6; color: #334155; }}
            h1, h2, h3 {{ color: #ea580c; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3em; margin-top: 1.5em; }}
            pre {{ background: #f1f5f9; padding: 1em; border-radius: 4px; white-space: pre-wrap; font-size: 0.9em; }}
            code {{ font-family: monospace; background: #f1f5f9; padding: 0.2em 0.4em; border-radius: 3px; font-size: 0.9em; }}
            ul, ol {{ margin-bottom: 1em; }}
        </style>
    </head>
    <body>{html_content}</body>
    </html>
    """

    print("🖨️  Renderizando documento PDF con WeasyPrint...")
    HTML(string=html_string).write_pdf(pdf_file)
    print(f"✅ Éxito. PDF generado listo para imprimir en: {pdf_file.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    main()