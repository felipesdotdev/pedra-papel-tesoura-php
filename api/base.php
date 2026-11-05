<?php
require_once __DIR__ . '/../includes/funcoes.php';

// Todos os endpoints devolvem JSON, inclusive em caso de erro.
function responderApi(callable $acao, bool $alterar = true): never
{
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    $conexao = null;
    try {
        if ($alterar) {
            exigirPost();
        } elseif ($_SERVER['REQUEST_METHOD'] !== 'GET') {
            throw new RuntimeException('Método inválido.');
        }
        $conexao = banco();
        $jogador = exigirJogador();
        // Não mantém a sessão bloqueada enquanto o banco trabalha.
        session_write_close();
        $dados = $acao((int) $jogador['id']);
        echo json_encode($dados, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
    } catch (Throwable $erro) {
        if ($conexao && $conexao->inTransaction()) {
            $conexao->rollBack();
        }
        $inesperado = !($erro instanceof RuntimeException) || $erro instanceof PDOException;
        http_response_code($inesperado ? 500 : 422);
        if ($inesperado) {
            error_log((string) $erro);
        }
        echo json_encode(['erro' => $inesperado ? 'Não foi possível concluir a ação. Tente novamente.' : $erro->getMessage()], JSON_UNESCAPED_UNICODE);
    }
    exit;
}

// Sala e rodada são sempre bloqueadas nessa ordem para serializar as ações.
function alterarRodada(int $jogadorId, callable $acao): array
{
    banco()->beginTransaction();
    $sala = obterSala((int) ($_POST['sala_id'] ?? 0), $jogadorId, true);
    if ($sala['status'] !== 'jogando') {
        throw new RuntimeException('A sala ainda está aguardando alguém ou já foi encerrada.');
    }
    $rodada = ultimaRodada((int) $sala['id'], true);
    if ((int) ($_POST['rodada_id'] ?? 0) !== (int) $rodada['id']) {
        throw new RuntimeException('A rodada mudou. Aguarde a atualização da tela.');
    }
    $posicao = (int) $sala['jogador1_id'] === $jogadorId ? 1 : 2;
    $acao($sala, $rodada, $posicao);
    banco()->commit();
    return ['ok' => true];
}
