<?php

function verificarInstalacao(): void
{
    static $verificado = false;
    if ($verificado) {
        return;
    }
    if (!function_exists('mb_strlen')) {
        throw new ErroConfiguracao('mbstring', 'A extensão mbstring do PHP não está habilitada.');
    }
    if (!function_exists('session_status') || session_status() !== PHP_SESSION_ACTIVE) {
        throw new ErroConfiguracao('sessao', 'O PHP não conseguiu iniciar a sessão.');
    }
    // LIMIT 0 verifica tabelas, colunas e permissão de leitura sem buscar jogadores.
    $estrutura = [
        'SELECT id, nome, nome_chave, jogador_principal_id, vitorias, derrotas, empates FROM jogadores LIMIT 0',
        'SELECT id, codigo, jogador1_id, jogador2_id, modo, status, criada_em FROM salas LIMIT 0',
        'SELECT id, sala_id, escolha1, escolha2, vencedor_id, resultado, status, revanche1, revanche2 FROM rodadas LIMIT 0',
    ];
    foreach ($estrutura as $sql) {
        banco()->query($sql);
    }
    $verificado = true;
}

// As mensagens são nossas: nunca enviamos a exceção SQL ou credenciais ao navegador.
function diagnosticoErro(Throwable $erro): array
{
    $tipo = $erro instanceof ErroConfiguracao ? $erro->tipo : 'consulta';
    if ($erro instanceof PDOException) {
        $numero = (int) ($erro->errorInfo[1] ?? 0);
        $tipos = [1049 => 'banco', 1045 => 'acesso', 1044 => 'permissao', 1142 => 'permissao',
            1143 => 'permissao', 1227 => 'permissao', 1146 => 'tabelas', 1054 => 'colunas',
            2002 => 'conexao', 2003 => 'conexao', 2006 => 'conexao', 2013 => 'conexao'];
        $tipo = $tipos[$numero] ?? 'consulta';
    }
    $problemas = [
        'conexao' => ['DB_CONEXAO', 'Servidor do banco indisponível',
            'O PHP não conseguiu se conectar ao MySQL ou MariaDB.',
            ['Inicie o serviço MySQL/MariaDB no servidor ou no painel da hospedagem.',
             'Confira host e porta em config/banco.local.php ou nas variáveis DB_HOST e DB_PORT.',
             'Se o banco estiver em outro servidor, confira se ele permite conexões desta aplicação.']],
        'acesso' => ['DB_ACESSO', 'Acesso ao banco recusado',
            'O servidor foi encontrado, mas não aceitou as credenciais.',
            ['Confira usuario e senha em config/banco.local.php ou em DB_USER e DB_PASS.',
             'Verifique no painel da hospedagem se esse usuário pode acessar o banco a partir deste servidor.']],
        'banco' => ['DB_NAO_ENCONTRADO', 'Banco de dados não encontrado',
            'O banco configurado ainda não existe ou seu nome está diferente.',
            ['Crie um banco MySQL/MariaDB no painel da hospedagem ou no phpMyAdmin.',
             'Coloque o nome exato do banco em nome ou DB_NAME. Hospedagens podem adicionar um prefixo.',
             'Selecione esse banco e importe banco.sql para criar as tabelas.']],
        'tabelas' => ['DB_TABELAS', 'Faltam tabelas no banco',
            'A conexão funciona, mas a estrutura do jogo ainda está incompleta.',
            ['Selecione o banco da aplicação no phpMyAdmin e importe banco.sql.',
             'O arquivo cria jogadores, salas e rodadas. Confira se importou no mesmo banco informado na configuração.']],
        'colunas' => ['DB_ESTRUTURA', 'A estrutura do banco está desatualizada',
            'Uma tabela existe, mas falta uma coluna usada por esta versão do jogo.',
            ['Faça um backup dos dados e compare a estrutura das tabelas com banco.sql.',
             'Adicione ou atualize as colunas que faltam. Importar novamente um CREATE TABLE IF NOT EXISTS não altera tabelas existentes.',
             'Para atualizar o ranking por nome, execute no terminal: php migrations/002_jogadores_por_nome.php.']],
        'permissao' => ['DB_PERMISSAO', 'Permissão insuficiente no banco',
            'O usuário configurado não tem permissão para uma operação necessária.',
            ['Associe o usuário ao banco no painel da hospedagem.',
             'Para executar o jogo, conceda SELECT, INSERT e UPDATE nas tabelas. Para a importação inicial, use um usuário com permissão de criar tabelas.']],
        'driver' => ['PHP_MYSQL', 'Habilite o driver MySQL do PHP',
            'Esta instalação do PHP não tem o driver pdo_mysql disponível.',
            ['No painel da hospedagem ou no php.ini usado pelo site, habilite PDO e pdo_mysql.',
             'Reinicie o serviço PHP/Apache se a configuração exigir. O PHP do terminal pode usar outro php.ini.']],
        'mbstring' => ['PHP_MBSTRING', 'Habilite a extensão mbstring',
            'O jogo usa mbstring para validar nomes com acentos.',
            ['Habilite mbstring no painel da hospedagem ou no php.ini usado pelo site.',
             'Reinicie o serviço PHP/Apache e verifique novamente.']],
        'sessao' => ['PHP_SESSAO', 'Não foi possível iniciar a sessão',
            'O PHP precisa salvar a sessão para identificar os jogadores.',
            ['Confira se a extensão session está habilitada e se session.save_path aponta para uma pasta gravável pelo PHP.',
             'Consulte o log de erros do PHP para identificar problemas de permissão ou espaço em disco.']],
        'arquivo' => ['CONFIG_ARQUIVO', 'Revise o arquivo de configuração',
            'config/banco.local.php não pôde ser carregado como uma configuração válida.',
            ['Use config/banco.local.exemplo.php como modelo: o arquivo precisa retornar um array PHP.',
             'Confira a sintaxe e a permissão de leitura do arquivo. No terminal, php -l config/banco.local.php verifica a sintaxe.']],
        'valores' => ['CONFIG_VALORES', 'Revise os dados da conexão',
            'A configuração contém campos vazios ou valores de formato inválido.',
            ['Preencha host, nome e usuario com texto. senha também deve ser texto, mesmo quando estiver vazia.',
             'A porta deve ser um número de 1 a 65535. Confira o exemplo abaixo.']],
        'consulta' => ['DB_CONSULTA', 'Não foi possível consultar o banco',
            'O banco devolveu um erro que exige verificação no servidor.',
            ['Consulte o log de erros do PHP para ver a causa técnica.',
             'Confira a estrutura de banco.sql e as permissões do usuário. Se foi uma falha temporária, tente novamente.']],
    ];
    [$codigo, $titulo, $descricao, $passos] = $problemas[$tipo] ?? $problemas['consulta'];
    return ['codigo' => $codigo, 'titulo' => $titulo, 'descricao' => $descricao, 'passos' => $passos,
        'http' => $tipo === 'consulta' ? 500 : 503, 'pronto' => false];
}

function mostrarConfiguracao(?Throwable $erro = null): never
{
    if (!$erro) {
        try {
            verificarInstalacao();
        } catch (Throwable $falha) {
            $erro = $falha;
        }
    }
    if ($erro) {
        $diagnostico = diagnosticoErro($erro);
        error_log('[configuracao] ' . $diagnostico['codigo'] . ': ' . $erro->getMessage());
    } else {
        $diagnostico = ['codigo' => 'PRONTO', 'titulo' => 'Conexão verificada',
            'descricao' => 'A sessão, as extensões necessárias e a leitura das tabelas estão funcionando.',
            'passos' => [], 'http' => 200, 'pronto' => true];
    }
    http_response_code($diagnostico['http']);
    header('Content-Type: text/html; charset=utf-8');
    header('Cache-Control: no-store');
    require __DIR__ . '/tela-configuracao.php';
    exit;
}
