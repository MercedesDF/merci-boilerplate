# Merci Boilerplate v1.10.0

Un ecosistema DevSecOps autónomo impulsado por Inteligencia Artificial Local (Shift-Left AI) y Desarrollo Guiado por Especificaciones (Spec-Driven Development). 

Combina un orquestador local en Python puro (Sistema Merci) que automatiza la calidad del código, un núcleo estático ultrarrápido (HTML5, SASS, Vanilla JS, BEM) y un motor dinámico aislado opcional (WordPress Headless). Diseñado para alcanzar un rendimiento perfecto (Core Web Vitals 100/100) con 0 dependencias externas bloqueantes en el pipeline.

> 🤖 **Inteligencia y Gobernanza:** El boilerplate incluye agentes de IA locales que auto-reparan código, auto-documentan el Roadmap y generan bases de conocimiento estáticas con coste cero y privacidad total. La justificación de las decisiones DevSecOps reside en la carpeta `/docs`.

## 🚀 Novedades en la v1.10.0 (Autonomía Local y Self-Healing Docs)

- **Lóbulo Frontal 100% Local (Zero Dependencies):** El agente `merci-brain.py` ha sido refactorizado para operar exclusivamente offline utilizando SLM (Small Language Models - Modelos de Lenguaje Pequeños) locales (Ollama). Esto erradica la latencia de red, elimina dependencias de claves de API (Application Programming Interface - Interfaz de Programación de Aplicaciones) y acelera radicalmente el tiempo de compilación.
- **Agente SSOT (Sincronización Documental Autónoma):** Introducción de `merci-ssot.py`. Este agente analiza semánticamente la bitácora activa y detecta deriva documental (Document Drift), auto-sanando y actualizando el Roadmap del proyecto para garantizar una SSOT (Single Source of Truth - Única Fuente de Verdad) sin intervención manual.
- **Automatización Social con Gatekeeper:** El publicador `merci-linkedin.py` ahora integra autenticación nativa OIDC (OpenID Connect) y un escudo interactivo (*Gatekeeper*). Exige confirmación humana antes de disparar peticiones a la API, previniendo publicación accidental (Spam) mientras automatiza la extracción de metadatos YAML.
- **Clean DX (Experiencia del Desarrollador Limpia):** Se ha reforzado la limpieza de consola silenciando los avisos internos de depuración de la capa de abstracción LiteLLM en todos los agentes, respetando la filosofía "Silence is Golden".
- **Máquina de Estados y Patrón Inbox (Zero-Code):** El entorno de incubación (`laboratorio/`) ha sido reestructurado. Se introduce el subdirectorio `incubacion/` como "Bandeja de Entrada" unificada para borradores crudos. Se formaliza el estado temporal `incubacion` en el YAML para ocultar documentos inmaduros del orquestador de promoción (`merci-promote.py`), el cual ahora también informa visualmente de la subcarpeta de origen exacta, reduciendo la fricción cognitiva a cero.
- **Agente Bibliotecario (Zero-Friction Formatting):** Rescatado y convertido en un orquestador 100% local. Transforma notas crudas en documentos YAML perfectamente estructurados. Se le ha inyectado una política "Zero-Hallucination" para que no invente código, actuando como un sintetizador de formato en lugar de un expansor de conocimiento.

## 🚀 Novedades en la v1.9.0 (Self-Healing System y WebP Automation)

- **El Agente Auditor (IA Local):** El orquestador de calidad (`merci-audit.py`) ha sido dotado de un lóbulo frontal en Python conectándose a Ollama/phi3 vía LiteLLM. Ahora no solo intercepta errores de código, sino que sugiere por terminal la maniobra de reparación exacta siguiendo las directrices de la arquitectura. Funciona con *Degradación Elegante* (Fail Gracefully) si la IA no está instalada o activada.
- **Auto-Healing en la Nube (CI/CD):** Nuevo flujo en GitHub Actions (`ia-fix.yml`) y agente autónomo (`merci-auto-fix.py`). Intercepta fallos del linter en la nube, delega la reparación a Gemini Flash API (*Hybrid Stack*) y aplica un auto-commit con el parche sin intervención humana.
- **WebP Automation (Fricción Cero):** Introducción de `merci-assets-watcher.py`, un agente local que vigila la carpeta `.assets-raw` en segundo plano. Al detectar nuevas imágenes en bruto, despierta a `merci-optimizer.py` para generar variantes WebP mágicamente.

