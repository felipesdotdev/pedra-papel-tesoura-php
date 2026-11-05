<?php
require __DIR__ . '/base.php';
responderApi(function (int $jogadorId): array {
    $escolha = (string) ($_POST['escolha'] ?? '');
    if (!in_array($escolha, ['pedra', 'papel', 'tesoura'], true)) {
        throw new RuntimeException('Escolha pedra, papel ou tesoura.');
    }
    return alterarRodada($jogadorId, function (array $sala, array $rodada, int $posicao) use ($escolha): void {
        if ($rodada['status'] !== 'aberta' || $rodada['escolha' . $posicao] !== null) {
            throw new RuntimeException('Sua escolha já foi registrada nesta rodada.');
        }
        // O nome da coluna vem da posição validada pelo servidor.
        consultar('UPDATE rodadas SET escolha' . $posicao . ' = ? WHERE id = ?', [$escolha, $rodada['id']]);
        $rodada['escolha' . $posicao] = $escolha;
        if ($sala['modo'] === 'bot') {
            $opcoes = ['pedra', 'papel', 'tesoura'];
            $rodada['escolha2'] = $opcoes[random_int(0, 2)];
            consultar('UPDATE rodadas SET escolha2 = ? WHERE id = ?', [$rodada['escolha2'], $rodada['id']]);
        }
        if ($rodada['escolha1'] !== null && $rodada['escolha2'] !== null) {
            finalizarRodada($sala, $rodada);
        }
    });
});
