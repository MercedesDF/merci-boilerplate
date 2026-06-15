#!/bin/bash
# merci-boot.sh - Orquestador de arranque del Ecosistema Merci (Tmux Bootstrapper)
# QUÉ HACE: Levanta toda la infraestructura local dividiendo una sola terminal en paneles.

SESSION="merci"

# Si la sesión de Tmux ya existe, simplemente nos conectamos a ella en lugar de duplicar servicios
tmux has-session -t $SESSION 2>/dev/null
if [ $? != 0 ]; then
    echo "🚀 [Merci Boot] Levantando infraestructura base..."
    
    # 1. Docker como Demonio (No necesita terminal abierta)
    (cd observabilidad && docker compose up -d)
    
    # 2. Crear sesión principal (Ventana 0: Consola de Trabajo)
    tmux new-session -d -s $SESSION -n "Matriz"
    
    # Habilitar soporte para ratón (Clics en pestañas y scroll)
    tmux set-option -t $SESSION mouse on
    
    tmux send-keys -t $SESSION:0 "source .venv/bin/activate && clear" C-m
    
    # 3. Ventana 1: Stack IA (LM Studio + LiteLLM divididos a la mitad)
    tmux new-window -t $SESSION:1 -n "IA-Stack"
    tmux send-keys -t $SESSION:1 "lms server start" C-m
    
    tmux split-window -h -t $SESSION:1
    tmux send-keys -t $SESSION:1 "source .venv/bin/activate && litellm --config observabilidad/router.yaml --port 4000" C-m
    
    # 4. Ventana 2: Servicios Base (SRE, Watcher SASS)
    tmux new-window -t $SESSION:2 -n "Servicios"
    tmux send-keys -t $SESSION:2 "source .venv/bin/activate && python3 scripts/merci/merci-watcher.py" C-m
    
    tmux split-window -h -t $SESSION:2
    tmux send-keys -t $SESSION:2 "source .venv/bin/activate && python3 scripts/merci/merci-sre.py" C-m
    
    # Volver al foco en la terminal de trabajo principal (Ventana 0)
    tmux select-window -t $SESSION:0
fi

# Entrar a la Matrix (conecta tu terminal a la sesión de tmux)
tmux attach-session -t $SESSION