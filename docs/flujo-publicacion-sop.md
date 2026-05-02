# SOP: Flujo de Publicación Dual (SSG y Headless WP)

Este documento define el Procedimiento Operativo Estándar (SOP) para la publicación de contenidos en el ecosistema híbrido **Merci Boilerplate**.

Por diseño arquitectónico (Environment Segregation), el núcleo estático (Biblioteca) y la capa dinámica (Blog/Tienda en WordPress) viven en universos separados. **Sus flujos de publicación nunca deben cruzarse.**

---

## FLUJO 1: La Biblioteca (Núcleo Estático / SSG)
**Destino:** `public/biblioteca/` y `public/descargas/`
**Características:** Contenido fundacional, manuales y proyectos. Genera HTML ultrarrápido y PDF descargable.

### Paso a Paso:
1. **Incubación:** Crea o edita tu documento Markdown (`.md`) dentro de la carpeta `laboratorio/`. Su YAML Frontmatter debe tener `estado: "borrador"`.
2. **Curación (Promote):** Cuando esté listo para publicarse, ejecuta en la terminal:
   ```bash
   python3 scripts/merci/merci-promote.py
   ```
   *Nota:* El asistente interactivo validará el SEO/Accesibilidad, cambiará el estado a `"publicado"` y moverá físicamente el archivo a la carpeta `biblioteca/`.
3. **Compilación y QA:** Ejecuta el orquestador maestro para transformar el Markdown en HTML/PDF, actualizar el índice y pasar la auditoría estricta:
   ```bash
   merci total
   ```
4. **Sello y Empaquetado:** Sella la publicación subiendo los archivos a Git (`merci commit`).

---

## FLUJO 2: Blog y Art de Coté (WordPress Headless)
**Destino:** Base de datos de WordPress (API REST).
**Características:** Contenido dinámico, artículos colaterales, reflexiones o novedades.

### Paso a Paso:
1. **Incubación:** Crea tu documento Markdown dentro de tu zona de pruebas (ej. `laboratorio/blog/` o `laboratorio/art-de-cote/`). 
   *Asegúrate de que el YAML tenga `estado: "publicado"` y un `tema:` que coincida con una categoría que ya exista en tu WordPress.*
2. **Curación (Promote):** Ejecuta `python3 scripts/merci/merci-promote.py` para curar el documento. El script detectará el destino y moverá físicamente el archivo a su carpeta definitiva en la raíz (`blog/` o `art-de-cote/`).
3. **Sincronización Directa (Headless):** Ejecuta el publicador Headless para escanear y sincronizar automáticamente todas las carpetas dinámicas de la raíz:
   ```bash
   python3 scripts/merci/merci-wp.py
   ```
4. **Actualización y Borradores:** El script **es 100% agnóstico al entorno**. Leerá el nombre de tu archivo (slug) y preguntará al servidor activo en tu `.env` si existe. Si no existe, lo crea. Si ya existe, lo actualiza limpiamente sin inyectar códigos locales.

---

## ⚠️ Reglas de Oro (Hardening Operativo)

- **Prevención de Posts Fantasma (Data Drift):** Nunca borres un archivo `.md` dinámico de tu disco duro si ya ha sido sincronizado con WordPress. Si lo eliminas, el script Headless lo ignorará y la base de datos jamás recibirá la orden de ocultarlo. Para despublicar, cambia su YAML a `estado: "borrador"` y ejecuta `merci wp` (El script lo ocultará del CMS y lo expulsará físicamente al laboratorio). Solo entonces puedes eliminarlo de tu ordenador.
- **Prohibición de cruce:** Nunca ejecutes `merci-promote.py` sobre un archivo que ya reside en las carpetas de producción de la raíz. Si lo haces, el script lo enviará a la `biblioteca/` estática provocando una colisión de arquitecturas.
- **Despublicación SSG (Kill-Switch):** Si necesitas retirar un artículo de la Biblioteca, edita su `.md` en la carpeta `biblioteca/`, cambia el YAML a `estado: "borrador"` y ejecuta `merci total`. El orquestador destruirá el HTML/PDF público y enviará el archivo de vuelta al `laboratorio/`.
- **Entorno encendido:** El *Flujo 2* requiere obligatoriamente que el servidor Nginx/MariaDB local esté encendido para poder comunicarse con la API REST de WordPress.