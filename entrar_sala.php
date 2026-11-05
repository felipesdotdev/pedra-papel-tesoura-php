<?php
require __DIR__ . '/includes/funcoes.php';
$conexao = null;
// O mesmo arquivo exibe o formulário e recebe o código, sem depender de JS.
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    try { exigirJogador(); } catch (Throwable $e) { falhaPagina($e); }
    inicioPagina('Entrar em uma sala', 'entrada');
    ?>
    <section class="intro"><h1>Entrar<br>na sala</h1></section>
    <section class="cartao estreito">
        <form method="post">
            <?php campoCsrf(); ?>
            <label for="codigo">Código da sala</label>
            <input id="codigo" name="codigo" maxlength="6" minlength="6" required placeholder="AB7K2P" pattern="[A-Fa-f0-9]{6}" autocomplete="off" spellcheck="false">
            <button type="submit">Entrar <span aria-hidden="true">↗</span></button>
        </form>
        <a class="voltar-menu" href="menu.php">← Voltar ao menu</a>
    </section>
    <?php
    fimPagina();
    exit;
}
try {
    exigirPost();
    $jogador = exigirJogador();
    $codigo = strtoupper(trim((string) ($_POST['codigo'] ?? '')));
    if (!preg_match('/^[A-F0-9]{6}$/', $codigo)) {
        throw new RuntimeException('Informe um código de sala válido com 6 caracteres.');
    }
    $conexao = banco();
    $conexao->beginTransaction();
    $sala = consultar('SELECT * FROM salas WHERE codigo = ? FOR UPDATE', [$codigo])->fetch();
    if (!$sala || $sala['modo'] !== 'multiplayer' || $sala['status'] === 'encerrada') {
        throw new RuntimeException('Sala não encontrada ou já encerrada.');
    }
    $id = (int) $jogador['id'];
    if ((int) $sala['jogador1_id'] !== $id && (int) $sala['jogador2_id'] !== $id) {
        if ($sala['jogador2_id'] !== null) {
            throw new RuntimeException('Esta sala já tem dois jogadores.');
        }
        consultar("UPDATE salas SET jogador2_id = ?, status = 'jogando' WHERE id = ?", [$id, $sala['id']]);
    }
    banco()->commit();
    redirecionar('sala.php?id=' . $sala['id']);
} catch (Throwable $e) {
    if ($conexao && $conexao->inTransaction()) { $conexao->rollBack(); }
    falhaPagina($e);
}
