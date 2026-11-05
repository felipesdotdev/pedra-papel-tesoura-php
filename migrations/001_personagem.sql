-- Execute uma vez em bancos criados antes da seleção de personagem.
ALTER TABLE jogadores ADD COLUMN personagem VARCHAR(20) NOT NULL DEFAULT 'classico';
