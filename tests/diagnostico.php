<?php
// Testes sem framework ou conexão com MySQL.
require __DIR__ . '/../config/banco.php';
require __DIR__ . '/../includes/diagnostico.php';

function conferir(bool $condicao, string $mensagem): void
{
    if (!$condicao) {
        throw new RuntimeException($mensagem);
    }
}

$casos = [1049 => 'DB_NAO_ENCONTRADO', 1045 => 'DB_ACESSO', 1044 => 'DB_PERMISSAO',
    1142 => 'DB_PERMISSAO', 1143 => 'DB_PERMISSAO', 1227 => 'DB_PERMISSAO',
    1146 => 'DB_TABELAS', 1054 => 'DB_ESTRUTURA', 2002 => 'DB_CONEXAO',
    2003 => 'DB_CONEXAO', 2006 => 'DB_CONEXAO', 2013 => 'DB_CONEXAO'];
foreach ($casos as $numero => $codigo) {
    $erro = new PDOException('DETALHE_PRIVADO_NAO_EXIBIR');
    $erro->errorInfo = ['HY000', $numero, 'DETALHE_PRIVADO_NAO_EXIBIR'];
    $info = diagnosticoErro($erro);
    conferir($info['codigo'] === $codigo && $info['http'] === 503, 'Classificação incorreta: ' . $numero);
    conferir(!str_contains(json_encode($info), 'DETALHE_PRIVADO'), 'Detalhe privado vazou.');
}
foreach (['arquivo' => 'CONFIG_ARQUIVO', 'valores' => 'CONFIG_VALORES', 'driver' => 'PHP_MYSQL',
    'mbstring' => 'PHP_MBSTRING', 'sessao' => 'PHP_SESSAO'] as $tipo => $codigo) {
    $info = diagnosticoErro(new ErroConfiguracao($tipo, 'DETALHE_PRIVADO_NAO_EXIBIR'));
    conferir($info['codigo'] === $codigo && $info['http'] === 503, 'Classificação incorreta: ' . $tipo);
    conferir(!str_contains(json_encode($info), 'DETALHE_PRIVADO'), 'Detalhe privado vazou.');
}
$generico = diagnosticoErro(new PDOException('SQL interno que não deve ser exibido'));
conferir($generico['http'] === 500 && $generico['codigo'] === 'DB_CONSULTA', 'Erro SQL desconhecido deve ser 500.');
echo "18 cenários de diagnóstico passaram, sem expor mensagens internas.\n";
