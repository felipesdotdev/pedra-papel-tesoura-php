<?php
// Copie banco.local.exemplo.php para banco.local.php se precisar alterar o acesso.
$config = [
    'host' => getenv('DB_HOST') ?: '127.0.0.1',
    'porta' => getenv('DB_PORT') ?: '3306',
    'nome' => getenv('DB_NAME') ?: 'pedra_papel_tesoura',
    'usuario' => getenv('DB_USER') ?: 'root',
    'senha' => getenv('DB_PASS') ?: '',
];
if (is_file(__DIR__ . '/banco.local.php')) {
    $config = array_merge($config, require __DIR__ . '/banco.local.php');
}

function banco(): PDO
{
    global $config;
    static $pdo;
    if (!$pdo) {
        $dsn = "mysql:host={$config['host']};port={$config['porta']};dbname={$config['nome']};charset=utf8mb4";
        $pdo = new PDO($dsn, $config['usuario'], $config['senha'], [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
    }
    return $pdo;
}
