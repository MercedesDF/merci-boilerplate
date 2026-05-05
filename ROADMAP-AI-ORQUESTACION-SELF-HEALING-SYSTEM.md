# 🗺️ ROADMAP: AI ORCHESTRATION & SELF-HEALING SYSTEM

Este roadmap marca la evolución de merci-boilerplate.es de un sitio estático a una plataforma orquestada por IA.  

## Fase 1: Cimientos y Conectividad (Semanas 1-2)

- [ ] Setup de Modelos (Hybrid Stack): Configurar Ollama para ejecución local y LiteLLM para fallback con Gemini Flash API.

- [ ] Directorio del Cerebro: Crear /merci-brain para centralizar los agentes de Python.

- [ ] Estandarización de Prompts: Crear /laboratorio/prompts con las reglas de estilo y arquitectura para que las IAs mantengan la coherencia del repo.  

## Fase 2: El Agente Auditor (Self-Healing Base) (Semanas 3-4)

- [ ] Evolución de merci-audit.py: Integrar IA para que el script no solo detecte errores, sino que sugiera el comando de reparación.  

- [ ] IA-Fix Workflow: Crear GitHub Action que dispare una corrección automática de IA ante fallos de Linter o formato de imágenes.  

- [ ] WebP Automation: Implementar agente que vigile /assets/images y convierta automáticamente cualquier subida a .webp optimizado.  

## Fase 3: Orquestación de Contenidos y Docs (Semanas 5-6)

- [ ] Agente Bibliotecario: Automatizar la creación de cuadernillos en /biblioteca a partir de notas rápidas en Markdown.  

- [ ] Sync SSOT (Single Source of Truth): Agente que verifique que el README.md y los /docs están siempre sincronizados tras cada cambio de código.  

- [ ] AI-Changelog: Generación automática de historial de cambios realizados por agentes en /docs/CHANGELOG_AI.md.

## Fase 4: Observabilidad y SRE IA (Semanas 7-8)

- [ ] Dashboard de Confianza: Implementar Grafana para visualizar cuántos cambios de IA han sido aprobados vs. rechazados.

- [ ] Chaos Engineering con IA: Script que use la IA para simular fallos en el merci-boilerplate y verificar que el sistema de rollback funciona.  

- [ ] Hardening Automation: Agente que audite el cumplimiento de la docs/checklist-hardening.md de forma continua.  

# 🛠️ STACK TECNOLÓGICO DEL ROADMAP

- Orquestador: Python 3.10+ (Framework: LangChain / LiteLLM).  

- Modelos: Llama 3 (Local) & Gemini Flash (Cloud).

- CI/CD: GitHub Actions (custom workflows).

- Infra: Docker Compose + Digital Ocean Droplet.