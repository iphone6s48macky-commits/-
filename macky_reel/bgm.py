"""オリジナルBGM 生成 (著作権フリー / numpy のみ)

make_bgm(out, duration, cuts, drop=None, hits=(), outro=None, bpm=120, seed=7)
  cuts  : カット点(秒)。各カット直前にウーシュ
  drop  : ドラムが入る時刻 (既定 = 最初のカット)
  hits  : 決めのヒット (ブーム + クラッシュ) を入れる時刻
  outro : この時刻からドラムを抜いて締めのコード → フェードアウト (エンドカード用)
"""
import wave
import numpy as np

SR = 48000


def make_bgm(out, duration, cuts, drop=None, hits=(), outro=None, bpm=120, seed=7):
    rng = np.random.default_rng(seed)
    N = int(SR * duration)
    BEAT = 60 / bpm
    BAR = 4 * BEAT
    L = np.zeros(N); R = np.zeros(N)
    drop = cuts[0] if drop is None else drop
    outro = duration if outro is None else outro

    def hz(n): return 440.0 * 2 ** ((n - 69) / 12)

    def env(n, a=0.005, d=0.2, s=0.0, r=0.05):
        t = np.arange(n) / SR
        e = np.exp(-(t - a) / max(d, 1e-4)) * (1 - s) + s
        ai = int(a * SR)
        if ai: e[:ai] = np.linspace(0, 1, ai)
        ri = int(r * SR)
        if 0 < ri < n: e[-ri:] *= np.linspace(1, 0, ri)
        return e

    def lp(x, k):
        if k <= 1: return x
        c = np.cumsum(np.concatenate([[0], x]))
        return np.concatenate([np.zeros(k - 1), (c[k:] - c[:-k]) / k])

    def add(sig, t0, g=1.0, pan=0.0):
        i = int(t0 * SR)
        if i >= N or i < 0: return
        sig = sig[:N - i]
        L[i:i + len(sig)] += sig * g * (1 - max(0, pan))
        R[i:i + len(sig)] += sig * g * (1 + min(0, pan))

    def saw(f, n, det=0.0):
        t = np.arange(n) / SR
        return sum(2 * ((t * f * (1 + d)) % 1) - 1 for d in (-det, 0, det)) / 3

    def sine(f, n): return np.sin(2 * np.pi * f * np.arange(n) / SR)

    def noise(n): return rng.standard_normal(n)

    def kick():
        n = int(0.35 * SR); t = np.arange(n) / SR
        f = 50 + 110 * np.exp(-t * 30)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) + 0.3 * noise(n) * np.exp(-t * 200)

    def clap():
        n = int(0.25 * SR); t = np.arange(n) / SR
        nz = noise(n); nz -= lp(nz, 6)
        e = np.exp(-t * 18)
        for off in (0.0, 0.012, 0.024):
            e += (t >= off) * np.exp(-np.clip(t - off, 0, None) * 120) * 0.6
        return nz * e * 0.5

    def hat(op=False):
        n = int((0.18 if op else 0.05) * SR); t = np.arange(n) / SR
        nz = noise(n); nz -= lp(nz, 3)
        return nz * np.exp(-t * (18 if op else 80)) * 0.35

    def crash():
        n = int(1.8 * SR); t = np.arange(n) / SR
        nz = noise(n); nz -= lp(nz, 4)
        return nz * np.exp(-t * 2.2) * 0.35

    def whoosh(ln=0.45):
        n = int(ln * SR); t = np.arange(n) / SR
        nz = noise(n); out = np.zeros(n); seg = n // 12
        for k in range(12):
            s = lp(nz, max(1, 40 - k * 3))[k * seg:(k + 1) * seg]
            out[k * seg:k * seg + len(s)] = s
        e = (t / ln) ** 2; e[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
        return out * e * 1.4

    def riser(ln):
        n = int(ln * SR); t = np.arange(n) / SR
        f = 200 * (8 ** (t / ln))
        nz = noise(n) - lp(noise(n), 5)
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + nz * 0.25) * (t / ln) ** 2

    def boom():
        n = int(1.6 * SR); t = np.arange(n) / SR
        f = 38 + 60 * np.exp(-t * 6)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)

    # Am - F - C - G ループ
    CH = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]
    def chord(t): return CH[int(t // BAR) % 4]

    # パッド
    nb = int(np.ceil(min(outro, duration) / BAR))
    for b in range(nb):
        t0 = b * BAR
        ln = min(BAR, outro - t0)
        if ln <= 0: break
        n = int((ln + 0.3) * SR)
        p = lp(sum(saw(hz(m + 12), n, 0.004) for m in CH[b % 4][1]), 22) * env(n, a=0.25, d=9, s=1, r=0.3)
        add(p, t0, 0.10, -0.3); add(p, t0 + 0.012, 0.10, 0.3)

    # イントロのプラック
    t = 0.0; i = 0
    while t < drop - 1e-6:
        _, notes = chord(t)
        n = int(0.6 * SR)
        m = notes[i % 3] + 24
        add((sine(hz(m), n) + 0.4 * sine(hz(m) * 2, n)) * env(n, d=0.35), t, 0.22, 0.4 if i % 2 else -0.4)
        t += BEAT; i += 1
    add(riser(min(1.4, drop)), drop - min(1.4, drop), 0.55)

    # 本編グルーヴ
    step = BEAT / 4
    t = drop; idx = 0
    while t < outro - 1e-6:
        bp = round((t - drop) / step)
        root, notes = chord(t)
        if bp % 4 == 0:
            add(kick(), t, 0.95)
            if round((t - drop) / BEAT) % 2 == 1: add(clap(), t, 0.55)
        if bp % 4 == 2: add(hat(True), t, 0.5, 0.2)
        elif bp % 2 == 1: add(hat(), t, 0.35, -0.2)
        if bp % 2 == 0:
            n = int(step * 2 * SR); f = hz(root - 12)
            add(lp(saw(f, n) * 0.6 + sine(f, n), 14) * env(n, 0.003, 0.18, 0.4, 0.02), t, 0.55)
        seq = [0, 1, 2, 1, 2, 0, 1, 2]
        m = notes[seq[idx % 8]] + 24 + (12 if idx % 8 == 4 else 0)
        n = int(step * 1.6 * SR)
        ar = lp(saw(hz(m), n, 0.003), 6) * env(n, 0.002, 0.09, 0, 0.02)
        pan = 0.35 if idx % 2 else -0.35
        add(ar, t, 0.17, pan); add(ar, t + BEAT * 0.75, 0.06, -pan)
        t += step; idx += 1

    for c in cuts:
        add(whoosh(), c - 0.45, 0.35)
    add(crash(), drop, 0.6)
    for h in hits:
        add(boom(), h, 0.8); add(crash(), h, 0.7)
        for k, m in enumerate([72, 76, 79, 84]):
            n = int(1.2 * SR)
            add((sine(hz(m), n) + 0.3 * sine(hz(m) * 2.76, n)) * env(n, d=0.6), h + 0.2 + k * 0.09, 0.11, -0.3 + 0.2 * k)

    # アウトロ: 締めのコード
    if outro < duration:
        add(boom(), outro, 0.7); add(kick(), outro, 0.8); add(crash(), outro, 0.6)
        n = int((duration - outro + 0.5) * SR)
        st = lp(sum(saw(hz(m + 12), n, 0.005) for m in [48, 55, 60, 62, 64, 67]), 10) * env(n, 0.01, 2.0, 0.25, 0.5)
        add(st, outro, 0.13, -0.2); add(st, outro + 0.015, 0.13, 0.2)
        for k, m in enumerate([72, 76, 79, 84, 88]):
            n2 = int(1.5 * SR)
            add((sine(hz(m), n2) + 0.3 * sine(hz(m) * 2.76, n2)) * env(n2, d=0.8), outro + 0.3 + k * 0.12, 0.10, -0.4 + 0.2 * k)

    mix = np.stack([L, R], 1)
    mix = np.tanh(mix * 1.3) / np.tanh(1.3)
    fo = int(1.2 * SR)
    mix[-fo:] *= (np.linspace(1, 0, fo) ** 1.5)[:, None]
    fi = int(0.05 * SR); mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix = mix / np.max(np.abs(mix)) * 0.89
    with wave.open(out, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return out
