# SOP: Flujo de Publicación Dual (SSG y Headless WP)

Este documento define el Procedimiento Operativo Estándar (SOP) para la publicación de contenidos en el ecosistema híbrido **Merci Boilerplate**.

Por diseño arquitectónico (Environment Segregation), el núcleo estático (Biblioteca) y la capa dinámica (Blog/Tienda en WordPress) viven en universos separados. **Sus flujos de publicación nunca deben cruzarse.**

---

## FLUJO 1: La Biblioteca y Art de Coté (Núcleo Estático / SSG)
**Destino:** `public/biblioteca/`, `public/art-de-cote/` y `public/descargas/`
**Características:** Contenido fundacional, manuales, proyectos y arte colateral (experimentos). Genera HTML ultrarrápido y PDF descargable.

### Paso a Paso:
1. **Incubación:** Crear o editar el documento Markdown (`.md`) dentro de la carpeta `laboratorio/` o sus subdirectorios de incubación. Usar `estado: "incubacion"` para documentos en desarrollo (fricción cero en terminal) y cambiar a `estado: "borrador"` cuando estén listos para ser procesados.
2. **Curación (Promote):** Al estar listo para su publicación, ejecutar en la terminal:
   ```bash
   python3 scripts/merci/merci-promote.py
   ```
   *Nota:* El asistente interactivo validará el SEO/Accesibilidad, cambiará el estado a `"publicado"` y moverá físicamente el archivo a la carpeta de producción correspondiente (`biblioteca/` o `art-de-cote/`).
3. **Compilación y QA:** Ejecutar el orquestador maestro para transformar el Markdown en HTML/PDF, actualizar el índice y pasar la auditoría estricta:
   ```bash
   merci total
   ```
4. **Sello y Empaquetado:** Sellar la publicación añadiendo los archivos a Git (`merci commit`).

---

## FLUJO 2: Blog (WordPress Headless)
**Destino:** Base de datos de WordPress (API REST).
**Características:** Contenido dinámico, noticias, reflexiones o novedades rápidas.

### Paso a Paso:
1. **Incubación:** Crear el documento Markdown dentro de la zona de pruebas destinada al entorno dinámico (ej. `laboratorio/blog/`). Usar `estado: "incubacion"` mientras se redacta.
   *Garantizar que el YAML cambie a `estado: "publicado"` (o "borrador" según tu flujo) y tenga un `tema:` que coincida con una categoría existente en el entorno WordPress para promover.*
2. **Curación (Promote):** Ejecutar `python3 scripts/merci/merci-promote.py` para curar el documento. El script detectará el destino y moverá físicamente el archivo a su carpeta definitiva en la raíz (`blog/`).
3. **Sincronización Directa (Headless):** Ejecutar el publicador Headless para escanear y sincronizar automáticamente las carpetas dinámicas de la raíz:
   ```bash
   python3 scripts/merci/merci-wp.py
   ```
4. **Actualización y Borradores:** El script **es 100% agnóstico al entorno**. Extrae el nombre del archivo (slug) y verifica su existencia en el servidor activo configurado en el archivo `.env`. Si no existe, lo crea; si ya existe, lo actualiza limpiamente sin inyectar códigos locales.

---

## ⚠️ Reglas de Oro (Hardening Operativo)

- **Prevención de Posts Fantasma (Data Drift):** Nunca borrar un archivo `.md` dinámico del disco si ya ha sido sincronizado con WordPress. En caso de eliminación física, el script Headless lo ignorará y la base de datos jamás recibirá la orden de ocultarlo. Para despublicar, cambiar su YAML a `estado: "borrador"` y ejecutar `merci wp` (El script lo ocultará del CMS y lo expulsará físicamente al laboratorio). Solo entonces se debe eliminar del entorno local.
- **Prohibición de cruce:** Nunca ejecutar `merci-promote.py` sobre un archivo que ya reside en las carpetas de producción de la raíz. En caso afirmativo, el script lo enviará a la `biblioteca/` estática provocando una colisión de arquitecturas.
- **Despublicación SSG (Kill-Switch):** En caso de requerir la retirada de un artículo de la Biblioteca o Art de Coté, editar el archivo `.md` en su carpeta de producción, cambiar el YAML a `estado: "borrador"` y ejecutar `merci total`. El orquestador destruirá el HTML/PDF público y enviará el archivo de vuelta al `laboratorio/`.
- **Entorno encendido:** El *Flujo 2* requiere obligatoriamente que el servidor Nginx/MariaDB local esté encendido para poder comunicarse con la API REST de WordPress.