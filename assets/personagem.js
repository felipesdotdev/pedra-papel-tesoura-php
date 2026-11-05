// Local, versioned dependency. No build step or CDN is required.
const componentes = [...document.querySelectorAll('[data-personagem]')];

for (const componente of componentes) {
    const modelo = componente.querySelector('model-viewer');
    const status = componente.querySelector('[role="status"]');
    const controles = [...componente.querySelectorAll('[data-personagem-acao]')];
    componente.dataset.estado = 'carregando';
    status.textContent = 'Carregando personagem 3D…';

    const falha = () => {
        componente.dataset.estado = 'erro';
        status.textContent = 'O 3D não está disponível neste navegador. Exibindo a imagem do personagem.';
        controles.forEach(botao => { botao.disabled = true; });
    };
    modelo.addEventListener('error', falha);
    modelo.addEventListener('load', () => {
        componente.dataset.estado = 'pronto';
        status.textContent = 'Arraste para girar · Use as setas quando o modelo estiver em foco';
        controles.forEach(botao => { botao.disabled = false; });
    });

    controles.forEach(botao => botao.addEventListener('click', () => {
        if (componente.dataset.estado !== 'pronto') return;
        if (botao.dataset.personagemAcao === 'frente') {
            modelo.cameraOrbit = '0deg 88deg 16m';
        } else {
            const orbita = modelo.getCameraOrbit();
            const fator = botao.dataset.personagemAcao === 'aproximar' ? 0.85 : 1.18;
            const raio = Math.max(8, Math.min(40, orbita.radius * fator));
            modelo.cameraOrbit = `${orbita.theta}rad ${orbita.phi}rad ${raio}m`;
        }
        requestAnimationFrame(() => modelo.jumpCameraToGoal());
    }));

    // Import failures (including unavailable WebGL) keep the static poster visible.
    import('./vendor/model-viewer.min.js').catch(falha);
}
