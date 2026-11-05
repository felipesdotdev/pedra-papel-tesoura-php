<?php

class ErroConfiguracao extends RuntimeException
{
    public string $tipo;

    public function __construct(string $tipo, string $mensagem)
    {
        $this->tipo = $tipo;
        parent::__construct($mensagem);
    }
}

function configuracaoBanco(): array
{
    $config = ['host' => '127.0.0.1', 'porta' => '3306', 'nome' => 'pedra_papel_tesoura', 'usuario' => 'root', 'senha' => ''];
    $variaveis = ['host' => 'DB_HOST', 'porta' => 'DB_PORT', 'nome' => 'DB_NAME', 'usuario' => 'DB_USER', 'senha' => 'DB_PASS'];
    foreach ($variaveis as $campo => $variavel) {
        $valor = getenv($variavel);
        if ($valor !== false) {
            $config[$campo] = $valor;
        }
    }

    // A configuração local tem prioridade sobre as variáveis de ambiente.
    $arquivo = __DIR__ . '/banco.local.php';
    if (is_file($arquivo)) {
        if (!is_readable($arquivo)) {
            throw new ErroConfiguracao('arquivo', 'O arquivo de configuração não pode ser lido.');
        }
        // Uma correção na conexão deve valer já na próxima tentativa, mesmo com OPcache.
        if (function_exists('opcache_invalidate')) {
            @opcache_invalidate($arquivo, true);
        }
        // Evita que um BOM ou texto fora de <?php vaze antes da tela de ajuda.
        ob_start();
        try {
            $local = require $arquivo;
        } catch (Throwable $erro) {
            throw new ErroConfiguracao('arquivo', 'O arquivo de configuração contém um erro de PHP.');
        } finally {
            ob_end_clean();
        }
        if (!is_array($local)) {
            throw new ErroConfiguracao('arquivo', 'O arquivo de configuração deve retornar um array.');
        }
        $config = array_merge($config, $local);
    }
    foreach (['host', 'nome', 'usuario', 'senha'] as $campo) {
        if (!is_string($config[$campo]) || ($campo !== 'senha' && trim($config[$campo]) === '')) {
            throw new ErroConfiguracao('valores', 'Existem campos inválidos na configuração do banco.');
        }
    }
    if (filter_var($config['porta'], FILTER_VALIDATE_INT, ['options' => ['min_range' => 1, 'max_range' => 65535]]) === false) {
        throw new ErroConfiguracao('valores', 'A porta do banco deve ser um número entre 1 e 65535.');
    }
    return $config;
}

function banco(): PDO
{
    static $pdo;
    if (!$pdo) {
        if (!class_exists('PDO') || !in_array('mysql', PDO::getAvailableDrivers(), true)) {
            throw new ErroConfiguracao('driver', 'O PHP não tem o driver PDO MySQL habilitado.');
        }
        $config = configuracaoBanco();
        $dsn = "mysql:host={$config['host']};port={$config['porta']};dbname={$config['nome']};charset=utf8mb4";
        $pdo = new PDO($dsn, $config['usuario'], $config['senha'], [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::ATTR_TIMEOUT => 3,
        ]);
    }
    return $pdo;
}

function cancelarTransacao(?PDO $conexao): void
{
    try {
        if ($conexao && $conexao->inTransaction()) {
            $conexao->rollBack();
        }
    } catch (PDOException $erro) {
        // Uma conexão que caiu também pode recusar o rollback; preserve o erro original.
        error_log('[rollback] ' . $erro->getMessage());
    }
}
