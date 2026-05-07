# Checklist de Hardening (Endurecimiento) de merci-boilerplate.es

Este documento consolida las medidas de seguridad aplicadas en la arquitectura híbrida del proyecto (Núcleo Estático + WordPress aislado). Actúa como lista de verificación de obligado cumplimiento antes de cualquier paso a producción.

## 1. Capa Frontend (Núcleo Estático)

- [x] **Reducción de Superficie de Ataque DOM (Document Object Model - Modelo de Objetos del Documento):**
  - Eliminación de scripts/estilos en línea injustificados y delegación de la seguridad (CSP (Content Security Policy - Política de Seguridad de Contenido)) a la capa de infraestructura (Nginx).
  - *Motivo:* Las cabeceras HTTP son órdenes estrictas para el navegador, mientras que las etiquetas `<meta>` son vulnerables a ser ignoradas y no soportan todas las directivas de seguridad modernas.

## 2. Capa Backend (Aislamiento de WordPress)

- [x] **Ofuscación de Versión:** Eliminado el tag generador de WordPress (`remove_action('wp_head', 'wp_generator')`).
  - *Motivo:* Dificulta el escaneo automatizado en busca de vulnerabilidades conocidas para una versión específica.
- [x] **Desactivación de XML-RPC:** Bloqueado mediante filtro (`add_filter('xmlrpc_enabled', '__return_false')`).
  - *Motivo:* Cierra uno de los vectores más comunes para ataques DDoS (Distributed Denial of Service - Denegación de Servicio Distribuida) y de fuerza bruta en WordPress.
- [x] **Ofuscación de Errores de Login:** Mensajes de error genéricos implementados (`login_errors`).
  - *Motivo:* Evita la enumeración de usuarios válidos (el atacante no sabe si falla el usuario o la contraseña).
- [x] **Limpieza de Cabeceras:** Eliminación de enlaces RSD y WLW Manifest.
  - *Motivo:* Reducción de superficie de ataque y limpieza de código basura no utilizado.

## 3. Capa de Infraestructura (Servidor LEMP (Linux, Nginx, MySQL/MariaDB, PHP))

- [x] **Principio de Mínimo Privilegio (Usuarios):**
  - Base de datos (`wp_merci-boilerplate_local`): Accedida mediante un usuario de MySQL dedicado (`wp_user_local`), sin privilegios globales.
  - WordPress no usa el usuario por defecto "admin".
- [x] **Permisos de Sistema de Archivos (CHMOD/CHOWN):**
  - Directorio base: Propiedad exclusiva de `www-data:www-data`.
  - Directorios (`755`): Lectura/Ejecución para todos, escritura solo para `www-data`.
  - Archivos (`644`): Lectura para todos, escritura solo para `www-data`.
  - Archivo crítico (`wp-config.php` a `600`): Lectura y escritura **solo** para `www-data`.
- [x] **Fronteras Inmutables (Nginx):**
  - El entorno dinámico (`/blog`) se sirve mediante un `alias` en Nginx desde un directorio físico separado (`/var/www/wordpress`).
  - WordPress no tiene permisos de escritura sobre la raíz estática (`/var/www/merci-boilerplate/public`).
- [x] **Hardening de Cabeceras HTTP (VHost Nginx / CloudPanel):**
  - **CSP:** Implementada como cabecera. Bloquea XSS (Cross-Site Scripting - Secuencias de Comandos en Sitios Cruzados) definiendo orígenes permitidos (incluye whitelist criptográfico mediante Hash SHA-256 para scripts benignos residuales de WP).
  - **HSTS (HTTP Strict Transport Security - Seguridad de Transporte Estricta HTTP):** Fuerza comunicaciones exclusivamente por HTTPS (incluyendo directiva `preload` para precarga en navegadores) para mitigar ataques de intermediario (*Man-in-the-Middle*).
  - **COOP y COEP:** Aísla el documento de ventanas emergentes e incrustaciones para mitigar ataques de canal lateral de CPU (Central Processing Unit - Unidad Central de Procesamiento) (Spectre).
  - **X-Frame-Options (SAMEORIGIN):** Previene ataques de *Clickjacking* bloqueando incrustaciones de nuestra web en iframes no autorizados.
  - **X-Content-Type-Options (nosniff):** Previene ataques basados en confusión y suplantación de tipo MIME.
  - **Referrer-Policy:** Protege la privacidad del usuario ocultando la URL de origen en las peticiones cruzadas.

## 4. Capa DevSecOps (Control de Calidad Local)

- [x] **Auditoría Pre-Commit (`merci-audit.py`):**
  - Bloqueo automático (Código de salida `1`) si se detectan:
    - Patrones de secretos expuestos (Tokens, claves privadas, API (Application Programming Interface - Interfaz de Programación de Aplicaciones) Keys).
    - Errores de sintaxis en Python o JSON.
    - Ausencia de etiquetas SEO (Search Engine Optimization - Optimización para Motores de Búsqueda) críticas (lang, title, description).
  - Detección de "PHP (Hypertext Preprocessor - Preprocesador de Hipertexto) Smells" (Advertencias por uso de funciones peligrosas como `eval()`, `exec()`, `shell_exec()`).
- [x] **Auditoría Estandarizada Pre-Merge:**
  - Obligatoriedad de ejecutar `python3 scripts/merci/merci-audit.py --strict-json-ld` para garantizar la presencia de datos estructurados antes de pasar a producción.

---
*Última revisión: Fase 11 Completada (2026-05-06). CI/CD, Lighthouse CI y Gobernanza Open Source.*