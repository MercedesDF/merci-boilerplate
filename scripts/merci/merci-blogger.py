#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-blogger.py — Agente Redactor DevRel (Fase 1: Motor de Difusión).
Transforma notas crudas en artículos atractivos para el blog y
redacta el anuncio para LinkedIn, dejándolo "en_cola" para la difusión asíncrona.
"""

import sys
import re
from datetime import datetime
from pathlib import Path

try:
    from litellm import completion
    import litellm
    litellm.telemetry = False
    litellm.suppress_debug_info = True
except ImportError:
    print("❌ [Merci Blogger] Falta 'litellm'. Instálalo con: pip install litellm")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO_ROOT / "laboratorio" / "prompts" / "prompt-blogger.md"
NOTAS_DIR = REPO_ROOT / "laboratorio" / "notas_rapidas"
INCUBACION_DIR = REPO_ROOT / "laboratorio" / "incubacion"

def slugify(texto: str) -> str:
    import unicodedata
    texto = str(texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

def main():
    print("✍️  [Merci Blogger] Iniciando Agente Redactor de Marketing...")
    
    if not PROMPT_PATH.exists():
        print(f"❌ Error: No se encuentra el cerebro del agente en {PROMPT_PATH.name}")
        sys.exit(1)
        
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    system_prompt = system_prompt.replace("{fecha}", datetime.now().strftime("%Y-%m-%d"))
    
    NOTAS_DIR.mkdir(parents=True, exist_ok=True)
    INCUBACION_DIR.mkdir(parents=True, exist_ok=True)
    
    # QUÉ HACE: Acepta un archivo por argumento (encadenamiento de agentes) o busca notas manuales.
    if len(sys.argv) > 1:
        nota_elegida = Path(sys.argv[1]).resolve()
        if not nota_elegida.exists():
            print(f"  ❌ Error: El documento origen '{nota_elegida.name}' no existe.")
            sys.exit(1)
    else:
        print("\n  ¿De dónde quieres extraer el contenido base para el post?")
        print("  [1] Notas Rápidas (laboratorio/notas_rapidas) [Defecto]")
        print("  [2] Biblioteca (biblioteca/)")
        print("  [3] Art de Coté (art-de-cote/)")
        
        opcion = input("  👉 Elige una opción [1]: ").strip() or "1"
        
        if opcion == "2":
            target_dir = REPO_ROOT / "biblioteca"
            notas = sorted(list(target_dir.rglob("*.md")), key=lambda x: x.name)
        elif opcion == "3":
            target_dir = REPO_ROOT / "art-de-cote"
            notas = sorted(list(target_dir.rglob("*.md")), key=lambda x: x.name)
        else:
            target_dir = NOTAS_DIR
            notas = sorted([f for f in target_dir.glob("*") if f.is_file() and f.name != ".gitkeep"], key=lambda x: x.name)
            
        if not notas:
            print(f"  🤷‍♀️ No hay documentos en {target_dir.relative_to(REPO_ROOT)}.")
            sys.exit(0)
            
        print(f"\n  📄 Documentos disponibles en {target_dir.name}:")
        for i, nota in enumerate(notas, 1):
            print(f"    {i}. {nota.name}")
            
        try:
            seleccion = int(input("\n  👉 Elige el número del documento a procesar (0 para salir): ").strip())
            if seleccion == 0: return
            nota_elegida = notas[seleccion - 1]
        except (ValueError, IndexError):
            print("  ❌ Selección inválida.")
            sys.exit(1)
        
    nota_contenido = nota_elegida.read_text(encoding="utf-8")
    if not nota_contenido.strip():
        print("  ❌ La nota está vacía.")
        sys.exit(1)
        
    # LÓGICA CONDICIONAL: Adaptamos el comportamiento según el origen del documento
    es_nota_rapida = nota_elegida.is_relative_to(NOTAS_DIR)
    
    if not es_nota_rapida and nota_elegida.suffix == '.md':
        meta_titulo = re.search(r'^titulo:\s*["\']?([^"\'\n]+)["\']?', nota_contenido, re.MULTILINE)
        meta_tema = re.search(r'^tema:\s*["\']?([^"\'\n]+)["\']?', nota_contenido, re.MULTILINE)
        
        if meta_titulo:
            titulo_doc = meta_titulo.group(1)
            tema = meta_tema.group(1).lower() if meta_tema else ""
            
            # Determinamos la URL canónica real basándonos en el tema o la ruta física
            if "art de cot" in tema or "art-de-cote" in tema or "art-de-cote" in nota_elegida.parts:
                base_path = "/art-de-cote/"
            else:
                base_path = "/biblioteca/"
                
            url_promocion = f"{base_path}{slugify(titulo_doc)}.html"
            nota_contenido += f"\n\n--- INSTRUCCIÓN EXTRA INNEGOCIABLE ---\nEl documento original ya está publicado o en proceso. DEBES incluir este enlace exacto al final de tu artículo invitando al lector a leerlo completo: {url_promocion}"
    elif es_nota_rapida:
        nota_contenido += "\n\n--- INSTRUCCIÓN EXTRA INNEGOCIABLE ---\nEste es un artículo INDEPENDIENTE y directo. Termina el post con una conclusión fuerte o una pregunta a la comunidad. NO invites a leer más información en la biblioteca porque no existe."

    print(f"\n  🧠 Redactando artículo a partir de '{nota_elegida.name}'...")
    
    print("  🏠 Consultando a motor local (Ollama - qwen2.5-coder)...")
    try:
        respuesta = completion(
            model="ollama/qwen2.5-coder",
            api_base="http://localhost:11434",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": nota_contenido}
            ],
            temperature=0.6,
            max_tokens=3000
        )
        respuesta_texto = respuesta.choices[0].message.content
    except Exception as e:
        print(f"  ❌ Error en motor local: {e}")
        sys.exit(1)
            
    # Limpieza de bloque de código Markdown residual
    if respuesta_texto.startswith("```markdown"):
        respuesta_texto = respuesta_texto[11:]
    if respuesta_texto.endswith("```"):
        respuesta_texto = respuesta_texto[:-3]
    respuesta_texto = respuesta_texto.strip()
    
    # Limpieza estricta: Amputar texto conversacional antes del YAML Frontmatter
    inicio_yaml = respuesta_texto.find("---\n")
    if inicio_yaml != -1:
        respuesta_texto = respuesta_texto[inicio_yaml:]
    
    # Autonombrado (Slugify)
    titulo_match = re.search(r'^titulo:\s*["\']?([^"\'\n]+)["\']?', respuesta_texto, re.MULTILINE)
    titulo = titulo_match.group(1) if titulo_match else "articulo-generado"
    filename = "blog-" + slugify(titulo) + ".md"
    
    # ESCUDO ANTI-DUPLICIDAD: Evitar generar marketing redundante
    post_en_produccion = REPO_ROOT / "blog" / filename
    if post_en_produccion.exists():
        print(f"\n  🛑 [Escudo DevRel] Operación abortada.")
        print(f"  Ya existe un post promocional publicado en: {post_en_produccion.relative_to(REPO_ROOT)}")
        print(f"  👉 Si quieres relanzarlo a redes, edita ese archivo cambiando `estado_social: \"aprobado\"`.")
        sys.exit(0)
    elif (INCUBACION_DIR / filename).exists():
        print(f"\n  ⚠️ Nota: Ya existe un borrador llamado '{filename}' en incubación. Se sobrescribirá.")

    # BARRERA SOCIAL: Preguntar si encolamos en LinkedIn
    while True:
        respuesta_encolar = input("\n  👉 ¿Quieres añadir este post a la cola automática de LinkedIn? (s/N): ").strip().lower()
        if respuesta_encolar in ['s', 'n', '']:
            encolar = (respuesta_encolar == 's')
            break
        print("  ❌ Opción no válida. Por favor, responde con 's' o 'n'.")
        
    estado_soc_val = "en_cola" if encolar else "ignorado"
    
    # QUÉ HACE: Fuerza matemáticamente los estados YAML con Regex.
    # POR QUÉ: Evita que alucinaciones de la IA (ej. escribir 'promoción') rompan las máquinas de estado.
    respuesta_texto = re.sub(r'^estado:\s*["\']?[^"\'\n]*["\']?', 'estado: "incubacion"', respuesta_texto, flags=re.MULTILINE)
    if re.search(r'^estado_social:', respuesta_texto, re.MULTILINE):
        respuesta_texto = re.sub(r'^estado_social:\s*["\']?[^"\'\n]*["\']?', f'estado_social: "{estado_soc_val}"', respuesta_texto, flags=re.MULTILINE)
    else:
        respuesta_texto = re.sub(r'(^estado:\s*["\']?incubacion["\']?)', rf'\1\nestado_social: "{estado_soc_val}"', respuesta_texto, flags=re.MULTILINE)

    # FUERZA MATEMÁTICA: Aseguramos que el post vaya destinado a WordPress
    if re.search(r'^tema:', respuesta_texto, re.MULTILINE):
        respuesta_texto = re.sub(r'^tema:\s*["\']?[^"\'\n]*["\']?', 'tema: "Blog"', respuesta_texto, flags=re.MULTILINE)
    else:
        respuesta_texto = re.sub(r'(^estado:\s*["\']?incubacion["\']?)', r'\1\ntema: "Blog"', respuesta_texto, flags=re.MULTILINE)

    out_path = INCUBACION_DIR / filename
    out_path.write_text(respuesta_texto, encoding="utf-8")
    
    if encolar:
        print(f"\n  ✅ ¡Artículo redactado con éxito y post encolado!")
    else:
        print(f"\n  ✅ ¡Artículo redactado con éxito (no encolado en LinkedIn)!")
    print(f"  📁 Guardado en: {out_path.relative_to(REPO_ROOT)}")

    # Solo archiva la nota original si venía de la carpeta de notas crudas
    if es_nota_rapida:
        archivo_dir = NOTAS_DIR / "_procesadas"
        archivo_dir.mkdir(exist_ok=True)
        nota_elegida.rename(archivo_dir / nota_elegida.name)
        print(f"  🧹 Nota original movida a: {archivo_dir.relative_to(REPO_ROOT)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  🛑 Cancelado por el usuario.")