/**
 * main.js - Lógica del Frontend (Vanilla JS)
 * Paradigma POO (Programación Orientada a Objetos) y principios SOLID.
 */

class NavigationController {
    /**
     * Inicializa el controlador del menú de navegación.
     * @param {string} toggleId - ID del botón hamburguesa.
     * @param {string} navId - ID del contenedor de navegación.
     */
    constructor(toggleId, navId) {
        this.menuToggle = document.getElementById(toggleId);
        this.mainNav = document.getElementById(navId);

        this.init();
    }

    /**
     * Vincula los eventos si los elementos requeridos existen en el DOM (Document Object Model - Modelo de Objetos del Documento).
     */
    init() {
        if (this.menuToggle && this.mainNav) {
            this.menuToggle.addEventListener('click', () => this.toggleMenu());
        }
    }

    /**
     * Alterna los estados de accesibilidad (WAI-ARIA) y las clases visuales BEM.
     */
    toggleMenu() {
        const isExpanded = this.menuToggle.getAttribute('aria-expanded') === 'true';
        this.menuToggle.setAttribute('aria-expanded', !isExpanded);
        this.menuToggle.classList.toggle('is-active');
        this.mainNav.classList.toggle('is-active');
    }
}

// Instanciación controlada al cargar el árbol de nodos
document.addEventListener('DOMContentLoaded', () => {
    // 1. Inicializamos el menú de navegación (tu código original)
    new NavigationController('menu-toggle', 'main-nav');
    
    // 2. Inicializamos a Merci solo si su script se ha cargado correctamente
    if (typeof MerciController !== 'undefined') {
        new MerciController('merci-ui');
    }
});
