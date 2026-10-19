"""Reel v3: new first 2 seconds. Opens on the funniest moment (him face-down while she rises into cobra),
slow-mo with a zoom-out reveal, then a quick "rewind" back into the flow. From 1.8 s on it is identical
to the Reel edit, so the music sync is unchanged.

Usage: python3 reel_v3.py OUT.mp4            full render
       python3 reel_v3.py x t1,t2,...         preview frames into frames/pv_*.jpg
"""
import subprocess
import numpy as np
import reel
S = reel.S

HOOK_END, REWIND_END = 1.45, 1.8          # out-times
SLOW_A, SLOW_B, REW_TO = 3.32, 3.54, 3.00  # source times
PRE_T0 = 2.95

# preload the few source frames the hook needs (graded, reframed)
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{PRE_T0}", "-t", "0.7", "-i", S.SRC,
                      "-vf", f"{S.CROP},{S.GRADE}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     capture_output=True, check=True).stdout
PRE = np.frombuffer(raw, np.uint8).reshape(-1, S.H, S.W, 3)

def pre_frame(s):
    f = (s - PRE_T0) * S.FPS_SRC
    i = int(np.clip(np.floor(f), 0, len(PRE) - 2)); fr = f - i
    return (PRE[i] * (1 - fr) + PRE[i + 1] * fr).astype(np.float32) / 255.0

_orig_source, _orig_zoom = S.source_frame, S.zoom_at

def source_frame(src, t):
    if t < HOOK_END:
        return pre_frame(SLOW_A + (SLOW_B - SLOW_A) * (t / HOOK_END))
    if t < REWIND_END:
        p = (t - HOOK_END) / (REWIND_END - HOOK_END)
        s = SLOW_B + (REW_TO - SLOW_B) * p
        acc = sum(pre_frame(s + d) for d in (-0.02, 0.0, 0.02)) / 3     # rewind motion blur
        grey = acc.mean(axis=2, keepdims=True)
        return np.clip(acc * 0.75 + grey * 0.25 + 0.03 * np.sin(t * 90), 0, 1)
    return _orig_source(src, t)

def zoom_at(t):
    if t < HOOK_END:
        p = S.ease_in_out(t / HOOK_END)
        return 1.12 + 0.10 * p, 540 - 110 * p, 1150
    if t < REWIND_END:
        p = (t - HOOK_END) / (REWIND_END - HOOK_END)
        return 1.22 - 0.22 * p, 430 + 110 * p, 1150 - 150 * p
    return _orig_zoom(t)

S.source_frame, S.zoom_at = source_frame, zoom_at

HOOK = reel.Stack(-0.35, HOOK_END - 0.02, [("me, 30 sec into", 80, S.INK, S.WHITE, None),
                                           ("couples yoga", 80, S.WHITE, S.ORANGE, "\U0001F480")], cy=300)
REWIND = reel.Stack(HOOK_END + 0.02, REWIND_END + 0.08, [("rewind", 64, S.WHITE, S.INK, "⏪")], cy=900)
PAYOFF = reel.Stack(10.84, 11.98, [("...still finished", 80, S.INK, S.WHITE, None),
                                   ("together", 80, S.WHITE, S.ORANGE, "✋")], cy=reel.LB - 40, cx=S.W / 2 - 60)
S.LABELS = [HOOK, REWIND] + S.LABELS[1:-1] + [PAYOFF]

if __name__ == "__main__":
    S.render()
