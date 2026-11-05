'use strict';

(async () => {
    const report = document.querySelector('#test-results');
    const resultados = [];
    const verificar = (nome, condicao) => {
        resultados.push({ nome, ok: !!condicao });
        if (!condicao) throw new Error(nome);
    };
    try {
        const duelo = new Duelo2D(document.querySelector('#jogo'), () => {});
        const nativeDepois = duelo.depois.bind(duelo);
        const personagens = ['classico', 'barbudo'];
        const acoes = ['pedra', 'papel', 'tesoura'];
        const images = [
            ...Object.values(duelo.acoesPersonagens).flatMap(Object.values),
            ...Object.values(duelo.resultadosPersonagens).flatMap(Object.values),
            ...Object.values(duelo.idleAtlas),
        ];
        await Promise.all(images.map(image => new Promise((resolve, reject) => {
            if (image.complete) {
                if (image.naturalWidth) resolve();
                else reject(new Error(`Atlas não carregou: ${image.src}`));
                return;
            }
            image.addEventListener('load', resolve, { once: true });
            image.addEventListener('error', () => reject(new Error(`Atlas não carregou: ${image.src}`)), { once: true });
        })));
        verificar('Todos os atlas de ação carregam em grade 3 × 2', Object.values(duelo.acoesPersonagens).flatMap(Object.values).every(image => image.naturalWidth === 960 && image.naturalHeight === 640));
        // Relógio controlado para verificar as transições sem esperar cada rodada.
        let agora = 0;
        let tarefas = [];
        let rodada = 0;
        duelo.movimentoReduzido = { matches: false };
        duelo.depois = (ms, acao) => tarefas.push({ instante: agora + ms, acao });
        function avancar(ms) {
            while (true) {
                tarefas.sort((a, b) => a.instante - b.instante);
                if (!tarefas.length || tarefas[0].instante > ms) break;
                const tarefa = tarefas.shift();
                agora = tarefa.instante;
                tarefa.acao();
            }
            agora = ms;
        }
        function estado(meu, outro, minha, dele, finalizada) {
            return {
                rodada_id: rodada, numero_rodada: rodada, sala_status: 'jogando',
                meu_personagem: meu, personagem_oponente: outro,
                minha_escolha: finalizada ? minha : null, escolha_oponente: finalizada ? dele : null,
                finalizada, oponente: 'Teste B', vencedor: 'voce', resultado: 'Você venceu!',
                placar: { voce: finalizada ? 1 : 0, oponente: 0, empates: 0 },
            };
        }
        for (const meu of personagens) for (const outro of personagens) {
            for (const minha of acoes) for (const dele of acoes) {
                agora = 0;
                tarefas = [];
                rodada++;
                const base = estado(meu, outro, minha, dele, false);
                duelo.atualizar(base);
                duelo.atualizar({ ...base, ...estado(meu, outro, minha, dele, true) });
                avancar(1650);
                const voce = document.querySelector('#lutador-voce .acao-sequencia');
                const oponente = document.querySelector('#lutador-oponente .acao-sequencia');
                verificar(`Atlases corretos: ${meu}/${minha} × ${outro}/${dele}`, voce?.dataset.personagem === meu && voce.dataset.acao === minha && oponente?.dataset.personagem === outro && oponente.dataset.acao === dele);
                verificar('Pose do adversário espelhada', getComputedStyle(oponente).transform.startsWith('matrix(-1,'));
                avancar(2300);
                verificar('Objetos não saem antes da pose de soltura', !document.querySelector('.pedra-projetil, .papel-projetil'));
                avancar(2610);
                const lancamentos = [minha, dele].filter(acao => acao !== 'tesoura').length;
                verificar('Objetos sincronizados com a soltura', document.querySelectorAll('.pedra-projetil, .papel-projetil').length === lancamentos);
                avancar(2800);
                const cortes = [minha, dele].filter(acao => acao === 'tesoura').length;
                verificar('Tesoura repete o efeito ao fechar as lâminas', document.querySelectorAll('.efeito-corte').length === cortes);
                avancar(3750);
                verificar('Resultado remove poses de ataque e projéteis', duelo.revelada && !duelo.animando && !document.querySelector('.acao-sequencia:not(.resultado-sequencia), [data-efeito-duelo]'));
                verificar('Vitória e derrota usam os personagens corretos',
                    document.querySelector('#lutador-voce .resultado-sequencia')?.dataset.personagem === meu
                    && document.querySelector('#lutador-voce .resultado-sequencia')?.dataset.resultado === 'vitoria'
                    && document.querySelector('#lutador-oponente .resultado-sequencia')?.dataset.personagem === outro
                    && document.querySelector('#lutador-oponente .resultado-sequencia')?.dataset.resultado === 'derrota');
            }
        }
        // Movimento reduzido e chegada à página com uma rodada já finalizada.
        for (const reduzido of [false, true]) {
            tarefas = [];
            rodada++;
            duelo.inicializado = false;
            duelo.movimentoReduzido.matches = reduzido;
            duelo.atualizar(estado('barbudo', 'barbudo', 'pedra', 'tesoura', true));
            verificar(`Rodada já finalizada sem reproduzir ataque (movimento reduzido: ${reduzido})`, !duelo.animando && tarefas.length === 0 && duelo.palco.dataset.fase === 'resultado');
        }
        duelo.movimentoReduzido.matches = true;
        tarefas = [];
        rodada++;
        duelo.atualizar(estado('barbudo', 'classico', 'papel', 'pedra', false));
        duelo.atualizar(estado('barbudo', 'classico', 'papel', 'pedra', true));
        verificar('Movimento reduzido pula a animação de uma nova rodada', !duelo.animando && tarefas.length === 0 && duelo.palco.dataset.fase === 'resultado');

        // Um atlas indisponível deve permitir o movimento alternativo existente.
        duelo.movimentoReduzido.matches = false;
        tarefas = [];
        agora = 0;
        rodada++;
        const salvo = duelo.acoesPersonagens.barbudo.pedra;
        duelo.acoesPersonagens.barbudo.pedra = new Image();
        duelo.atualizar(estado('barbudo', 'classico', 'pedra', 'papel', false));
        duelo.atualizar(estado('barbudo', 'classico', 'pedra', 'papel', true));
        avancar(1650);
        verificar('Atlas indisponível usa a investida alternativa', document.querySelector('#lutador-voce').classList.contains('atacando') && !document.querySelector('#lutador-voce .acao-sequencia'));
        duelo.acoesPersonagens.barbudo.pedra = salvo;
        avancar(3750);

        // Cancelamento com timers reais, como ocorre ao encerrar ou trocar rodada.
        duelo.depois = nativeDepois;
        duelo.apresentar(estado('barbudo', 'barbudo', 'pedra', 'papel', true));
        duelo.cancelar();
        verificar('Cancelamento remove timers, poses e efeitos', !duelo.animando && duelo.tempos.length === 0 && !document.querySelector('.acao-sequencia, [data-efeito-duelo]'));
        await new Promise(resolve => setTimeout(resolve, 1800));
        verificar('Ataque cancelado não reaparece', !document.querySelector('.acao-sequencia, [data-efeito-duelo]'));

        // Prévia final de Márcio dos dois lados, sem chamadas de rede da partida.
        duelo.depois = (ms, acao) => tarefas.push({ instante: agora + ms, acao });
        tarefas = [];
        agora = 0;
        rodada++;
        duelo.atualizar(estado('barbudo', 'barbudo', 'pedra', 'tesoura', false));
        duelo.atualizar(estado('barbudo', 'barbudo', 'pedra', 'tesoura', true));
        avancar(2210);
        report.dataset.status = 'aprovado';
        report.textContent = `${resultados.length} verificações aprovadas.\n` + JSON.stringify(resultados, null, 2);
    } catch (erro) {
        report.dataset.status = 'falhou';
        report.textContent = `${erro.stack}\n` + JSON.stringify(resultados, null, 2);
    }
})();
