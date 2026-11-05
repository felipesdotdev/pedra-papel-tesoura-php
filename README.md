# Pedra, papel e tesoura

Projeto escolar com PHP puro, MySQL, sessões e JavaScript. Sem frameworks, Composer, WebSocket ou timer de jogada.

## Requisitos

- PHP 8.1 ou superior, com `pdo_mysql` e `mbstring` habilitados.
- MySQL 8 ou MariaDB 10.6 ou superior.
- Navegador atualizado com JavaScript habilitado.

## Como executar

Para continuar em outro computador, clone o repositório e siga os passos abaixo. O PHP, o MySQL/MariaDB e o Blender precisam estar instalados nesse computador; as instalações locais não fazem parte do repositório.

```sh
git clone https://github.com/felipesdotdev/pedra-papel-tesoura-php.git
cd pedra-papel-tesoura-php
```

1. Inicie seu servidor MySQL/MariaDB.
2. Importe `banco.sql` usando a aba **Importar** do phpMyAdmin. Também pode executar `mysql -u root -p < banco.sql` em um terminal que aceite esse redirecionamento, como CMD ou Bash. O arquivo cria o banco e as tabelas sem apagar registros existentes.
3. Por padrão, o projeto conecta em `127.0.0.1:3306`, banco `pedra_papel_tesoura`, usuário `root`, senha vazia. Se necessário, copie `config/banco.local.exemplo.php` para `config/banco.local.php` e edite os valores. O arquivo local está no `.gitignore`.
4. Na pasta do projeto, execute:

   ```sh
   php -S localhost:8000
   ```

5. Acesse <http://localhost:8000>.

Também é possível colocar a pasta no diretório público do XAMPP/Laragon ou utilizar o Herd. O servidor embutido do PHP serve para desenvolvimento e apresentação local.

As variáveis de ambiente `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASS` também são aceitas. A configuração local tem prioridade.

## Arquivos dos personagens e continuação do trabalho

As versões salvas dos personagens ficam em `output/personagem/`, incluindo arquivos editáveis `.blend`, backups `.blend1`, renders e scripts Python de criação e refinamento. As exportações usadas pelo navegador ficam em `assets/personagem/`. Esses arquivos estão incluídos no Git, sem excluir os backups do Blender.

Os trabalhos 3D ainda estão em desenvolvimento. Consulte os arquivos mais recentes e os scripts de cada versão antes de editar. Alterações feitas depois de uma publicação precisam de outro commit e push para aparecerem no computador da escola:

```sh
git add -A
git commit -m "Salva progresso"
git push
```

No outro computador, use `git pull` antes de continuar. As credenciais de `config/banco.local.php` são locais e não são publicadas; crie esse arquivo a partir do exemplo em cada máquina. `banco.sql` contém a estrutura necessária para criar o banco.

## Personagem 3D na web

Com o servidor PHP iniciado, abra **http://localhost:8000/personagem.php**. Essa página é independente do MySQL e não exige login. O personagem pode ser girado e aproximado no navegador. O PHP serve a página; a renderização 3D acontece no navegador com WebGL.

O modelo exportado está em `assets/personagem/personagem.glb` (aproximadamente 96 KB), com os materiais incorporados. A imagem de reserva está em `assets/personagem/poster.png`. A biblioteca `model-viewer` 4.4.0 está incluída em `assets/vendor/`, com sua licença, sem CDN ou instalação de pacotes para executar a página.

O arquivo editável da versão atual é `output/personagem/personagem.blend`. O componente usa a data de modificação nas URLs do modelo e do poster para evitar exibir versões antigas após uma atualização.

Para incluir em outra página PHP na raiz do projeto:

```php
<?php require __DIR__ . '/includes/personagem.php'; ?>
```

Carregue também `assets/estilo.css` no `<head>` para os estilos base dos botões. O componente inclui automaticamente seu CSS e JavaScript próprios. Em páginas de subpastas, defina `$personagemAssets = '../assets';` antes do `require`, ajustando o caminho público dos assets conforme necessário. É possível incluir o componente mais de uma vez na mesma página.

Para hospedar, envie `personagem.php`, `includes/personagem.php` e a pasta `assets/` para um servidor PHP. Sirva `.js` como JavaScript e `.glb` como `model/gltf-binary` (ou `application/octet-stream`). Use HTTP/HTTPS; abrir pelo explorador de arquivos não executa o PHP. Em caso de falha de WebGL ou JavaScript desativado, a imagem permanece visível.

O modelo atual é estático, sem esqueleto ou animações corporais. A iluminação em tempo real pode diferir da renderização do Blender. A vista frontal é a vista principal da referência.

