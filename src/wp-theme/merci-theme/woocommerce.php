<?php
// Resolutor dinámico de versiones
$root_dir = dirname(ABSPATH) . '/tuempresa.es/public';
$css_v = time();
$js_merci_v = time();
$js_main_v = time();
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="/favicon.ico?v=3" type="image/x-icon">
    <link rel="stylesheet" href="/css/main.css?v=<?php echo $css_v; ?>">
    <script src="/js/MerciController.js?v=<?php echo $js_merci_v; ?>" defer></script>
    <script src="/js/main.js?v=<?php echo $js_main_v; ?>" defer></script>
    <?php wp_head(); ?>
</head>
<body id="page-tienda" <?php body_class('theme-body page'); ?>>
    <header class="header" id="top">
        <a href="/" class="header__brand">
            <img src="/assets/images/tu_logo.webp?v=1781768797" alt="tuempresa" class="header__logo" width="263" height="65" fetchpriority="low" decoding="async">
        </a>
        
        <?php 
        $cart_count = ( class_exists('WooCommerce') && !is_null(WC()->cart) ) ? WC()->cart->get_cart_contents_count() : 0;
        ?>
        <a href="<?php echo function_exists('wc_get_cart_url') ? esc_url(wc_get_cart_url()) : '/blog/carrito/'; ?>" class="header__cart-mobile" aria-label="Ver carrito">
            ☁️
            <?php if ( $cart_count > 0 ) : ?>
                <span class="header__cart-count"><?php echo $cart_count; ?></span>
            <?php endif; ?>
        </a>
        
        <button class="header__toggle" id="menu-toggle" aria-label="Abrir menú" aria-expanded="false">
            <span class="header__toggle-icon"></span>
        </button>
        <nav class="header__nav nav" id="main-nav" aria-label="Navegación principal">
            <a href="/" class="nav__link">Home</a>
            <a href="/biblioteca/" class="nav__link">Biblioteca</a>
            <a href="/sobre-mi/" class="nav__link">Sobre Mí</a>
            <a href="/blog/" class="nav__link" aria-label="Ir a la portada del Blog">Blog</a>
            <a href="/proyectos/" class="nav__link">Proyectos</a>
            <a href="/blog/tienda/" class="nav__link">Tienda</a>
            <a href="<?php echo function_exists('wc_get_cart_url') ? esc_url(wc_get_cart_url()) : '/blog/carrito/'; ?>" class="nav__link">🛒 Carrito</a>
            <a href="/contacto/" class="nav__link">Contacto</a>
        </nav>
    </header>

    <main class="main" id="main">
        <section class="hero">
            <h1 class="hero__title">Merci'<span class="hero__highlight">Shop</span></h1>
            <p class="hero__subtitle"><strong><em>la tienda no tienda</em></strong><br>merchandising oficial del ecosistema Mercí</p>
            <?php
            if ( function_exists('merci_get_sre_badge_html') && function_exists('is_shop') && is_shop() ) {
                echo merci_get_sre_badge_html('https://tuempresa.es/blog/tienda/');
            }
            ?>
            <?php if ( function_exists('is_shop') && is_shop() ) : ?>
                <div class="woocommerce">
                    <div class="woocommerce-notices-wrapper">
                        <div class="woocommerce-info woocommerce-info--store-notice">
                            ℹ️ <strong>Economía Simulada:</strong> <br>Este catálogo es una demostración técnica (E-commerce Zero-JS).<br>
                            Los precios están en <em>Merci-coins</em> <img src="/assets/images/tu_logo-80w.webp" alt="Llama" width="16" height="16" class="merci-coin-icon"><br>
                            ¡Añade al carrito sin miedo!
                        </div>
                    </div>
                </div>
            <?php endif; ?>
        </section>
        <section class="section">
            <?php if ( is_product() ) : ?>
                <a href="<?php echo esc_url( get_permalink( wc_get_page_id( 'shop' ) ) ); ?>" class="card__back-link">← Volver a la Tienda</a>
            <?php endif; ?>

            <!-- Aquí es donde inyectamos la magia de WooCommerce -->
            <?php woocommerce_content(); ?>
        </section>
    </main>

    <a href="#top" class="floating-back-to-top" aria-label="Volver arriba">↑</a>
    <footer class="footer">
        <div class="footer__links">
            <a href="https://linkedin.com/in/tu-perfil/" target="_blank" rel="noopener noreferrer" class="footer__link">LinkedIn</a>
            <a href="https://github.com/tu-usuario" target="_blank" rel="noopener noreferrer" class="footer__link">GitHub</a>
            <a href="https://github.com/MercedesDF/merci-boilerplate" target="_blank" rel="noopener noreferrer" class="footer__link">Merci Boilerplate</a>
        </div>
        <div class="footer__text">
            <a href="#top">↑ Volver arriba</a><br>
            &copy; 2026 <strong>tuempresa</strong> — Base de código abierto bajo Licencia MIT.
        </div>
    </footer>
    <aside class="merci-ui" id="merci-ui" aria-label="Asistente virtual Merci">
        <div class="merci-ui__message-box" id="merci-message" aria-live="polite" aria-hidden="true"><span class="merci-ui__message-text"></span></div>
        <button class="merci-ui__trigger" aria-controls="merci-message" aria-expanded="false"><img class="merci-ui__avatar" src="/assets/images/tu_avatar.webp?v=1781768797" alt="Interactuar con el asistente" width="80" height="80" fetchpriority="low" decoding="async"></button>
    </aside>
    <?php wp_footer(); ?>
</body>
</html>