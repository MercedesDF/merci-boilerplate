# Integración y Aislamiento Dinámico (WordPress)

Este documento define la arquitectura técnica y operativa para la **Fase 4.1**. El objetivo es implementar espacios dinámicos administrables (`/blog`, `/tienda`) sin que el componente dinámico (WordPress) vulnere ni contamine la arquitectura estricta del núcleo servido desde `public/`.

## Estrategia de Enrutamiento (Nginx + Symlink)

Se prescribe el uso de **Nginx** como interceptador maestro. En el servidor huésped (Ubuntu), el entorno estático y el entorno dinámico vivirán en directorios separados (`/var/www/merci-boilerlate` y `/var/www/wordpress`). 

**Nota de Arquitectura Crítica:** Para evitar bugs históricos de Nginx con la directiva `alias` y la API REST de WordPress (errores de JSON inválido al guardar), la unión de ambos mundos se realiza mediante un **Enlace Simbólico físico** a nivel de sistema operativo:
`ln -s /home/merci-boilerlate-php/htdocs/wordpress /home/merci-boilerlate-php/htdocs/merci-boilerlate.es/public/blog`

Para que el tema diseñado (Child Theme) esté disponible en el CMS, se traza un segundo enlace:
`ln -s /home/merci-boilerlate-php/htdocs/merci-boilerlate.es/src/wp-theme/merci-theme /home/merci-boilerlate-php/htdocs/wordpress/wp-content/themes/merci-theme`

### Reglas de Configuración (Virtual Host en CloudPanel)

A diferencia de un entorno LEMP local, CloudPanel utiliza un motor de plantillas (`{{root}}`). La configuración se divide en dos maniobras para no romper la interfaz del IaaS (Infrastructure as a Service - Infraestructura como Servicio).

#### 1. Definir la Frontera Estática
Desde la interfaz de Settings del sitio en CloudPanel, se añade `/public` al campo *Document Root*:
`Document Root: /home/merci-boilerlate-php/htdocs/merci-boilerlate.es/public`
Esto propaga de forma segura la raíz a todas las variables de Nginx para el puerto 80 y 443.

#### 2. Enrutador Híbrido (Procesamiento PHP - Puerto 8080)
En la pestaña VHost, dentro del bloque `server` del puerto 8080, se elimina la regla genérica `try_files` y se inyecta el cortafuegos lógico:

```nginx
  # ---------------------------------------------------------
  # MERCI BOILERPLATE: Hardening Avanzado de Cabeceras HTTP
  # ---------------------------------------------------------
  add_header X-Frame-Options "SAMEORIGIN" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
  add_header Cross-Origin-Opener-Policy "same-origin" always;
  add_header Cross-Origin-Embedder-Policy "require-corp" always;
  add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'sha256-eHL/Izx7K/qWL0kdBXXnHwsLSHvGOJn/THLHydUZdog='; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none';" always;

  # ---------------------------------------------------------
  # MERCI BOILERPLATE: Enrutamiento Híbrido Estático/Dinámico
  # ---------------------------------------------------------
  
  # 1. El núcleo estático: Se sirve directamente, si no existe, devuelve 404.
  location / {
      try_files $uri $uri/ =404;
  }

  # 2. El motor aislado (WordPress): Redirige el tráfico de /blog al CMS.
  location /blog {
      try_files $uri $uri/ /blog/index.php?$args;
  }
```

## Definición de Fronteras y Blindajes

Para asegurar la supervivencia del paradigma minimalista y la puntuación perfecta de rendimiento en la raíz, deben cumplirse las siguientes fronteras:

1. **`public/` es _Read Only_ para el CMS:** Ningún script, actualizador o plugin de WordPress tendrá permisos de escritura (CHMOD) sobre el directorio `public/` ni sus predecesores en el proyecto Git.
2. **Dependencias Separadas:** Las actualizaciones de seguridad de WP, temas y plugins se ejecutan dentro del alcance de su alias (`/var/www/wordpress`). No viajan por nuestro repositorio Git, excepto el *Child Theme* diseñado en la Fase 4.2 si decidimos versionarlo en una carpeta separada (ej. `src/wp-theme/`).
3. **Consumo de Assets Unidireccional:** WordPress reutilizará las hojas de estilo y utilidades web compiladas en la carpeta universal `/assets/`. **Nunca** inyectará código a la inversa (hacia la home o estáticas).

## Preservación Canónica y de Indexación

La sobreposición de rutas tiene el riesgo de romper la cadena de rastreo de SEO (Search Engine Optimization - Optimización para Motores de Búsqueda) técnico. Se previene implementando:

1. **Bloqueo del Canibalismo de Portada:** En las opciones globales de WordPress, las rutas `siteurl` y `home` se unifican obligatoriamente como `https://merci-boilerlate.es/blog`. No se debe instalar en la raíz ni usar plugins para desviar "la portada de WordPress" a la raíz del dominio principal.
2. **Jerarquía Unificada del Sitemap:** Un sitemap de índice (`sitemap_index.xml`) puede declarar dónde localizar los XML locales estáticos creados por `merci_sitemap.py` y dónde iniciar la traza generada automáticamente por WordPress para el contenido.

---
*Conclusión de Fase 4.1. Este documento sella la decisión de diseño arquitectónico y marca la pauta de despliegue antes de iniciar el Child Theme en la Fase 4.2.*
