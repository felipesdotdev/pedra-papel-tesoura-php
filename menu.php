<?php
require __DIR__ . '/includes/funcoes.php';
try { $jogador = exigirJogador(); } catch (Throwable $e) { falhaPagina($e); }
inicioPagina('Menu principal', 'menu');
?>
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
    <a class="opcao-menu" data-menu href="index.php">Trocar jogador</a>
</nav>
<section class="perfil-menu" aria-label="Seu jogador e placar">
    <p class="rotulo">JOGADOR ATUAL</p>
    <p class="nome-jogador"><?= escapar($jogador['nome']) ?> <span class="identificador">#<?= $jogador['id'] ?></span></p>
    <div class="placar"><span><strong><?= $jogador['vitorias'] ?></strong> VITÓRIAS</span><span><strong><?= $jogador['empates'] ?></strong> EMPATES</span><span><strong><?= $jogador['derrotas'] ?></strong> DERROTAS</span></div>
</section>
<?php fimPagina(); ?>
