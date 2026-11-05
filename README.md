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
2. Crie um banco com charset `utf8mb4`, selecione-o no phpMyAdmin e importe `banco.sql`. No terminal, um exemplo é `mysql -u root -p pedra_papel_tesoura < banco.sql`, depois de criar esse banco. Use um terminal que aceite esse redirecionamento, como CMD ou Bash. O arquivo cria somente as tabelas, sem apagar registros existentes e sem impor um nome de banco.
3. Por padrão, o projeto conecta em `127.0.0.1:3306`, banco `pedra_papel_tesoura`, usuário `root`, senha vazia. Se necessário, copie `config/banco.local.exemplo.php` para `config/banco.local.php` e edite os valores. O arquivo local está no `.gitignore`.
4. Na pasta do projeto, execute:

   ```sh
   php -S localhost:8000
   ```

5. Acesse <http://localhost:8000>.

Também é possível colocar a pasta no diretório público do XAMPP/Laragon ou utilizar o Herd. O servidor embutido do PHP serve para desenvolvimento e apresentação local.

As variáveis de ambiente `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASS` também são aceitas. A configuração local tem prioridade.

### Atualização do ranking por nome

Em bancos de uma versão anterior, faça backup e execute `php migrations/002_jogadores_por_nome.php` sem partidas em andamento. A migração exige permissão de alterar a estrutura da tabela. Em instalações novas, importe o `banco.sql` atualizado.

A migração reúne as estatísticas dos nomes equivalentes no perfil de menor ID e atualiza os participantes das salas e os vencedores das rodadas. Os IDs antigos permanecem como referências ao perfil principal, com os contadores zerados, para que sessões antigas continuem funcionando. O histórico não é apagado. Salas antigas entre dois IDs do mesmo nome são encerradas, pois agora representam um só jogador. Reexecutar a migração não soma os pontos outra vez.

Para verificar a entrada por nome, o acúmulo de pontos e a migração, execute `php tests/ranking.php`. O teste usa tabelas com prefixo aleatório e as remove ao terminar; o usuário precisa de permissão para criar e remover essas tabelas. Os registros do jogo não são usados como dados de teste.


## Configuração e diagnóstico no deploy

A página inicial verifica extensões, sessão, conexão, tabelas e colunas antes de exibir o jogo. Se algo estiver faltando, apresenta a causa e instruções específicas. Também é possível abrir `configuracao.php` diretamente para verificar novamente; com a instalação correta, ela mostra a confirmação.

- Erros de configuração retornam HTTP **503**; falhas SQL não identificadas retornam **500**. A verificação bem-sucedida retorna **200**.
- As APIs continuam respondendo JSON, com um código de diagnóstico e o endereço da ajuda. Se o banco cair durante uma partida, a tela oferece o link para as instruções e continua tentando atualizar.
- A página não cria banco, usuário, tabelas ou permissões automaticamente. Ela não exibe senha, usuário, host, SQL interno ou stack trace. Os detalhes técnicos ficam no log de erros do PHP.
- Em hospedagem compartilhada, use o nome completo fornecido pelo painel, incluindo prefixos. Importe `banco.sql` no banco selecionado. O usuário da aplicação precisa de `SELECT`, `INSERT` e `UPDATE`; a importação deve ser feita por alguém com permissão de criar tabelas.
- Se já houver tabelas de uma versão anterior, faça backup e atualize as colunas conforme `banco.sql`. `CREATE TABLE IF NOT EXISTS` não modifica tabelas existentes.
- A verificação confirma a leitura das tabelas. Permissões de escrita são conferidas quando uma ação do jogo tenta salvar dados; erros também abrem a ajuda.

Para testar a classificação dos erros sem instalar dependências: `php tests/diagnostico.php`.

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

O modelo animado atual está em `assets/personagem/animacoes/personagem-combinado.glb` (aproximadamente 1,6 MB), com geometria, materiais, textura de barba e quatro clipes incorporados. O rosto e o cabelo frontais vêm da versão original aprovada; a rigagem, o corpo e os detalhes aproveitam o trabalho posterior. A imagem de reserva está em `assets/personagem/animacoes/poster-combinado.png`. A biblioteca `model-viewer` 4.4.0 está incluída em `assets/vendor/`, com sua licença, sem CDN ou instalação de pacotes para executar a página.

