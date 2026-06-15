---
titulo: "Showcase: Inyección Multimedia"
descripcion: "Prueba de renderizado nativo de imágenes responsivas y vídeos HTML5 en la arquitectura estática."
tipo: "proyecto"
tema: "Proyectos Satélite"
subtema: "Pruebas de Estrés"
fecha: "2026-06-14"
estado: "publicado"
alt_portada: "Pantallas de visualización de vídeos e imágenes"
destacado: "true"
---

Esta es la primera publicación dentro del nuevo ecosistema **Proyectos Satélite**. El objetivo principal de este documento es poner a prueba las reglas de preprocesado multimedia definidas en `merci-publish.py` y las clases BEM responsivas (`multimedia-video`).

## Prueba 1: Imagen Responsiva

A continuación, una imagen tradicional. WeasyPrint la convertirá al PDF y el HTML la mostrará sin problemas.

![Camiseta DevSecOps con logos](/assets/images/camiseta-devsecops.webp){: .aspect-square width="2048" height="2048" loading="lazy" }

## Prueba 2: Reproductor de Vídeo HTML5 (Zero-Bloat)

Markdown no soporta vídeos de manera nativa, pero nuestro conversor en `merci-publish.py` está programado para detectar enlaces a `.mp4` y `.webm` disfrazados de imágenes e inyectar el código HTML5 con la clase `.multimedia-video`, añadiendo un *fallback* automático para el PDF (que no puede reproducir vídeo).

![Demostración del Agente Merci](/assets/videos/funcionamiento-merci-bibliotecario.mp4)

---

### 💡 El Aprendizaje / Deuda Técnica
La inyección mediante Expresiones Regulares en Python permite a los redactores no tener que saber escribir etiquetas `<video>` a mano. Al usar la sintaxis nativa de imagen de Markdown, el código fuente se mantiene limpio, y es el SSG quien asume el peso de la compilación HTML5.