## 🚀 Novedades en la v1.8.0 (Automatización de Rendimiento y Multi-Bitácora)

- **Cache Busting Dinámico (Fricción Cero):** El motor SSG (`merci-publish.py`) ahora lee automáticamente la fecha de modificación física (`st_mtime`) de los archivos CSS y JS para auto-inyectar marcas de tiempo (ej. `?v=X`) directamente en el código de la portada estática. Esto purga la caché de forma 100% automatizada tras cada compilación.
- **Extracción de Métricas Nativa:** El script `merci-extract-metrics.py` se ha promovido al núcleo DevSecOps e inyectado en el orquestador maestro (`merci-total.py`). Los datos del Engineering Dashboard ahora se auto-actualizan durante la fase de Build, previniendo el Data Drift (Deriva de Datos).
- **Soporte Multi-Bitácora en Pipeline:** El orquestador de commits atómicos (`merci-commit.py`) ahora cuenta con autodescubrimiento de contexto. Detecta de forma inteligente la "bitácora activa" leyendo las fechas de modificación más recientes, lo que permite dividir la documentación en ramas temáticas (Roadmap IA vs Ecosistema Base) sin destruir el flujo de Git.

## 🚀 Novedades en la v1.7.0 (SSG Dual y Engineering Dashboard)

- **Arquitectura SSG Dual:** `merci-publish.py` compila ahora dos secciones independientes en paralelo: `/biblioteca/` y `/art-de-cote/`, cada una con su propio índice autogenerado, flujo de publicación y PDFs descargables. Art de Coté abandona WordPress y pasa a ser un ciudadano de primera clase del motor estático.
- **Desacoplamiento Art de Coté de WordPress:** `merci-wp.py` ya no procesa la carpeta `art-de-cote/`. `merci-promote.py` enruta correctamente hacia `merci total` en lugar de `merci wp` para este tipo de contenido. `merci-sync-pages.py` excluye `art-de-cote/` para no sobreescribir las páginas autogeneradas por el SSG (Static Site Generation - Generación de Sitios Estáticos).
- **Robustez de Parseo YAML:** Las expresiones regulares de extracción de Frontmatter en `merci-publish.py`, `merci-promote.py` y `merci-wp.py` se han reforzado para tolerar espacios residuales, BOM (Byte Order Mark) y saltos de línea irregulares.
- **Engineering Dashboard:** Nueva sección en la portada con 10 métricas de rendimiento extraídas de auditorías reales de Google PageSpeed Insights. Nuevos bloques SASS BEM: `hero__dashboard`, `hero__metric`, `hero__dashboard-legend`.
- **Doctrina Art de Coté formalizada:** La Regla 10 de `instrucciones.md` se ha actualizado para establecer formalmente la taxonomía de preservación de artefactos funcionales descartados por decisiones de arquitectura.

## 🚀 Novedades en la v1.6.1 (Hotfix Accesibilidad y UX Dinámica)
- **Accesibilidad Quirúrgica (Scoped CSS):** Resolución de conflictos de contraste WCAG AA aplicando variables SASS dinámicas (`$color-regular`) con alcance limitado (`p a, li a`), logrando el 100/100 en herramientas automatizadas sin romper el diseño global.
- **Robustez de Enrutamiento Dinámico:** Los enlaces de retroceso en las vistas individuales del CMS ya no dependen del frágil historial del navegador (JS). Ahora infieren estructuralmente la jerarquía de subcategorías mediante PHP, anclando al usuario en su contexto de navegación de forma infalible.

## 🚀 Novedades en la v1.6.0 (Autoridad Técnica y Zero Maintenance)

