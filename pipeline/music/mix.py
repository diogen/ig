import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
BEAT = 0.6
BAR = 2.4
TOTAL = 15.6  # seconds of audio delivered

def load(name):
    sr, x = wavfile.read(f"/home/claude/work/music/{name}.wav")
    assert sr == SR
    x = x.astype(np.float32) / 32768.0
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    n = int(TOTAL * SR)
    out = np.zeros((n, 2), np.float32)
    out[:min(n, len(x))] = x[:n]
    return out

def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)

def gain_to(x, target_db):
    return x * 10 ** ((target_db - rms_db(x)) / 20)

def lowpass(x, fc, order=2):
    sos = butter(order, fc, "low", fs=SR, output="sos")
    return sosfilt(sos, x, axis=0).astype(np.float32)

def highpass(x, fc, order=2):
    sos = butter(order, fc, "high", fs=SR, output="sos")
    return sosfilt(sos, x, axis=0).astype(np.float32)

stems = {k: load(k) for k in ["ep", "bass", "mel", "pad", "drums"]}
stems["ep"] = lowpass(stems["ep"], 5500)        # warmer keys
stems["pad"] = highpass(lowpass(stems["pad"], 3000), 180)
stems["mel"] = highpass(stems["mel"], 250)
stems["bass"] = lowpass(stems["bass"], 1800)

levels = {"drums": -17, "bass": -19, "ep": -20, "mel": -21.5, "pad": -27}
mix_parts = {k: gain_to(v, levels[k]) for k, v in stems.items()}

# sidechain pump on pad + keys from kick hits
kicks = []
for bar in range(1, 7):
    beats = [0, 2] if bar in (1, 5) else [0, 1.5, 2, 3.5] if bar != 4 else [0, 1.5, 2, 2.75, 3.5]
    kicks += [(bar - 1) * BAR + b * BEAT for b in beats]
kicks.append(6 * BAR)
n = int(TOTAL * SR)
tt = np.arange(n) / SR
duck = np.ones(n, np.float32)
for k in kicks:
    m = (tt >= k) & (tt < k + 0.35)
    d = 1 - 0.45 * np.exp(-(tt[m] - k) / 0.09)
    duck[m] = np.minimum(duck[m], d)
for k in ("pad", "ep"):
    amt = 1.0 if k == "pad" else 0.5
    mix_parts[k] *= (1 - amt * (1 - duck))[:, None]

# whoosh / riser sound effects aligned to the edit
rng = np.random.default_rng(3)
def whoosh(center, length, peak_db, lo=500, hi=7000, rise=False):
    m = int(length * SR)
    noise = rng.standard_normal((m, 2)).astype(np.float32)
    sos = butter(2, [lo, hi], "band", fs=SR, output="sos")
    noise = sosfilt(sos, noise, axis=0)
    x = np.linspace(0, 1, m)
    env = (x ** 2.5) if rise else np.sin(np.pi * x) ** 2
    pan = np.linspace(-0.6, 0.6, m)
    noise[:, 0] *= env * (1 - pan) / 2 * 2
    noise[:, 1] *= env * (1 + pan) / 2 * 2
    noise = gain_to(noise, peak_db - 6)
    out = np.zeros((n, 2), np.float32)
    s = int((center - (length if rise else length / 2)) * SR)
    out[max(0, s):s + m] += noise[: n - s]
    return out

sfx = (whoosh(1.5, 0.75, -24) + whoosh(4.5, 0.75, -24) +
       whoosh(6.6, 0.7, -23, rise=True) + whoosh(12.0, 0.9, -24, lo=300, hi=5000, rise=True))

mix = sum(mix_parts.values()) + sfx
# gentle glue: soft saturation
mix = np.tanh(mix * 1.6) / 1.6
# fades
fi = int(0.05 * SR); mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo_start = int(14.9 * SR); fo = n - fo_start
mix[fo_start:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
mix /= max(1e-6, np.abs(mix).max()) / 0.9
wavfile.write("/home/claude/work/music/mix_raw.wav", SR, (mix * 32767).astype(np.int16))
for k, v in mix_parts.items():
    print(k, round(rms_db(v), 1))
print("peak ok, len", len(mix) / SR)
