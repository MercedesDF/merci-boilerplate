# Directrices Base: Merci Boilerplate

Este documento define las reglas de arquitectura e interacción de esta plantilla. Todo desarrollo construido sobre este código base debe respetar estos principios.

## 1. Filosofía del Proyecto
- **Rendimiento > Todo:** Prioridad absoluta a los Core Web Vitals (100/100).
- **Trazabilidad del Error:** Cada problema técnico se documenta en `laboratorio/bitacora-merci-boilerplate.md` usando 3 átomos: Desafío (Síntoma) -> Maniobra (Lógica) -> Aprendizaje.

## 2. Stack Tecnológico y Arquitectura
- **Núcleo Estático:** HTML5 semántico, SASS 7-1 (BEM (Block, Element, Modifier - Modificador de Elemento de Bloque)) compilado localmente y Vanilla JS (0 dependencias).
- **Sistema "Merci":** Automatización local DevSecOps basada en scripts puros de Python 3.10+ en la carpeta `/scripts/merci/`.
- **Capa Dinámica:** WordPress aislado (`/blog`) sirviendo como CMS (Content Management System - Sistema de Gestión de Contenidos) headless bajo Nginx proxy inverso, sin invadir `/public`.

## 3. Reglas de Interacción y Código
1. **Seguridad Shift-Left:** Todo el código debe pasar obligatoriamente por `python3 scripts/merci/merci-audit.py` antes del commit.
2. **Manejo de Errores:** Todo código debe incluir gestión de excepciones para evitar colapsos silentes.
3. **Bitácora Obligatoria:** `merci-commit.py` bloqueará los empaquetados si no se ha documentado el cambio cronológicamente en la bitácora del laboratorio.
4. **Copias de Seguridad (Disaster Recovery):** Utilizar `python3 scripts/merci/merci-backup.py` antes de cualquier operación destructiva o reescritura de historial.
5. **Convención de Commits:** Utilizar prefijos semánticos (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `perf:`).
6. **Aislamiento de WordPress:** El CMS nunca debe escribir ni modificar archivos en el directorio `/public`. Su comunicación con el frontend es unidireccional y controlada por Nginx.

## 4. Flujo Maestro de Publicación de Contenidos (SOP)
El ecosistema cuenta con su propio SSG (Static Site Generation - Generación de Sitios Estáticos). Para publicar artículos en la Biblioteca estática:
1. **Sincronización:** `git pull` para evitar conflictos con el servidor remoto.
2. **Incubación:** Crear archivo Markdown con YAML Frontmatter en `laboratorio/`.
3. **Curación:** Ejecutar `python3 scripts/merci/merci-promote.py` para auditar accesibilidad (WAI-ARIA - Web Accessibility Initiative - Accessible Rich Internet Applications) y moverlo a la Biblioteca (soporta subcarpetas temáticas).
4. **Compilación:** Ejecutar `python3 scripts/merci/merci-publish.py` para compilar el HTML (con auto-nombrado de URL) y generar los PDFs.
5. **QA Total:** Ejecutar `python3 scripts/merci/merci-total.py` para validar SEO (Search Engine Optimization - Optimización para Motores de Búsqueda), enlaces rotos y compilar SASS.
6. **Trazabilidad:** Documentar los cambios en `laboratorio/bitacora-merci-boilerplate.md`.
7. **Empaquetado:** Sellar atómicamente con `python3 scripts/merci/merci-commit.py`.

## 5. Decisiones Arquitectónicas Restringidas
- **Cero dependencias visuales:** Prohibido el uso de librerías de animación de terceros o frameworks reactivos (Vue/React/Tailwind) en el frontend.
- **Accesibilidad Nativa:** Toda la UI (User Interface - Interfaz de Usuario) debe ser navegable mediante Tabulador y usar etiquetas semánticas (WAI-ARIA).
- **Focus Management:** No se debe usar `tabindex="-1"` en el `body`.

---
Cualquier colaborador que herede este repositorio debe leer este documento antes de solicitar integraciones o añadir dependencias externas.