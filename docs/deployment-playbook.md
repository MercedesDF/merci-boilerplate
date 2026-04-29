# Deployment Playbook (Manual de Despliegue)

Este documento define el proceso estandarizado para desplegar la arquitectura híbrida **Merci Boilerplate** en un entorno de producción Ubuntu limpio. Inicia desde la adquisición del dominio hasta la verificación final.

## PASO 0: Fundamentos y Preparación de Infraestructura
**Concepto:** Separar el Registro del Dominio (el "nombre") de la Infraestructura IaaS (Infrastructure as a Service - Infraestructura como Servicio) donde residirán los datos (el VPS o Servidor Privado Virtual).

1. Adquirir un servidor VPS (Virtual Private Server - Servidor Privado Virtual) "Bare Metal" o Cloud (ej. DigitalOcean, Hetzner, Linode) e instalar **Ubuntu 24.04 LTS o 22.04 LTS** en blanco.
2. Acceder al panel del registrador del dominio (proveedor donde se compró el dominio).
3. Configurar la Zona DNS (Domain Name System - Sistema de Nombres de Dominio): modificar el Registro 'A' para que apunte a la dirección IPv4 pública del nuevo servidor VPS.
4. Esperar el tiempo de propagación DNS (TTL) antes de emitir certificados de seguridad.

## PASO 1: Aprovisionamiento del Servidor (CloudPanel)
**Concepto:** Delegar la instalación y optimización de la pila LEMP (Linux, Nginx, MariaDB, PHP) a un panel de control enfocado en rendimiento y seguridad.

1. Acceder vía SSH (Secure Shell - Consola Segura) al servidor de producción como usuario `root`.
2. Ejecutar la instalación del gestor CloudPanel (Motor Nginx + MariaDB + PHP integrado):
   `curl -sS https://installer.cloudpanel.io/ce/v2/install.sh -o install.sh; \`
   `echo "85762db0edc00ce19a2cd5496d1627903e6198ad850bffdef4f085d00db1dddb install.sh" | \`
   `sha256sum -c && sudo bash install.sh`
3. Acceder al panel web (`https://IP:8443`) y crear el usuario administrador.
4. Crear el sitio web desde el panel (Tipo: "PHP Site") apuntando al dominio oficial.

## PASO 2: Despliegue de Código (Git)
1. Generar clave SSH para el usuario del sitio en CloudPanel.
2. Vincular la clave en GitHub (Deploy Key) para permitir acceso de lectura.
3. Clonar el repositorio en el Document Root asignado (ej. `/home/usuario-php/htdocs/dominio.com`).

## PASO 3: Aislamiento del CMS (WordPress)
1. Crear base de datos y usuario asociado desde la interfaz de CloudPanel.
2. Descargar y extraer WordPress en una carpeta hermana a la web (`/home/merci-boilerplate-php/htdocs/wordpress`).
3. Configurar `wp-config.php` de forma manual, generando Salts criptográficos y aplicando restricciones de seguridad (`chmod 600`).
4. Crear los enlaces simbólicos físicos (Symlinks) para orquestar la arquitectura híbrida:
   - **Puente del CMS:** `ln -s /home/merci-boilerplate-php/htdocs/wordpress /home/merci-boilerplate-php/htdocs/merci-boilerplate.es/public/blog`
   - **Puente del Tema:** `ln -s /home/merci-boilerplate-php/htdocs/merci-boilerplate.es/src/wp-theme/merci-theme /home/merci-boilerplate-php/htdocs/wordpress/wp-content/themes/merci-theme`
   - **Puente de Assets:** `ln -s /home/merci-boilerplate-php/htdocs/merci-boilerplate.es/assets /home/merci-boilerplate-php/htdocs/merci-boilerplate.es/public/assets`

## PASO 4: Enrutamiento y SSL (CloudPanel)
1. Emitir el Certificado SSL/TLS (Secure Sockets Layer / Transport Layer Security) gratuito (Let's Encrypt) desde la pestaña SSL de CloudPanel.
2. Configurar la frontera estática: En la pestaña **Settings**, modificar el *Document Root* añadiendo `/public` al final (`/home/merci-boilerplate-php/htdocs/merci-boilerplate.es/public`).
3. Configurar el enrutador dinámico: En la pestaña **VHost**, localizar el bloque `server` del puerto **8080** (procesamiento PHP), eliminar la regla global `try_files` e inyectar los bloques lógicos (`location /` y `location /blog`) definidos en `docs/integracion-wordpress.md`.
4. Inyectar el bloque de cabeceras HTTP de seguridad (CSP, HSTS, COOP, etc.) en el mismo bloque `server` del puerto 8080 para blindar el frontend contra ataques XSS y *Clickjacking*.
5. Acceder a la ruta `/blog` en el navegador, completar la instalación de WordPress, guardar los **Enlaces Permanentes** ("Nombre de la entrada") y activar el Child Theme.

## PASO 5: Verificación
1. Ejecutar `merci-linkcheck.py` contra el dominio público para auditar la ausencia de enlaces rotos (404).
2. Realizar auditoría de Core Web Vitals (Google PageSpeed Insights) para certificar el rendimiento.
3. Comprobar accesos y bloqueos de seguridad en el panel de administración del CMS (Content Management System - Sistema de Gestión de Contenidos).

---
*Nota: Las futuras actualizaciones de código se realizarán ejecutando `git pull` dentro de la carpeta clonada en el servidor.*