<?php
require __DIR__ . '/base.php';
responderApi(function (int $jogadorId): array {
    // Uma leitura consistente evita misturar sala/rodada durante uma atualização.
    banco()->beginTransaction();
    $estado = estadoSala((int) ($_GET['sala_id'] ?? 0), $jogadorId);
    banco()->commit();
    return $estado;
}, false);
