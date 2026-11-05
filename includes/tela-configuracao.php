<?php
if (!isset($diagnostico) || !function_exists('escapar')) {
    http_response_code(404);
    exit;
}
$exemplo = <<<'PHP'
<?php
return [
    'host' => '127.0.0.1',
    'porta' => '3306',
    'nome' => 'seu_banco',
    'usuario' => 'seu_usuario',
    'senha' => 'senha_do_banco',
];
PHP;
?>
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= escapar($diagnostico['titulo']) ?> · Configuração</title>
    <link rel="stylesheet" href="assets/estilo.css?v=6">
    <link rel="stylesheet" href="assets/configuracao.css">
</head>
<body class="tela-configuracao">
<main class="configuracao">
    <a class="marca" href="index.php">Pedra / Papel / Tesoura</a>
    <section class="problema-configuracao <?= $diagnostico['pronto'] ? 'configuracao-pronta' : '' ?>" aria-labelledby="titulo-configuracao">
        <span class="codigo-diagnostico"><?= escapar($diagnostico['codigo']) ?></span>
        <h1 id="titulo-configuracao"><?= escapar($diagnostico['titulo']) ?></h1>
        <p><?= escapar($diagnostico['descricao']) ?></p>
        <?php if ($diagnostico['passos']): ?>
        <h2>Como resolver</h2>
        <ol><?php foreach ($diagnostico['passos'] as $passo): ?><li><?= escapar($passo) ?></li><?php endforeach; ?></ol>
        <?php endif; ?>
        <div class="acoes">
            <a class="botao-jogo" href="<?= $diagnostico['pronto'] ? 'index.php' : 'configuracao.php' ?>"><?= $diagnostico['pronto'] ? 'Abrir jogo' : 'Verificar novamente' ?></a>
            <?php if (!$diagnostico['pronto']): ?><a href="index.php">Voltar ao início</a><?php endif; ?>
        </div>
    </section>
    <details class="guia-configuracao" <?= !$diagnostico['pronto'] ? 'open' : '' ?>>
        <summary>Configuração em outro computador ou hospedagem</summary>
        <ol>
            <li><strong>Conexão:</strong> copie <code>config/banco.local.exemplo.php</code> para <code>config/banco.local.php</code> e preencha os dados fornecidos pela hospedagem.</li>
            <li><strong>Tabelas:</strong> crie ou selecione o banco correto no phpMyAdmin e importe <code>banco.sql</code>. O arquivo não escolhe o nome do banco e não apaga dados existentes.</li>
            <li><strong>PHP:</strong> use PHP 8.1 ou superior, com PDO MySQL, mbstring e sessões habilitados.</li>
        </ol>
        <pre><code><?= escapar($exemplo) ?></code></pre>
        <p>Também é possível usar <code>DB_HOST</code>, <code>DB_PORT</code>, <code>DB_NAME</code>, <code>DB_USER</code> e <code>DB_PASS</code>. Se o arquivo local existir, os valores dele têm prioridade.</p>
        <p>Esta página apenas verifica a instalação. Ela não cria o banco nem altera dados. Os detalhes técnicos dos erros ficam no log do PHP; as credenciais não são exibidas aqui.</p>
    </details>
</main>
</body>
</html>
