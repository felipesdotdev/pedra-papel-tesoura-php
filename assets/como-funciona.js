'use strict';

// Exemplo local de comunicação. Os IDs são fictícios e não há chamadas à API.
const etapasGuia = [
    {
        escolha1: 'Sem escolha', escolha2: 'Sem escolha', titulo: 'Sala compartilhada',
        texto: 'Os IDs dos dois jogadores estão associados à mesma sala no MySQL. Cada navegador tem sua própria sessão.',
        payload: 'salas: jogador1_id = 12, jogador2_id = 27', acao: 'Ver o POST →',
    },
    {
        escolha1: 'POST enviado', escolha2: 'Sem escolha', titulo: 'O navegador A envia a escolha',
        texto: 'O fetch envia um POST para api/jogar.php. O cookie identifica a sessão; o corpo do pedido leva o token, a sala, a rodada e a escolha.',
        payload: 'POST api/jogar.php\nsala_id=8&rodada_id=31\n&escolha=pedra&csrf=…', acao: 'Ver a gravação →',
    },
    {
        escolha1: 'Pedra salva', escolha2: 'Escolha de A: null', titulo: 'O PHP valida e grava no MySQL',
        texto: 'Após validar a sessão e o pedido, o PHP salva escolha1. O navegador B consulta o estado: recebe o aviso de que A jogou, mas ainda não recebe a escolha.',
        payload: '// Trecho do JSON recebido por B\n{\n  "oponente_jogou": true,\n  "escolha_oponente": null,\n  "finalizada": false\n}', acao: 'Ver o segundo POST →',
    },
    {
        escolha1: 'Pedra salva', escolha2: 'Tesoura salva', titulo: 'O segundo POST permite finalizar a rodada',
        texto: 'O navegador B envia tesoura. Com as duas escolhas salvas, o PHP compara os valores, finaliza a rodada e atualiza as estatísticas dentro da transação.',
        payload: 'rodadas:\nescolha1 = pedra\nescolha2 = tesoura\nresultado = jogador1\nstatus = finalizada', acao: 'Ver o GET →',
    },
    {
        escolha1: 'JSON atualizado', escolha2: 'JSON atualizado', titulo: 'O GET devolve o resultado',
        texto: 'Cada navegador consulta api/estado_sala.php e recebe o resultado do seu ponto de vista. O JavaScript atualiza a interface. Este trecho é a resposta para A.',
        payload: '{\n  "finalizada": true,\n  "escolha_oponente": "tesoura",\n  "resultado": "Você venceu!"\n}', acao: 'Rever o fluxo ↺',
    },
];
let etapaGuia = 0;
const demoGuia = document.querySelector('.guia-demo');
const proximoGuia = document.querySelector('#demo-proximo');
function desenharGuia() {
    const etapa = etapasGuia[etapaGuia];
    document.querySelector('#demo-escolha1').textContent = etapa.escolha1;
    document.querySelector('#demo-escolha2').textContent = etapa.escolha2;
    document.querySelector('#demo-etapa').textContent = `Etapa ${etapaGuia + 1} / ${etapasGuia.length}`;
    document.querySelector('#demo-titulo').textContent = etapa.titulo;
    document.querySelector('#demo-texto').textContent = etapa.texto;
    document.querySelector('#demo-payload').textContent = etapa.payload;
    proximoGuia.textContent = etapa.acao;
    demoGuia.classList.toggle('guia-demo-vitoria', etapaGuia === etapasGuia.length - 1);
}
proximoGuia.addEventListener('click', () => {
    etapaGuia = (etapaGuia + 1) % etapasGuia.length;
    desenharGuia();
});
document.querySelector('#demo-reiniciar').addEventListener('click', () => {
    etapaGuia = 0;
    desenharGuia();
});
document.querySelector('#demo-controles').hidden = false;
