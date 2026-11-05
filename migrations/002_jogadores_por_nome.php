<?php
// Execute no terminal, com o jogo sem partidas em andamento:
// php migrations/002_jogadores_por_nome.php
// A constante é usada somente por verificações internas que incluem este arquivo.
if (PHP_SAPI !== 'cli' && !defined('MIGRACAO_INTERNA')) {
    http_response_code(404);
    exit;
}
require_once __DIR__ . '/../config/banco.php';

function migrarJogadoresPorNome(PDO $pdo): array
{
    $colunas = $pdo->query('SHOW COLUMNS FROM jogadores')->fetchAll(PDO::FETCH_COLUMN);
    if (!in_array('jogador_principal_id', $colunas, true)) {
        $pdo->exec('ALTER TABLE jogadores ADD COLUMN jogador_principal_id INT UNSIGNED NULL');
    }
    if (!in_array('nome_chave', $colunas, true)) {
        $pdo->exec('ALTER TABLE jogadores ADD COLUMN nome_chave VARCHAR(90)
            CHARACTER SET utf8mb4 COLLATE utf8mb4_bin
            GENERATED ALWAYS AS (CASE WHEN jogador_principal_id IS NULL THEN LOWER(TRIM(nome)) ELSE NULL END) STORED');
    }
    $unificados = 0;
    $salasEncerradas = 0;
    $pdo->beginTransaction();
    try {
        $grupos = [];
        foreach ($pdo->query('SELECT * FROM jogadores WHERE jogador_principal_id IS NULL ORDER BY id FOR UPDATE')->fetchAll() as $jogador) {
            $grupos['nome:' . $jogador['nome_chave']][] = $jogador;
        }
        $moverPrimeiro = $pdo->prepare('UPDATE salas SET jogador1_id = ? WHERE jogador1_id = ?');
        $moverSegundo = $pdo->prepare('UPDATE salas SET jogador2_id = ? WHERE jogador2_id = ?');
        $moverVencedor = $pdo->prepare('UPDATE rodadas SET vencedor_id = ? WHERE vencedor_id = ?');
        $moverReferencias = $pdo->prepare('UPDATE jogadores SET jogador_principal_id = ? WHERE jogador_principal_id = ?');
        $criarReferencia = $pdo->prepare('UPDATE jogadores SET jogador_principal_id = ?, vitorias = 0, derrotas = 0, empates = 0 WHERE id = ?');
        $somar = $pdo->prepare('UPDATE jogadores SET vitorias = ?, derrotas = ?, empates = ? WHERE id = ?');
        foreach ($grupos as $grupo) {
            if (count($grupo) < 2) {
                continue;
            }
            $principal = (int) $grupo[0]['id'];
            $vitorias = $derrotas = $empates = 0;
            foreach ($grupo as $jogador) {
                $vitorias += (int) $jogador['vitorias'];
                $derrotas += (int) $jogador['derrotas'];
                $empates += (int) $jogador['empates'];
                $antigo = (int) $jogador['id'];
                if ($antigo === $principal) {
                    continue;
                }
                foreach ([$moverPrimeiro, $moverSegundo, $moverVencedor, $moverReferencias, $criarReferencia] as $consulta) {
                    $consulta->execute([$principal, $antigo]);
                }
                $unificados++;
            }
            $somar->execute([$vitorias, $derrotas, $empates, $principal]);
        }
        // Dois perfis antigos do mesmo nome agora representam uma só pessoa.
        // Preserve as rodadas, mas não deixe essa sala esperando duas identidades iguais.
        $salasEncerradas = $pdo->exec("UPDATE salas SET status = 'encerrada'
            WHERE jogador1_id = jogador2_id AND status <> 'encerrada'");
        $pdo->commit();
    } catch (Throwable $erro) {
        cancelarTransacao($pdo);
        throw $erro;
    }
    $indices = $pdo->query('SHOW INDEX FROM jogadores')->fetchAll();
    $temUnico = false;
    foreach ($indices as $indice) {
        if ($indice['Key_name'] === 'jogadores_nome_chave' && (int) $indice['Non_unique'] === 0) {
            $temUnico = true;
        }
    }
    if (!$temUnico) {
        $pdo->exec('ALTER TABLE jogadores ADD UNIQUE KEY jogadores_nome_chave (nome_chave)');
    }
    $restricao = $pdo->query("SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'jogadores'
        AND CONSTRAINT_NAME = 'jogadores_principal_fk' AND CONSTRAINT_TYPE = 'FOREIGN KEY'")->fetchColumn();
    if (!(int) $restricao) {
        $pdo->exec('ALTER TABLE jogadores ADD CONSTRAINT jogadores_principal_fk
            FOREIGN KEY (jogador_principal_id) REFERENCES jogadores(id)');
    }
    return ['perfis_unificados' => $unificados, 'salas_encerradas' => $salasEncerradas];
}

if (PHP_SAPI === 'cli' && realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) {
    try {
        $resultado = migrarJogadoresPorNome(banco());
        echo 'Ranking por nome atualizado: ' . $resultado['perfis_unificados'] . " perfis unificados.\n";
    } catch (Throwable $erro) {
        fwrite(STDERR, 'Falha na migração: ' . $erro->getMessage() . "\n");
        exit(1);
    }
}
