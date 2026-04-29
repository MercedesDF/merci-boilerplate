# Bitácora de Proyecto: Merci Boilerplate

Documento central para el registro de decisiones arquitectónicas, resolución de problemas y evolución del código. (Formato: El Desafío -> La Maniobra -> El Aprendizaje).

## Registro cronológico

### AAAA-MM-DD — Instanciación del repositorio base

**Contexto:** Arranque de un nuevo proyecto utilizando la infraestructura fundacional de Merci Boilerplate. Se requiere limpiar las referencias del proyecto matriz y establecer el estado en blanco.

**Hecho:**
- Clonación del repositorio original.
- Ejecución destructiva de `python3 scripts/merci/merci-init.py`.
- Promoción de archivos documentales agnósticos (`README.md`, `instrucciones.md`).

**Motivo / criterio:** *Single Source of Truth*. Utilizar este script asegura que el nuevo proyecto no herede deuda técnica ni identidad visual del autor original, proveyendo un lienzo estricto DevSecOps desde el commit cero.

**Siguiente paso o deuda:** Configurar la base de datos local y revisar `docs/integracion-wordpress.md`.