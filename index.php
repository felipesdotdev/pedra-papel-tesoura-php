<?php
require __DIR__ . '/includes/funcoes.php';
$erro = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    try {
        exigirPost();
        $nome = trim((string) ($_POST['nome'] ?? ''));
        if ($nome === '' || mb_strlen($nome) > 30 || preg_match('/[\x00-\x1F\x7F]/u', $nome)) {
            throw new RuntimeException('Informe um nome entre 1 e 30 caracteres.');
        }
        consultar('INSERT INTO jogadores (nome) VALUES (?)', [$nome]);
        session_regenerate_id(true);
        $_SESSION['jogador_id'] = (int) banco()->lastInsertId();
        redirecionar('menu.php');
    } catch (Throwable $e) {
        if ($e instanceof PDOException) {
            error_log((string) $e);
            $erro = 'Não foi possível acessar o banco. Confira config/banco.php e importe banco.sql.';
        } else {
            $erro = $e->getMessage();
        }
    }
}
inicioPagina('Vamos jogar', 'entrada');
?>
<section class="intro"><p class="etiqueta">O CLÁSSICO, ENTRE AMIGOS</p>
<h1>Pedra.<br>Papel.<br>Tesoura.</h1>
<p>Desafie um amigo. Treine contra o bot.<br>Sua próxima jogada começa aqui.</p></section>
<section class="cartao estreito">
<h2>Entre no jogo</h2>
<?php if ($erro): ?><p class="aviso" role="alert"><?= escapar($erro) ?></p><?php endif; ?>
<form method="post">
<?php campoCsrf(); ?>
<label for="nome">Seu nome</label>
<input id="nome" name="nome" maxlength="30" required autocomplete="nickname" placeholder="Ex.: Lucas">
<button type="submit">Começar a jogar <span aria-hidden="true">↗</span></button>
</form>
<p class="ajuda">Seu placar fica ligado à sessão deste navegador. Nomes podem se repetir.</p>
<?php if (!empty($_SESSION['jogador_id'])): ?><a href="menu.php">Continuar com minha sessão atual</a><?php endif; ?>
</section>
<?php fimPagina(); ?>
