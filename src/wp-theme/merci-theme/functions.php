<?php
/**
 * Merci Theme - functions.php
 * Escudo de rendimiento y enlazador de assets estáticos (Fase 4.2).
 * 
 * NOTA ARQUITECTÓNICA: Este archivo tiene la responsabilidad exclusiva 
 * de bloquear la inyección de código basura de WP (WordPress) y enlazar 
 * el CSS compilado del núcleo estático.
 */

// =========================================================================
// 1. LIMPIEZA DE CABECERA (Bloqueo de código basura)
// =========================================================================

// Eliminar el soporte nativo de emojis (inyecta JS y CSS innecesario en el DOM)
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');

/**
 * Función para desencolar (dequeue) estilos masivos que WP inyecta por defecto.
 */
function merci_limpiar_estilos_por_defecto() {
    // Elimina el CSS de la librería de bloques (Gutenberg)
    wp_dequeue_style('wp-block-library');
    wp_dequeue_style('wp-block-library-theme');
    // Elimina el CSS masivo de los bloques de WooCommerce (causa #1 de pérdida de rendimiento)
    wp_dequeue_style('wc-blocks-style');
    wp_dequeue_style('wc-blocks-vendors-style');
    // Elimina el CSS de variables globales (theme.json inyectado en línea)
    wp_dequeue_style('global-styles');
    // Elimina estilos clásicos residuales
    wp_dequeue_style('classic-theme-styles');
}
// Enganchamos nuestra función de limpieza al momento exacto en que WP carga estilos, 
// dándole una prioridad de '100' para asegurarnos de que se ejecute al final y pise a los demás.
add_action('wp_enqueue_scripts', 'merci_limpiar_estilos_por_defecto', 100);

// Eliminar la inyección forzada del motor de global-styles en línea
remove_action('wp_enqueue_scripts', 'wp_enqueue_global_styles');
remove_action('wp_body_open', 'wp_enqueue_global_styles');

// =========================================================================
// 2. ENLACE CON EL NÚCLEO ESTÁTICO
// =========================================================================

function merci_cargar_assets_estaticos() {
    // Obtenemos la URL oficial y segura de WordPress (ej. https://{{DOMINIO}}/blog o http://localhost/blog).
    // Al usar home_url(), esquivamos la inyección del puerto interno 8080 que Varnish hace en $_SERVER['HTTP_HOST'].
    // Luego, eliminamos el sufijo '/blog' para apuntar a la raíz estática pública.
    $domain_root = preg_replace('#/blog/?$#', '', home_url());
    // wp_enqueue_style('merci-core-styles', $domain_root . '/css/main.css', array(), '1.0.1', 'all');
    // Encolar el JavaScript unificado (el filtro de defer lo procesará automáticamente)
    // wp_enqueue_script('merci-core-js', $domain_root . '/js/main.js', array(), '1.0.0', true);
}
add_action('wp_enqueue_scripts', 'merci_cargar_assets_estaticos');

// =========================================================================
// 2.5 RENDIMIENTO: CARGA DIFERIDA DE SCRIPTS (Fase 4.4)
// =========================================================================

// Forzar atributo 'defer' en todos los scripts del frontend para no bloquear el renderizado
function merci_defer_js_frontend($tag, $handle) {
    // No tocar los scripts si estamos en el panel de administración
    if (is_admin() || strpos($tag, ' defer') !== false) {
        return $tag;
    }
    // Reemplazar ' src' por ' defer src'
    return str_replace(' src', ' defer src', $tag);
}
add_filter('script_loader_tag', 'merci_defer_js_frontend', 10, 2);

// =========================================================================
// 3. WOOCOMMERCE EN MODO CATÁLOGO (Fase 4.3)
// =========================================================================

// Declarar soporte básico para evitar que WP/WooCommerce lance errores y delegar <title>
function merci_theme_setup() {
    add_theme_support('woocommerce');
    add_theme_support('title-tag'); // Renderizado nativo del título (Fase 2 y limpieza de deprecaciones)
}
add_action('after_setup_theme', 'merci_theme_setup');

// Escudo de rendimiento: Eliminar botones de "Añadir al carrito"
remove_action('woocommerce_after_shop_loop_item', 'woocommerce_template_loop_add_to_cart', 10);
remove_action('woocommerce_single_product_summary', 'woocommerce_template_single_add_to_cart', 30);

