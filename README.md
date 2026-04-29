# Merci Boilerplate v1.0.0

Un entorno web híbrido, minimalista y seguro desde el diseño (Shift-Left). 
Combina un núcleo estático ultrarrápido (HTML5, SASS, Vanilla JS y BEM (Block, Element, Modifier - Modificador de Elemento de Bloque)) con un motor dinámico aislado (WordPress). Diseñado para alcanzar un rendimiento perfecto (Core Web Vitals 100/100) y operar con 0 dependencias externas en el frontend.

> 📖 **Historia y Arquitectura:** La justificación de las decisiones DevSecOps, el aislamiento del CMS y los manuales operativos se encuentran en la carpeta `/docs`.

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
- `merci-total.py`: Orquestador maestro del pipeline de compilación.
- `merci-publish.py` y `merci-promote.py`: Motor SSG (Static Site Generation - Generación de Sitios Estáticos) y curación de contenidos.
- `merci-backup.py`: Creación instantánea de copias de seguridad locales en formato ZIP.
- `merci-optimizer.py`: Optimización de imágenes a WebP.
- `merci-linkcheck.py`: Rastreo DAST (Dynamic Application Security Testing - Pruebas Dinámicas de Seguridad de Aplicaciones) de enlaces rotos.

---
*Desarrollado bajo licencia MIT.*