- **Perfil Semántico "Anti-ATS":** Nueva estructura de página estática (`/sobre-mi/`) diseñada para eludir los errores de lectura de los reclutadores corporativos (ATS). Entrega el perfil profesional directamente en código máquina nativo mediante microdatos JSON-LD (`schema.org/Person`), asegurando un 100% de precisión en la extracción de capacidades técnicas.
- **Autodescubrimiento SSG (Zero Maintenance):** El orquestador `merci-sync-pages.py` abandona las rutas fijas (hardcoding) e implementa un motor de búsqueda recursivo (`Path.rglob()`). Ahora detecta y sincroniza mágicamente cualquier nueva página estática independiente que se añada al directorio `public/`, inyectando el menú y el pie de página de la portada (SSOT) sin intervención manual.

## 🚀 Novedades en la v1.5.0 (Shift-Left AI y Autonomía)

- **Inteligencia Estática (Zero Latency):** Integración nativa con la API de Google Gemini (`merci-brain.py`) sin exponer claves en el frontend ni penalizar el rendimiento. El orquestador escanea la documentación local durante la fase de compilación y genera un `brain_data.json` estático para respuestas contextualizadas instantáneas.
- **Autodescubrimiento y Degradación Elegante:** El lóbulo frontal en Python detecta automáticamente los modelos de IA disponibles en la capa gratuita, gestiona inteligentemente las cuotas de red (Rate Limiting) y proporciona respuestas de contingencia (Fallbacks estáticos) para garantizar que la web nunca falle por caídas de la API externa.
- **Fail-Gracefully en Lóbulo Frontal:** El orquestador de Inteligencia Artificial ya no detiene el pipeline maestro si el usuario no ha configurado una clave API de Gemini. Emite una advertencia informativa y permite al asistente operar con sus respuestas genéricas por defecto (Out-of-the-Box Experience).
- **Experiencia de Desarrollo (DX):** Refactorización integral de los orquestadores CLI para aplicar la "Filosofía Unix" (Silence is Golden). Los comandos muestran ahora reportes ultra-minimalistas orientados al éxito, ocultando el ruido de procesamiento tras la bandera opcional `--verbose` y mejorando el espaciado visual.

## 🚀 Novedades en la v1.4.0 (Gobernanza y CI/CD en la nube)

- **Integración Continua (CI):** Añadido flujo de trabajo automatizado con GitHub Actions (`.github/workflows/audit.yml`). La auditoría estricta de seguridad y calidad (Shift-Left) se ejecuta ahora automáticamente en la nube en cada *push* o *pull request*, forzando el uso de Node.js 24.
- **Gobernanza Open Source:** Incorporación de *Issue Templates* (Bug Report, Feature Request) y *Pull Request Template* estandarizadas bajo la estructura de 3 átomos (Desafío, Maniobra, Criterio), exigiendo validación estricta y limitando la fricción de mantenimiento.

## 🚀 Novedades en la v1.3.1 (Paridad Dev/Prod y Proxy Bypass)

- **SSOT (Single Source of Truth - Única Fuente de Verdad) Dinámico por Slug:** Erradicada la inyección de `wp_id` fijos en los archivos Markdown. El orquestador Headless ahora resuelve la existencia de los artículos interrogando al servidor mediante su nombre de archivo (slug), permitiendo publicar exactamente el mismo documento contra Localhost, Staging o Producción sin colisiones.
- **Escudo Anti-Proxy:** Inyectadas cabeceras personalizadas (`X-Authorization`) y firmas corporativas (`User-Agent`) en Python, junto a parches en el tema hijo para atravesar barreras de seguridad (Varnish Cache, OPcache, WAF - Web Application Firewall - Cortafuegos de Aplicaciones Web) garantizando la publicación ininterrumpida en ecosistemas Cloud.

## 🚀 Novedades en la v1.3.0 (Paridad Dev/Prod y Shift-Left Quality)

