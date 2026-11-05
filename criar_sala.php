<?php
require __DIR__ . '/includes/funcoes.php';
try {
    exigirPost();
    $jogador = exigirJogador();
    $modo = (string) ($_POST['modo'] ?? '');
    if (!in_array($modo, ['multiplayer', 'bot'], true)) {
        throw new RuntimeException('Modo de jogo inválido.');
    }
    $id = criarSala((int) $jogador['id'], $modo);
    redirecionar('sala.php?id=' . $id);
} catch (Throwable $e) { falhaPagina($e); }