## Como testar o multiplayer

1. Abra o jogo em um navegador normal e informe um nome.
2. Crie uma sala e copie seu código de seis caracteres.
3. Abra uma janela anônima ou outro navegador, informe outro nome e entre com esse código.
4. Escolha uma jogada em cada janela. O resultado aparece nos dois lados.
5. Clique em **Jogar novamente** nos dois lados para iniciar outra rodada.

Duas abas do mesmo perfil compartilham a sessão e representam o mesmo jogador. Para duas pessoas, use sessões diferentes.

Para jogar em dois dispositivos na mesma rede, inicie com `php -S 0.0.0.0:8000` e acesse `http://IP-DO-COMPUTADOR:8000` no outro dispositivo. Pode ser necessário liberar a porta no firewall. O servidor e o banco precisam continuar ligados.

## Regras e decisões

- Cada partida é uma rodada. Pedra vence tesoura, tesoura vence papel e papel vence pedra.
- As escolhas são definitivas naquela rodada e só são reveladas depois que os dois jogam.
- O navegador consulta o estado da sala a cada dois segundos. O servidor salva escolhas e determina o resultado.
- Contra o bot, a escolha é sorteada no PHP. O treino não altera o ranking.
- O ranking mostra os 50 primeiros jogadores com partidas multiplayer concluídas: mais vitórias, menos derrotas, mais empates e menor ID, nessa ordem.
- Uma revanche multiplayer só começa quando os dois pedem. Contra o bot, começa imediatamente.
- **Sair da sala** encerra a sala para os dois. Rodadas incompletas não geram pontos. Resultados já concluídos continuam valendo.
- Fechar a aba ou perder a conexão não encerra a sala automaticamente. Como não há timer, o outro jogador pode aguardar, recarregar a página ou sair pelo botão.
- Não existe autenticação. O jogador é identificado pelo ID guardado na sessão PHP. Nomes repetidos são permitidos e diferenciados por `#ID`. Uma nova sessão não recupera um jogador antigo só pelo nome.
- Trocar de nome na página inicial cria outro jogador; os registros antigos permanecem no banco.

## Organização

A interface segue um menu de jogo: painel branco com recorte diagonal, opção selecionada em ciano e fundo azul com linhas discretas. O fundo é feito em CSS, sem imagem ou dependência externa. A área à direita fica livre para uma ambientação futura.

No menu, use o mouse, Tab ou as setas para selecionar uma opção, e Enter para abrir. Os formulários e links continuam funcionando sem JavaScript; apenas a navegação por setas exige o script. O jogo multiplayer continua precisando de JavaScript para o polling.

A fonte Barlow Condensed é servida localmente em `assets/fonts/`, com a licença OFL incluída na mesma pasta.

| Arquivo/pasta | Responsabilidade |
| --- | --- |
| `index.php` | Entrada por nome e criação da sessão |
| `menu.php` | Menu e estatísticas do jogador |
| `criar_sala.php`, `entrar_sala.php` | Criação e entrada por código |
| `sala.php` | Interface da partida |
| `ranking.php` | Classificação multiplayer |
| `config/banco.php` | Conexão PDO |
| `includes/funcoes.php` | Sessão, consultas e regras compartilhadas |
| `api/` | Endpoints JSON de consulta e ações |
| `assets/jogo.js` | Polling e atualização da interface |
| `assets/estilo.css` | Estilos responsivos |
| `banco.sql` | Estrutura do banco |

## Como o banco evita pontos duplicados

As ações abrem uma transação e bloqueiam primeiro a sala, depois a rodada com `SELECT ... FOR UPDATE`. Assim, duas requisições da mesma sala são processadas em sequência. A rodada só pode ser finalizada enquanto estiver aberta, e o ranking é atualizado na mesma transação do resultado. O ID da rodada também é validado, para uma requisição atrasada não jogar em uma revanche.

O endpoint de polling apenas lê dados. Ele nunca soma pontos. As consultas usam parâmetros preparados; nomes são escapados ao gerar HTML e inseridos como texto no JavaScript. Ações exigem sessão, participação na sala e token CSRF.

## Verificações manuais

- Confira vitória, derrota e empate, incluindo uma revanche.
- Atualize a página depois de escolher: a escolha deve continuar registrada.
- Antes de escolher, confira que a escolha do adversário não aparece na resposta de `api/estado_sala.php`.
- Tente entrar com uma terceira sessão: a sala deve recusar.
- Saia durante uma rodada incompleta: o ranking não deve mudar.
- Jogue contra o bot e confira que o ranking não mudou.
- Tente enviar uma escolha inválida ou repetir uma jogada: a API deve recusar.
