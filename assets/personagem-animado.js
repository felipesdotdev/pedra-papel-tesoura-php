const biblioteca = import('./vendor/model-viewer.min.js');
const reduzirMovimento = window.matchMedia('(prefers-reduced-motion: reduce)');

for (const componente of document.querySelectorAll('[data-personagem]')) {
    const modelo = componente.querySelector('model-viewer');
    const status = componente.querySelector('[role="status"]');
    const camera = [...componente.querySelectorAll('[data-personagem-acao]')];
    const gestos = [...componente.querySelectorAll('[data-personagem-clip]')];
    const pausa = componente.querySelector('[data-personagem-pausa]');
    const velocidade = componente.querySelector('[data-personagem-velocidade]');
    const tempo = componente.querySelector('[data-personagem-tempo]');
    const nomes = { Idle: 'Repouso', Pedra: 'Pedra · Retirar do bolso e arremessar', Papel: 'Papel · Lançar avião de papel', Tesoura: 'Tesoura · Retirar do bolso e picotar o ar' };
    let pedido = 0, clip = 'Idle', carregado = false, intervalo;
    componente.dataset.estado = 'carregando';
    status.textContent = 'Carregando personagem e animações…';

    function atualizarPausa() {
        pausa.textContent = modelo.paused ? 'Reproduzir' : 'Pausar';
        pausa.setAttribute('aria-label', modelo.paused ? 'Reproduzir animação' : 'Pausar animação');
    }
    function atualizarTempo() {
        if (Number.isFinite(modelo.duration) && modelo.duration > 0 && document.activeElement !== tempo) {
            tempo.value = String(Math.round(1000 * modelo.currentTime / modelo.duration));
        }
    }
    function observar() {
        clearInterval(intervalo);
        if (!modelo.paused) intervalo = setInterval(atualizarTempo, 100);
        atualizarPausa();
    }
    function falha() {
        carregado = false;
        componente.dataset.estado = 'erro';
        status.textContent = 'O 3D não está disponível neste navegador. Exibindo a imagem do personagem.';
        [...camera, ...gestos, pausa, tempo].forEach(el => { el.disabled = true; });
        clearInterval(intervalo);
    }
    async function reproduzir(nome, iniciar = true) {
        if (!carregado || !modelo.availableAnimations.includes(nome)) return;
        const versao = ++pedido;
        modelo.pause(); clip = nome;
        modelo.animationCrossfadeDuration = reduzirMovimento.matches ? 0 : 180;
        modelo.animationName = nome;
        await modelo.updateComplete;
        if (versao !== pedido) return;
        modelo.currentTime = 0;
        modelo.timeScale = Number(velocidade.value);
        gestos.forEach(botao => botao.setAttribute('aria-pressed', String(botao.dataset.personagemClip === nome)));
        status.textContent = nomes[nome] || nome;
        tempo.value = '0';
        if (iniciar) modelo.play({ repetitions: nome === 'Idle' ? Infinity : 1 });
        observar();
    }
    modelo.addEventListener('error', falha);
    modelo.addEventListener('load', () => {
        carregado = true; componente.dataset.estado = 'pronto';
        camera.forEach(botao => { botao.disabled = false; });
        gestos.forEach(botao => { botao.disabled = !modelo.availableAnimations.includes(botao.dataset.personagemClip); });
        pausa.disabled = false; tempo.disabled = false;
        reproduzir('Idle', !reduzirMovimento.matches);
    });
    modelo.addEventListener('finished', () => {
        modelo.pause(); clearInterval(intervalo); tempo.value = '1000';
        status.textContent = `${nomes[clip]} · Concluído`; atualizarPausa();
    });
    gestos.forEach(botao => botao.addEventListener('click', () => reproduzir(botao.dataset.personagemClip)));
    pausa.addEventListener('click', () => {
        if (!carregado) return;
        if (modelo.paused) {
            if (modelo.currentTime >= modelo.duration - 0.025) modelo.currentTime = 0;
            modelo.play({ repetitions: clip === 'Idle' ? Infinity : 1 });
        } else modelo.pause();
        observar();
    });
    velocidade.addEventListener('change', () => { modelo.timeScale = Number(velocidade.value); });
    tempo.addEventListener('input', () => {
        if (!carregado) return;
        modelo.pause(); modelo.currentTime = Number(tempo.value) / 1000 * modelo.duration;
        clearInterval(intervalo); atualizarPausa();
    });
    camera.forEach(botao => botao.addEventListener('click', () => {
        if (!carregado) return;
        if (botao.dataset.personagemAcao === 'frente') modelo.cameraOrbit = '0deg 85deg 15m';
        else {
            const orbita = modelo.getCameraOrbit();
            const raio = Math.max(8, Math.min(40, orbita.radius * (botao.dataset.personagemAcao === 'aproximar' ? 0.85 : 1.18)));
            modelo.cameraOrbit = `${orbita.theta}rad ${orbita.phi}rad ${raio}m`;
        }
        requestAnimationFrame(() => modelo.jumpCameraToGoal());
    }));
    document.addEventListener('visibilitychange', () => { if (document.hidden && carregado) { modelo.pause(); observar(); } });
    reduzirMovimento.addEventListener('change', event => { if (event.matches && carregado) { modelo.pause(); observar(); } });
    biblioteca.catch(falha);
}
