<?php

function entrarOuCriarJogador(PDO $pdo, string $nome, string $personagem): int
{
    // nome_chave é calculado pelo banco e tem um índice UNIQUE.
    // LAST_INSERT_ID também retorna o perfil existente no caso de reentrada.
    $consulta = $pdo->prepare('INSERT INTO jogadores (nome, personagem) VALUES (?, ?)
        ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id), personagem = VALUES(personagem)');
    $consulta->execute([trim($nome), $personagem]);
    return (int) $pdo->lastInsertId();
}

function buscarJogadorPorId(PDO $pdo, int $id): ?array
{
    $consulta = $pdo->prepare('SELECT principal.* FROM jogadores origem
        JOIN jogadores principal ON principal.id = COALESCE(origem.jogador_principal_id, origem.id)
        WHERE origem.id = ?');
    $consulta->execute([$id]);
    return $consulta->fetch() ?: null;
}
