-- Selecione antes o banco da aplicação (ex.: no phpMyAdmin).
-- Este arquivo cria somente as tabelas, para aceitar nomes de banco da hospedagem.

CREATE TABLE IF NOT EXISTS jogadores (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(30) NOT NULL,
    vitorias INT UNSIGNED NOT NULL DEFAULT 0,
    derrotas INT UNSIGNED NOT NULL DEFAULT 0,
    empates INT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS salas (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    codigo CHAR(6) NOT NULL UNIQUE,
    jogador1_id INT UNSIGNED NOT NULL,
    jogador2_id INT UNSIGNED NULL,
    modo ENUM('multiplayer', 'bot') NOT NULL,
    status ENUM('aguardando', 'jogando', 'encerrada') NOT NULL,
    criada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (jogador1_id) REFERENCES jogadores(id),
    FOREIGN KEY (jogador2_id) REFERENCES jogadores(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rodadas (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sala_id INT UNSIGNED NOT NULL,
    escolha1 ENUM('pedra', 'papel', 'tesoura') NULL,
    escolha2 ENUM('pedra', 'papel', 'tesoura') NULL,
    vencedor_id INT UNSIGNED NULL,
    resultado ENUM('jogador1', 'jogador2', 'empate') NULL,
    status ENUM('aberta', 'finalizada') NOT NULL DEFAULT 'aberta',
    revanche1 BOOLEAN NOT NULL DEFAULT FALSE,
    revanche2 BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (sala_id) REFERENCES salas(id),
    FOREIGN KEY (vencedor_id) REFERENCES jogadores(id),
    INDEX (sala_id, id)
) ENGINE=InnoDB;
