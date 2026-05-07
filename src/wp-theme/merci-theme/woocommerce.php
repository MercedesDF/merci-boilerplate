<?php
// Resolutor dinámico de versiones
$root_dir = dirname(ABSPATH) . '/miproyecto.com/public';
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
<body <?php body_class('theme-body page'); ?>>
    <div id="top" tabindex="-1" style="position: absolute; top: 0; left: 0;"></div>
    <header class="header">
        <a href="/" class="header__brand">
            <img src="/assets/images/logo.webp?v=2" alt="miproyecto" class="header__logo" width="263" height="65">
        </a>
        <button class="header__toggle" id="menu-toggle" aria-label="Abrir menú" aria-expanded="false">
            <span class="header__toggle-icon"></span>
        </button>
        <nav class="header__nav nav" id="main-nav" aria-label="Navegación principal">
            <a href="/" class="nav__link">Home</a>
            <a href="/biblioteca/" class="nav__link">Biblioteca</a>
            <a href="/sobre-mi/" class="nav__link">Sobre Mí</a>
            <a href="/blog/" class="nav__link" aria-label="Ir a la portada del Blog">Blog</a>
            <a href="/art-de-cote/" class="nav__link">Art de Coté</a>
            <a href="/blog/tienda/" class="nav__link">Tienda</a>
            <a href="/contacto/" class="nav__link">Contacto</a>
        </nav>
    </header>

    <main class="main" id="main">
        <section class="hero">
            <h1 class="hero__title">Tienda</h1>
            <p class="hero__subtitle">Catálogo de recursos, herramientas y merchandising oficial.</p>
        </section>
        <section class="section">
            <?php if ( is_product() ) : ?>
                <a href="<?php echo esc_url( get_permalink( wc_get_page_id( 'shop' ) ) ); ?>" class="card__back-link">← Volver a la Tienda</a>
            <?php endif; ?>

            <!-- Aquí es donde inyectamos la magia de WooCommerce -->
            <?php woocommerce_content(); ?>
        </section>
    </main>

    <footer class="footer" style="text-align: left; padding-bottom: 6rem;">
        <div class="footer__text">
            <a href="#top" style="color: inherit; text-decoration: underline; font-weight: 600; display: inline-block; margin-bottom: 1rem;">↑ Volver arriba</a><br>
            &copy; 2026 <strong>miproyecto</strong> — Base de código abierto bajo Licencia MIT.
        </div>
    </footer>
    <aside class="merci-ui" id="merci-ui" aria-label="Asistente virtual Merci">
        <div class="merci-ui__message-box" id="merci-message" aria-live="polite" aria-hidden="true"><span class="merci-ui__message-text"></span></div>
        <button class="merci-ui__trigger" aria-controls="merci-message" aria-expanded="false"><img class="merci-ui__avatar" src="/assets/images/Merci-en-la-nube.webp" alt="Interactuar con el asistente" width="80" height="80" loading="lazy"></button>
    </aside>
    <?php wp_footer(); ?>
</body>
</html>