- **Paridad Total SSG/CMS:** El tema de WordPress (`merci-theme`) ha sido refactorizado para clonar la experiencia de la Biblioteca Estática. Ahora autogenera un "Mega-Menú" de navegación interna y agrupa visualmente las tarjetas de artículos basándose en sus subcategorías reales, ignorando las taxonomías estructurales.
- **Publicador Headless Avanzado (`merci-wp.py`):** El motor de sincronización dinámico ahora genera automáticamente réplicas locales en PDF de los artículos de WordPress y los nombra basándose estrictamente en la respuesta de la API REST (*Single Source of Truth*), erradicando los enlaces rotos. Además, inyecta los resúmenes (`excerpt`) directamente en el CMS, manteniendo la política de 0 dependencias en el frontend.
- **Shift-Left Quality (QA):** Se ha integrado la regla `UI_INLINE_STYLE` en el auditor maestro (`merci-audit.py`). El orquestador ahora escanea y advierte sobre el uso de estilos en línea (`style="..."`) en archivos HTML, PHP y JS, protegiendo la metodología CSS BEM desde la fase de pre-commit. Además, se ha resuelto a nivel de orquestador la colisión de enlaces ancla para garantizar el 100/100 en accesibilidad WAI-ARIA.

## 🚀 Novedades en la v1.2.3 (Lintern de estilos y blindaje anti-tokens OIDC)

- **Linter Estricto de Estilos en Línea:** El auditor maestro (`merci-audit.py`) ahora escanea y advierte sobre el uso de atributos `style="..."` para proteger la arquitectura SASS 7-1 (BEM). Incluye soporte para silenciamiento explícito de falsos positivos mediante la inyección del comentario HTML `<!-- merci-audit:silence-style -->` en la línea afectada.
- **Blindaje Anti-Fugas (Tokens OIDC):** Implementación de una doble capa de seguridad (Shift-Left) para las credenciales de LinkedIn. Además de la exclusión pasiva en `.gitignore`, el orquestador intercepta activamente el archivo `.linkedin_token.json` en el área de preparación (Stage) y bloquea el commit atómico de forma fulminante si detecta riesgo de exposición.

## 🚀 Novedades en la v1.2.2 (Hotfix de Seguridad y Estructura)

- **Prevención de Fuga de Datos (DLP):** El destructor de instanciación (`merci-init.py`) ahora purga y reconstruye desde cero las carpetas dinámicas (`blog/`, `art-de-cote/`), asegurando que ningún borrador o propiedad intelectual del proyecto matriz se filtre al repositorio público.
- **Preservación de Andamiaje Headless:** Se han inyectado archivos `.gitkeep` gestionados automáticamente para garantizar que los directorios de incubación dinámicos sobrevivan al control de versiones, eliminando advertencias de "directorio no encontrado" en la primera ejecución de `merci total`.

## 🚀 Novedades en la v1.2.1 (Hotfix)

- **Generación de Entorno Seguro:** El script de instanciación (`merci-init.py`) ahora genera automáticamente una plantilla `.env` con credenciales de WordPress ficticias. Esto previene colapsos en la ejecución inicial de `merci total` y guía al desarrollador en la configuración del publicador Headless.

## 🚀 Novedades en la v1.2.0 (Consolidación Headless y QA)

Esta versión transforma el Boilerplate de un simple generador de sitios estáticos a un ecosistema híbrido maduro con publicación Headless y herramientas de QA estandarizadas:

- **Publicador Headless para WordPress (`merci-wp.py`):** Permite escribir en Markdown localmente, compilar a HTML y publicar o actualizar posts masivamente a través de la API REST del CMS (Content Management System - Sistema de Gestión de Contenidos). Incluye "Kill-Switch" automático para devolver borradores despublicados al laboratorio.
- **Asistente de Promoción Inteligente (`merci-promote.py`):** Ahora posee "conciencia de contexto". Detecta automáticamente si un borrador está destinado a la Biblioteca estática o a las rutas dinámicas de WordPress (`/blog`, `/art-de-cote`) y lo enruta al directorio correcto.
- **Shift-Left Accessibility (QA Local):** El rastreador `merci-linkcheck.py` ha sido refactorizado para detectar colisiones de enlaces WAI-ARIA (identificando enlaces con el mismo texto pero distinto destino) antes de compilar.
- **Sincronización SSOT (`merci-sync-pages.py`):** Las páginas estáticas independientes (como Contacto) ahora heredan automáticamente el `<header>`, `<footer>` y la UI del asistente desde la portada, eliminando la deriva de diseño.
- **Backups Ultraligeros:** `merci-backup.py` optimizado mediante rutas absolutas para ignorar binarios y el CMS, generando copias de seguridad completas del código fuente en milisegundos (reducción de peso al 99%).
- **UX Purista y Privacidad:** Nueva plantilla base de contacto estática. Cero formularios, cero latencia, preparada nativamente para alojamiento de claves PGP y cifrado E2EE.

