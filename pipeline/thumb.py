"""Click-focused Reel cover: the funniest moment (him face-down, her perfect cobra) + meme labels.

Usage: python3 thumb.py OUT.jpg
Key content stays inside the centre 1080x1440 so the 3:4 profile-grid crop keeps it.
"""
import sys
import numpy as np
from PIL import Image
import story as S
import subprocess
def grab(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", S.SRC, "-frames:v", "1", "-vf", f"{S.CROP},{S.GRADE}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3))

out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/work/out/reel_thumb.jpg"
img = np.asarray(grab(3.40)).astype(np.float32) / 255.0
img = S.apply_zoom(img, 1.2, 470, 1170)          # bring both people up close
fr = img.copy()

title = [S.pill("Couples yoga", S.F_BLACK, 104, S.INK, S.WHITE + (255,), padx=40, pady=24),
         S.pill("day 1", S.F_BLACK, 104, S.WHITE, S.ORANGE + (255,), padx=40, pady=24, emoji="\U0001F605")]
y = 330
for spr in title:
    S.blit(fr, spr, S.W / 2, y + spr.height / 2, 1.0, 1.0)
    y += spr.height - 40

her = S.pill("her: cobra", S.F_BLACK, 62, S.INK, S.WHITE + (250,), padx=28, pady=16, emoji="\U0001F40D", rot=-4)
me = S.pill("me: power nap", S.F_BLACK, 62, S.WHITE, S.INK + (250,), padx=28, pady=16, emoji="\U0001F634", rot=4)
S.blit(fr, her, float(sys.argv[2]) if len(sys.argv) > 2 else 760, float(sys.argv[3]) if len(sys.argv) > 3 else 880, 1.0, 1.0)
S.blit(fr, me, float(sys.argv[4]) if len(sys.argv) > 4 else 330, float(sys.argv[5]) if len(sys.argv) > 5 else 1560, 1.0, 1.0)

Image.fromarray((np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(out, quality=94)
print("thumb saved", out)
