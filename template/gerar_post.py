#!/usr/bin/env python3
"""Template fixo de posts do Instagram @onlyextremo.ia.

Uso:
    python gerar_post.py posts.json pasta_saida [--stories]

posts.json é uma lista de objetos:
    {
      "arquivo": "2026-11-16_moraes",      # nome base do arquivo de saída
      "data": "16 NOV 2026",               # data real da publicação
      "etiqueta": "STF",                   # DESTAQUE, BRASIL, STF, GOVERNO, ENTENDA, URGENTE...
      "manchete": "MORAES NEGA VISITAS DE *ALIADOS* A BOLSONARO",
                                           # trecho entre *asteriscos* = ciano; entre _sublinhados_ = verde
      "apoio": "Linha curta de apoio.",    # opcional
      "fonte": "SBT News / Jovem Pan",     # opcional
      "fundo": "stf"                       # stf | congresso | bandeira | caminho de uma foto | "" (tipográfico)
    }

Só muda o conteúdo; logo, paleta, tipografia e margens são fixas.
Requer apenas Pillow. Fontes e logo ficam nesta pasta.
"""
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
FUNDO, BRANCO = (11, 14, 19), (255, 255, 255)
CIANO, VERDE, VERMELHO = (0, 221, 232), (117, 243, 0), (231, 29, 46)
CINZA, PRETO = (214, 220, 228), (12, 12, 14)
W, M = 1080, 60  # largura e margem lateral
USUARIO = "@onlyextremo.ia"


def fonte(peso, tam):
    return ImageFont.truetype(os.path.join(AQUI, "fontes", f"Montserrat-{peso}.ttf"), tam)


def logo(diametro):
    """Logo original, recortada em círculo, sem redesenho."""
    im = Image.open(os.path.join(AQUI, "logo.png")).convert("RGB")
    lado = min(im.size)
    im = im.crop((0, 0, lado, lado)).resize((diametro * 2, diametro * 2), Image.LANCZOS)
    masc = Image.new("L", im.size, 0)
    ImageDraw.Draw(masc).ellipse([6, 6, im.size[0] - 6, im.size[1] - 6], fill=255)
    im.putalpha(masc)
    return im.resize((diametro, diametro), Image.LANCZOS)


def degrade_h(larg, alt, c1, c2):
    faixa = Image.new("RGB", (larg, alt))
    px = faixa.load()
    for x in range(larg):
        t = x / max(larg - 1, 1)
        cor = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        for y in range(alt):
            px[x, y] = cor
    return faixa


def tokens(manchete):
    """Divide a manchete em (palavra, cor)."""
    out = []
    for a, b, c in re.findall(r"\*([^*]+)\*|_([^_]+)_|([^*_]+)", manchete):
        cor = CIANO if a else VERDE if b else BRANCO
        for palavra in (a or b or c).upper().split():
            out.append((palavra, cor))
    return out


def quebrar(d, toks, f, larg):
    linhas, atual, esp = [], [], d.textlength(" ", font=f)
    for pal, cor in toks:
        teste = sum(d.textlength(p, font=f) for p, _ in atual) + esp * len(atual) + d.textlength(pal, font=f)
        if atual and teste > larg:
            linhas.append(atual)
            atual = []
        atual.append((pal, cor))
    if atual:
        linhas.append(atual)
    return linhas


def quebrar_texto(d, texto, f, larg):
    linhas, atual = [], ""
    for pal in texto.split():
        teste = (atual + " " + pal).strip()
        if atual and d.textlength(teste, font=f) > larg:
            linhas.append(atual)
            atual = pal
        else:
            atual = teste
    if atual:
        linhas.append(atual)
    return linhas


