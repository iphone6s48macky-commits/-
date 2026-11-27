#!/usr/bin/env python3
"""15秒 オリジナルBGM 生成 (120BPM / Aマイナー / カット点に効果音)

出力: media/bgm.wav (48kHz / 16bit / ステレオ)
カット点 2.5 / 4.5 / 6.5 / 8.5 / 10.5 / 12.0 秒に合わせて
ウーシュ、12秒の「取付完了」で決めのヒットが入る。
"""
import os, wave
import numpy as np

SR = 48000
DUR = 15.0
BPM = 120
BEAT = 60 / BPM
N = int(SR * DUR)
rng = np.random.default_rng(7)
HERE = os.path.dirname(os.path.abspath(__file__))
CUTS = [2.5, 4.5, 6.5, 8.5, 10.5, 12.0]
DROP, FINAL = 2.5, 12.0

L = np.zeros(N)
R = np.zeros(N)

def hz(n):  # MIDI → Hz
    return 440.0 * 2 ** ((n - 69) / 12)

def env(n, a=0.005, d=0.2, s=0.0, r=0.05, hold=None):
    t = np.arange(n) / SR
    e = np.ones(n)
    ai = int(a * SR)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    dec = np.exp(-(t - a) / max(d, 1e-4)) * (1 - s) + s
    e[ai:] = dec[ai:]
    ri = int(r * SR)
    if ri and ri < n: e[-ri:] *= np.linspace(1, 0, ri)
    return e

def lowpass(x, k):
    if k <= 1: return x
    c = np.cumsum(np.concatenate([[0], x]))
    y = (c[k:] - c[:-k]) / k
    return np.concatenate([x[:k - 1] * 0, y])

def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[: N - i]
    L[i:i + len(sig)] += sig * gain * (1 - max(0, pan))
    R[i:i + len(sig)] += sig * gain * (1 + min(0, pan))

def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-detune, 0, detune):
        out += 2 * ((t * f * (1 + d)) % 1) - 1
    return out / 3

def sine(f, n):
    return np.sin(2 * np.pi * f * np.arange(n) / SR)

# ---------------- 楽器
def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) + 0.3 * rng.standard_normal(n) * np.exp(-t * 200)

def clap():
    n = int(0.25 * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    nz = nz - lowpass(nz, 6)
    e = np.exp(-t * 18)
    for off in (0.0, 0.012, 0.024):
        e += (t >= off) * np.exp(-np.clip(t - off, 0, None) * 120) * 0.6
    return nz * e * 0.5

def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    nz = nz - lowpass(nz, 3)
    return nz * np.exp(-t * (18 if open_ else 80)) * 0.35

def crash():
    n = int(1.8 * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n); nz = nz - lowpass(nz, 4)
    return nz * np.exp(-t * 2.2) * 0.35

def whoosh(length=0.45):
    n = int(length * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    out = np.zeros(n)
    seg = n // 12
    for k in range(12):  # 徐々にフィルタが開く
        kk = max(1, 40 - k * 3)
        s = lowpass(nz, kk)[k * seg:(k + 1) * seg]
        out[k * seg:k * seg + len(s)] = s
    e = (t / length) ** 2
    e[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    return out * e * 1.4

def riser(length):
    n = int(length * SR); t = np.arange(n) / SR
    f = 200 * (8 ** (t / length))
    ph = 2 * np.pi * np.cumsum(f) / SR
    nz = rng.standard_normal(n) - lowpass(rng.standard_normal(n), 5)
    return (np.sin(ph) * 0.25 + nz * 0.25) * (t / length) ** 2

def boom():
    n = int(1.6 * SR); t = np.arange(n) / SR
    f = 38 + 60 * np.exp(-t * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)

# ---------------- コード進行 (1小節 = 2秒)
# Am - F - C - G - Am - F | 12秒〜 C(add9) で締め
CHORDS = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]),
          (55, [55, 59, 62]), (57, [57, 60, 64]), (53, [53, 57, 60])]
BAR = 4 * BEAT

