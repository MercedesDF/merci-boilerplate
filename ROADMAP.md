# 🗺️ ROADMAP MAESTRO: Ecosistema merci-boilerplate.es

Única Fuente de Verdad (SSOT) del avance del proyecto y de las automatizaciones DevSecOps.

## ÉPICA 1: FUNDACIÓN DEVSECOPS (Concluida)

### Fase 1 - Infraestructura y Automatización Base
- [x] Verificar la estructura aprobada (`docs/`, `biblioteca/`, `laboratorio/`, `scripts/merci/`, `assets/`, `public/`, `.assets-raw/`).
- [x] Confirmar que `.assets-raw/` mantiene solo `.gitkeep` como contenido versionado.
- [x] Definir y documentar una convención estable de nombres de archivos y rutas.
- [x] Ejecutar `python3 scripts/merci/merci-audit.py` en local y registrar resultado base.
- [x] Ejecutar `python3 scripts/merci/merci-audit.py --git-staged` para validar el flujo staged.
- [x] Corregir advertencias críticas detectadas por `merci-audit.py` antes de nuevas fases.
- [x] Aplicar permisos de ejecución a `scripts/merci/pre-commit` y `scripts/merci/merci-audit.py`.
- [x] Enlazar hook local a `.git/hooks/pre-commit` y validar su ejecución en un commit de prueba.
- [x] Asegurar que los commits con fallos de auditoría se bloquean correctamente.
- [x] Crear entrada de bitácora en `laboratorio/bitacora-merci-boilerplate.md` con contexto de arranque.
- [x] Registrar comandos estándar de trabajo para facilitar continuidad entre sesiones.
- [x] Confirmar que la documentación del repo no incluye notas personales ni recordatorios en segunda persona.

### Fase 2 - Arquitectura Semántica y SEO Técnico
- [x] Estructurar `public/index.html` con semántica HTML5 estricta (`header`, `main`, `section`, `footer`).
- [x] Validar jerarquía de encabezados (`h1`-`h6`) sin saltos estructurales.
- [x] Incorporar landmarks accesibles para navegación asistida.
- [x] Definir metadatos esenciales (`title`, `description`, `canonical`, `viewport`).
- [x] Insertar bloque JSON-LD mínimo alineado con el tipo de sitio.
- [x] Verificar sintaxis del JSON-LD y su coherencia con el contenido real de la página.
- [x] Crear `public/robots.txt` con reglas explícitas de rastreo.
- [x] Crear `public/sitemap.xml` con URLs canónicas previstas para producción.
- [x] Revisar consistencia entre `robots.txt`, `sitemap.xml` y canónicas.
- [x] Automatizar actualización de `lastmod` mediante `merci-sitemap.py`.
- [x] Integrar `merci-sitemap.py` en el hook de pre-commit para actualización automática.
- [x] Implementar `laboratorio/scripts_temporales/merci_ingestor.py` para escanear y mover archivos recientes a `.assets-raw/`.
- [x] Documentar rutas de escaneo configurables para `merci_ingestor.py`.
- [x] Confirmar atributos `lang`, `charset` y semántica documental mínima.
- [x] Verificar que imágenes críticas incluyen texto alternativo útil.
- [x] Registrar en bitácora los criterios de aceptación SEO para cierre de fase.

### Fase 3 - Ingeniería de Estilos
- [x] Crear árbol SASS 7-1 y documentar responsabilidad de cada carpeta.
- [x] Definir un punto de entrada único de compilación hacia un solo CSS final.
- [x] Verificar orden de importación para evitar cascadas inesperadas.
- [x] Establecer convención BEM para bloques, elementos y modificadores.
- [x] Reflejar la convención BEM en los componentes HTML clave.
- [x] Revisar y eliminar clases ambiguas o no alineadas con BEM.
- [x] Implementar estilos base para móvil antes de breakpoints superiores.
- [x] Definir breakpoints justificados por contenido, no por dispositivo.
- [x] Reducir reglas redundantes y validar peso final del CSS compilado.
- [x] Implementar o consolidar `merci-optimizer.py` para generar WebP responsivo.
- [x] Definir tamaños objetivo y nomenclatura de salida en `assets/`.
- [x] Validar que los originales en `.assets-raw/` no pasan al remoto.

