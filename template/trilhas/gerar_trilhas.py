"""Sintetiza trilhas originais (sem direitos de terceiros) para os Reels."""
import sys, wave
import numpy as np
SR, DUR = 44100, 10.0
t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
rng = np.random.default_rng(7)

def env_fade(x, fi=0.6, fo=1.2):
    e = np.ones_like(t); e[t < fi] = t[t < fi] / fi; m = t > DUR - fo; e[m] = (DUR - t[m]) / fo
    return x * e

def hit(t0, f, dec, amp=1.0, queda=0.0):
    d = t - t0; m = d >= 0; y = np.zeros_like(t)
    fr = f * np.exp(-queda * d[m])
    y[m] = amp * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-d[m] / dec)
    return y

def ruido_filtrado(corte):
    n = rng.standard_normal(len(t)); k = int(SR / corte)
    return np.convolve(n, np.ones(k) / k, mode="same")

def suspense():
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t)
    y = 0.30 * np.sin(2 * np.pi * 55 * t) + 0.22 * np.sin(2 * np.pi * 55.6 * t) + 0.16 * np.sin(2 * np.pi * 82.4 * t) * lfo
    y += 0.05 * np.sin(2 * np.pi * 622.3 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t)) * np.clip(t / 6, 0, 1)
    y += 0.04 * np.sin(2 * np.pi * 659.3 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t + 1)) * np.clip(t / 6, 0, 1)
    for b in np.arange(0.5, DUR - 0.5, 1.25):                       # batida de coração
        y += hit(b, 62, 0.16, 0.55, 6) + hit(b + 0.28, 56, 0.14, 0.38, 6)
    y += 0.10 * ruido_filtrado(400) * np.clip((t - 5) / 5, 0, 1) ** 2   # tensão crescente
    return y

def urgente():
    y = 0.22 * np.sin(2 * np.pi * 55 * t)
    for b in np.arange(0.0, DUR - 0.2, 0.25):                        # pulso de baixo em colcheias
        y += hit(b, 110 if int(b * 4) % 8 < 6 else 130.8, 0.11, 0.42)
    for b in np.arange(0.0, DUR - 0.1, 0.5):                         # tique de relógio
        d = t - b; m = (d >= 0) & (d < 0.03)
        y[m] += 0.25 * rng.standard_normal(m.sum()) * np.exp(-d[m] / 0.008)
    for b in np.arange(0.0, DUR - 1, 2.0):                           # bumbo grave
        y += hit(b, 90, 0.20, 0.7, 12)
    y += 0.12 * ruido_filtrado(900) * np.clip((t - 6) / 4, 0, 1) ** 2
    return y

def neutro():
    y = np.zeros_like(t)
    for f, a in [(110, .22), (220, .16), (261.63, .13), (329.63, .12), (392, .07)]:
        y += a * np.sin(2 * np.pi * f * t) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.13 * t + f))
        y += a * 0.5 * np.sin(2 * np.pi * f * 1.004 * t)
    for b in np.arange(1.0, DUR - 1, 2.0):
        y += hit(b, 70, 0.25, 0.30, 5)
    return y

for nome, fn in [("suspense", suspense), ("urgente", urgente), ("neutro", neutro)]:
    y = env_fade(fn()); y = 0.8 * y / np.max(np.abs(y))
    st = np.stack([y, np.roll(y, 180)], axis=1)                      # leve abertura estéreo
    with wave.open(f"{sys.argv[1]}/{nome}.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())