O arquivo editável atual é `output/animacoes/personagem_combinado_animado.blend`. A versão estática anterior continua preservada em `output/personagem/personagem.blend` e `assets/personagem/personagem.glb`. O componente usa a data de modificação nas URLs para evitar exibir modelos antigos após uma atualização.

Para incluir em outra página PHP na raiz do projeto:

```php
<?php require __DIR__ . '/includes/personagem.php'; ?>
```

Carregue também `assets/estilo.css` no `<head>` para os estilos base dos botões. O componente inclui automaticamente seu CSS e JavaScript próprios. Em páginas de subpastas, defina `$personagemAssets = '../assets';` antes do `require`, ajustando o caminho público dos assets conforme necessário. É possível incluir o componente mais de uma vez na mesma página.

Para hospedar, envie `personagem.php`, `includes/personagem.php` e a pasta `assets/` para um servidor PHP. Sirva `.js` como JavaScript e `.glb` como `model/gltf-binary` (ou `application/octet-stream`). Use HTTP/HTTPS; abrir pelo explorador de arquivos não executa o PHP. Em caso de falha de WebGL ou JavaScript desativado, a imagem permanece visível.

O pack inclui `Idle` (repouso), `Pedra` (retirada do bolso e arremesso), `Papel` (lançamento de avião) e `Tesoura` (retirada do bolso e três cortes no ar). A página oferece reprodução, pausa, velocidade e uma barra para inspecionar as poses. Com preferência por movimento reduzido, o repouso não começa automaticamente; os gestos continuam disponíveis por ação do usuário. A iluminação em tempo real pode diferir da renderização do Blender. Consulte `output/animacoes/LEIA-ME.md` para detalhes do rig e dos clipes.

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
- O nome identifica o perfil, sem diferenciar maiúsculas e minúsculas e ignorando espaços nas pontas: `luis`, `Luis` e `LUIS` recuperam o mesmo jogador e suas estatísticas. Acentos continuam distintos: `Luis` e `Luís` são nomes diferentes. O banco usa uma chave normalizada com índice UNIQUE; o ID desse perfil fica na sessão PHP.
- Ao entrar novamente com um nome existente, o sistema mantém os pontos e atualiza o personagem escolhido. Um nome ainda não cadastrado cria outro perfil. Como o projeto não usa senha, qualquer pessoa que informe o mesmo nome acessa esse perfil.

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

## Seleção de personagem

A entrada oferece imagens dos personagens Froldi e Márcio. A opção é salva em `jogadores.personagem` e na sessão. Clique na imagem ou no nome para selecionar; o teclado também funciona com os botões de rádio. A tela inicial não carrega modelos 3D, WebGL ou a biblioteca model-viewer, para reduzir o uso de processador e memória.

Em bancos existentes, execute uma vez `migrations/001_personagem.sql` antes de usar a nova entrada. Instalações novas já recebem a coluna por `banco.sql`. A arena usa essa escolha para exibir o personagem de cada jogador.

## Duelo 2D

A sala usa um cenário low poly em tela inteira, com profundidade ilustrada, personagens transparentes, placar por sala e controles sobrepostos. O personagem vem de `jogadores.personagem`; no treino, o bot usa o outro personagem. Os dois jogadores podem escolher o mesmo personagem.

Quando as duas escolhas chegam ao servidor, a interface apresenta a contagem, revela as jogadas e reproduz movimentos 2D curtos de investida, vitória e derrota. Recarregar uma rodada concluída mostra diretamente o resultado. A preferência de movimento reduzido elimina a contagem animada. O placar é calculado a partir das rodadas concluídas e não modifica as regras do ranking; treino continua sem pontuar no ranking.

A partida anima sprites com CSS, sem WebGL ou renderização 3D em tempo real. Os arquivos editáveis do rig e suas animações continuam preservados. As imagens usadas estão em `assets/duelo/`, junto dos PNGs originais e dos prompts usados na ferramenta integrada `image_gen`. O cenário e as duas imagens estáticas dos personagens somam aproximadamente 82 KB; os atlas de animação são carregados à parte.