### Fase 4 - Integración de Sistemas Dinámicos
- [x] Verificar instalación de pila LEMP (Nginx, MariaDB, PHP) en PC local.
- [x] Crear base de datos local y usuario para el entorno de WordPress.
- [x] Desplegar WordPress en directorio de desarrollo local replicando la estructura de producción.
- [x] Definir integración de WordPress en rutas aisladas (`/blog`, `/tienda`) sin invadir `public/`.
- [x] Documentar fronteras entre núcleo estático y capa dinámica (`docs/integracion-wordpress.md`).
- [x] Verificar que el routing previsto no rompe URLs canónicas del núcleo.
- [x] Crear child theme con sobrecarga mínima y sin lógica innecesaria.
- [x] Enlazar estilos compartidos de forma controlada para mantener coherencia visual.
- [x] Validar que no se introducen dependencias pesadas en frontend.
- [x] Configurar WooCommerce en modo catálogo para merchandising de Merci según alcance funcional definido.
- [x] Limitar plugins y extensiones a los estrictamente necesarios.
- [x] Revisar impacto de scripts dinámicos en tiempos de carga.
- [x] Medir impacto de `/blog` y `/tienda` sobre Core Web Vitals del sitio principal.
- [x] Asegurar carga diferida o condicional de recursos dinámicos.
- [x] Registrar decisiones de integración y deuda técnica asociada en bitácora.
- [x] Definir rol de Merci en interfaz (acompañamiento, estados y límites de interacción).
- [x] Diseñar contrato técnico entre backend de Merci y capa visual sin acoplar al núcleo estático.
- [x] Validar que animación, voz o movimiento de Merci no degrada accesibilidad ni rendimiento.

### Fase 5 - Quality Assurance y Hardening
- [x] Definir una política CSP progresiva con modo de validación inicial.
- [x] Ajustar orígenes permitidos para scripts, estilos, fuentes e imágenes.
- [x] Verificar que la CSP final no rompe funcionalidad crítica.
- [x] Aplicar endurecimiento básico de WP (superficie de ataque mínima).
- [x] Revisar permisos, usuarios administrativos y exposición de endpoints.
- [x] Comprobar desactivación de funcionalidades no necesarias.
- [x] Ampliar checks de pre-commit para cubrir validaciones críticas recurrentes.
- [x] Estandarizar ejecución local de auditorías antes de merge.
- [x] Documentar criterios de fallo/bloqueo para que sean reproducibles.
- [x] Ejecutar una pasada integral de auditoría estática y corregir hallazgos críticos.
- [x] Confirmar que no hay secretos ni credenciales en el árbol versionado.
- [x] Consolidar checklist de hardening completado en documentación interna.
- [x] Implementar HSTS, COOP/COEP y políticas de Referrer/X-Content-Type.
- [x] Migrar la CSP desde la etiqueta `<meta>` a una cabecera HTTP robusta.
- [x] Validar la nueva configuración de seguridad con herramientas externas.

### Fase 6 - Despliegue y Auditoría Final
- [x] Definir proceso de despliegue paso a paso para entorno de producción.
- [x] Verificar artefactos finales del núcleo estático antes del deploy.
- [x] Confirmar consistencia de rutas absolutas/relativas para entorno real.
- [x] Ejecutar mediciones de Core Web Vitals con metodología reproducible.
- [x] Validar accesibilidad técnica base y corregir desviaciones críticas.
- [x] Comparar resultados frente a objetivos de la filosofía del proyecto.
- [x] Revisar indexabilidad efectiva, canónicas y metadatos finales.
- [x] Validar `robots.txt` y `sitemap.xml` contra el estado real de URLs.
- [x] Confirmar coherencia entre contenido visible y datos estructurados.
- [x] Registrar evidencias del despliegue y resultados de auditoría.
- [x] Documentar incidencias y mitigaciones aplicadas durante la salida.
- [x] Dejar criterios explícitos de rollback y recuperación operativa.

### Fase 7 - Automatización y Clasificación
- [x] Diseñar flujo de publicación que minimice tareas manuales repetitivas.
- [x] Definir puntos de validación automática previos a publicación.
- [x] Documentar dependencias y responsabilidades del pipeline.
- [x] Definir plantillas estándar para documentos definitivos en `biblioteca/`.
- [x] Integrar la estructura de 3 átomos (desafío, maniobra, aprendizaje/deuda).
- [x] Validar consistencia editorial y técnica entre estanterías temáticas.
- [x] Formalizar criterio para promover contenido desde `laboratorio/` a `biblioteca/`.
- [x] Añadir checklist de curación y revisión previa a promoción.
- [x] Registrar trazabilidad del origen de cada pieza publicada.
- [x] Definir cadencia de revisión del roadmap y actualización de hitos.
- [x] Revisar periódicamente deuda técnica acumulada por fase.
- [x] Mantener sincronía entre `README.md`, `instrucciones.md` y bitácora activa.
- [x] Planificar carpeta/proyecto dedicado para Merci con límites claros frente a `merci-boilerplate.es`.
- [x] Definir roadmap propio de Merci: avatar/estado visual, diálogo y comportamiento por contexto.
- [x] Establecer versión mínima de integración en `merci-boilerplate.es` antes de ampliar capacidades.
- [x] Documentar criterio de evolución de Merci para evitar desvíos fuera del orden de fases.

