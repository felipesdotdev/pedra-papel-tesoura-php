<?php
require __DIR__ . '/includes/funcoes.php';
try {
    $jogadores = consultar('SELECT * FROM jogadores WHERE vitorias + derrotas + empates > 0 ORDER BY vitorias DESC, derrotas ASC, empates DESC, id ASC LIMIT 50')->fetchAll();
    $meuJogador = !empty($_SESSION['jogador_id'])
        ? consultar('SELECT nome, vitorias, empates, derrotas FROM jogadores WHERE id = ?', [(int) $_SESSION['jogador_id']])->fetch()
        : null;
} catch (Throwable $e) { falhaPagina($e); }
$destino = empty($_SESSION['jogador_id']) ? 'index.php' : 'menu.php';
inicioPagina('Classificação', 'ranking');
?>
<header class="barra-jogo">
    <a class="marca" href="<?= $destino ?>">Pedra / Papel / Tesoura</a>
    <a class="voltar-jogo" href="<?= $destino ?>">← Menu principal</a>
</header>
<section class="titulo-ranking">
    <h1>Classificação</h1>
</section>
<?php if ($meuJogador): ?>
<section class="meu-placar" aria-label="Seu placar">
    <strong><?= escapar($meuJogador['nome']) ?></strong>
    <dl><?php foreach (['vitorias' => 'Vitórias', 'empates' => 'Empates', 'derrotas' => 'Derrotas'] as $campo => $rotulo): ?>
        <div><dt><?= $rotulo ?></dt><dd><?= $meuJogador[$campo] ?></dd></div>
    <?php endforeach; ?></dl>
</section>
<?php endif; ?>
<div class="faixa-ranking"><span>Ranking geral</span><span><?= count($jogadores) ?> classificados</span></div>
<?php if (!$jogadores): ?>
<section class="ranking-vazio" aria-labelledby="titulo-vazio">
    <div class="emblema-trofeu" aria-hidden="true">
        <svg viewBox="0 0 64 64" fill="none"><path d="M20 10h24v17c0 10-5 16-12 16s-12-6-12-16V10Z"/><path d="M20 15H10v7c0 9 5 13 12 13M44 15h10v7c0 9-5 13-12 13M32 43v11M23 55h18"/><path d="m32 19 2.5 5 5.5.8-4 3.9.9 5.5-4.9-2.6-4.9 2.6.9-5.5-4-3.9 5.5-.8L32 19Z"/></svg>
    </div>
    <h2 id="titulo-vazio">Nenhuma partida ainda.</h2>
    <a class="botao-jogo" href="<?= $destino ?>">Jogar <span aria-hidden="true">↗</span></a>
</section>
<?php else: ?>
<section class="tabela tabela-ranking" aria-label="Classificação dos jogadores">
<table>
    <caption class="somente-leitor">Os 50 melhores jogadores em partidas multiplayer concluídas.</caption>
    <thead><tr><th scope="col">Pos.</th><th scope="col">Jogador</th><th scope="col"><span class="coluna-desktop">Vitórias</span><abbr class="coluna-mobile" title="Vitórias">V</abbr></th><th scope="col"><span class="coluna-desktop">Empates</span><abbr class="coluna-mobile" title="Empates">E</abbr></th><th scope="col"><span class="coluna-desktop">Derrotas</span><abbr class="coluna-mobile" title="Derrotas">D</abbr></th></tr></thead>
    <tbody>
    <?php foreach ($jogadores as $i => $pessoa): $souEu = (int) ($_SESSION['jogador_id'] ?? 0) === (int) $pessoa['id']; ?>
        <tr class="<?= $souEu ? 'eu' : '' ?>">
            <td class="posicao-ranking"><span><?= str_pad((string) ($i + 1), 2, '0', STR_PAD_LEFT) ?></span></td>
            <th scope="row"><?= escapar($pessoa['nome']) ?> <span class="identificador">#<?= $pessoa['id'] ?></span><?php if ($souEu): ?> <span class="tag-voce">VOCÊ</span><?php endif; ?></th>
            <td class="vitorias-ranking"><?= $pessoa['vitorias'] ?></td><td><?= $pessoa['empates'] ?></td><td><?= $pessoa['derrotas'] ?></td>
        </tr>
    <?php endforeach; ?>
    </tbody>
</table>
</section>
<?php endif; ?>
<?php fimPagina(); ?>
