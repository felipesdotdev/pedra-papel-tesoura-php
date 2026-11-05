'use strict';

class Duelo2D {
    constructor(jogo, redesenhar) {
        this.jogo = jogo;
        this.redesenhar = redesenhar;
        this.palco = document.querySelector('#palco-duelo');
        this.anuncio = document.querySelector('#duelo-anuncio');
        this.titulo = document.querySelector('#anuncio-titulo');
        this.legenda = document.querySelector('#anuncio-legenda');
        this.status = document.querySelector('#status');
        this.detalhes = document.querySelector('#detalhes');
        this.revanche = document.querySelector('#revanche');
        this.movimentoReduzido = matchMedia('(prefers-reduced-motion: reduce)');
        this.tempos = [];
        this.rodada = null;
        this.inicializado = false;
        this.revelada = false;
        this.animando = false;
        this.estado = null;
        this.personagens = {
            classico: { nome: 'Froldi', imagem: 'assets/duelo/froldi.webp' },
            barbudo: { nome: 'Márcio', imagem: 'assets/duelo/marcio.webp' },
        };
        this.acoesPersonagens = {};
        for (const [chave, nome] of [['classico', 'froldi'], ['barbudo', 'marcio']]) {
            this.acoesPersonagens[chave] = {};
            for (const acao of ['pedra', 'papel', 'tesoura']) {
                const atlas = new Image();
                atlas.src = `assets/duelo/${nome}-acoes/${acao}/${chave === 'classico' ? 'spritesheet-alinhado.webp' : 'spritesheet.webp'}`;
                this.acoesPersonagens[chave][acao] = atlas;
            }
        }
        this.resultadosPersonagens = {};
        for (const [chave, nome] of [['classico', 'froldi'], ['barbudo', 'marcio']]) {
            this.resultadosPersonagens[chave] = {};
            for (const tipo of ['vitoria', 'derrota']) {
                const atlas = new Image();
                atlas.src = `assets/duelo/${nome}-resultados/${tipo}/spritesheet.webp`;
                this.resultadosPersonagens[chave][tipo] = atlas;
            }
        }
        this.gestos = { pedra: '✊', papel: '✋', tesoura: '✌' };
        this.idleAtlas = {};
        for (const [chave, nome] of [['classico', 'froldi'], ['barbudo', 'marcio']]) {
            const imagem = new Image();
            this.idleAtlas[chave] = imagem;
            imagem.onload = () => this.atualizarIdle();
            imagem.src = chave === 'barbudo' ? 'assets/duelo/marcio-idle/spritesheet.webp' : `assets/duelo/${nome}-idle/spritesheet-v2.webp`;
        }
        const visibilidade = () => { this.palco.dataset.pausado = String(document.hidden); };
        document.addEventListener('visibilitychange', visibilidade);
        visibilidade();
        this.movimentoReduzido.addEventListener('change', () => this.atualizarIdle());
    }