### Fase 8 - Expansión de Contenido y Contexto Inteligente
- [x] Implementar respuestas contextuales basadas en la ruta (`window.location.pathname`).
- [x] Mantener 0 latencia y 0 dependencias (evitar consultas a base de datos en frontend).
- [x] Emplear `merci-promote` para trasladar cuadernillos históricos a la Biblioteca.
- [x] Unificar enlaces globales en pie de página (LinkedIn, GitHub, Boilerplate) manteniendo paridad Dev/Prod.
- [x] Completar página estática de contacto (`public/contacto/index.html`) y afinar la portada (Sincronización SSOT).
- [x] Generar un pequeño índice curado de los artículos publicados en la biblioteca (Auto-generado por merci-publish).
- [x] Desarrollar publicador Headless (`merci-wp.py`) agnóstico al entorno (Local/Nube) con resolución dinámica por Slug y Proxy Bypass.
- [x] Implementar automatización social para publicar entradas del blog directamente en LinkedIn.
- [x] Prevenir *Data Drift* (Posts Fantasma) aislando el borrado y estableciendo el Kill-Switch de despublicación.
- [x] Actualización de posicionamiento público y copy de portada (`index.html`).
- [x] Propagación de enlaces de navegación en cabeceras de plantillas estáticas y dinámicas para evitar asimetría visual.
- [x] Diseño e implementación del CV Semántico "Anti-ATS" (`/sobre-mi/index.html`) expuesto con marcado de microdatos JSON-LD (`schema.org/Person`).
- [x] Consolidación documental del patrón arquitectónico en la Biblioteca (`cuadernillo-cv-anti-ats-json-ld.md`).

### Fase 9 - Inteligencia y Autonomía (Merci Avanzado)
- [x] Evaluar integración segura con APIs de LLM o modelos locales para respuestas dinámicas (Shift-Left AI con Gemini).
- [x] Garantizar que la IA no rompe la política de 0 dependencias bloqueantes (Graceful Degradation y Fallback estático).

### Fase 10 - Empaquetado y Ecosistema (Release 1.0.0)
- [x] Crear script de instanciación (`merci-init.py`) para limpiar datos base y arrancar proyectos nuevos.
- [x] Revisión final de documentación pública y lanzamiento de la versión 1.0.0.

### Fase 11 - Integración Continua y Calidad en la Nube (CI/CD)
- [x] Implementar flujos de GitHub Actions para automatizar `merci-audit` en cada Pull Request.
- [x] ~~Automatizar la compilación SSG (`merci-publish`) directamente en el servidor de despliegue~~ (🛑 **Descartado/Rollback:** Preferencia de Arquitectura por control manual mediante `git pull`).
- [x] Integrar Lighthouse CI para garantizar que ninguna actualización degrade el 100/100 en Core Web Vitals.
- [x] Configurar *Issue Templates* y *Pull Request Templates* para estandarizar las contribuciones en repositorios públicos.

---

## ÉPICA 2: ORQUESTACIÓN IA & SELF-HEALING (En curso)

### Fase 1: Cimientos y Conectividad 
- [x] Setup de Modelos (Hybrid Stack): Configurar Ollama para ejecución local y LiteLLM para fallback con Gemini Flash API.
- [x] Directorio del Cerebro: Crear /merci-brain para centralizar los agentes de Python.
- [x] Estandarización de Prompts: Crear /laboratorio/prompts con las reglas de estilo y arquitectura para que las IAs mantengan la coherencia del repo.

### Fase 2: El Agente Auditor (Self-Healing Base) 
- [x] Evolución de merci-audit.py: Integrar IA para que el script no solo detecte errores, sino que sugiera el comando de reparación.
- [x] IA-Fix Workflow: Crear GitHub Action que dispare una corrección automática de IA ante fallos del linter utilizando el *Hybrid Stack*.
- [x] WebP Automation: Implementar agente que vigile /.assets-raw y convierta automáticamente cualquier subida a .webp optimizado.

### Fase 3: Orquestación de Contenidos y Docs
- [x] Agente Bibliotecario (Zero-Hallucination): Rescatado como orquestador 100% local. Transforma notas crudas en documentos YAML perfectamente estructurados sin inventar código.
- [x] Sync SSOT (Self-Healing Docs): Agente híbrido (Cloud/Local con Qwen 2.5) que verifica y auto-sana la deriva documental mediante Shift-Left Parsing.
- [x] 🔴 AI-Changelog (descartado por límites cognitivos locales): Generación automática de historial de cambios realizados por agentes en /docs/CHANGELOG_AI.md.
- [x] Pipeline WP → LinkedIn (Automatización Social): Conectar `merci-wp.py` con `merci-linkedin.py` para que al publicar o actualizar un post en WordPress se dispare automáticamente a LinkedIn.

### Fase 4: Observabilidad y SRE IA
- [ ] Dashboard de Confianza: Implementar Grafana para visualizar cuántos cambios de IA han sido aprobados vs. rechazados.
- [ ] Chaos Engineering con IA: Script que use la IA para simular fallos en el merci-boilerplate y verificar que el sistema de rollback funciona.
- [ ] Hardening Automation: Agente que audite el cumplimiento de la docs/checklist-hardening.md de forma continua.
- [ ] **Evaluación de Tienda WooCommerce (Deuda Fase 4.3):** Estudiar la viabilidad de activar WooCommerce más allá del modo catálogo actual. Evaluar: pasarela de pago compatible con la arquitectura (sin degradar Core Web Vitals), impacto en CSP (Content Security Policy), y si el volumen de productos justifica la complejidad operativa. Decisión de arquitectura previa obligatoria antes de cualquier implementación.