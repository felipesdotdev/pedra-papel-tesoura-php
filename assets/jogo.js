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
const duelo = new Duelo2D(jogo, () => desenhar());

function mostrarErro(mensagem) {
    erro.textContent = mensagem;
    erro.hidden = !mensagem;
}

function desenhar() {
    if (!estado) return;
    encerrada = estado.sala_status === 'encerrada';
    jogo.classList.toggle('aguardando', estado.sala_status === 'aguardando');
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
        ? (estado.minha_revanche ? 'Aguardando adversário…'
            : estado.oponente_revanche ? 'Seu adversário pediu revanche.' : '') : '';

    if (encerrada) {
        statusJogo.textContent = 'Sala encerrada';
        detalhes.textContent = estado.finalizada
            ? `${estado.resultado} Você: ${estado.minha_escolha}. Oponente: ${estado.escolha_oponente}.`
            : 'O outro jogador saiu.';
    } else if (estado.sala_status === 'aguardando') {
        statusJogo.textContent = 'Aguardando jogador…';
        detalhes.textContent = '';
    } else if (estado.finalizada) {
        statusJogo.textContent = estado.resultado;
        detalhes.textContent = `${estado.oponente} escolheu ${estado.escolha_oponente}.`;
    } else if (estado.minha_escolha) {
        statusJogo.textContent = `Você escolheu ${estado.minha_escolha}`;
        detalhes.textContent = 'Aguardando adversário…';
    } else {
        statusJogo.textContent = 'Faça sua escolha';
        detalhes.textContent = estado.oponente_jogou ? 'Seu adversário já escolheu.' : '';
    }
    detalhes.hidden = !detalhes.textContent;
    duelo.atualizar(estado);
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
    document.querySelector('#ajuda-configuracao').hidden = !json.configuracao;
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
    if (enviando || (arquivo === 'revanche' && duelo.animando)) return;
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
document.querySelector('#copiar-codigo')?.addEventListener('click', async (evento) => {
    const botao = evento.currentTarget;
    const codigo = document.querySelector('#codigo-convite');
    try {
        await navigator.clipboard.writeText(codigo.textContent);
        botao.textContent = 'Copiado';
    } catch {
        const selecao = window.getSelection();
        const faixa = document.createRange();
        faixa.selectNodeContents(codigo);
        selecao.removeAllRanges();
        selecao.addRange(faixa);
        botao.textContent = 'Use Ctrl+C';
    }
});
atualizarSala();
