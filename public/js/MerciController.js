/**
 * MerciController.js
 * @description Controlador interactivo del asistente Merci.
 * Combina la máquina de estados con mensajes aleatorios bajo estricta accesibilidad (WAI-ARIA).
 */
class MerciController {
    
    constructor(containerId) {
        this.container = document.getElementById(containerId);

        if (!this.container) {
            console.debug(`[Merci] Contenedor #${containerId} no encontrado. El asistente permanecerá en reposo.`);
            return;
        }

        // Cacheamos los elementos BEM interactivos
        this.trigger = this.container.querySelector('.merci-ui__trigger');
        this.messageBox = this.container.querySelector('.merci-ui__message-box');
        this.messageText = this.container.querySelector('.merci-ui__message-text');

        // QUÉ HACE: Carga la base genérica primero y luego intenta conectar el lóbulo frontal (JSON).
        this.messages = this._loadStandardKnowledgeBase();
        this._connectBrain();

        this.state = 'idle'; 
        this.timeoutId = null; // Guarda la referencia del temporizador para no superponer mensajes
        this.lastMsgIndex = -1; // Historial para evitar repetir la misma frase 2 veces seguidas

        this.init();
    }

    init() {
        // QUÉ HACE: Escucha el evento 'click' en el avatar.
        // POR QUÉ: Al usar un <button>, esto también captura automáticamente la pulsación 
        // de la tecla "Enter" o "Espacio" de usuarios de teclado, gratis.
        if (this.trigger) {
            this.trigger.addEventListener('click', () => this.handleInteraction());
        }
        console.log('[Merci] Controlador inicializado correctamente.');
    }

    /**
     * QUÉ HACE: Lee el archivo estático generado por Python (Shift-Left AI) en segundo plano.
     * POR QUÉ: Si el usuario está en un artículo, Merci sustituirá sus saludos genéricos
     * por la frase inteligente pre-generada por Gemini, sin gastar cuota de API ni latencia.
     */
    async _connectBrain() {
        try {
            const response = await fetch('/js/brain_data.json');
            if (!response.ok) return;
            
            const brainData = await response.json();
            
            // QUÉ HACE: Cede el control al hilo principal (Yielding) tras el parseo del JSON.
            // POR QUÉ: Evita que la asignación en memoria sature el límite de 50ms de la CPU.
            await new Promise(resolve => setTimeout(resolve, 0));
            
            const currentPath = window.location.pathname;
            
            if (brainData[currentPath]) {
                let aiMessage = brainData[currentPath];
                // Degradación elegante: Si la cuota falló durante la compilación, limpiamos el prefijo.
                if (aiMessage.startsWith('[Fallback]')) {
                    aiMessage = aiMessage.replace('[Fallback]', '').trim();
                }
                // Si hay respuesta de la IA, la inyectamos como opción prioritaria en lugar de sobrescribir todo,
                // para evitar que se quede sin opciones y repita siempre lo mismo en la biblioteca.
                this.messages.unshift(aiMessage);
                console.log('[Merci Brain] Sinapsis conectada. Frase contextual cargada.');
            }
        } catch (error) {
            console.log('[Merci Brain] Usando base genérica (JSON no encontrado).');
        }
    }

