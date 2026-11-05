<?php
require __DIR__ . '/includes/funcoes.php';
try {
    $jogador = exigirJogador();
    $sala = obterSala((int) ($_GET['id'] ?? 0), (int) $jogador['id']);
} catch (Throwable $e) { falhaPagina($e); }
inicioPagina('Sala ' . $sala['codigo'], 'duelo');
?>
<link rel="stylesheet" href="assets/duelo.css?v=16">
<section id="jogo" class="<?= $sala['status'] === 'aguardando' ? 'aguardando' : '' ?>" data-sala="<?= $sala['id'] ?>" data-csrf="<?= escapar($_SESSION['csrf']) ?>">
<header class="duelo-cabecalho"><div><p class="etiqueta">Pedra / Papel / Tesoura</p><h1><?= $sala['modo'] === 'bot' ? 'Duelo de treino' : 'Duelo online' ?></h1></div><a href="menu.php" class="voltar-jogo">Menu principal</a></header>
<?php if ($sala['modo'] === 'multiplayer'): ?>
<section class="convite-sala" aria-label="Convite para a sala">
    <div><span class="label-codigo">Código da sala</span><strong class="codigo" id="codigo-convite"><?= escapar($sala['codigo']) ?></strong></div>
    <button type="button" id="copiar-codigo" class="secundario" aria-live="polite">Copiar código</button>
</section>
<?php endif; ?>
<section class="cartao arena">
<div class="duelo-hud">
<div class="hud-jogador"><span>Você</span><strong><?= escapar($jogador['nome']) ?></strong><small id="meu-personagem">…</small></div>
<div class="hud-placar"><span id="numero-rodada">RODADA 1</span><strong><b id="pontos-voce">0</b><i>:</i><b id="pontos-oponente">0</b></strong><small id="empates-duelo">0 empates</small></div>
<div class="hud-jogador hud-oponente"><span><?= $sala['modo'] === 'bot' ? 'Treino' : 'Adversário' ?></span><strong id="oponente">…</strong><small id="outro-personagem">…</small></div>
</div>
<div class="palco-duelo" id="palco-duelo" data-fase="conectando" role="img" aria-label="Arena do duelo: aguardando conexão.">
<div class="lutador lutador-voce" id="lutador-voce"><img id="sprite-voce" src="assets/duelo/froldi.webp" alt="" width="420" height="560"><span class="jogada-revelada" id="gesto-voce" hidden></span></div>
<div class="lutador lutador-oponente" id="lutador-oponente"><img id="sprite-oponente" src="assets/duelo/marcio.webp" alt="" width="420" height="560"><span class="jogada-revelada" id="gesto-oponente" hidden></span></div>
<div class="duelo-anuncio" id="duelo-anuncio" aria-hidden="true"><span id="anuncio-legenda">Prepare-se</span><strong id="anuncio-titulo">VS</strong></div>
<div class="duelo-faixa"><span>ARENA DAS RUÍNAS</span><span id="fase-duelo">Conectando…</span></div>
</div>
<div class="duelo-painel">
<h2 id="status" role="status" aria-live="polite">Conectando à sala…</h2>
<p id="detalhes" hidden></p>
<p class="duelo-instrucao">Pedra vence tesoura · Tesoura vence papel · Papel vence pedra</p>
<div class="escolhas" aria-label="Escolha sua jogada">
<button type="button" data-escolha="pedra" disabled><span>✊</span>Pedra</button>
<button type="button" data-escolha="papel" disabled><span>✋</span>Papel</button>
<button type="button" data-escolha="tesoura" disabled><span>✌️</span>Tesoura</button>
</div>
<p id="erro" class="aviso" role="alert" hidden></p>
<a id="ajuda-configuracao" href="configuracao.php" hidden>Ver instruções de configuração</a>
<button type="button" id="revanche" hidden>Jogar novamente</button>
<p id="pedido-revanche" class="ajuda"></p>
</div>
</section>
<div class="acoes"><button type="button" id="sair" class="secundario"><?= $sala['modo'] === 'bot' ? 'Voltar ao menu' : 'Sair da sala' ?></button><a id="voltar" href="menu.php" hidden>Voltar ao menu</a></div>
</section>
<script src="assets/duelo.js?v=14" defer></script>
<script src="assets/jogo.js?v=2" defer></script>
<?php fimPagina(); ?>
