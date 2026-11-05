<?php
ini_set('session.use_strict_mode', '1');
session_set_cookie_params([
    'httponly' => true,
    'samesite' => 'Lax',
    'secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
]);
session_start();
require_once __DIR__ . '/../config/banco.php';

if (empty($_SESSION['csrf'])) {
    $_SESSION['csrf'] = bin2hex(random_bytes(24));
}

function escapar($valor): string
{
    return htmlspecialchars((string) $valor, ENT_QUOTES, 'UTF-8');
}

function consultar(string $sql, array $dados = []): PDOStatement
{
    $consulta = banco()->prepare($sql);
    $consulta->execute($dados);
    return $consulta;
}

function redirecionar(string $destino): never
{
    header('Location: ' . $destino);
    exit;
}

function exigirJogador(): array
{
    $id = (int) ($_SESSION['jogador_id'] ?? 0);
    $jogador = consultar('SELECT * FROM jogadores WHERE id = ?', [$id])->fetch();
    if (!$jogador) {
        throw new RuntimeException('Informe seu nome na página inicial para continuar.');
    }
    return $jogador;
}

function exigirPost(): void
{
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        throw new RuntimeException('Esta ação precisa ser enviada pelo formulário.');
    }
    if (!hash_equals($_SESSION['csrf'], (string) ($_POST['csrf'] ?? ''))) {
        throw new RuntimeException('Sua sessão mudou. Atualize a página e tente novamente.');
    }
}

function campoCsrf(): void
{
    echo '<input type="hidden" name="csrf" value="' . escapar($_SESSION['csrf']) . '">';
}

function inicioPagina(string $titulo, string $layout = 'pagina'): void
{
    global $layoutPagina;
    $layoutPagina = $layout;
    header('Cache-Control: no-store');
    echo '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">';
    echo '<meta name="viewport" content="width=device-width, initial-scale=1">';
    echo '<title>' . escapar($titulo) . ' · Pedra, papel e tesoura</title>';
    echo '<link rel="preload" href="assets/fonts/BarlowCondensed-BlackItalic.ttf" as="font" type="font/ttf" crossorigin>';
    echo '<link rel="stylesheet" href="assets/estilo.css?v=4"></head><body class="tela-' . escapar($layout) . '">';
    echo '<div class="fundo-cenario" aria-hidden="true"></div><div class="painel-menu" aria-hidden="true"></div>';
    echo '<main class="container" id="conteudo">';
    if ($layout === 'pagina') {
        echo '<header><a class="marca" href="menu.php">Pedra / Papel / Tesoura</a>';
        echo '<a class="voltar-jogo" href="menu.php">← Menu principal</a></header>';
    }
    if (!empty($_SESSION['mensagem'])) {
        echo '<p class="aviso" role="alert">' . escapar($_SESSION['mensagem']) . '</p>';
        unset($_SESSION['mensagem']);
    }
}

function fimPagina(): void
{
    global $layoutPagina;
    echo '</main>';
    if ($layoutPagina === 'menu') {
        echo '<div class="comandos" aria-label="Controles do menu"><span><kbd>↑</kbd><kbd>↓</kbd> Navegar</span><i>/</i><span><kbd>↵</kbd> Selecionar</span></div>';
        echo '<script src="assets/menu.js" defer></script>';
    }
    echo '</body></html>';
}

function falhaPagina(Throwable $erro): never
{
    if ($erro instanceof PDOException) {
        error_log((string) $erro);
        $mensagem = 'Não foi possível acessar o banco. Confira a configuração e a importação de banco.sql.';
    } else {
        $mensagem = $erro->getMessage();
    }
    $_SESSION['mensagem'] = $mensagem;
    redirecionar('index.php');
}

// Retorna qual posição venceu; null representa empate.
function compararEscolhas(string $primeira, string $segunda): ?int
{
    if ($primeira === $segunda) {
        return null;
    }
    $vence = ['pedra' => 'tesoura', 'papel' => 'pedra', 'tesoura' => 'papel'];
    return $vence[$primeira] === $segunda ? 1 : 2;
}

function obterSala(int $id, int $jogadorId, bool $bloquear = false): array
{
    $sala = consultar('SELECT * FROM salas WHERE id = ?' . ($bloquear ? ' FOR UPDATE' : ''), [$id])->fetch();
    if (!$sala || !in_array($jogadorId, [(int) $sala['jogador1_id'], (int) $sala['jogador2_id']], true)) {
        throw new RuntimeException('Sala não encontrada ou você não participa dela.');
    }
    return $sala;
}