### Ações do Froldi e do Márcio

Os dois personagens usam seis poses por ação, em folhas de sprites transparentes com três colunas e duas linhas. Os arquivos ficam em `assets/duelo/froldi-acoes/` e `assets/duelo/marcio-acoes/`, separados em `pedra`, `papel` e `tesoura`. Cada pasta contém o WebP de 960 × 640, o PNG original, o prompt de geração e um `atlas.json` com os tempos e a sequência. Cada quadro mede 320 × 320.

O Froldi carrega a versão `spritesheet-alinhado.webp` de cada ação; o Márcio carrega `spritesheet.webp`. A seleção desses arquivos fica em `assets/duelo.js`.

Pedra e Papel passam por preparação, arremesso e recuperação. A pedra ou o avião de papel começa a voar aos 960 ms da ação, em uma camada CSS separada. Tesoura repete as poses de lâminas abertas e fechadas, com efeitos de corte aos 690 e 1150 ms. O JavaScript escolhe o atlas pelo personagem e pela jogada; o CSS espelha as poses do adversário. Quando o resultado aparece ou a rodada muda, as poses e os efeitos são removidos. Se um atlas ainda não carregou, a interface usa a investida simples como alternativa. Com movimento reduzido, mostra o resultado diretamente.

A versão anterior do arremesso do Froldi, com 16 poses, permanece em `assets/duelo/froldi-pedra/` como histórico; a partida usa os seis quadros de `froldi-acoes/pedra/`.

Para verificar o carregamento dos atlas, as combinações de personagens e jogadas, o espelhamento, a sincronização dos objetos, o cancelamento e o movimento reduzido, abra `http://localhost:8000/tests/duelo-animacoes.html`. A página usa estados fictícios, sem chamar a API ou alterar o banco, e mostra o resultado das verificações.

### Idle do Froldi e do Márcio

Froldi usa três poses selecionadas dos sprites gerados, com cadência marcada de 0,9 segundo, em `assets/duelo/froldi-idle/spritesheet-v2.webp`. Márcio usa as três primeiras poses do atlas `assets/duelo/marcio-idle/spritesheet.webp`, com flexão curta dos joelhos e cadência marcada de 0,9 segundo, sem escala animada. Os loops pausam durante ataques e resultados e quando a aba está oculta. A preferência de movimento reduzido exibe as imagens estáticas. A seleção inicial continua estática. A exportação experimental do rig do Froldi fica preservada em `assets/duelo/froldi-idle/rig/`, mas não é carregada pela partida.

### Alinhamento das ações do Froldi

As três ações do Froldi usam `assets/duelo/froldi-acoes/{pedra,papel,tesoura}/spritesheet-alinhado.webp`. A escala é calculada em relação à pose neutra do idle e aplicada uma única vez, igualmente a todos os quadros da mesma ação, com ancoragem nos pés. Os PNGs e atlas anteriores permanecem preservados. `atlas.json` registra a escala e o deslocamento usados. O primeiro e o último quadro da sequência exibida reaproveitam diretamente o quadro de idle que estava na tela, com o mesmo tamanho e posição, evitando saltos na entrada e na saída do ataque.

### Vitória e derrota

Froldi e Márcio têm seis poses de vitória e seis de derrota em `assets/duelo/froldi-resultados/{vitoria,derrota}/` e `assets/duelo/marcio-resultados/{vitoria,derrota}/`. Cada pasta preserva o PNG original, o WebP alinhado, o prompt usado no `image_gen` e os metadados em `atlas.json`.

As poses avançam aos 0, 300, 600, 950, 1300 e 1700 ms, uma vez por resultado, e seguram o quadro final até a próxima rodada. Vitória levanta os punhos em comemoração; derrota ajoelha e baixa a cabeça. A primeira pose reaproveita o quadro de idle que estava na tela, com a grade correta de cada personagem. A escala e a ancoragem dos pés são fixas em toda a sequência. Empates não acionam vitória ou derrota. Recarregar uma rodada concluída ou usar movimento reduzido mostra a pose final diretamente. Iniciar revanche ou encerrar a sala cancela os quadros pendentes e remove as poses anteriores.