def aplicar_fundo(im, caminho, y0, y1):
    """Foto na zona inferior, com degradê escuro para preservar a leitura."""
    foto = Image.open(caminho).convert("RGB")
    alt = y1 - y0
    esc = max(W / foto.width, alt / foto.height)
    foto = foto.resize((int(foto.width * esc) + 1, int(foto.height * esc) + 1), Image.LANCZOS)
    x = (foto.width - W) // 2
    y = max(0, (foto.height - alt) // 2)
    foto = foto.crop((x, y, x + W, y + alt))
    masc = Image.new("L", (W, alt), 255)
    pm = masc.load()
    topo, base = int(alt * 0.42), int(alt * 0.16)
    for yy in range(alt):
        if yy < topo:
            a = int(255 * (yy / topo) ** 1.6)
        elif yy > alt - base:
            a = int(255 * ((alt - yy) / base))
        else:
            a = 255
        for xx in range(W):
            pm[xx, yy] = a
    im.paste(foto, (0, y0), masc)


def gerar(p, caminho_saida, stories=False):
    H = 1920 if stories else 1080
    im = Image.new("RGB", (W, H), FUNDO)
    d = ImageDraw.Draw(im)

    # --- cabeçalho fixo ---
    CAB = 150
    d.rectangle([0, 0, W, CAB], fill=BRANCO)
    lg = logo(136)
    im.paste(lg, (36, 7), lg)
    d.line([(196, 34), (196, 116)], fill=PRETO, width=3)
    d.text((218, 75), USUARIO, font=fonte("800", 50), fill=PRETO, anchor="lm")
    fd = fonte("600", 32)
    ld = d.textlength(p["data"], font=fd)
    d.text((W - 44, 75), p["data"], font=fd, fill=(40, 40, 44), anchor="rm")
    d.line([(W - 44 - ld - 22, 44), (W - 44 - ld - 22, 106)], fill=(120, 120, 126), width=2)
    im.paste(degrade_h(W, 6, CIANO, VERDE), (0, CAB))

    y = CAB + (300 if stories else 50)

    # --- etiqueta ---
    ft = fonte("900i", 40)
    etq = p.get("etiqueta", "DESTAQUE").upper()
    lt = d.textlength(etq, font=ft)
    cor_etq = VERMELHO
    d.polygon([(M + 14, y), (M + lt + 62, y), (M + lt + 48, y + 64), (M, y + 64)], fill=cor_etq)
    d.text((M + 31 + lt / 2, y + 32), etq, font=ft, fill=BRANCO, anchor="mm")
    xs = M + lt + 78
    for i in range(3):
        cor = CIANO if i < 2 else VERDE
        d.polygon([(xs + 10, y + 6), (xs + 22, y + 6), (xs + 12, y + 58), (xs, y + 58)], fill=cor)
        xs += 24
    y += 64 + 34

    # --- orçamento de espaço: com foto, o texto termina cedo para a foto respirar ---
    rodape_y = H - 58
    base_zona = rodape_y - 44
    fundo = p.get("fundo") or ""
    caminho = fundo if os.path.isfile(fundo) else os.path.join(AQUI, "fundos", f"{fundo}.jpg")
    tem_foto = bool(fundo) and os.path.isfile(caminho)
    limite = (1080 if stories else 780) if tem_foto else base_zona - 70

    # --- manchete: 2 a 4 linhas, com trecho realçado ---
    toks = tokens(p["manchete"])
    larg = W - 2 * M
    tam = 150 if not tem_foto else 124
    while True:
        fm = fonte("900", tam)
        tam_apoio = 38 if tam >= 84 else 34
        fa = fonte("500", tam_apoio)
        linhas = quebrar(d, toks, fm, larg)
        apoio = quebrar_texto(d, p.get("apoio", ""), fa, larg - 20)
        maior = max(d.textlength(pal, font=fm) for pal, _ in toks)
        fim = y + len(linhas) * int(tam * 1.08) + 62 + len(apoio) * int(tam_apoio * 1.32)
        if (len(linhas) <= 4 and maior <= larg and fim <= limite) or tam <= 56:
            break
        tam -= 4
    esp = d.textlength(" ", font=fm)
    for linha in linhas:
        x = M
        for pal, cor in linha:
            d.text((x, y), pal, font=fm, fill=cor)
            x += d.textlength(pal, font=fm) + esp
        y += int(tam * 1.08)
    y += 18
    im.paste(degrade_h(260, 10, CIANO, VERDE), (M, y))
    y += 10 + 34

    # --- apoio ---
    for l in apoio:
        d.text((M, y), l, font=fa, fill=CINZA)
        y += int(tam_apoio * 1.32)

    # --- zona da foto / fundo temático ---
    if tem_foto and base_zona - y >= 160:
        aplicar_fundo(im, caminho, max(y - 40, base_zona - (1100 if stories else 520)), base_zona)
    else:
        # layout tipográfico: só detalhes gráficos, sem inventar imagens
        d.line([(W - 360, CAB + 46), (W - 250, CAB + 46), (W - 215, CAB + 81), (W, CAB + 81)], fill=CIANO, width=3)
        d.polygon([(W - 150, CAB + 6), (W, CAB + 6), (W, CAB + 30), (W - 126, CAB + 30)], fill=VERDE)
        if base_zona - y > 230:
            camada = Image.new("RGBA", im.size, (0, 0, 0, 0))
            dc = ImageDraw.Draw(camada)
            yb = base_zona - 10
            for i, cor in enumerate([CIANO, CIANO, VERDE]):
                x0 = W - 420 + i * 130
                dc.polygon([(x0 + 90, y + 30), (x0 + 170, y + 30), (x0 + 80, yb), (x0, yb)], fill=cor + (46,))
            im.paste(camada, (0, 0), camada)

    # --- fonte (discreta, acima do rodapé) ---
    if p.get("fonte"):
        ff = fonte("600", 22)
        txt = "Fonte: " + p["fonte"]
        lf = d.textlength(txt, font=ff)
        d.rounded_rectangle([M - 12, base_zona - 44, M + lf + 12, base_zona - 6], 8, fill=FUNDO)
        d.text((M, base_zona - 25), txt, font=ff, fill=(170, 178, 190), anchor="lm")

    # --- rodapé fixo ---
    fr = fonte("800", 34)
    partes = [("ONLYEXTREMO ", BRANCO), ("IA", VERDE), ("  •  ", CIANO), ("NOTÍCIAS", BRANCO)]
    total = sum(d.textlength(t, font=fr) for t, _ in partes)
    x = (W - total) / 2
    d.line([(M, rodape_y), (x - 28, rodape_y)], fill=CIANO, width=4)
    d.line([(x + total + 28, rodape_y), (W - M, rodape_y)], fill=CIANO, width=4)
    for t, cor in partes:
        d.text((x, rodape_y), t, font=fr, fill=cor, anchor="lm")
        x += d.textlength(t, font=fr)

    im.save(caminho_saida + ".png")
    im.save(caminho_saida + ".jpg", quality=93)  # o Instagram exige JPEG
    return caminho_saida


if __name__ == "__main__":
    posts = json.load(open(sys.argv[1], encoding="utf-8"))
    saida = sys.argv[2]
    os.makedirs(saida, exist_ok=True)
    stories = "--stories" in sys.argv
    for p in posts:
        base = os.path.join(saida, p["arquivo"] + ("_stories" if stories else "_feed"))
        print(gerar(p, base, stories))
