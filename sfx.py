import numpy as np
from config import SR

_rng = np.random.default_rng(7)


def _t(d):
    return np.arange(int(SR * d)) / SR


def _env(n, att, dec):
    t = np.arange(n) / SR
    return np.minimum(t / att, 1.0) * np.exp(-dec * t)


def _tone(f, d, vol, dec, att=0.003):
    t = _t(d)
    return (np.sin(2 * np.pi * f * t) * _env(len(t), att, dec) * vol).astype(np.float32)


def tick(f=1400, vol=0.35):
    return _tone(f, 0.07, vol, 55, 0.001)


def beep(f=880, d=0.25, vol=0.4):
    return _tone(f, d, vol, 6)


def timeup():
    a = beep(660, 0.18, 0.4)
    b = beep(440, 0.4, 0.45)
    out = np.zeros(int(SR * 0.7), np.float32)
    out[:len(a)] += a
    i = int(SR * 0.2)
    out[i:i + len(b)] += b
    return out


def ding():
    return (_tone(1046, 1.0, 0.5, 4) + _tone(2093, 1.0, 0.25, 6) + _tone(1568, 1.0, 0.2, 5)).astype(np.float32)


def buzz():
    t = _t(0.45)
    x = np.sign(np.sin(2 * np.pi * 110 * t)) * 0.3 + np.sin(2 * np.pi * 165 * t) * 0.15
    return (x * _env(len(t), 0.005, 5)).astype(np.float32)


def pop():
    t = _t(0.12)
    ph = 2 * np.pi * (500 * t + 2500 * t * t)
    return (np.sin(ph) * _env(len(t), 0.002, 28) * 0.4).astype(np.float32)


def whoosh(d=0.5):
    n = int(SR * d)
    noise = _rng.standard_normal(n)
    coef = 0.02 + 0.5 * np.sin(np.pi * np.arange(n) / n)
    y = np.zeros(n)
    prev = 0.0
    for i in range(n):
        prev += coef[i] * (noise[i] - prev)
        y[i] = prev
    y *= np.sin(np.pi * np.arange(n) / n) ** 2
    y /= max(1e-6, np.abs(y).max())
    return (y * 0.4).astype(np.float32)


def scribble(d):
    n = int(SR * d)
    t = np.arange(n) / SR
    x = np.diff(_rng.standard_normal(n), prepend=0.0)
    x *= (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * t))) * 0.05
    fade = np.minimum(1.0, np.minimum(t / 0.05, (d - t) / 0.05))
    return (x * np.clip(fade, 0, 1)).astype(np.float32)


def success():
    out = np.zeros(int(SR * 1.2), np.float32)
    for k, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
        s = _tone(f, 0.5, 0.35, 5)
        i = int(SR * 0.08 * k)
        out[i:i + len(s)] += s
    return out


def bgm(dur):
    seg, hop = 4.0, 2.0
    n = int(SR * (dur + seg + 1))
    out = np.zeros(n, np.float32)
    chords = [(261.63, 329.63, 392.0), (220.0, 261.63, 329.63),
              (174.61, 220.0, 261.63), (196.0, 246.94, 293.66)]
    pos, k = 0.0, 0
    while pos < dur:
        ch = chords[k % 4]
        t = _t(seg)
        w = np.sin(np.pi * t / seg) ** 2
        s = sum(np.sin(2 * np.pi * f * t) for f in ch) / 3 + 0.3 * np.sin(2 * np.pi * (ch[0] / 2) * t)
        i = int(pos * SR)
        out[i:i + len(t)] += (s * w * 0.06).astype(np.float32)
        pos += hop
        k += 1
    return out[:int(SR * dur)]
