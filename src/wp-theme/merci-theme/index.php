<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <?php
    // Rompe-cachés dinámico para scripts: lee la fecha de modificación del archivo
    $root_dir = dirname(ABSPATH) . '/merci-boilerplate.es/public';
    $css_v = time();
    $js_merci_v = time();
    $js_main_v = time();
    ?>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Favicon explícito para la capa dinámica y Mercí -->
    <link rel="icon" href="/favicon.ico?v=3" type="image/x-icon">
    <link rel="stylesheet" href="/css/main.css?v=<?php echo $css_v; ?>">
    <script src="/js/MerciController.js?v=<?php echo $js_merci_v; ?>" defer></script>
    <script src="/js/main.js?v=<?php echo $js_main_v; ?>" defer></script>

    <?php 
    wp_head(); 
    ?>
</head>
<?php
$body_id = 'page-blog';
if ( is_page('tienda') || (function_exists('is_shop') && is_shop()) ) {
    $body_id = 'page-tienda';
} elseif ( is_category('art-de-cote') || (is_singular() && has_category('art-de-cote')) ) {
    $body_id = 'page-art-de-cote';
}
?>
<body id="<?php echo $body_id; ?>" <?php body_class('theme-body page'); ?>>

    <!-- Ancla invisible WAI-ARIA para Volver Arriba -->
    <div id="top" tabindex="-1" style="position: absolute; top: 0; left: 0;"></div>
    <header class="header">
        <a href="/" class="header__brand">
            <img src="/assets/images/logo.webp?v=2" alt="merci-boilerplate" class="header__logo" width="263" height="65">
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
        <?php 
        // 1. Inyección de Cabeceras Estilo "Boilerplate" para Vistas Dinámicas
        $header_title = '';
        $header_desc = '';
        $hero_modifier = '';

        if ( is_page('tienda') || (function_exists('is_shop') && is_shop()) ) {
            $header_title = 'Tienda';
            $header_desc = 'Catálogo de recursos, herramientas y merchandising oficial del entorno Merci Boilerplate.';
        } elseif ( is_home() || is_archive() ) {
            $header_title = 'Blog';
            $header_desc = 'Bitácora cronológica, diario de desarrollo y artículos de marketing.';
            $hero_modifier = ' hero--compact';
        }

        if ( $header_title ) : 
        ?>
            <section class="hero<?php echo $hero_modifier; ?>">
                <h1 class="hero__title"><?php echo $header_title; ?></h1>
                <p class="hero__subtitle"><?php echo $header_desc; ?></p>
            </section>
        <?php endif; ?>

        <!-- Atomización definitiva: Usamos el componente estructural genérico -->
        <section class="section">
        <?php 
        // 2. Bucle principal de contenido (The Loop)
        if ( have_posts() ) :
        ?>
            
            <?php if ( is_singular() ) : ?>
                <!-- VISTA DE LECTURA (Artículo individual) -->
                <?php while ( have_posts() ) : the_post(); ?>
                    <?php $es_blog_individual = is_singular() && has_category('blog'); ?>
                    
                    <?php if ( $es_blog_individual ) : ?>
                        <!-- VISTA DE LECTURA LIGERA (Blog DevRel) -->
                        <article class="prose">
                            <a href="/blog/" class="prose__back-link">← Volver al Blog</a>
                            <header class="prose__header">
                                <h1 class="prose__title"><?php the_title(); ?></h1>
                            </header>
                            <div class="prose__content">
                                <?php the_content(); ?>
                            </div>
                        </article>
                    <?php else : ?>
                        <!-- VISTA DE LECTURA DENSA (Biblioteca / Art de Coté) -->
                        <article class="card card--booklet">
                            <a href="/blog/" class="card__back-link">← Volver al Blog</a>
                        <header class="card__header">
                                <?php if ( ! $header_title ) : ?>
                                <h1 class="card__title card__title--highlight"><?php the_title(); ?></h1>
                                <?php endif; ?>
                                <a href="/descargas/<?php echo $post->post_name; ?>.pdf" class="card__download" download>📄 Descargar Edición PDF</a>
                            </header>
                            <div class="card__content">
                                <?php the_content(); ?>
                            </div>
                        </article>
                    <?php endif; ?>
                <?php endwhile; ?>
            <?php else : ?>
                <!-- VISTA DE LISTADO (Blog Cronológico Vertical) -->
            <div class="blog-feed">
                    <?php while ( have_posts() ) : the_post(); ?>
                    <article class="blog-feed__article" id="post-<?php the_ID(); ?>">
                        <header class="blog-feed__header">
                            <span class="blog-feed__meta"><?php echo get_the_date(); ?></span>
                            <h2 class="blog-feed__title"><a href="<?php the_permalink(); ?>" aria-label="Leer artículo completo: <?php echo esc_attr(get_the_title()); ?> (<?php echo esc_attr(get_the_date()); ?>)"><?php the_title(); ?></a></h2>
                        </header>
                        <div class="blog-feed__excerpt">
                                <?php the_excerpt(); ?>
                            </div>
                        </article>
                    <?php endwhile; ?>
                </div>
            <?php endif; ?>

        <?php 
        else : 
            echo '<p>No se encontraron artículos.</p>';
        endif; 
        // Fin de "The Loop"
        ?>
        </section>
    </main>
    <footer class="footer">
        <div class="footer__links">
            <a href="https://www.linkedin.com/in/mercedesdf-ingenieria/" target="_blank" rel="noopener noreferrer" class="footer__link">LinkedIn</a>
            <a href="https://github.com/MercedesDF" target="_blank" rel="noopener noreferrer" class="footer__link">GitHub</a>
            <a href="https://github.com/MercedesDF/merci-boilerplate" target="_blank" rel="noopener noreferrer" class="footer__link">Merci Boilerplate</a>
        </div>
        <div class="footer__text">
            <a href="#top">↑ Volver arriba</a><br>
            &copy; 2026 <strong>merci-boilerplate</strong> — Base de código abierto bajo Licencia MIT.
        </div>
    </footer>

    <!-- Asistente Virtual -->
    <aside class="merci-ui" id="merci-ui" aria-label="Asistente virtual Merci">
        <div class="merci-ui__message-box" id="merci-message" aria-live="polite" aria-hidden="true">
            <span class="merci-ui__message-text"></span>
        </div>
        <button class="merci-ui__trigger" aria-controls="merci-message" aria-expanded="false">
            <img class="merci-ui__avatar" src="/assets/images/Merci-en-la-nube.webp" alt="Interactuar con el asistente" width="80" height="80" loading="lazy">
        </button>
    </aside>

    <!-- wp_footer() es obligatorio para scripts de cierre y barra de administración (si estás logueada) -->
    <?php wp_footer(); ?>
</body>
</html>