def chord_at(t):
    return CHORDS[min(int(t // BAR), len(CHORDS) - 1)]

# パッド (全編)
for b, (root, notes) in enumerate(CHORDS):
    t0 = b * BAR
    n = int(BAR * SR) + int(0.3 * SR)
    p = sum(saw(hz(m + 12), n, detune=0.004) for m in notes)
    p = lowpass(p, 22) * env(n, a=0.25, d=9, s=1, r=0.3)
    add(p, t0, 0.10, pan=-0.3)
    add(p, t0 + 0.012, 0.10, pan=0.3)

# イントロ: ピアノ風プラック (0〜2.5秒) + ライザー
for i in range(5):
    root, notes = chord_at(i * BEAT)
    m = notes[i % 3] + 24
    n = int(0.6 * SR)
    pl = (sine(hz(m), n) + 0.4 * sine(hz(m) * 2, n)) * env(n, d=0.35)
    add(pl, i * BEAT, 0.22, pan=(-0.4 if i % 2 else 0.4))
add(riser(1.4), DROP - 1.4, 0.55)

# メイン: 2.5〜12秒
t = DROP
step = BEAT / 4
idx = 0
while t < FINAL - 1e-6:
    beat_pos = round((t - DROP) / step)
    on_beat = beat_pos % 4 == 0
    root, notes = chord_at(t)
    # キック (4つ打ち)
    if on_beat:
        add(kick(), t, 0.95)
    # クラップ (2・4拍目)
    if on_beat and round(t / BEAT) % 2 == 1:
        add(clap(), t, 0.55)
    # ハイハット (裏拍=オープン、16分=クローズ)
    if beat_pos % 4 == 2:
        add(hat(True), t, 0.5, pan=0.2)
    elif beat_pos % 2 == 1:
        add(hat(False), t, 0.35, pan=-0.2)
    # ベース (8分)
    if beat_pos % 2 == 0:
        n = int(step * 2 * SR)
        f = hz(root - 12)
        bs = (saw(f, n) * 0.6 + sine(f, n))
        bs = lowpass(bs, 14) * env(n, a=0.003, d=0.18, s=0.4, r=0.02)
        add(bs, t, 0.55)
    # アルペジオ (16分, シーケンス)
    seq = [0, 1, 2, 1, 2, 0, 1, 2]
    m = notes[seq[idx % 8]] + 24 + (12 if idx % 8 == 4 else 0)
    n = int(step * 1.6 * SR)
    ar = lowpass(saw(hz(m), n, detune=0.003), 6) * env(n, a=0.002, d=0.09, r=0.02)
    pan = 0.35 if idx % 2 else -0.35
    add(ar, t, 0.17, pan=pan)
    add(ar, t + BEAT * 0.75, 0.06, pan=-pan)  # ディレイ
    t += step
    idx += 1

# カット点: ウーシュ + クラッシュ
for c in CUTS:
    add(whoosh(0.45), c - 0.45, 0.35)
add(crash(), DROP, 0.6)

# フィナーレ 12秒: 決めのヒット → 余韻
add(boom(), FINAL, 0.9)
add(kick(), FINAL, 0.9)
add(crash(), FINAL, 0.75)
n = int(3.0 * SR)
fin = [48, 55, 60, 62, 64, 67]  # C add9
st = sum(saw(hz(m + 12), n, detune=0.005) for m in fin)
st = lowpass(st, 10) * env(n, a=0.01, d=1.4, s=0.0, r=0.5)
add(st, FINAL, 0.12, pan=-0.2)
add(st, FINAL + 0.015, 0.12, pan=0.2)
for k, m in enumerate([72, 76, 79, 84]):  # キラッとした上昇音
    nn = int(1.2 * SR)
    bell = (sine(hz(m), nn) + 0.3 * sine(hz(m) * 2.76, nn)) * env(nn, d=0.6)
    add(bell, FINAL + 0.25 + k * 0.09, 0.12, pan=(-0.3 + 0.2 * k))

# ---------------- マスター
mix = np.stack([L, R], axis=1)
mix = np.tanh(mix * 1.3) / np.tanh(1.3)            # 軽いサチュレーション
fo = int(1.2 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5  # ラストフェード
fi = int(0.05 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
mix = mix / np.max(np.abs(mix)) * 0.89             # 約 -1 dBFS
pcm = (mix * 32767).astype(np.int16)

os.makedirs(os.path.join(HERE, "media"), exist_ok=True)
out = os.path.join(HERE, "media", "bgm.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", out)
