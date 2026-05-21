# Directrices Base: Merci Boilerplate

Este documento define las reglas de arquitectura e interacción de esta plantilla. Todo desarrollo construido sobre este código base debe respetar estos principios.

## 1. Filosofía del Proyecto
- **Rendimiento > Todo:** Prioridad absoluta a los Core Web Vitals (100/100).
- **Trazabilidad del Error:** Cada problema técnico se documenta en `laboratorio/bitacora-merci-boilerplate.md` usando 3 átomos: Desafío (Síntoma) -> Maniobra (Lógica) -> Aprendizaje.

## 2. Stack Tecnológico y Arquitectura
- **Núcleo Estático:** HTML5 semántico, SASS 7-1 (BEM (Block, Element, Modifier - Modificador de Elemento de Bloque)) compilado localmente y Vanilla JS (0 dependencias).
- **Sistema "Merci":** Automatización local DevSecOps basada en scripts puros de Python 3.10+ en la carpeta `/scripts/merci/`.
  - `merci-audit.py`: Auditoría estática y bloqueo de secretos.
  - `merci-auto-fix.py`: Agente autónomo de auto-reparación.
  - `merci-commit.py`: Empaquetado atómico de commits.
  - `merci-total.py`: Orquestador maestro del pipeline.
  - `merci-brain.py`: Lóbulo frontal de Inteligencia Artificial.
  - `merci-ssot.py`: Curación autónoma de la deriva documental.
  - `merci-librarian.py`: Agente Bibliotecario (Zero-Hallucination).
  - `merci-glosario.py`: Compilador de Glosario Autónomo.
  - `merci-blogger.py`: Agente Redactor DevRel.
  - `merci-publish.py` y `merci-promote.py`: Motor SSG y promoción de contenidos.
  - `merci-sync-pages.py`: Sincronizador de estructuras comunes estáticas.
  - `merci-sitemap.py` y `merci-linkcheck.py`: Rastreador dinámico (DAST) y mapa XML.
  - `merci-backup.py`: Generador de instantáneas.
  - `merci-init.py`: Inicializador destructivo.
  - `merci-linkedin.py`: Publicación en LinkedIn.
  - `merci-wp.py`: Sincronizador Headless para WordPress.
  - `merci-extract-metrics.py`: Extractor automatizado de métricas.
  - `merci-telemetry.py`: Inyector dinámico de telemetría.
  - `merci-styles.py` y `merci-watcher.py`: Compilador SASS local.
  - `merci-optimizer.py` y `merci-assets-watcher.py`: Procesamiento WebP.
  - `merci-sre.py`: Telemetría pasiva para Prometheus y Grafana.
  - `merci-hardening.py`: Auditoría continua de seguridad.
  - `merci-chaos.py`: Chaos Engineering con IA local.
  - `merci-drift.py`: Detector de Deriva Documental.
  - `merci-queue.py`: Visor de terminal interactivo para el buffer social.
- **Capa Dinámica:** WordPress aislado (`/blog`) sirviendo como CMS (Content Management System - Sistema de Gestión de Contenidos) headless bajo Nginx proxy inverso, sin invadir `/public`.

## 3. Reglas de Interacción y Código
1. **Seguridad Shift-Left:** Todo el código debe pasar obligatoriamente por `python3 scripts/merci/merci-audit.py` antes del commit. Cualquier cadena inyectada dinámicamente en el HTML debe ser sanitizada previamente (`html.escape`) para evitar ataques XSS y roturas del DOM (Document Object Model - Modelo de Objetos del Documento).
2. **Manejo de Errores:** Todo código debe incluir gestión de excepciones para evitar colapsos silentes.
3. **Bitácora Obligatoria:** `merci-commit.py` bloqueará los empaquetados si no se ha documentado el cambio cronológicamente en la bitácora del laboratorio.
4. **Copias de Seguridad (Disaster Recovery):** Utilizar `python3 scripts/merci/merci-backup.py` antes de cualquier operación destructiva o reescritura de historial.
5. **Convención de Commits:** Utilizar prefijos semánticos (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `perf:`).
6. **Aislamiento de WordPress:** El CMS nunca debe escribir ni modificar archivos en el directorio `/public`. Su comunicación con el frontend es unidireccional y controlada por Nginx.
7. **Filosofía de Dependencias:**
   - **Runtime (Navegador):** 0 dependencias externas. Prohibido inyectar librerías JS o CSS externas.
   - **Build-time (Pipeline):** Se permiten librerías Python para automatización, auditoría y compilación. Estas deben gestionarse siempre dentro de un entorno virtual (`.venv`) y estar declaradas en `requirements.txt`.
