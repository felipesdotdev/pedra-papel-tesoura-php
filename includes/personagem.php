<?php
// Caminho público dos assets, relativo à URL da página que inclui este componente.
$personagemAssets = rtrim($personagemAssets ?? 'assets', '/');
$personagemModeloVersao = (string) filemtime(__DIR__ . '/../assets/personagem/personagem.glb');
$personagemPosterVersao = (string) filemtime(__DIR__ . '/../assets/personagem/poster.png');
$assetPersonagem = static fn(string $path): string => htmlspecialchars(
    $personagemAssets . '/' . $path, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'
);
if (!defined('PERSONAGEM_ASSETS_LOADED')):
    define('PERSONAGEM_ASSETS_LOADED', true);
?>
<link rel="stylesheet" href="<?= $assetPersonagem('personagem.css') ?>">
<script type="module" src="<?= $assetPersonagem('personagem.js') ?>"></script>
<?php endif; ?>
<section class="personagem" data-personagem aria-label="Visualização do personagem">
    <div class="personagem__palco">
        <img class="personagem__poster" src="<?= $assetPersonagem('personagem/poster.png?v=' . $personagemPosterVersao) ?>"
            alt="Personagem low poly com cabelo escuro, camiseta cinza, calça preta e tênis com solado claro."
            width="1122" height="1402">
        <model-viewer
            class="personagem__modelo"
            src="<?= $assetPersonagem('personagem/personagem.glb?v=' . $personagemModeloVersao) ?>"
            alt="Personagem low poly em 3D. Use as setas do teclado para girar."
            camera-controls touch-action="pan-y" disable-pan
            camera-orbit="0deg 88deg 16m" field-of-view="30deg"
            min-camera-orbit="auto 35deg 8m" max-camera-orbit="auto 110deg 40m"
            shadow-intensity="0.7" shadow-softness="1"
            environment-image="neutral" exposure="1"
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
    <noscript><p class="personagem__aviso">Ative o JavaScript para explorar o personagem em 3D.</p></noscript>
</section>

