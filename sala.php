<?php
require __DIR__ . '/includes/funcoes.php';
try {
    $jogador = exigirJogador();
    $sala = obterSala((int) ($_GET['id'] ?? 0), (int) $jogador['id']);
} catch (Throwable $e) { falhaPagina($e); }
inicioPagina('Sala ' . $sala['codigo']);
?>
<section id="jogo" class="<?= $sala['status'] === 'aguardando' ? 'aguardando' : '' ?>" data-sala="<?= $sala['id'] ?>" data-csrf="<?= escapar($_SESSION['csrf']) ?>">
<section class="intro"><h1><?= $sala['modo'] === 'bot' ? 'Contra o bot' : 'Sala' ?></h1></section>
<?php if ($sala['modo'] === 'multiplayer'): ?>
<section class="convite-sala" aria-label="Convite para a sala">
    <div><span class="label-codigo">Código da sala</span><strong class="codigo" id="codigo-convite"><?= escapar($sala['codigo']) ?></strong></div>
    <button type="button" id="copiar-codigo" class="secundario" aria-live="polite">Copiar código</button>
</section>
<?php endif; ?>
<section class="cartao arena">
<div class="duelo"><div><strong><?= escapar($jogador['nome']) ?></strong></div><span class="versus">VS</span><div><strong id="oponente">…</strong></div></div>
<h2 id="status" role="status" aria-live="polite">Conectando à sala…</h2>
<p id="detalhes" hidden></p>
<div class="escolhas" aria-label="Escolha sua jogada">
<button type="button" data-escolha="pedra" disabled><span>✊</span>Pedra</button>
<button type="button" data-escolha="papel" disabled><span>✋</span>Papel</button>
<button type="button" data-escolha="tesoura" disabled><span>✌️</span>Tesoura</button>
</div>
<p id="erro" class="aviso" role="alert" hidden></p>
<a id="ajuda-configuracao" href="configuracao.php" hidden>Ver instruções de configuração</a>
<button type="button" id="revanche" hidden>Jogar novamente</button>
<p id="pedido-revanche" class="ajuda"></p>
</section>
<div class="acoes"><button type="button" id="sair" class="secundario"><?= $sala['modo'] === 'bot' ? 'Voltar ao menu' : 'Sair da sala' ?></button><a id="voltar" href="menu.php" hidden>Voltar ao menu</a></div>
</section>
<script src="assets/jogo.js" defer></script>
<?php fimPagina(); ?>
