<?php
require __DIR__ . '/includes/funcoes.php';
try {
    verificarInstalacao();
} catch (Throwable $e) {
    mostrarConfiguracao($e);
}
$personagens = [
    'classico' => ['nome' => 'Froldi', 'poster' => 'assets/personagem/cards/classico.webp?v=1', 'descricao' => 'Cabelo cheio e expressão concentrada.'],
    'barbudo' => ['nome' => 'Márcio', 'poster' => 'assets/personagem/cards/barbudo.webp?v=1', 'descricao' => 'Personagem de barba, camiseta verde, colar e gesto de positivo.'],
];
$selecionado = (string) ($_SESSION['personagem'] ?? 'classico');
if (!isset($personagens[$selecionado])) {
    $selecionado = 'classico';
}
$nome = '';
$erro = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        exigirPost();
        $nome = trim((string) ($_POST['nome'] ?? ''));
        $selecionado = (string) ($_POST['personagem'] ?? 'classico');
        if (!isset($personagens[$selecionado])) {
            throw new RuntimeException('Escolha um dos personagens disponíveis.');
        }
        if ($nome === '' || mb_strlen($nome) > 30 || preg_match('/[\x00-\x1F\x7F]/u', $nome)) {
            throw new RuntimeException('Informe um nome entre 1 e 30 caracteres.');
        }
        $jogadorId = entrarOuCriarJogador(banco(), $nome, $selecionado);
        session_regenerate_id(true);
        $_SESSION['jogador_id'] = $jogadorId;
        $_SESSION['personagem'] = $selecionado;
        redirecionar('menu.php');
    } catch (Throwable $e) {
        if ($e instanceof PDOException || $e instanceof ErroConfiguracao) {
            mostrarConfiguracao($e);
        } else {
            $erro = $e->getMessage();
        }
    }
}
inicioPagina('Vamos jogar', 'entrada');
?>
<link rel="stylesheet" href="assets/selecao-personagem.css?v=4">
<form method="post" class="entrada-jogador">
<?php campoCsrf(); ?>
<div class="entrada-identidade">
<section class="intro"><p class="etiqueta">Prepare-se para o duelo</p><h1>Pedra.<br>Papel.<br>Tesoura.</h1></section>
<section class="cartao estreito">
<?php if ($erro): ?><p class="aviso" role="alert"><?= escapar($erro) ?></p><?php endif; ?>
<label for="nome">Seu nome</label>
<input id="nome" name="nome" value="<?= escapar($nome) ?>" maxlength="30" required autocomplete="nickname" placeholder="Ex.: Lucas">
<button type="submit" class="entrada-jogar">Jogar <span aria-hidden="true">↗</span></button>
<?php if (!empty($_SESSION['jogador_id'])): ?><a href="menu.php">Voltar ao menu</a><?php endif; ?>
</section>
</div>
<fieldset class="selecao-personagem">
<legend>Escolha seu personagem</legend>
<p class="selecao-dica">Selecione seu favorito para entrar no jogo.</p>
<div class="selecao-opcoes">
<?php foreach ($personagens as $id => $personagem): ?>
<div class="personagem-opcao" data-opcao-personagem>
<label class="personagem-previa" for="personagem-<?= escapar($id) ?>">
<img src="<?= escapar($personagem['poster']) ?>" alt="<?= escapar($personagem['nome'] . ': ' . $personagem['descricao']) ?>" class="personagem-imagem" decoding="async">
</label>
<label class="personagem-seletor">
<input type="radio" id="personagem-<?= escapar($id) ?>" name="personagem" value="<?= escapar($id) ?>" <?= $selecionado === $id ? 'checked' : '' ?> required>
<span class="personagem-rotulo"><strong><?= escapar($personagem['nome']) ?></strong><span class="personagem-marca" aria-hidden="true">✓</span></span>
</label>
</div>
<?php endforeach; ?>
</div>
</fieldset>
</form>
<?php fimPagina(); ?>