// Desencolar scripts pesados del carrito (AJAX) que WC inyecta globalmente
function merci_limpiar_scripts_wc() {
    wp_dequeue_script('wc-cart-fragments');
    wp_dequeue_script('wc-add-to-cart');
    wp_dequeue_script('woocommerce');
    wp_dequeue_script('wc-order-attribution');
    
    // Erradicar jQuery del frontend para mantener la regla de 0 dependencias
    wp_deregister_script('jquery');
}
add_action('wp_enqueue_scripts', 'merci_limpiar_scripts_wc', 100);

// Desencolar ABSOLUTAMENTE TODO el CSS por defecto de WooCommerce
add_filter( 'woocommerce_enqueue_styles', '__return_empty_array' );

// Ocultar el título duplicado ("Tienda") nativo de WooCommerce (ya tenemos nuestro Hero)
add_filter( 'woocommerce_show_page_title', '__return_false' );

// Encapsular la purga de inyecciones inline en el hook 'init' para garantizar
// que se ejecuten DESPUÉS de que los plugins (WC/WP) las hayan registrado.
function merci_purgar_inyecciones_inline() {
    // Eliminar script inline de detección de JS de WooCommerce (Generador de violación CSP - Prioridad 0)
    remove_action('wp_head', 'wc_javascript_is_active', 0);
    
    // Eliminar las Speculation Rules de WP (inyectan bloques <script> bloqueados por la CSP)
    remove_action('wp_head', 'wp_print_speculation_rules');
    remove_action('wp_footer', 'wp_print_speculation_rules');
    
    // Eliminar filtros SVG de Gutenberg que se inyectan en línea en el body/footer
    remove_action('wp_body_open', 'wp_global_styles_render_svg_filters');
    remove_action('wp_footer', 'wp_global_styles_render_svg_filters');
}
add_action('init', 'merci_purgar_inyecciones_inline');

// =========================================================================
// 4. HARDENING Y SEGURIDAD (Fase 5.2)
// =========================================================================

// Ocultar la versión exacta de WordPress (Security by Obscurity)
remove_action('wp_head', 'wp_generator');

// Eliminar enlaces a manifiestos no utilizados (Windows Live Writer y RSD)
remove_action('wp_head', 'wlwmanifest_link');
remove_action('wp_head', 'rsd_link');

// Desactivar la API XML-RPC (Cierra un vector crítico de ataques de fuerza bruta)
add_filter('xmlrpc_enabled', '__return_false');

// Eliminar scripts de oEmbed y enlaces de la API REST del head (Ruido innecesario)
remove_action('wp_head', 'wp_oembed_add_discovery_links');
remove_action('wp_head', 'wp_oembed_add_host_js');
remove_action('wp_head', 'rest_output_link_wp_head', 10);
remove_action('template_redirect', 'rest_output_link_header', 11);

// Ofuscar mensajes de error en el inicio de sesión (Evita enumeración de usuarios)
function merci_ofuscar_errores_login() {
    return 'Credenciales incorrectas.';
}
add_filter('login_errors', 'merci_ofuscar_errores_login');

// Desactivar la barra de administración en el frontend para evitar inyecciones ocultas ("Tabs Fantasma")
add_filter('show_admin_bar', '__return_false');

// =========================================================================
// 5. AUTO-CONFIGURACIÓN DEL BOILERPLATE (Infraestructura como Código)
// =========================================================================

function merci_boilerplate_auto_setup() {
    // 1. Configurar Enlaces Permanentes (Permalinks) a "Nombre de la entrada"
    if (get_option('permalink_structure') !== '/%postname%/') {
        global $wp_rewrite;
        update_option('permalink_structure', '/%postname%/');
        $wp_rewrite->set_permalink_structure('/%postname%/');
        $wp_rewrite->flush_rules();
    }

    // 2. Autocrear las categorías requeridas por el enrutamiento del menú
    if (!term_exists('fichas', 'category')) {
        wp_insert_term('Fichas Técnicas', 'category', array('slug' => 'fichas'));
    }
    if (!term_exists('art-de-cote', 'category')) {
        wp_insert_term('Art de Coté', 'category', array('slug' => 'art-de-cote'));
    }
    if (!term_exists('blog', 'category')) {
        wp_insert_term('Blog', 'category', array('slug' => 'blog'));
    }

    // 3. Purgar contenido basura por defecto ("¡Hola, mundo!" y "Página de ejemplo")
    // Localizamos los posts por su ID habitual en instalaciones nuevas y validamos su slug
    $default_post = get_post(1);
    if ($default_post && in_array($default_post->post_name, array('hola-mundo', 'hello-world'))) {
        wp_delete_post(1, true); // true = forzar borrado sin pasar por la papelera
    }
    $default_page = get_post(2);
    if ($default_page && in_array($default_page->post_name, array('pagina-ejemplo', 'pagina-de-ejemplo', 'sample-page'))) {
        wp_delete_post(2, true);
    }
}
// after_switch_theme asegura que la carga a base de datos ocurra solo 1 vez al activar el tema
add_action('after_switch_theme', 'merci_boilerplate_auto_setup');

