<?php
// Caminho público dos assets, relativo à URL da página que inclui este componente.
$personagemAssets = rtrim($personagemAssets ?? 'assets', '/');
$personagemModeloVersao = (string) filemtime(__DIR__ . '/../assets/personagem/animacoes/personagem-combinado.glb');
$personagemPosterVersao = (string) filemtime(__DIR__ . '/../assets/personagem/animacoes/poster-combinado.png');
$personagemJsVersao = (string) filemtime(__DIR__ . '/../assets/personagem-animado.js');
$assetPersonagem = static fn(string $path): string => htmlspecialchars(
    $personagemAssets . '/' . $path, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'
);
if (!defined('PERSONAGEM_ASSETS_LOADED')):
    define('PERSONAGEM_ASSETS_LOADED', true);
?>
<link rel="stylesheet" href="<?= $assetPersonagem('personagem.css') ?>">
<link rel="stylesheet" href="<?= $assetPersonagem('personagem-animado.css') ?>">
<script type="module" src="<?= $assetPersonagem('personagem-animado.js?v=' . $personagemJsVersao) ?>"></script>
<?php endif; ?>
<section class="personagem" data-personagem aria-label="Visualização do personagem">
        <div class="personagem__gestos" role="group" aria-label="Escolha uma animação">
            <button type="button" data-personagem-clip="Pedra" disabled aria-pressed="false">✊ Pedra</button>
            <button type="button" data-personagem-clip="Papel" disabled aria-pressed="false">✋ Papel</button>
            <button type="button" data-personagem-clip="Tesoura" disabled aria-pressed="false">✌ Tesoura</button>
            <button type="button" class="secundario" data-personagem-clip="Idle" disabled aria-pressed="false">Repouso</button>
        </div>
    <div class="personagem__palco">
        <img class="personagem__poster" src="<?= $assetPersonagem('personagem/animacoes/poster-combinado.png?v=' . $personagemPosterVersao) ?>"
            alt="Personagem low poly com o rosto original, óculos, camiseta vermelha e calça azul."
            width="760" height="900">
        <model-viewer
            class="personagem__modelo"
            src="<?= $assetPersonagem('personagem/animacoes/personagem-combinado.glb?v=' . $personagemModeloVersao) ?>"
            alt="Personagem low poly em 3D. Use as setas do teclado para girar."
            camera-controls touch-action="pan-y" disable-pan
            camera-orbit="12deg 85deg 15m" camera-target="0m 3.2m 0m" field-of-view="30deg"
            animation-name="Idle" animation-crossfade-duration="180"
            min-camera-orbit="auto 35deg 8m" max-camera-orbit="auto 110deg 40m"
            shadow-intensity="0.9" shadow-softness="0.6"
            environment-image="<?= $assetPersonagem('personagem/animacoes/estudio.hdr') ?>" exposure="1.4"
            interaction-prompt="none" loading="eager">
        </model-viewer>
    </div>
    <div class="personagem__barra">
        <p class="personagem__status" role="status" aria-live="polite">Prévia do personagem</p>
        <div class="personagem__controles" aria-label="Controles do personagem">
            <button type="button" class="secundario" data-personagem-acao="frente" disabled>Vista frontal</button>
            <button type="button" class="secundario" data-personagem-acao="aproximar" disabled aria-label="Aproximar personagem">+ Zoom</button>
            <button type="button" class="secundario" data-personagem-acao="afastar" disabled aria-label="Afastar personagem">− Zoom</button>
        </div>
    </div>
    <div class="personagem__animacoes" aria-label="Pack de animações">
        <div class="personagem__reproducao">
            <button type="button" class="secundario" data-personagem-pausa disabled>Pausar</button>
            <label>Velocidade
                <select data-personagem-velocidade aria-label="Velocidade da animação">
                    <option value="0.5">0,5× · Câmera lenta</option>
                    <option value="1" selected>1× · Normal</option>
                    <option value="1.25">1,25×</option>
                </select>
            </label>
            <input type="range" min="0" max="1000" value="0" step="1" data-personagem-tempo aria-label="Posição na animação" disabled>
        </div>
    </div>
    <noscript><p class="personagem__aviso">Ative o JavaScript para explorar o personagem em 3D.</p></noscript>
</section>

