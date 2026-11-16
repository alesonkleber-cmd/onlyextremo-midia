#!/usr/bin/env python3
"""Reel curto (9 s, 1080x1920, MP4) a partir do mesmo template dos posts.

Uso:
    python gerar_reel.py posts.json pasta_saida

A manchete entra linha a linha, depois o apoio; o fundo faz um zoom lento.
Campo extra por post: "trilha" = suspense (padrão), urgente ou neutro. As trilhas são
originais, sintetizadas por trilhas/gerar_trilhas.py, sem direitos de terceiros.
Requer Pillow e ffmpeg. Também salva a capa em JPEG.
"""
import json
import os
import subprocess
import sys

from PIL import Image

from gerar_post import render

FPS, DUR = 30, 9.0
BASE_LIVRE = 330  # faixa inferior que a interface do Reels cobre (legenda e botões)


def gerar_reel(p, caminho):
    final = render(p, True, base_livre=BASE_LIVRE)
    n = final.info["linhas"]
    # instantes em que cada linha (e por fim o apoio) começa a aparecer
    inicio = [0.5 + 0.7 * i for i in range(n + 1)]
    fade = 0.35
    nome = p.get("trilha") or "suspense"   # suspense | urgente | neutro
    trilha = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trilhas", nome + ".m4a")
    if not os.path.isfile(trilha):
        raise SystemExit(f"trilha não encontrada: {nome}")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
           "-r", str(FPS), "-i", "-", "-i", trilha, "-t", str(DUR), "-af", f"afade=t=out:st={DUR - 1.0}:d=1.0",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", caminho + ".mp4"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = int(FPS * DUR)
    for f in range(total):
        t = f / FPS
        zoom = 1.0 + 0.07 * (f / total)
        etapa = sum(1 for x in inicio if t >= x)           # quantos itens já começaram
        def quadro(k):
            return render(p, True, linhas_visiveis=min(k, n), mostrar_apoio=k > n, zoom=zoom, base_livre=BASE_LIVRE)
        im = quadro(etapa)
        if etapa > 0 and t - inicio[etapa - 1] < fade:      # transição suave do item mais recente
            a = (t - inicio[etapa - 1]) / fade
            im = Image.blend(quadro(etapa - 1), im, a)
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg falhou")
    final.save(caminho + "_capa.jpg", quality=93)
    return caminho + ".mp4"


if __name__ == "__main__":
    posts = json.load(open(sys.argv[1], encoding="utf-8"))
    os.makedirs(sys.argv[2], exist_ok=True)
    for p in posts:
        print(gerar_reel(p, os.path.join(sys.argv[2], p["arquivo"] + "_reel")))
