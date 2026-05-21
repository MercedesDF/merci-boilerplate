
# SOP: Flujo de Publicación Dual (SSG y Headless WP)

Este documento define el Procedimiento Operativo Estándar (SOP) para la publicación de contenidos en el ecosistema híbrido **Merci Boilerplate**.

Por diseño arquitectónico (Environment Segregation), el núcleo estático (Biblioteca) y la capa dinámica (Blog/Tienda en WordPress) viven en universos separados. **Sus flujos de publicación nunca deben cruzarse.**

---

## FLUJO 1: La Biblioteca y Art de Coté (Núcleo Estático / SSG)
**Destino:** `public/biblioteca/`, `public/art-de-cote/` y `public/descargas/`
**Características:** Contenido fundacional, manuales, proyectos y arte colateral (experimentos). Genera HTML ultrarrápido y PDF descargable.

### Paso a Paso:
1. **Incubación (IA o Manual):** Volcar notas crudas en `laboratorio/notas_rapidas/` y ejecutar `merci librarian` para que la IA local estructure el documento. Todos los borradores nacen en la bandeja unificada `laboratorio/incubacion/` con `estado: "incubacion"`. Cambiar el YAML a `estado: "borrador"` cuando estén listos para ser promovidos.
2. **Curación Dinámica (Promote):** Ejecutar en la terminal:
   ```bash
   merci promote
   ```
   *Nota:* El asistente leerá el campo `tema` del YAML para enrutar mágicamente el archivo a `biblioteca/` o `art-de-cote/`. Al finalizar con éxito, **te preguntará si deseas invocar al Agente Blogger** para que genere automáticamente el post promocional y lo deje en la incubadora.
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
1. **Incubación:** Nace de la llamada automática de `merci promote` (Agent Chaining) o invocando manualmente a `merci-blogger.py`. El Blogger genera el post en `incubacion/` con `estado: "incubacion"`, `tema: "Blog"` y `estado_social: "en_cola"`. Una vez revisado, cambiar el estado a `"borrador"` y el estado social a `"aprobado"`.
2. **Curación Minimalista (Promote):** Ejecutar `merci promote`. El orquestador detectará que el tema es "Blog", ocultará las preguntas estructurales burocráticas (Alt de portada, Fase) y lo moverá a la carpeta `blog/` en la raíz.
3. **Sincronización Directa (Headless WP):** Ejecutar el publicador masivo para enviar los posts a WordPress:
   ```bash
   merci wp
   ```
   *(Nota: `merci total` lo hace automáticamente en el pipeline global).*
4. **Despliegue a Producción (Contenido Dinámico):** Para enviar los posts a la web pública, edita tu archivo `.env` y cambia el `WP_URL` a las credenciales de producción. Luego ejecuta de nuevo `merci wp`. La caché multi-entorno detectará automáticamente el cambio de destino e invalidará el registro, forzando la sincronización completa hacia producción sin necesidad de purgar nada manualmente.
5. **Gobernanza del Buffer Social (LinkedIn):** La gestión de la cola de redes es puramente declarativa a través de los archivos Markdown:
   *   **Monitorizar cola:** Ejecutar `merci queue` para visualizar qué artículos están aprobados o pendientes en el buffer.
   *   **Editar publicación:** Modificar libremente el texto dentro del bloque `<!-- linkedin: ... -->` en el archivo `.md`.
   *   **Cancelar publicación:** Borrar el valor del metadato dejándolo como `estado_social: ""` para que el orquestador lo ignore por completo.
   *   **Aprobar (Interactivo):** Ejecutar `merci linkedin`. El script muestra un menú numerado ordenado por fecha con los posts pendientes, te permite elegir cuál revisar, y tras tu confirmación (`s/N`) lo pasa a estado `"aprobado"`.
   *   **Publicar (Automático):** Una tarea programada (`merci linkedin --auto`) extraerá periódicamente el post aprobado más antiguo, lo emitirá y sellará el YAML a `"publicado_linkedin"`.

---

## ⚠️ Reglas de Oro (Hardening Operativo)

- **Prevención de Posts Fantasma (Data Drift):** Nunca borrar un archivo `.md` dinámico del disco si ya ha sido sincronizado con WordPress. En caso de eliminación física, el script Headless lo ignorará y la base de datos jamás recibirá la orden de ocultarlo. Para despublicar, cambiar su YAML a `estado: "borrador"` y ejecutar `merci wp` (El script lo ocultará del CMS y lo expulsará físicamente al laboratorio). Solo entonces se debe eliminar del entorno local.
- **Actualización de Contenidos y Fechas (El control del tiempo):** Para editar un documento ya publicado, modifica el `.md` en su carpeta de producción y ejecuta su orquestador (`merci wp` o `merci total`). El sistema lo actualizará sin duplicarlo. **Sobre la fecha:** Si mantienes el campo `fecha` original intacto, harás una *"actualización silenciosa"* (ideal para corregir erratas sin alterar el orden cronológico). Si deseas indicar que el contenido ha sido profundamente revisado o quieres que vuelva a subir al principio del blog, cambia manualmente el campo `fecha: "YYYY-MM-DD"` en el YAML Frontmatter a la fecha de hoy antes de sincronizar.
- **Prohibición de cruce:** Nunca ejecutar `merci-promote.py` sobre un archivo que ya reside en las carpetas de producción de la raíz. En caso afirmativo, el script lo enviará a la `biblioteca/` estática provocando una colisión de arquitecturas.
- **Despublicación SSG (Kill-Switch):** En caso de requerir la retirada de un artículo de la Biblioteca o Art de Coté, editar el archivo `.md` en su carpeta de producción, cambiar el YAML a `estado: "borrador"` y ejecutar `merci total`. El orquestador destruirá el HTML/PDF público y enviará el archivo de vuelta al `laboratorio/`.
- **Entorno encendido:** El *Flujo 2* requiere obligatoriamente que el servidor Nginx/MariaDB local esté encendido para poder comunicarse con la API REST de WordPress.