8. **Higiene de Importaciones (PEP 8):** Todas las importaciones en scripts Python deben declararse estrictamente al principio del archivo. Queda terminantemente prohibido realizar importaciones en medio del código.
9. **Blindaje Supply Chain (Cadena de Suministro):** La regla `audit_python_imports` del auditor valida mediante AST (Abstract Syntax Tree - Árbol de Sintaxis Abstracta) que todas las importaciones pertenezcan a la `stdlib` o a la lista blanca de `requirements.txt`. No incluir librerías no declaradas.

## 4. Flujo Maestro de Publicación (SOP Dual)
El ecosistema cuenta con un flujo estático (SSG) y otro dinámico (Headless WP).

**Para la Biblioteca (Núcleo Estático):**
1. **Sincronización:** `git pull` para evitar conflictos con el servidor remoto.
2. **Incubación:** Crear un `.md` en `laboratorio/incubacion/` con `estado: "incubacion"`. Una vez revisado, cambiar a `estado: "borrador"`.
3. **Curación:** Ejecutar `python3 scripts/merci/merci-promote.py` para curarlo y moverlo a la `biblioteca/`.
4. **QA y Compilación:** Ejecutar `python3 scripts/merci/merci-total.py` (compila SSG, sincroniza páginas y audita el código resultante).

**Para WordPress (Capa Dinámica):**
1. **Incubación:** Crear un `.md` en `laboratorio/` con un `tema:` válido en tu WP.
2. **Curación:** Ejecutar `merci-promote.py` para moverlo a las carpetas dinámicas de la raíz.
3. **Sincronización:** Ejecutar `python3 scripts/merci/merci-wp.py` para publicarlo masivamente vía API REST (Resolución dinámica por slug, cero inyecciones locales).
4. **Despublicación:** Cambiar a `estado: "borrador"` y re-ejecutar el script expulsará el archivo de vuelta al laboratorio.

## 5. Decisiones Arquitectónicas Restringidas
- **Cero dependencias visuales:** Prohibido el uso de librerías de animación de terceros o frameworks reactivos (Vue/React/Tailwind) en el frontend.
- **Accesibilidad Nativa:** Toda la UI (User Interface - Interfaz de Usuario) debe ser navegable mediante Tabulador y usar etiquetas semánticas (WAI-ARIA).
- **Focus Management:** No se debe usar `tabindex="-1"` en el `body`.
- **Enrutamiento Visual Zero-JS:** El resaltado de enlaces activos se maneja exclusivamente a través de CSS mediante el uso semántico del atributo `id` de la etiqueta `<body>`.
- **Caché Multi-Entorno (Headless WP):** El archivo `observabilidad/.wp_sync.json` almacena la clave `_entorno` (valor del `WP_URL`). Al cambiar el entorno en `.env`, la caché se invalida automáticamente. No purgar el JSON manualmente salvo en el primer arranque de un proyecto nuevo.

## 6. Protocolo Estricto de Cierre de Fase (Definition of Done)
Antes de dar por concluida una funcionalidad mayor o transicionar a un nuevo hito, se recomienda ejecutar este checklist para asegurar la higiene del repositorio:

1. **Conciliación de Deuda Técnica:** ¿Queda algún `TODO` en el código o un error silenciado temporalmente? Se deben resolver o registrar en la bitácora.
2. **Cosecha de Conocimiento:** Extraer los desafíos superados y lecciones aprendidas hacia la bitácora.
3. **Auditoría Documental:** Asegurar que el `README.md` y las directrices reflejan las nuevas herramientas o arquitecturas creadas.
4. **Snapshot (Backup Local):** Generar una copia de seguridad (`merci-backup.py`) para tener un punto de restauración garantizado.
5. **Sello Definitivo:** Una vez confirmados los 4 puntos anteriores, realizar el commit atómico de cierre.

---
Cualquier colaborador que herede este repositorio debe leer este documento antes de solicitar integraciones o añadir dependencias externas.