// =========================================================================
// 6. SEO BÁSICO Y METADATOS DINÁMICOS (Fase 6.3)
// =========================================================================

function merci_inyectar_metadatos_seo() {
    // Prevenir inyección si en un futuro se usa un plugin de SEO
    if ( class_exists( 'WPSEO_Frontend' ) || class_exists( 'RankMath' ) ) {
        return;
    }

    $descripcion = '';

    if ( function_exists('is_shop') && ( is_shop() || is_product_category() ) ) {
        $descripcion = 'Catálogo oficial de merchandising y productos del ecosistema Merci Boilerplate.';
    } elseif ( is_front_page() || is_home() ) {
        $descripcion = get_bloginfo( 'description' );
    } elseif ( is_category() || is_tag() ) {
        $descripcion = strip_tags( term_description() );
        if ( empty( $descripcion ) ) {
            $descripcion = 'Publicaciones y artículos de la categoría ' . single_term_title( '', false );
        }
    } elseif ( is_singular() ) {
        global $post;
        $descripcion = wp_trim_words( $post->post_excerpt, 25, '' );
        if ( empty( $descripcion ) ) {
            $descripcion = wp_trim_words( $post->post_content, 25, '' );
        }
    }

    // Limpieza básica de la cadena y fallback
    $descripcion = trim( esc_attr( strip_tags( str_replace( array( "\r", "\n" ), ' ', $descripcion ) ) ) );

    if ( empty( $descripcion ) ) {
        $descripcion = 'Contenido dinámico gestionado por la arquitectura Merci Boilerplate.';
    }

    echo '<meta name="description" content="' . $descripcion . '">' . "\n";

    // Inyección de JSON-LD Dinámico y Contextual (SEO Avanzado)
    $domain_root = preg_replace('#/blog/?$#', '', home_url());
    $json_ld = array(
        "@context" => "https://schema.org",
        "name"     => "{{DOMINIO}}"
    );

    // Si es un artículo individual, usamos el esquema de Artículo
    if ( is_singular() ) {
        $json_ld["@type"] = "Article";
        $json_ld["url"] = get_permalink();
        $json_ld["headline"] = get_the_title();
    } else {
        $json_ld["@type"] = "WebSite";
        $json_ld["url"] = $domain_root;
    }
    
    echo '<script type="application/ld+json">' . wp_json_encode($json_ld) . '</script>' . "\n";
}
add_action( 'wp_head', 'merci_inyectar_metadatos_seo', 5 );

// =========================================================================
// 7. ARQUITECTURA DE LA INFORMACIÓN (Segregación de Feeds)
// =========================================================================

/*
 * QUÉ HACE: Restringe el feed principal del blog para mostrar ÚNICAMENTE la categoría "Blog".
 * POR QUÉ: Convierte la portada dinámica en un espacio exclusivo (Whitelist), evitando que
 * colecciones independientes como "Art de Coté" u otras taxonomías contaminen el feed.
 */
function merci_filtrar_feed_principal($query) {
    // Solo aplicamos esta regla en la página principal del blog (is_home)
    // y solo a la consulta principal (is_main_query), no a menús o widgets.
    if ( ! is_admin() && $query->is_home() && $query->is_main_query() ) {
        
        // QUÉ HACE: Delega la resolución del slug directamente al motor principal de WordPress.
        // POR QUÉ: Evita el "fallo abierto" (mostrar todos los posts) si el ID de la categoría falla al cargarse.
        // Si la categoría 'blog' no existe o está vacía, se mostrarán 0 posts (Fallo Seguro).
        $query->set( 'category_name', 'blog' );
    }
}
// Enganchamos nuestra función al 'hook' de WordPress que se dispara antes de obtener los posts.
add_action( 'pre_get_posts', 'merci_filtrar_feed_principal' );