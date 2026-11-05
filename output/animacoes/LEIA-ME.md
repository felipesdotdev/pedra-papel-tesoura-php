# Personagem combinado — pack de animações

O rosto, os olhos, o nariz, a mandíbula e o cabelo frontal preservam a versão original. A testa recebeu uma curvatura local e a parte posterior da cabeça ganhou volume. O corpo, os óculos e a barba discreta aproveitam a versão mais recente. Não se trata de uma reprodução exata da folha de referência.

## Arquivos finais

- `personagem_combinado_animado.blend`: cena editável, objetos separados, rig IK e quatro Actions nos tracks NLA.
- `personagem-combinado.glb`: exportação para web, uma malha skinned com materiais separados e quatro clipes. Está em `assets/personagem/animacoes/` no projeto.
- `pack.json`: nomes, duração, fps e frames de soltura dos objetos.

## Clipes (30 fps)

| Nome | Duração | Conteúdo |
| --- | --- | --- |
| Idle | 2,97 s | Respiração e transferência discreta de peso, em loop |
| Pedra | 3,77 s | Retirada do bolso, preparação, passo de apoio, arremesso e recuperação |
| Papel | 4,17 s | Preparação do avião, lançamento, voo com leve inclinação e recuperação |
| Tesoura | 4,77 s | Retirada do bolso, três ciclos de corte e retorno |

Os clipes de ação começam e terminam em repouso. Pedra é solta no frame 63, o avião no 67. Os objetos são animados junto com o corpo e as lâminas da tesoura são articuladas.

## Rig no Blender

65 ossos no total, incluindo controles: quadril, coluna, peito, pescoço, cabeça, clavículas, braços, antebraços, mãos, coxas, canelas, pés, dedos dos pés, três falanges por dedo da mão e ossos dos objetos.

Use os controles `CTRL_hand.R/L` e `CTRL_foot.R/L` para as cadeias IK. `POLE_arm.R/L` e `POLE_leg.R/L` orientam cotovelos e joelhos. O corpo possui pesos normalizados nas dobras e a cabeça é rígida em um único osso para manter a correspondência entre rosto, cabelo e óculos.

Para reproduzir uma Action no Blender, mantenha os tracks NLA mutados e selecione a Action desejada no Action Editor. Os nomes internos podem ter um sufixo numérico por coexistirem outras versões na sessão; os tracks e clipes GLB têm os nomes canônicos acima.

## Web

Execute `php -S localhost:8000` na raiz do projeto e abra `http://localhost:8000/personagem.php`. O componente reutilizável é `includes/personagem.php`. O JavaScript `assets/personagem-animado.js` permite disparar os clipes, pausar, alterar a velocidade e inspecionar o tempo. O GLB não depende de Blender, PHP gráfico ou pacotes npm no servidor. A página usa `estudio.hdr` como iluminação lateral para evidenciar os planos do rosto; ela não está embutida no GLB e pode ser substituída pelo ambiente do aplicativo de destino.

No glTF, +Y é o eixo vertical. As restrições IK foram amostradas em canais de deformação a 30 fps. Objetos de cena ficam ocultos fora de sua respectiva ação e suas posições de repouso foram ajustadas para não deslocar o chão/sombra do visualizador.

## Verificação

Foram conferidos os nomes dos quatro clipes, a existência da skin, poses de preparação/soltura/corte, pesos das malhas e a correspondência dos controles IK. A percepção de semelhança e o acabamento artístico continuam sujeitos à revisão do usuário. A iluminação do visualizador web difere da iluminação do Blender.
