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
<section class="intro"><h1>Pedra.<br>Papel.<br>Tesoura.</h1></section>
<section class="cartao estreito">
<?php if ($erro): ?><p class="aviso" role="alert"><?= escapar($erro) ?></p><?php endif; ?>
<form method="post">
<?php campoCsrf(); ?>
<label for="nome">Seu nome</label>
<input id="nome" name="nome" maxlength="30" required autocomplete="nickname" placeholder="Ex.: Lucas">
<button type="submit">Jogar <span aria-hidden="true">↗</span></button>
</form>
<?php if (!empty($_SESSION['jogador_id'])): ?><a href="menu.php">Voltar ao menu</a><?php endif; ?>
</section>
<?php fimPagina(); ?>
