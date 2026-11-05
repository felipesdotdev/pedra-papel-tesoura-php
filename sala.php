<?php
require __DIR__ . '/includes/funcoes.php';
try {
    $jogador = exigirJogador();
    $sala = obterSala((int) ($_GET['id'] ?? 0), (int) $jogador['id']);
} catch (Throwable $e) { falhaPagina($e); }
inicioPagina('Sala ' . $sala['codigo']);
?>
<section id="jogo" data-sala="<?= $sala['id'] ?>" data-csrf="<?= escapar($_SESSION['csrf']) ?>">
<section class="intro"><p class="etiqueta"><?= $sala['modo'] === 'bot' ? 'MODO TREINO' : 'SALA MULTIPLAYER' ?></p>
<h1><?= $sala['modo'] === 'bot' ? 'Treino livre' : 'Duelo' ?></h1>
<?php if ($sala['modo'] === 'multiplayer'): ?><p>Compartilhe este código: <strong class="codigo"><?= escapar($sala['codigo']) ?></strong></p><?php else: ?><p>O bot escolhe ao acaso. Este jogo não altera seu ranking.</p><?php endif; ?></section>
<section class="cartao arena">
<div class="duelo"><div><span>JOGADOR 01 · VOCÊ</span><strong><?= escapar($jogador['nome']) ?></strong></div><span class="versus">VS</span><div><span>JOGADOR 02 · OPONENTE</span><strong id="oponente">Carregando…</strong></div></div>
<h2 id="status" role="status" aria-live="polite">Conectando à sala…</h2>
<p id="detalhes">Aguarde um instante.</p>
<div class="escolhas" aria-label="Escolha sua jogada">
<button type="button" data-escolha="pedra" disabled><small aria-hidden="true">01</small><span>✊</span>Pedra</button>
<button type="button" data-escolha="papel" disabled><small aria-hidden="true">02</small><span>✋</span>Papel</button>
<button type="button" data-escolha="tesoura" disabled><small aria-hidden="true">03</small><span>✌️</span>Tesoura</button>
</div>
<p id="erro" class="aviso" role="alert" hidden></p>
<button type="button" id="revanche" hidden>Jogar novamente</button>
<p id="pedido-revanche" class="ajuda"></p>
</section>
<div class="acoes"><button type="button" id="sair" class="secundario">Sair da sala</button><a id="voltar" href="menu.php" hidden>Voltar ao início</a><a href="ranking.php">Ver ranking</a></div>
<p class="ajuda">A sala atualiza a cada 2 segundos. Cada escolha fica oculta até os dois jogarem.</p>
</section>
<script src="assets/jogo.js" defer></script>
<?php fimPagina(); ?>
