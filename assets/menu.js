'use strict';

const opcoesMenu = [...document.querySelectorAll('[data-menu]')];
let opcaoAtual = 0;

function selecionarOpcao(indice, focar = false) {
    opcaoAtual = indice;
    opcoesMenu.forEach((opcao, i) => opcao.classList.toggle('selecionada', i === indice));
    if (focar) opcoesMenu[indice].focus();
}

opcoesMenu.forEach((opcao, i) => {
    opcao.addEventListener('focus', () => selecionarOpcao(i));
    opcao.addEventListener('pointerenter', (evento) => {
        if (evento.pointerType === 'mouse') selecionarOpcao(i);
    });
});

document.addEventListener('keydown', (evento) => {
    if (evento.altKey || evento.ctrlKey || evento.metaKey || evento.isComposing) return;
    if (evento.key === 'ArrowDown' || evento.key === 'ArrowUp') {
        evento.preventDefault();
        const direcao = evento.key === 'ArrowDown' ? 1 : -1;
        selecionarOpcao((opcaoAtual + direcao + opcoesMenu.length) % opcoesMenu.length, true);
    } else if (evento.key === 'Enter') {
        evento.preventDefault();
        opcoesMenu[opcaoAtual].click();
    }
});