function ultimaRodada(int $salaId, bool $bloquear = false): array
{
    $rodada = consultar('SELECT * FROM rodadas WHERE sala_id = ? ORDER BY id DESC LIMIT 1' . ($bloquear ? ' FOR UPDATE' : ''), [$salaId])->fetch();
    if (!$rodada) {
        throw new RuntimeException('Rodada não encontrada.');
    }
    return $rodada;
}

function criarSala(int $jogadorId, string $modo): int
{
    banco()->beginTransaction();
    try {
        // Índice UNIQUE no código também protege contra uma eventual colisão.
        for ($tentativa = 0; $tentativa < 5; $tentativa++) {
            $codigo = strtoupper(bin2hex(random_bytes(3)));
            try {
                consultar('INSERT INTO salas (codigo, jogador1_id, modo, status) VALUES (?, ?, ?, ?)',
                    [$codigo, $jogadorId, $modo, $modo === 'bot' ? 'jogando' : 'aguardando']);
                break;
            } catch (PDOException $erro) {
                if (($erro->errorInfo[1] ?? 0) !== 1062 || $tentativa === 4) {
                    throw $erro;
                }
            }
        }
        $id = (int) banco()->lastInsertId();
        consultar('INSERT INTO rodadas (sala_id) VALUES (?)', [$id]);
        banco()->commit();
        return $id;
    } catch (Throwable $erro) {
        banco()->rollBack();
        throw $erro;
    }
}

function finalizarRodada(array $sala, array $rodada): void
{
    $vencedor = compararEscolhas($rodada['escolha1'], $rodada['escolha2']);
    $resultado = $vencedor === null ? 'empate' : 'jogador' . $vencedor;
    $vencedorId = $vencedor === null ? null : $sala['jogador' . $vencedor . '_id'];
    consultar("UPDATE rodadas SET status = 'finalizada', resultado = ?, vencedor_id = ? WHERE id = ?",
        [$resultado, $vencedorId, $rodada['id']]);
    // O bot é treino e não altera o ranking.
    if ($sala['modo'] !== 'multiplayer') {
        return;
    }
    if ($vencedor === null) {
        consultar('UPDATE jogadores SET empates = empates + 1 WHERE id IN (?, ?)', [$sala['jogador1_id'], $sala['jogador2_id']]);
    } else {
        $perdedorId = $sala['jogador' . (3 - $vencedor) . '_id'];
        // Uma única atualização mantém a mesma ordem de locks entre partidas.
        consultar('UPDATE jogadores SET vitorias = vitorias + (id = ?), derrotas = derrotas + (id = ?) WHERE id IN (?, ?) ORDER BY id',
            [$vencedorId, $perdedorId, $sala['jogador1_id'], $sala['jogador2_id']]);
    }
}

function estadoSala(int $salaId, int $jogadorId): array
{
    $sala = obterSala($salaId, $jogadorId);
    $rodada = ultimaRodada($salaId);
    $posicao = (int) $sala['jogador1_id'] === $jogadorId ? 1 : 2;
    $outra = 3 - $posicao;
    $oponente = $sala['modo'] === 'bot' ? 'Bot' : 'Aguardando jogador';
    if ($sala['modo'] === 'multiplayer' && $sala['jogador' . $outra . '_id']) {
        $pessoa = consultar('SELECT nome FROM jogadores WHERE id = ?', [$sala['jogador' . $outra . '_id']])->fetch();
        $oponente = $pessoa['nome'];
    }
    $finalizada = $rodada['status'] === 'finalizada';
    $resultado = null;
    if ($finalizada) {
        $resultado = $rodada['resultado'] === 'empate' ? 'Empate!' :
            ($rodada['resultado'] === 'jogador' . $posicao ? 'Você venceu!' : 'Você perdeu!');
    }
    return [
        'sala_status' => $sala['status'], 'modo' => $sala['modo'],
        'rodada_id' => (int) $rodada['id'], 'finalizada' => $finalizada,
        'oponente' => $oponente, 'minha_escolha' => $rodada['escolha' . $posicao],
        'oponente_jogou' => $rodada['escolha' . $outra] !== null,
        'escolha_oponente' => $finalizada ? $rodada['escolha' . $outra] : null,
        'resultado' => $resultado,
        'minha_revanche' => (bool) $rodada['revanche' . $posicao],
        'oponente_revanche' => (bool) $rodada['revanche' . $outra],
    ];
}
