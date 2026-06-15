#!/bin/bash
# merci-down.sh - Apagado total del Ecosistema Merci
# QUÉ HACE: Destruye la sesión de Tmux y apaga los contenedores Docker en segundo plano.

echo "🛑 [Merci Down] Apagando la Matrix..."

# 1. Matar la sesión de Tmux (apaga LM Studio, LiteLLM, Web Server, SRE y Watcher)
tmux kill-session -t merci 2>/dev/null
echo "✅ [Tmux] Servicios locales (IA, Web, SRE, Watcher) detenidos."

# 2. Apagar la infraestructura de observabilidad en Docker
(cd observabilidad && docker compose down)

echo "💤 [Éxito] Entorno DevSecOps apagado limpiamente. Fricción cero."