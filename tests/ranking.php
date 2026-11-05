<?php
require_once __DIR__ . '/../includes/jogadores.php';
require_once __DIR__ . '/../migrations/002_jogadores_por_nome.php';

// Prefixa tabelas e a chave estrangeira para isolar os testes no mesmo banco.
// Isso dispensa a permissão administrativa de criar outro banco de dados.
final class BancoRankingTeste extends PDO
{
    private string $prefixo;

    public function __construct(string $dsn, string $usuario, string $senha)
    {
        parent::__construct($dsn, $usuario, $senha, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
        $this->prefixo = 'teste_ranking_' . bin2hex(random_bytes(6)) . '_';
    }

    private function sqlIsolado(string $sql): string
    {
        return preg_replace_callback('/\b(jogadores|salas|rodadas|jogadores_principal_fk)\b/',
            fn (array $trecho): string => $this->prefixo . $trecho[0], $sql);
    }

    public function exec(string $statement): int|false
    {
        return parent::exec($this->sqlIsolado($statement));
    }

    public function prepare(string $query, array $options = []): PDOStatement|false
    {
        return parent::prepare($this->sqlIsolado($query), $options);
    }

    public function query(string $query, ?int $fetchMode = null, mixed ...$fetchModeArgs): PDOStatement|false
    {
        return $fetchMode === null
            ? parent::query($this->sqlIsolado($query))
            : parent::query($this->sqlIsolado($query), $fetchMode, ...$fetchModeArgs);
    }
}

// Recebe somente uma conexão que isola todas as tabelas de teste.
function testarRankingPorNome(BancoRankingTeste $pdo): array
{
    $resultados = [];
    $verificar = static function (string $nome, bool $correto) use (&$resultados): void {
        if (!$correto) {
            throw new RuntimeException('Falhou: ' . $nome);
        }
        $resultados[] = $nome;
    };
    $limpar = static function () use ($pdo): void {
        $pdo->exec('DROP TABLE IF EXISTS rodadas, salas, jogadores');
    };
    $pdo->exec(file_get_contents(__DIR__ . '/../banco.sql'));
    $primeiro = entrarOuCriarJogador($pdo, 'luis', 'classico');
    $pdo->exec("UPDATE jogadores SET vitorias = 2 WHERE id = $primeiro");
    $segundo = entrarOuCriarJogador($pdo, 'Luis', 'barbudo');
    $verificar('luis e Luis retornam o mesmo ID', $primeiro === $segundo);
    $pdo->exec("UPDATE jogadores SET vitorias = vitorias + 2 WHERE id = $segundo");
    $luis = buscarJogadorPorId($pdo, $primeiro);
    $verificar('Duas vitórias mais duas vitórias somam quatro', (int) $luis['vitorias'] === 4);
    $verificar('Trocar o personagem conserva os pontos', $luis['personagem'] === 'barbudo');
    $verificar('LUIS e espaços nas pontas recuperam o perfil', entrarOuCriarJogador($pdo, ' LUIS ', 'classico') === $primeiro);
    $verificar('Reentradas não criam perfis extras', (int) $pdo->query('SELECT COUNT(*) FROM jogadores')->fetchColumn() === 1);
    $acentuado = entrarOuCriarJogador($pdo, 'Luís', 'classico');
    $verificar('Acentos são preservados na identidade', $acentuado !== $primeiro);
    $verificar('Maiúsculas acentuadas também recuperam o perfil', entrarOuCriarJogador($pdo, 'LUÍS', 'barbudo') === $acentuado);
    $verificar('Outro nome tem estatísticas próprias', (int) buscarJogadorPorId($pdo, $acentuado)['vitorias'] === 0);
    $pdo->exec("INSERT INTO jogadores (nome, personagem) VALUES ('referência', 'classico')");
    $antes = (int) $pdo->lastInsertId();
    $verificar('lastInsertId retorna o ID recuperado após outro INSERT', entrarOuCriarJogador($pdo, 'Luis', 'classico') === $primeiro && $antes !== $primeiro);
    try {
        $pdo->exec("INSERT INTO jogadores (nome) VALUES ('LUIS')");
        $verificar('Índice UNIQUE impede duplicação fora do formulário', false);
    } catch (PDOException $erro) {
        $verificar('Índice UNIQUE impede duplicação fora do formulário', ($erro->errorInfo[1] ?? null) === 1062);
    }
    $verificar('Migração aceita instalação nova', migrarJogadoresPorNome($pdo)['perfis_unificados'] === 0);

    // Banco da versão antiga: nomes duplicados e histórico referenciando esses IDs.
    $limpar();
    $pdo->exec("CREATE TABLE jogadores (
        id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(30) NOT NULL,
        personagem VARCHAR(20) NOT NULL DEFAULT 'classico', vitorias INT UNSIGNED NOT NULL DEFAULT 0,
        derrotas INT UNSIGNED NOT NULL DEFAULT 0, empates INT UNSIGNED NOT NULL DEFAULT 0
    ) ENGINE=InnoDB CHARACTER SET utf8mb4");
    $pdo->exec("CREATE TABLE salas (
        id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, codigo CHAR(6) NOT NULL UNIQUE,
        jogador1_id INT UNSIGNED NOT NULL, jogador2_id INT UNSIGNED NULL,
        modo ENUM('multiplayer','bot') NOT NULL, status ENUM('aguardando','jogando','encerrada') NOT NULL,
        FOREIGN KEY (jogador1_id) REFERENCES jogadores(id), FOREIGN KEY (jogador2_id) REFERENCES jogadores(id)
    ) ENGINE=InnoDB");
    $pdo->exec("CREATE TABLE rodadas (
        id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, sala_id INT UNSIGNED NOT NULL,
        vencedor_id INT UNSIGNED NULL, resultado VARCHAR(10),
        FOREIGN KEY (sala_id) REFERENCES salas(id), FOREIGN KEY (vencedor_id) REFERENCES jogadores(id)
    ) ENGINE=InnoDB");
    $pdo->exec("INSERT INTO jogadores (nome, vitorias, derrotas, empates) VALUES
        ('luis', 2, 1, 1), ('Luis', 2, 3, 2), ('Ana', 4, 0, 0), ('ANA', 1, 1, 2)");
    $pdo->exec("INSERT INTO salas (codigo, jogador1_id, jogador2_id, modo, status) VALUES
        ('A00001', 2, 3, 'multiplayer', 'jogando'),
        ('A00002', 3, 2, 'multiplayer', 'jogando'),
        ('A00003', 1, 2, 'multiplayer', 'jogando'),
        ('A00004', 4, NULL, 'bot', 'jogando')");
    $pdo->exec("INSERT INTO rodadas (sala_id, vencedor_id, resultado) VALUES (1,2,'jogador1'), (2,3,'jogador1'), (3,2,'jogador2')");
    $migracao = migrarJogadoresPorNome($pdo);
    $verificar('Migração consolida os dois grupos duplicados', $migracao['perfis_unificados'] === 2);
    $luis = buscarJogadorPorId($pdo, 1);
    $verificar('Migração soma vitórias, derrotas e empates', (int) $luis['vitorias'] === 4 && (int) $luis['derrotas'] === 4 && (int) $luis['empates'] === 3);
    $verificar('ID antigo da sessão recupera o perfil principal', (int) buscarJogadorPorId($pdo, 2)['id'] === 1);
    $verificar('Referências antigas não duplicam estatísticas', (int) $pdo->query('SELECT SUM(vitorias) FROM jogadores')->fetchColumn() === 9);
    $verificar('Participante da primeira posição é atualizado', (int) $pdo->query('SELECT jogador1_id FROM salas WHERE id = 1')->fetchColumn() === 1);
    $verificar('Participante da segunda posição é atualizado', (int) $pdo->query('SELECT jogador2_id FROM salas WHERE id = 2')->fetchColumn() === 1);
    $verificar('Vencedor antigo continua associado ao mesmo nome', (int) $pdo->query('SELECT vencedor_id FROM rodadas WHERE id = 1')->fetchColumn() === 1);
    $verificar('Histórico de salas e rodadas é preservado', (int) $pdo->query('SELECT COUNT(*) FROM salas')->fetchColumn() === 4 && (int) $pdo->query('SELECT COUNT(*) FROM rodadas')->fetchColumn() === 3);
    $verificar('Sala antiga entre duplicados é encerrada', $pdo->query('SELECT status FROM salas WHERE id = 3')->fetchColumn() === 'encerrada');
    $verificar('Sala entre pessoas diferentes continua aberta', $pdo->query('SELECT status FROM salas WHERE id = 1')->fetchColumn() === 'jogando');
    $verificar('Perfil unificado pode entrar novamente sem zerar', entrarOuCriarJogador($pdo, 'LUIS', 'barbudo') === 1 && (int) buscarJogadorPorId($pdo, 1)['vitorias'] === 4);
    $ranking = $pdo->query('SELECT * FROM jogadores WHERE jogador_principal_id IS NULL AND vitorias + derrotas + empates > 0 ORDER BY vitorias DESC, derrotas ASC, empates DESC, id ASC LIMIT 50')->fetchAll();
    $verificar('Ranking exibe somente uma linha por nome', count($ranking) === 2 && (int) $ranking[0]['id'] === 3 && (int) $ranking[1]['id'] === 1);
    $verificar('Reexecutar a migração não soma os pontos novamente', migrarJogadoresPorNome($pdo)['perfis_unificados'] === 0 && (int) buscarJogadorPorId($pdo, 1)['vitorias'] === 4);
    return $resultados;
}

if (PHP_SAPI === 'cli' && realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) {
    $teste = null;
    try {
        $config = configuracaoBanco();
        $dsn = "mysql:host={$config['host']};port={$config['porta']};dbname={$config['nome']};charset=utf8mb4";
        $teste = new BancoRankingTeste($dsn, $config['usuario'], $config['senha']);
        $resultados = testarRankingPorNome($teste);
        echo count($resultados) . " verificações de ranking aprovadas.\n";
    } catch (Throwable $erro) {
        fwrite(STDERR, $erro->getMessage() . "\n");
        $falhou = true;
    } finally {
        if ($teste) {
            cancelarTransacao($teste);
            $teste->exec('DROP TABLE IF EXISTS rodadas, salas, jogadores');
        }
    }
    exit(!empty($falhou) ? 1 : 0);
}
