# Merci Boilerplate v1.3.1

Un entorno web híbrido, minimalista y seguro desde el diseño (Shift-Left). 
Combina un núcleo estático ultrarrápido (HTML5, SASS, Vanilla JS y BEM (Block, Element, Modifier - Modificador de Elemento de Bloque)) con un motor dinámico aislado (WordPress). Diseñado para alcanzar un rendimiento perfecto (Core Web Vitals 100/100) y operar con 0 dependencias externas en el frontend.

> 📖 **Historia y Arquitectura:** La justificación de las decisiones DevSecOps, el aislamiento del CMS y los manuales operativos se encuentran en la carpeta `/docs`.

### Novedades en v1.3.1 (Paridad Dev/Prod y Proxy Bypass)

- **SSOT Dinámico por Slug:** Erradicada la inyección de `wp_id` fijos en los archivos Markdown. El orquestador Headless ahora resuelve la existencia de los artículos interrogando al servidor mediante su nombre de archivo (slug), permitiendo publicar exactamente el mismo documento contra Localhost, Staging o Producción sin colisiones.
- **Escudo Anti-Proxy:** Inyectadas cabeceras personalizadas (`X-Authorization`) y firmas corporativas (`User-Agent`) en Python, junto a parches en el tema hijo para atravesar barreras de seguridad (Varnish Cache, OPcache, WAF) garantizando la publicación ininterrumpida en ecosistemas Cloud.

### Novedades en v1.3.0 (Paridad Dev/Prod y Shift-Left Quality)

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

# 3. Audita el código resultante
python3 scripts/merci/merci-audit.py
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
- `merci-publish.py` y `merci-promote.py`: Motor SSG (Static Site Generation - Generación de Sitios Estáticos) y curación de contenidos.
- `merci-backup.py`: Creación instantánea de copias de seguridad locales en formato ZIP.
- `merci-optimizer.py`: Optimización de imágenes a WebP.
- `merci-linkcheck.py`: Rastreo DAST (Dynamic Application Security Testing - Pruebas Dinámicas de Seguridad de Aplicaciones) de enlaces rotos.
- `merci-sync-pages.py`: Sincronizador de estructuras estáticas (SSOT).
- `merci-wp.py`: Publicador Headless masivo para integración nativa con WordPress.

---
*Desarrollado bajo licencia MIT.*