## 🚀 Puesta en marcha (Instanciación)

Este repositorio es una plantilla fundacional. Para arrancar tu propio proyecto, clona el código y ejecuta el script de inicialización.

```bash
# 1. Clona el repositorio
git clone <https://github.com/TU_USUARIO/TU_REPOSITORIO.git>
cd TU_REPOSITORIO

# 2. Ejecuta la instanciación (¡Destructivo para la plantilla base!)
python3 scripts/merci/merci-init.py

# 3. Aprovisiona el entorno de construcción (Build-time)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Ejecuta el pipeline completo
merci total
```

## 📋 Requisitos del Sistema

- **Python 3.10+** (para la automatización DevSecOps del ecosistema *Merci*).
- **Git** y terminal compatible (**sh**, **bash** o **zsh**).
- *Cero dependencias bloqueantes (No requiere `pip install` para arrancar).*

## 💻 Entorno de Desarrollo Local
Para mantener la separación de responsabilidades y la alta velocidad (0 ms de latencia), el desarrollo se divide en dos fases con servidores y ecosistemas distintos:

### 1. Desarrollo UI/UX (User Interface / User Experience - Interfaz de Usuario / Experiencia de Usuario) Estático (Python)
Para maquetar HTML5, Vanilla JS y compilar SASS. Abre dos terminales:
1. `python3 scripts/merci/merci-watcher.py` (Vigila y compila SASS)
2. `cd public && python3 -m http.server 8000` (Servidor Web Efímero)

### 2. Integración Dinámica WP (WordPress) (Nginx / LEMP (Linux, Nginx, MariaDB, PHP))
El servidor nativo de Python **no procesa PHP (Hypertext Preprocessor - Preprocesador de Hipertexto)**. Cuando llegues a la fase de integrar el CMS (Content Management System - Sistema de Gestión de Contenidos), levanta un entorno Nginx local y crea los enlaces simbólicos tal y como se detalla en `docs/integracion-wordpress.md`.

## 🛠️ El Ecosistema "Merci" (DevSecOps Local)

Este boilerplate incluye su propia cadena de suministro CI/CD (Continuous Integration / Continuous Deployment - Integración Continua / Despliegue Continuo) local basada íntegramente en Python puro:

- `merci-audit.py`: Auditoría estática y bloqueo de secretos (SAST - Static Application Security Testing - Pruebas Estáticas de Seguridad de Aplicaciones).
- `merci-commit.py`: Automatización de commits empaquetados atómicamente e impulsados por la lectura de la bitácora.
- `merci-total.py`: Orquestador maestro del pipeline (Build y QA).
- `merci-brain.py`: Generador de base de conocimientos estática (Shift-Left AI).
- `merci-publish.py` y `merci-promote.py`: Motor SSG (Static Site Generation - Generación de Sitios Estáticos) y curación de contenidos.
- `merci-backup.py`: Creación instantánea de copias de seguridad locales en formato ZIP.
- `merci-optimizer.py`: Optimización de imágenes a WebP.
- `merci-sitemap.py` y `merci-linkcheck.py`: Rastreo DAST de enlaces rotos y actualización de XML.
- `merci-sync-pages.py`: Sincronizador de estructuras estáticas (SSOT).
- `merci-wp.py`: Publicador Headless masivo para integración nativa con WordPress.
- `merci-styles.py` y `merci-watcher.py`: Compilador y vigilante de SASS local.
- `merci-init.py`: Inicializador destructivo para nuevos proyectos.

---
*Desarrollado bajo licencia MIT.*