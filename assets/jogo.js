'use strict';

const jogo = document.querySelector('#jogo');
const botoes = [...document.querySelectorAll('[data-escolha]')];
const statusJogo = document.querySelector('#status');
const detalhes = document.querySelector('#detalhes');
const erro = document.querySelector('#erro');
const revanche = document.querySelector('#revanche');
const sair = document.querySelector('#sair');
let estado = null;
let enviando = false;
let consultando = false;
let falhaConsulta = false;
let encerrada = false;
let proximaConsulta;

function mostrarErro(mensagem) {
    erro.textContent = mensagem;
    erro.hidden = !mensagem;
}

function desenhar() {
    if (!estado) return;
    encerrada = estado.sala_status === 'encerrada';
    document.querySelector('#oponente').textContent = estado.oponente;
    const podeJogar = !encerrada && !falhaConsulta && !enviando && estado.sala_status === 'jogando'
        && !estado.finalizada && !estado.minha_escolha;
    for (const botao of botoes) {
        botao.disabled = !podeJogar;
        const selecionada = estado.minha_escolha === botao.dataset.escolha;
        botao.classList.toggle('selecionada', selecionada);
        botao.setAttribute('aria-pressed', String(selecionada));
    }
    revanche.hidden = encerrada || !estado.finalizada;
    revanche.disabled = enviando || falhaConsulta || estado.minha_revanche;
    revanche.textContent = estado.minha_revanche ? 'Revanche solicitada' : 'Jogar novamente';
    sair.hidden = encerrada;
    document.querySelector('#voltar').hidden = !encerrada;
    document.querySelector('#pedido-revanche').textContent = !encerrada && estado.finalizada && estado.modo !== 'bot'
        ? (estado.minha_revanche ? 'Aguardando o outro jogador aceitar.'
            : estado.oponente_revanche ? 'Seu oponente quer uma revanche!' : 'Uma nova rodada começa quando os dois pedirem revanche.') : '';

    if (encerrada) {
        statusJogo.textContent = 'Sala encerrada';
        detalhes.textContent = estado.finalizada
            ? `${estado.resultado} Você: ${estado.minha_escolha}. Oponente: ${estado.escolha_oponente}.`
            : 'Um jogador saiu. A rodada incompleta não conta para o ranking.';
    } else if (estado.sala_status === 'aguardando') {
        statusJogo.textContent = 'Aguardando seu amigo…';
        detalhes.textContent = 'Peça para ele entrar com o código desta sala.';
    } else if (estado.finalizada) {
        statusJogo.textContent = estado.resultado;
        detalhes.textContent = `Você escolheu ${estado.minha_escolha}. ${estado.oponente} escolheu ${estado.escolha_oponente}.`;
    } else if (estado.minha_escolha) {
        statusJogo.textContent = 'Escolha registrada!';
        detalhes.textContent = 'Aguardando a escolha do outro jogador…';
    } else {
        statusJogo.textContent = 'Qual vai ser sua escolha?';
        detalhes.textContent = estado.oponente_jogou ? 'Seu oponente já escolheu. Agora é com você.' : 'As escolhas só aparecem depois que os dois jogarem.';
    }
}

async function requisicao(caminho, dados) {
    const opcoes = { cache: 'no-store', signal: AbortSignal.timeout(10000) };
    if (dados) {
        opcoes.method = 'POST';
        opcoes.body = new URLSearchParams({
            csrf: jogo.dataset.csrf, sala_id: jogo.dataset.sala,
            rodada_id: estado?.rodada_id ?? '', ...dados,
        });
    }
    const resposta = await fetch(caminho, opcoes);
    let json;
    try { json = await resposta.json(); }
    catch { throw new Error('O servidor não respondeu corretamente. Tente novamente.'); }
    if (!resposta.ok) throw new Error(json.erro || 'Não foi possível concluir a ação.');
    return json;
}

async function atualizarSala() {
    if (consultando || enviando || encerrada) return;
    consultando = true;
    clearTimeout(proximaConsulta);
    try {
        estado = await requisicao(`api/estado_sala.php?sala_id=${encodeURIComponent(jogo.dataset.sala)}`);
        if (falhaConsulta) mostrarErro('');
        falhaConsulta = false;
        desenhar();
    } catch (e) {
        falhaConsulta = true;
        mostrarErro(`${e.message} Tentaremos atualizar novamente em instantes.`);
        desenhar();
    } finally {
        consultando = false;
        if (!encerrada) proximaConsulta = setTimeout(atualizarSala, 2000);
    }
}

async function executar(arquivo, dados = {}) {
    if (enviando) return;
    enviando = true;
    sair.disabled = true;
    clearTimeout(proximaConsulta);
    mostrarErro('');
    desenhar();
    try {
        await requisicao(`api/${arquivo}.php`, dados);
        if (arquivo === 'sair_sala') {
            window.location.href = 'menu.php';
            return;
        }
    } catch (e) {
        mostrarErro(e.message);
    } finally {
        enviando = false;
        sair.disabled = false;
        await atualizarSala();
        desenhar();
    }
}

for (const botao of botoes) {
    botao.addEventListener('click', () => executar('jogar', { escolha: botao.dataset.escolha }));
}
revanche.addEventListener('click', () => executar('revanche'));
sair.addEventListener('click', () => executar('sair_sala'));
atualizarSala();
