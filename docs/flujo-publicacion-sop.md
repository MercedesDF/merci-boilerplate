
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
4. **Despliegue a Producción (Contenido Dinámico):** Añade las variables `WP_PROD_URL`, `WP_PROD_USER` y `WP_PROD_APP_PASSWORD` a tu archivo `.env`. Al ejecutar `merci deploy` (o `merci completo`), el orquestador leerá estas variables temporalmente en memoria y enviará los artículos a producción sin que tengas que modificar tu archivo `.env` a mano, validando la caché multi-entorno automáticamente.
5. **Gobernanza del Buffer Social (LinkedIn):** La gestión de la cola de redes es puramente declarativa a través de los archivos Markdown:
   *   **Monitorizar cola:** Ejecutar `merci queue` para visualizar qué artículos están aprobados o pendientes en el buffer.
   *   **Editar publicación:** Modificar libremente el texto dentro del bloque `<!-- linkedin: ... -->` en el archivo `.md`.
   *   **Cancelar publicación:** Borrar el valor del metadato dejándolo como `estado_social: ""` para que el orquestador lo ignore por completo.
   *   **Aprobar (Interactivo):** Ejecutar `merci linkedin`. El script muestra un menú numerado ordenado por fecha con los posts pendientes, te permite elegir cuál revisar, y tras tu confirmación (`s/N`) lo pasa a estado `"aprobado"`.
   *   **Publicar (Automático):** Una tarea programada (`merci linkedin --auto`) extraerá periódicamente el post aprobado más antiguo, lo emitirá y sellará el YAML a `"publicado_linkedin"`.

---

## FLUJO 3: Tienda (WooCommerce Headless)
**Destino:** API REST de WooCommerce.
**Características:** Catálogo de productos (Mock E-commerce), gestionado mediante archivos Markdown con metadatos de precio e imagen.

### Paso a Paso:
1. **Incubación:** Crear un producto en `laboratorio/incubacion/` con `tema: "tienda"` y metadatos obligatorios como `precio` y `imagen`. Cambiar su estado a `"borrador"`.
2. **Promoción:** Ejecutar `merci promote`. El sistema lo detectará automáticamente por sus variables y lo moverá al directorio raíz `/tienda/`.
3. **Sincronización Headless:** Ejecutar el orquestador de la tienda:
   ```bash
   merci shop
   ```
   *(Nota: El script creará o actualizará el producto resolviéndolo por su slug. Si un producto en `/tienda/` vuelve a estado `"borrador"`, `merci shop` ejecutará el Kill-Switch, eliminándolo de WooCommerce mediante Hard Delete para prevenir colisiones WAI-ARIA, y devolviendo el archivo a la incubadora).*

---

## FLUJO 4: Release y Showcase (Boilerplate)
**Destino:** Repositorio público (`merci-boilerplate`) y Subdominio de demostración (`boilerplate.tu_dominio.com`).
**Características:** Generación de clones efímeros aislados para distribución y demostración, purgando metadatos de identidad (DLP) y rompiendo cachés estáticas persistentes.

### Paso a Paso (Showcase):
1. **Despliegue Interactivo:** Ejecutar `merci showcase`.
2. **Orquestación:** El script crea un Clon Efímero en memoria, purga toda la identidad corporativa mediante la inyección del Patrón Gemelo Multimedia (sustituye logotipos y avatares) y elimina el menú de Art de Coté.
3. **Invalidación de Caché (Zero-Stale):** Para evitar que el servidor Nginx muestre imágenes fantasma (por su caché de 10 años), el orquestador inyecta un *Timestamp Unix* dinámico en los reemplazos multimedia.
4. **Sincronización:** El código resultante (purificado y anónimo) se sincroniza vía SSH/rsync al servidor en el subdominio de demostración.

### Paso a Paso (Release Público):
1. **Empaquetado:** Ejecutar `merci release`.
2. **Clon Efímero:** El script crea el clon y lo purga internamente, igual que el Showcase.
3. **Sincronización Local:** En lugar de enviarlo a un servidor remoto, sincroniza el código resultante en la ruta del repositorio público hermano local (ej. `../merci-boilerplate`).
4. **Validación:** Ejecuta un `merci total` completo en el repositorio destino para asegurar que el código no se ha roto.
5. **Git Push:** Finalmente, empaqueta y hace un commit con la nueva versión detectada en el README, subiéndolo a GitHub.

---

## ⚠️ Reglas de Oro (Hardening Operativo)

- **Prevención de Posts Fantasma (Data Drift):** Nunca borrar un archivo `.md` dinámico del disco si ya ha sido sincronizado con WordPress. En caso de eliminación física, el script Headless lo ignorará y la base de datos jamás recibirá la orden de ocultarlo. Para despublicar, cambiar su YAML a `estado: "borrador"` y ejecutar `merci wp` (El script lo ocultará del CMS y lo expulsará físicamente al laboratorio). Solo entonces se debe eliminar del entorno local.
- **Actualización de Contenidos y Fechas (El control del tiempo):** Para editar un documento ya publicado, modifica el `.md` en su carpeta de producción y ejecuta su orquestador (`merci wp` o `merci total`). El sistema lo actualizará sin duplicarlo. **Sobre la fecha:** Si mantienes el campo `fecha` original intacto, harás una *"actualización silenciosa"* (ideal para corregir erratas sin alterar el orden cronológico). Si deseas indicar que el contenido ha sido profundamente revisado o quieres que vuelva a subir al principio del blog, cambia manualmente el campo `fecha: "YYYY-MM-DD"` en el YAML Frontmatter a la fecha de hoy antes de sincronizar.
- **Prohibición de cruce:** Nunca ejecutar `merci-promote.py` sobre un archivo que ya reside en las carpetas de producción de la raíz. En caso afirmativo, el script lo enviará a la `biblioteca/` estática provocando una colisión de arquitecturas.
- **Despublicación SSG (Kill-Switch):** En caso de requerir la retirada de un artículo de la Biblioteca o Art de Coté, editar el archivo `.md` en su carpeta de producción, cambiar el YAML a `estado: "borrador"` y ejecutar `merci total`. El orquestador destruirá el HTML/PDF público y enviará el archivo de vuelta al `laboratorio/`.
- **Entorno encendido:** El *Flujo 2* requiere obligatoriamente que el servidor Nginx/MariaDB local esté encendido para poder comunicarse con la API REST de WordPress.