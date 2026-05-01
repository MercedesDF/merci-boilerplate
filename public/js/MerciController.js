/**
 * MerciController.js
 * @description Controlador interactivo del asistente Merci.
 * Combina la máquina de estados con mensajes aleatorios bajo estricta accesibilidad (WAI-ARIA).
 */
class MerciController {
    
    constructor(containerId) {
        this.container = document.getElementById(containerId);

        if (!this.container) {
            console.warn(`[Merci] Contenedor #${containerId} no encontrado. El asistente permanecerá en reposo.`);
            return;
        }

        // Cacheamos los elementos BEM interactivos
        this.trigger = this.container.querySelector('.merci-ui__trigger');
        this.messageBox = this.container.querySelector('.merci-ui__message-box');
        this.messageText = this.container.querySelector('.merci-ui__message-text');

        // QUÉ HACE: Carga el "cerebro" específico basándose en la URL actual.
        // POR QUÉ: Permite respuestas contextuales sin consultas pesadas al servidor.
        this.messages = this._loadKnowledgeBase();

        this.state = 'idle'; 
        this.timeoutId = null; // Guarda la referencia del temporizador para no superponer mensajes

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
     * QUÉ HACE: Analiza la ruta del navegador y devuelve el diccionario adecuado.
     * POR QUÉ: Principio de Responsabilidad Única. Aísla los textos de la lógica de la UI.
     * Al usar .includes(), nos aseguramos de atrapar también las subrutas (ej. un artículo específico).
     */
    _loadKnowledgeBase() {
        const path = window.location.pathname;

        if (path === '/' || path === '/index.html') {
            return [
                '¡Hola! Me llamo Mercí, asistente de merci-boilerplate👋',
                'merci-boilerplate es la base de este proyecto🚀',
                'Todo operando a 100/100 en Web Vitals ⚡'
            ];
        } else if (path.includes('/biblioteca')) {
            return [
                'Bienvenida a la Biblioteca 📚',
                'Aquí guardamos el conocimiento inmutable.',
                'Recuerda que puedes descargar los artículos en PDF 📄'
            ];
        } else if (path.includes('/art-de-cote')) {
            return [
                'Estás en Art de Coté 🎨',
                'I+D, experimentos y hallazgos colaterales 🧪',
                'Esta zona la sirve WordPress de forma aislada 🛡️'
            ];
        } else if (path.includes('/tienda')) {
            return [
                '¡Bienvenid@ a la Tienda! 🛒',
                'Merchandising y catálogo oficial.',
                'Gestionado por WooCommerce bajo el capó 🛍️'
            ];
        } else if (path.includes('/blog')) {
            return [
                'Estás en el Blog ✍️',
                'Nuestra bitácora dinámica impulsada por PHP.',
                'Nginx actúa como proxy inverso aquí 🔄'
            ];
        } else if (path.includes('/contacto')) {
            return [
                'Estás en la zona de contacto.',
                '¿Quieres hablar con merci-boilerplate, el cerebro de la web? 📨',
                'No dejes de visitar la Biblioteca, la fuente de saber.😊'
            ];
        }

        // Matriz por defecto de contingencia
        return [
            '¡Hola! 👋',
            'Soy Merci, tu asistente DevSecOps 🤖',
            'Mi código es Vanilla JS puro 💻'
        ];
    }

    handleInteraction() {
        // Escoge un mensaje aleatorio de la matriz
        const randomMsg = this.messages[Math.floor(Math.random() * this.messages.length)];
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