    /**
     * QUÉ HACE: Analiza la ruta del navegador y devuelve el diccionario adecuado.
     * POR QUÉ: Principio de Responsabilidad Única. Aísla los textos de la lógica de la UI.
     * Al usar .includes(), nos aseguramos de atrapar también las subrutas (ej. un artículo específico).
     */
    _loadStandardKnowledgeBase() {
        const path = window.location.pathname;

        if (path === '/' || path === '/index.html') {
            return [
                'Operando al 100/100 en Core Web Vitals. Fricción cero.',
                'La arquitectura subyacente es de código abierto en GitHub.',
                'Cero dependencias. Cero JS bloqueante. Máximo rendimiento.'
            ];
        } else if (path.includes('/biblioteca')) {
            return [
                'Accediendo a la documentación técnica oficial.',
                'Los registros de la biblioteca son inmutables (Single Source of Truth).',
                'Los cuadernillos están compilados estáticamente para exportación limpia a PDF.'
            ];
        } else if (path.includes('/art-de-cote')) {
            return [
                'Sector Art de Coté: I+D y hallazgos paralelos.',
                'Estos experimentos están desacoplados del núcleo principal.',
                'Migrado desde WordPress a SSG para optimizar el mantenimiento.'
            ];
        } else if (path.includes('/tienda')) {
            return [
                'Tienda Headless desplegada. Backend aislado.',
                'El backend de WooCommerce procesa las transacciones de forma segura.',
                'El frontend mantiene un TBT de 0ms gracias a la arquitectura Zero-JS.'
            ];
        } else if (path.includes('/carrito')) {
            return [
                'Simulación de carrito activa. Formularios nativos sin AJAX.',
                'Entorno transaccional estático. Sin pasarelas de pago reales.',
                'Fíjate qué rápido carga sin los pesados scripts tradicionales.'
            ];
        } else if (path.includes('/checkout') || path.includes('/finalizar-comprar')) {
            return [
                'Simulación de caja (Checkout) activa.',
                'Finaliza la transacción de prueba en el entorno Zero-JS.',
                'Operaciones en entorno estático sin pasarelas de pago reales.'
            ];
        } else if (path.includes('/blog')) {
            return [
                'Accediendo a la bitácora dinámica impulsada por PHP.',
                'Nginx actúa como proxy inverso en este segmento.',
                'Zona de lecturas y actualizaciones.'
            ];
        } else if (path.includes('/contacto')) {
            return [
                'Protocolos de comunicación directa habilitados.',
                'Para transmisión de datos sensibles, utiliza la clave pública PGP.',
                'Revisa la biblioteca para documentación técnica adicional.'
            ];
        }

        // Matriz por defecto de contingencia
        return [
            'Asistente DevSecOps residente a la escucha.',
            'Sistema en estado nominal.',
            'Interfaz estática en Vanilla JS pura.'
        ];
    }

    handleInteraction() {
        // Toggle: Si ya está hablando, lo silenciamos/ocultamos y detenemos la ejecución
        if (this.state === 'speaking') {
            clearTimeout(this.timeoutId);
            this.sleep();
            return;
        }

        // Evitar repetir el mismo mensaje dos veces seguidas (pseudo-aleatorio)
        let newIndex;
        if (this.messages.length > 1) {
            do {
                newIndex = Math.floor(Math.random() * this.messages.length);
            } while (newIndex === this.lastMsgIndex);
            this.lastMsgIndex = newIndex;
        } else {
            newIndex = 0;
        }

        const randomMsg = this.messages[newIndex];
        this.speak(randomMsg);
    }

    speak(text) {
        this.state = 'speaking';
        
        // 1. Inyecta el texto
        this.messageText.textContent = text;
        
        // 2. Modifica el DOM para que el CSS actúe (hace visible el globo)
        this.messageBox.setAttribute('aria-hidden', 'false');
        this.trigger.setAttribute('aria-expanded', 'true');

        // QUÉ HACE: Reinicia el reloj para ocultar el mensaje.
        // POR QUÉ: Si el usuario hace clic 3 veces seguidas rápido, clearTimeout evita 
        // que el mensaje parpadee y se asegura de que dure 3 segundos exactos desde el último clic.
        clearTimeout(this.timeoutId);
        this.timeoutId = setTimeout(() => this.sleep(), 3500);
    }

    sleep() {
        this.state = 'idle';
        
        // Oculta el globo delegando la animación al CSS
        this.messageBox.setAttribute('aria-hidden', 'true');
        this.trigger.setAttribute('aria-expanded', 'false');
        
        // Nota: NO borramos el textContent aquí. 
        // Esto permite que el lector de pantalla termine de hablar y que 
        // la transición CSS de opacidad termine suavemente sin que el texto desaparezca de golpe.
    }
}
