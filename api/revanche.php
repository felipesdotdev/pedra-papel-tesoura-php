<?php
require __DIR__ . '/base.php';
responderApi(function (int $jogadorId): array {
    return alterarRodada($jogadorId, function (array $sala, array $rodada, int $posicao): void {
        if ($rodada['status'] !== 'finalizada') {
            throw new RuntimeException('Espere o resultado antes de pedir uma revanche.');
        }
        consultar('UPDATE rodadas SET revanche' . $posicao . ' = 1 WHERE id = ?', [$rodada['id']]);
        $rodada['revanche' . $posicao] = 1;
        if ($sala['modo'] === 'bot' || ($rodada['revanche1'] && $rodada['revanche2'])) {
            consultar('INSERT INTO rodadas (sala_id) VALUES (?)', [$sala['id']]);
        }
    });
});
