# Template fixo de posts — @onlyextremo.ia

Padrão visual oficial: cabeçalho branco com a logo original, @onlyextremo.ia e data; corpo #0B0E13; acentos ciano #00DDE8 e verde #75F300; etiqueta vermelha #E71D2E; rodapé "ONLYEXTREMO IA • NOTÍCIAS".

## Como gerar

    pip install pillow
    python template/gerar_post.py posts.json saida            # feed 1080x1080
    python template/gerar_post.py posts.json saida --stories  # 1080x1920

Cada item de `posts.json`: `arquivo`, `data`, `etiqueta`, `manchete`, `apoio`, `fonte`, `fundo`.
Na manchete, `*trecho*` sai em ciano e `_trecho_` em verde.
`fundo`: `stf`, `congresso`, `bandeira`, o caminho de uma foto autorizada, ou vazio (layout tipográfico).

Saída: PNG e JPEG (o Instagram exige JPEG).

## Arquivos

- `logo.png`: logo da marca. Hoje é a versão extraída de um print; troque pelo PNG original mantendo o nome.
- `fundos/`: fundos temáticos sem texto. Novos fundos: salvar como `fundos/<nome>.jpg`.
- `fontes/`: Montserrat (licença aberta OFL).

## Reels

    python template/gerar_reel.py posts.json saida

Gera um MP4 de 9 s (1080x1920, H.264, 30 fps) com o mesmo `posts.json`: a manchete entra linha a linha, depois o apoio, com zoom lento no fundo. Requer ffmpeg. Também salva a capa em JPEG. A faixa inferior fica livre porque a interface do Reels cobre essa área.

Campo extra nos Reels: `trilha` = `suspense` (padrão), `urgente` ou `neutro`. As trilhas em `trilhas/` são originais, sintetizadas por `trilhas/gerar_trilhas.py`, sem direitos de terceiros.
