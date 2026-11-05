<?php
require __DIR__ . '/includes/funcoes.php';
try { $jogador = exigirJogador(); } catch (Throwable $e) { falhaPagina($e); }
inicioPagina('Menu principal', 'menu');
?>
<link rel="stylesheet" href="assets/menu-cenario.css?v=1">
<header class="cabecalho-menu"><h1>Menu principal</h1></header>
<nav class="opcoes-menu" aria-label="Menu principal">
    <form action="criar_sala.php" method="post">
        <?php campoCsrf(); ?>
        <input type="hidden" name="modo" value="bot">
        <button class="opcao-menu selecionada" data-menu type="submit">Jogar contra o bot</button>
    </form>
    <form action="criar_sala.php" method="post">
        <?php campoCsrf(); ?>
        <input type="hidden" name="modo" value="multiplayer">
        <button class="opcao-menu" data-menu type="submit">Criar sala</button>
    </form>
    <a class="opcao-menu" data-menu href="entrar_sala.php">Entrar em uma sala</a>
    <a class="opcao-menu" data-menu href="ranking.php">Ranking</a>
    <a class="opcao-menu" data-menu href="como-funciona.php">Como funciona</a>
    <a class="opcao-menu" data-menu href="index.php">Trocar jogador</a>
</nav>
<section class="perfil-menu" aria-label="Jogador">
    <p class="nome-jogador"><?= escapar($jogador['nome']) ?></p>
</section>
<?php fimPagina(); ?>
