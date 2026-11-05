<?php
require __DIR__ . '/base.php';
responderApi(function (int $jogadorId): array {
    banco()->beginTransaction();
    $sala = obterSala((int) ($_POST['sala_id'] ?? 0), $jogadorId, true);
    consultar("UPDATE salas SET status = 'encerrada' WHERE id = ?", [$sala['id']]);
    banco()->commit();
    return ['ok' => true];
});
