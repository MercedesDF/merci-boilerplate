#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merci-promote.py — Flujo de Promoción Laboratorio -> Biblioteca (Fase 7.3).
Herramienta interactiva de consola (CLI) para trasladar, curar y estandarizar borradores.
"""

import re
from datetime import datetime
from pathlib import Path

# 1. Definición de rutas absolutas unificadas
REPO_ROOT = Path(__file__).resolve().parents[2]
LABORATORIO_DIR = REPO_ROOT / "laboratorio"
DESTINOS_DIR = [
    REPO_ROOT / "biblioteca",
    REPO_ROOT / "blog",
    REPO_ROOT / "art-de-cote"
]

def main():
    print("🚀 [Merci Promote] Iniciando flujo de promoción de conocimiento...")

    # 2. Escaneo Global: Laboratorio (nuevos) y Directorios Raíz (despublicados / huérfanos)
    # QUÉ HACE: Usa rglob para buscar en subcarpetas, pero aplica un filtro estricto de estado YAML.
    # POR QUÉ: Evita listar bitácoras, roadmaps, prompts o notas crudas sin YAML.
    borradores_totales = []
    directorios_a_escanear = [LABORATORIO_DIR] + DESTINOS_DIR

    for dir_base in directorios_a_escanear:
        if not dir_base.exists():
            continue
        for f in dir_base.rglob("*.md"):
            # Exclusión de infraestructura (nunca se promueven)
            if f.name.startswith("bitacora-") or "ROADMAP" in f.name or "prompts" in f.parts or "historico" in f.parts or "evidencias" in f.parts:
                continue

            content = f.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)", content, flags=re.DOTALL | re.MULTILINE)
            if match:
                estado_match = re.search(r"^estado:\s*[\"']?(.*?)[\"']?\s*$", match.group(1), re.MULTILINE)
                estado = estado_match.group(1).lower() if estado_match else ""
                
                # Máquina de Estados estricta: Solo lo que dice explícitamente "borrador"
                if estado == "borrador":
                    borradores_totales.append(f)

    if not borradores_totales:
        print("  ℹ️ No se encontraron borradores pendientes de curación.")
        return

    print("\n📄 Borradores pendientes de curación:")
    for idx, f in enumerate(borradores_totales, start=1):
        # QUÉ HACE: Identifica visualmente la subcarpeta exacta de origen o si es una despublicación de la raíz.
        if LABORATORIO_DIR in f.parents:
            subcarpeta = f.parent.relative_to(LABORATORIO_DIR)
            origen = str(subcarpeta) if str(subcarpeta) != "." else "raíz"
        else:
            origen = f"Despublicado: {f.parent.name}"
        print(f"  [{idx}] {f.name} ({origen})")

    # 3. Interfaz de selección por consola
    try:
        seleccion = int(input("\n👉 Selecciona el número del borrador a promover/republicar (0 para cancelar): "))
        if seleccion == 0:
            print("  🛑 Operación cancelada.")
            return
        if seleccion < 1 or seleccion > len(borradores_totales):
            print("  ❌ Selección inválida.")
            return
    except ValueError:
        print("  ❌ Entrada inválida. Debes introducir un número.")
        return

    borrador_elegido = borradores_totales[seleccion - 1]
    # QUÉ HACE: Leemos con utf-8-sig para limpiar automáticamente el Byte Order Mark (BOM) invisible.
    contenido = borrador_elegido.read_text(encoding="utf-8-sig")

    # 4. Extracción de Metadatos usando expresiones regulares
    # Extrae el bloque entre los dos --- iniciales
    # QUÉ HACE: Expresión regular robusta y tolerante a espacios y saltos de línea irregulares.
    match = re.search(r"^\s*---\s*\n(.*?)\n---\s*(?:\n|$)(.*)", contenido, flags=re.DOTALL | re.MULTILINE)
    if not match:
        print(f"  ❌ Error: El archivo {borrador_elegido.name} no tiene un YAML Frontmatter válido.")
        print("  Por favor, añade la estructura base (plantilla) antes de promoverlo.")
        return

    yaml_raw, md_body = match.groups()
    
    # Parseo manual del YAML para evitar instalar PyYAML (Cero dependencias externas)
    meta = {}
    for linea in yaml_raw.splitlines():
        if ":" in linea:
            key, val = linea.split(":", 1)
            # Limpiamos espacios y comillas residuales
            meta[key.strip()] = val.strip().strip('"\'')

    print(f"\n⚙️ Curación de metadatos para: {meta.get('titulo', borrador_elegido.name)}")
    
    # 5. Auditoría interactiva y curación de datos (Shift-Left Quality)
    # Mostramos el valor actual por defecto. Si el usuario pulsa Enter sin escribir, se conserva.
    nuevo_tema = input(f"  🏷️  Tema/Estantería [{meta.get('tema', 'General')}]: ").strip() or meta.get('tema', 'General')
    nueva_desc = input(f"  📝 Descripción [{meta.get('descripcion', '')}]: ").strip() or meta.get('descripcion', '')
    nuevo_alt = input(f"  👁️  Alt de la portada [{meta.get('alt_portada', '')}]: ").strip() or meta.get('alt_portada', '')
    nueva_fase = input(f"  🏗️  Fase del Roadmap [{meta.get('fase', '')}]: ").strip() or meta.get('fase', '')
    
    # Al republicar, permitimos conservar la fecha original o sobreescribirla con la actual
    fecha_defecto = meta.get('fecha', '').strip()
    if not fecha_defecto or fecha_defecto == "AAAA-MM-DD" or "YYYY" in fecha_defecto:
        fecha_defecto = datetime.now().strftime("%Y-%m-%d")
        
    nueva_fecha = input(f"  📅 Fecha de publicación [{fecha_defecto}]: ").strip() or fecha_defecto

    # Bloqueo estricto si falta el atributo de accesibilidad
    if not nuevo_alt:
        print("  ❌ Error: El texto alternativo 'alt_portada' es obligatorio para mantener el 100/100 en WAI-ARIA.")
        return

    # 6. Máquina de Estados: Reconstrucción del YAML definitivo
    meta['tema'] = nuevo_tema
    meta['descripcion'] = nueva_desc
    meta['alt_portada'] = nuevo_alt
    meta['fase'] = nueva_fase
    meta['estado'] = 'publicado'  # Cambio de estado automatizado
    meta['fecha'] = nueva_fecha

    nuevo_yaml = "---\n"
    for k, v in meta.items():
        # Reinyectamos las comillas dobles para seguridad del string en YAML
        nuevo_yaml += f'{k}: "{v}"\n'
    nuevo_yaml += "---"

    # Ensamblamos el contenido final
    nuevo_contenido = f"{nuevo_yaml}\n{md_body}"

    # 7. Enrutamiento Dinámico: Determinar el destino basado en el origen
    # QUÉ HACE: Analiza la ruta relativa del archivo para saber a qué directorio pertenece.
    # POR QUÉ: Permite usar un solo script de curación para la Biblioteca (SSG) y para WordPress.
    rel_path = borrador_elegido.relative_to(REPO_ROOT)
    
    if "blog" in rel_path.parts[:-1]:
        directorio_destino = REPO_ROOT / "blog"
        comando_sugerido = "merci wp"
    elif "art-de-cote" in rel_path.parts[:-1]:
        directorio_destino = REPO_ROOT / "art-de-cote"
        comando_sugerido = "merci total"
    else:
        directorio_destino = REPO_ROOT / "biblioteca"
        comando_sugerido = "merci total"

    directorio_destino.mkdir(parents=True, exist_ok=True)
    destino = directorio_destino / borrador_elegido.name
    
    # 8. Traslado físico o Actualización In-Place
    if LABORATORIO_DIR in borrador_elegido.parents:
        destino.write_text(nuevo_contenido, encoding="utf-8")
        borrador_elegido.unlink()
        print(f"\n✅ Promoción exitosa. El archivo fue movido a: {directorio_destino.name}/{destino.name}")
    else:
        destino.write_text(nuevo_contenido, encoding="utf-8")
        print(f"\n✅ Republicación exitosa. El borrador fue actualizado en: {directorio_destino.name}/{destino.name}")
        
    print(f"  💡 Siguiente paso: Ejecuta '{comando_sugerido}' para aplicar los cambios.")

if __name__ == "__main__":
    main()