    depois(ms, acao) { this.tempos.push(setTimeout(acao, ms)); }
    cancelar() {
        this.tempos.forEach(clearTimeout);
        this.tempos = [];
        this.animando = false;
        this.limparSprites();
        this.palco.querySelectorAll('.lutador').forEach(el => { el.className = el.id === 'lutador-voce' ? 'lutador lutador-voce' : 'lutador lutador-oponente'; });
    }
    limparSprites() {
        this.palco.querySelectorAll('.acao-sequencia, [data-efeito-duelo]').forEach(el => el.remove());
        this.palco.querySelectorAll('.lutador').forEach(el => el.classList.remove('usando-sprites'));
    }
    arremessar(lado, tipo) {
        const projetil = document.createElement('span');
        projetil.className = `${tipo}-projetil ${tipo}-${lado}`;
        projetil.dataset.efeitoDuelo = tipo;
        projetil.setAttribute('aria-hidden', 'true');
        this.palco.append(projetil);
        this.depois(tipo === 'papel' ? 880 : 670, () => projetil.remove());
    }
    cortar(lado) {
        const corte = document.createElement('span');
        corte.className = `efeito-corte corte-${lado}`;
        corte.dataset.efeitoDuelo = 'tesoura';
        corte.setAttribute('aria-hidden', 'true');
        this.palco.append(corte);
        this.depois(300, () => corte.remove());
    }
    animarAcao(lado, personagem, acao) {
        const atlas = this.acoesPersonagens[personagem]?.[acao];
        if (!atlas?.complete || !atlas.naturalWidth) return false;
        const lutador = document.querySelector(`#lutador-${lado}`);
        const sprite = document.createElement('span');
        sprite.className = 'acao-sequencia';
        sprite.dataset.personagem = personagem;
        sprite.dataset.acao = acao;
        sprite.style.backgroundImage = `url("${atlas.src}")`;
        sprite.setAttribute('aria-hidden', 'true');
        lutador.append(sprite);
        lutador.classList.add('usando-sprites');
        const idle = lutador.querySelector('.idle-sequencia');
        const idlePosicao = idle ? getComputedStyle(idle).backgroundPosition : '0 0';
        const idleImagem = this.idleAtlas[personagem].src;
        if (personagem === 'classico') {
            sprite.style.backgroundImage = `url("${idleImagem}")`;
            sprite.style.backgroundSize = '400% 400%';
            sprite.style.backgroundPosition = idlePosicao;
        }
        const sequencia = acao === 'tesoura' ? [0, 1, 2, 3, 2, 3, 4, 5] : [0, 1, 2, 3, 4, 5];
        const tempos = acao === 'tesoura' ? [0, 230, 460, 690, 920, 1150, 1380, 1610] : [0, 260, 560, 960, 1320, 1560];
        sequencia.forEach((frame, i) => {
            this.depois(tempos[i], () => {
                const neutro = personagem === 'classico' && (frame === 0 || frame === 5);
                sprite.style.backgroundImage = `url("${neutro ? idleImagem : atlas.src}")`;
                sprite.style.backgroundSize = neutro ? '400% 400%' : '300% 200%';
                sprite.style.backgroundPosition = neutro ? idlePosicao : `${(frame % 3) * 50}% ${Math.floor(frame / 3) * 100}%`;
                sprite.dataset.frame = String(frame);
            });
        });
        if (acao === 'tesoura') {
            this.depois(690, () => this.cortar(lado));
            this.depois(1150, () => this.cortar(lado));
        } else this.depois(960, () => this.arremessar(lado, acao));
        return true;
    }
    animarResultado(lado, personagem, tipo, animar) {
        const atlas = this.resultadosPersonagens[personagem]?.[tipo];
        if (!atlas?.complete || !atlas.naturalWidth) return false;
        const lutador = document.querySelector(`#lutador-${lado}`);
        const idle = lutador.querySelector('.idle-sequencia');
        lutador.classList.add('usando-sprites');
        const sprite = document.createElement('span');
        sprite.className = 'acao-sequencia resultado-sequencia';
        sprite.dataset.personagem = personagem;
        sprite.dataset.resultado = tipo;
        sprite.setAttribute('aria-hidden', 'true');
        lutador.append(sprite);
        const inicio = () => {
            sprite.style.backgroundImage = `url("${this.idleAtlas[personagem].src}")`;
            sprite.style.backgroundSize = personagem === 'classico' ? '400% 400%' : '400% 200%';
            sprite.style.backgroundPosition = idle ? getComputedStyle(idle).backgroundPosition : '0 0';
            sprite.dataset.frame = '0';
        };
        const quadro = frame => {
            sprite.style.backgroundImage = `url("${atlas.src}")`;
            sprite.style.backgroundSize = '300% 200%';
            sprite.style.backgroundPosition = `${(frame % 3) * 50}% ${Math.floor(frame / 3) * 100}%`;
            sprite.dataset.frame = String(frame);
        };
        if (animar && !this.movimentoReduzido.matches) {
            inicio();
            [300, 600, 950, 1300, 1700].forEach((tempo, i) => this.depois(tempo, () => quadro(i + 1)));
        } else quadro(5);
        return true;
    }
    atualizarIdle() {
        if (!this.estado) return;
        for (const [lado, chave] of [['voce', this.estado.meu_personagem], ['oponente', this.estado.personagem_oponente]]) {
            const atlas = this.idleAtlas[chave];
            const lutador = document.querySelector(`#lutador-${lado}`);
            const pronto = !!atlas?.complete && !!atlas.naturalWidth && !this.movimentoReduzido.matches;
            lutador.classList.toggle('idle-pronto', pronto);
            if (!pronto) continue;
            let sprite = lutador.querySelector('.idle-sequencia');
            if (!sprite) {
                sprite = document.createElement('span');
                sprite.className = 'idle-sequencia';
                sprite.setAttribute('aria-hidden', 'true');
                lutador.append(sprite);
            }
            sprite.classList.remove('idle-fixo', 'idle-rig');
            sprite.classList.toggle('idle-marcio', chave === 'barbudo');
            sprite.classList.toggle('idle-froldi', chave === 'classico');
            if (sprite.dataset.personagem !== chave) {
                sprite.style.backgroundImage = `url("${atlas.src}")`;
                sprite.dataset.personagem = chave;
            }
        }
    }
    anuncioTexto(titulo, legenda) {
        this.titulo.textContent = titulo;
        this.legenda.textContent = legenda;
    }
    placar(estado) {
        document.querySelector('#pontos-voce').textContent = estado.placar.voce;
        document.querySelector('#pontos-oponente').textContent = estado.placar.oponente;
        document.querySelector('#empates-duelo').textContent = `${estado.placar.empates} empate${estado.placar.empates === 1 ? '' : 's'}`;
    }
    mostrarGestos(estado) {
        [['voce', estado.minha_escolha], ['oponente', estado.escolha_oponente]].forEach(([lado, escolha]) => {
            const el = document.querySelector(`#gesto-${lado}`);
            el.textContent = this.gestos[escolha] || '';
            el.hidden = !escolha;
            el.setAttribute('aria-label', escolha || '');
        });
    }
    resultado(estado, animar) {
        this.limparSprites();
        this.revelada = true;
        this.animando = false;
        this.palco.dataset.fase = 'resultado';
        this.mostrarGestos(estado);
        this.placar(estado);
        const empate = estado.vencedor === 'empate';
        this.anuncioTexto(empate ? 'EMPATE' : estado.vencedor === 'voce' ? 'VITÓRIA' : 'DERROTA', `${estado.minha_escolha} × ${estado.escolha_oponente}`);
        if (!empate) {
            const vencedor = document.querySelector(`#lutador-${estado.vencedor}`);
            const perdedor = document.querySelector(`#lutador-${estado.vencedor === 'voce' ? 'oponente' : 'voce'}`);
            const ladoVencedor = estado.vencedor;
            const ladoPerdedor = ladoVencedor === 'voce' ? 'oponente' : 'voce';
            const personagemVencedor = ladoVencedor === 'voce' ? estado.meu_personagem : estado.personagem_oponente;
            const personagemPerdedor = ladoPerdedor === 'voce' ? estado.meu_personagem : estado.personagem_oponente;
            if (!this.animarResultado(ladoVencedor, personagemVencedor, 'vitoria', animar)) {
                vencedor.classList.add(animar ? 'vencedor' : 'vencedor-parado');
            }
            if (!this.animarResultado(ladoPerdedor, personagemPerdedor, 'derrota', animar)) perdedor.classList.add('derrotado');
        }
        this.palco.setAttribute('aria-label', `${estado.resultado} Você jogou ${estado.minha_escolha}; ${estado.oponente} jogou ${estado.escolha_oponente}.`);
        document.querySelector('#fase-duelo').textContent = 'Rodada concluída';
    }
    apresentar(estado) {
        this.animando = true;
        this.palco.dataset.fase = 'contagem';
        this.anuncioTexto('PEDRA', 'Prepare sua jogada');
        this.depois(550, () => this.anuncioTexto('PAPEL', 'Prepare sua jogada'));
        this.depois(1100, () => this.anuncioTexto('TESOURA!', 'Valendo!'));
        this.depois(1650, () => {
            this.palco.dataset.fase = 'ataque';
            this.anuncioTexto('DUELO!', 'Jogadas reveladas');
            this.mostrarGestos(estado);
            [['voce', estado.meu_personagem, estado.minha_escolha], ['oponente', estado.personagem_oponente, estado.escolha_oponente]].forEach(([lado, personagem, escolha]) => {
                const animado = this.animarAcao(lado, personagem, escolha);
                if (!animado) document.querySelector(`#lutador-${lado}`).classList.add('atacando');
            });
        });
        this.depois(3750, () => {
            this.palco.querySelectorAll('.lutador').forEach(el => el.classList.remove('atacando'));
            this.resultado(estado, true);
            this.redesenhar();
        });
    }
    atualizar(estado) {
        this.estado = estado;
        const primeiro = !this.inicializado;
        this.inicializado = true;
        if (estado.rodada_id !== this.rodada) {
            this.cancelar();
            this.rodada = estado.rodada_id;
            this.revelada = false;
            document.querySelectorAll('.jogada-revelada').forEach(el => { el.hidden = true; });
        }
        const personagens = [this.personagens[estado.meu_personagem] || this.personagens.classico, this.personagens[estado.personagem_oponente] || this.personagens.barbudo];
        [['voce', personagens[0]], ['oponente', personagens[1]]].forEach(([lado, p]) => {
            const img = document.querySelector(`#sprite-${lado}`);
            if (img.getAttribute('src') !== p.imagem) img.src = p.imagem;
        });
        this.atualizarIdle();
        document.querySelector('#meu-personagem').textContent = personagens[0].nome;
        document.querySelector('#outro-personagem').textContent = personagens[1].nome;
        document.querySelector('#numero-rodada').textContent = `RODADA ${estado.numero_rodada}`;
        if (estado.sala_status === 'encerrada') {
            this.cancelar();
            this.palco.dataset.fase = 'encerrada';
            this.anuncioTexto('FIM DO DUELO', 'Sala encerrada');
            document.querySelector('#fase-duelo').textContent = 'Encerrada';
            return;
        }
        if (estado.finalizada && !this.revelada && !this.animando) {
            if (primeiro || this.movimentoReduzido.matches) this.resultado(estado, false);
            else this.apresentar(estado);
        }
        if (this.animando) {
            this.status.textContent = 'Pedra, papel, tesoura…';
            this.detalhes.hidden = true;
            this.revanche.hidden = true;
            document.querySelector('#pedido-revanche').textContent = '';
            document.querySelector('#fase-duelo').textContent = 'Duelo em andamento';
            return;
        }
        if (estado.finalizada) return;
        this.placar(estado);
        const aguardando = estado.sala_status === 'aguardando';
        this.palco.dataset.fase = aguardando ? 'aguardando' : 'pronto';
        document.querySelector('#lutador-oponente').classList.toggle('ausente', aguardando);
        this.anuncioTexto(aguardando ? 'VS' : estado.minha_escolha ? 'PRONTO!' : 'VS', aguardando ? 'Convide um adversário' : estado.minha_escolha ? 'Aguardando oponente' : 'Faça sua escolha');
        document.querySelector('#fase-duelo').textContent = aguardando ? 'Aguardando jogador' : estado.minha_escolha ? 'Jogada enviada em segredo' : 'Escolha sua jogada';
        this.palco.setAttribute('aria-label', aguardando ? 'Arena aguardando adversário.' : `${personagens[0].nome} contra ${personagens[1].nome}. Aguardando jogadas.`);
    }
}
