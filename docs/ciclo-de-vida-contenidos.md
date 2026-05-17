# Gestión de Tipos y Metadatos YAML (El Motor de Enrutamiento)

Este documento explica cómo el *YAML Frontmatter* actúa como el "volante" del ecosistema Merci. Dependiendo de las variables declaradas aquí, los agentes de Python saben cómo maquetar el documento, a qué base de datos enviarlo y cuándo publicarlo.

## 1. Anatomía del YAML (El DNI del Documento)

*   `titulo`: El nombre humano. *El motor SSG lo convierte automáticamente en URL (ej. `mi-titulo.html`).*
*   `descripcion`: Se inyecta en la etiqueta `<meta name="description">` y en el JSON-LD para el SEO, y sirve de resumen en las tarjetas.
*   `tipo`: Define el diseño CSS (Metodología BEM). 
    *   `"cuadernillo"`: Se le aplica la clase `.card--booklet` (diseño fluido azul). 
    *   `"proyecto"` o `"compendio"`: Se aplica `.card--book` (diseño sólido verde). 
    *   `"articulo"`: Diseño ligero para el blog. WordPress le quita los bordes pesados.
*   `tema`: **El Enrutador Maestro**. 
    *   Si contiene `"Art de Coté"`, el orquestador lo manda a esa sección estática.
    *   Si contiene `"Blog"`, va destinado a WordPress.
    *   Si pones cualquier otra cosa (ej. `"DevSecOps"`), va a la **Biblioteca** y el SSG crea una estantería nueva automáticamente con ese nombre.
*   `fecha`: Ordena los artículos. El orquestador la actualiza sola con `datetime.now()`.
*   `estado`: La llave de paso (Kill-Switch). 
    *   `"incubacion"`: Invisible para todos.
    *   `"borrador"`: Listo para ser promovido.
    *   `"publicado"`: Live en la web.
*   `estado_social`: La válvula del Buffer de LinkedIn. 
    *   `"en_cola"`: Pendiente de tu revisión humana.
    *   `"aprobado"`: Listo para que el robot (cronjob) lo dispare.
    *   `"publicado_linkedin"`: Ya emitido en la red.
*   `alt_portada`: El escudo WAI-ARIA. Si está vacío en la capa estática, el auditor bloquea la compilación para mantener el 100/100 de accesibilidad.

---

## 2. El Flujo de Trabajo Completo (Ciclo de Vida)

### A. El Flujo Estático (Biblioteca / Art de Coté)
1. **Nacimiento:** Echas una idea cruda en `laboratorio/notas_rapidas`. La IA (`merci librarian`) redacta el documento, le pone `estado: "incubacion"` y lo deja en `laboratorio/incubacion/`.
2. **Maduración:** Lo revisas. Si te gusta, cambias a `estado: "borrador"`.
3. **Curación:** Ejecutas `merci promote`. El script lee el YAML, ve que el *tema* es "DevSecOps" y mueve físicamente el archivo a `/biblioteca/`. Lo sella como `publicado`.
4. **Compilación:** Ejecutas `merci total`. Python convierte el Markdown a HTML, genera el PDF, inyecta el SEO, crea la estantería y lo sube.

### B. El Flujo Dinámico (Blog en WordPress)
1. **Marketing:** La IA (`merci blogger`) crea el artículo de marketing en `incubacion/` con tema "Blog" a partir de otro post técnico. Lo pasas a `borrador`.
2. **Curación Ligera:** Ejecutas `merci promote`. El script lo mueve a la carpeta `/blog/` en la raíz local.
3. **Sincronización API:** Ejecutas `merci wp` (o `merci total`). Python dialoga con WordPress, sube el artículo y **escribe el `wp_id`** dentro del YAML de tu archivo para mantenerlos gemelos para siempre.

### C. El Flujo Social (LinkedIn)
1. **Aprobación (Humano):** Ejecutas `merci linkedin`. El script te muestra los posts `en_cola` y te pregunta si están bien. Si dices que sí, los cambia a `aprobado`.
2. **Disparo (Robot):** Una tarea automática de Ubuntu (`cron`) ejecuta `merci linkedin --auto` cada varios días. Coge un post `aprobado`, lo publica en LinkedIn, y lo sella como `publicado_linkedin`.

---

*Nota Arquitectónica: Todo documento Markdown es la Única Fuente de Verdad (SSOT). Si se quiere retirar un artículo de la web (o de WP), basta con cambiar `estado: "borrador"` en su YAML y ejecutar `merci total`. El sistema se encargará de purgar los HTML/PDFs públicos o lanzar la petición DELETE a la API correspondiente y devolver el archivo físico al Laboratorio.*