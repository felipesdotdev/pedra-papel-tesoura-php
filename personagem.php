<?php
declare(strict_types=1);
?>
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Explore o personagem low poly em 3D.">
    <title>Personagem 3D · Pedra, papel e tesoura</title>
    <link rel="stylesheet" href="assets/estilo.css">
</head>
<body>
<main class="container">
    <header>
        <a class="marca" href="index.php">✊ ✋ ✌️ <span>Pedra, papel e tesoura</span></a>
        <a href="index.php">Voltar ao jogo</a>
    </header>
    <section class="intro">
        <p class="etiqueta">DO BLENDER PARA O NAVEGADOR</p>
        <h1>Seu personagem, em 3D.</h1>
        <p>Arraste para girar e use a roda do mouse ou dois dedos para aproximar. Você também pode usar os controles abaixo.</p>
    </section>
    <?php require __DIR__ . '/includes/personagem.php'; ?>
    <footer>Personagem low poly · Visualização interativa</footer>
</main>
</body>
</html>
