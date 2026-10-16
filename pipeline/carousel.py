"""Expectation vs Reality carousel: 4 slides, 1080x1350, top caption band + graded video frame."""
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import story as S

W, H = 1080, 1350
BAND = 250
PH = H - BAND
OUT = "/home/claude/work/out/carousel_{}.jpg"

SLIDES = [
    # src time, crop top (in 1080x1920 frame), tag, tag color, text, emoji
    (8.10, 250, "EXPECTATION", S.ORANGE, "A graceful, perfectly synchronized morning flow.", None),
    (3.40, 470, "REALITY", S.ORANGE, "One of us is doing cobra. One of us is negotiating with gravity.", None),
    (7.50, 250, "SYNC LEVEL", S.ORANGE, "Buffering...", "\U0001F504"),
    (18.33, 330, "BUT", S.ORANGE, "We high-fived at the end, so it counts.", "✋"),
]

def grab(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", S.SRC, "-frames:v", "1",
                          "-vf", f"{S.CROP},{S.GRADE}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3))

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= maxw:
            cur = test
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines

f_text = ImageFont.truetype(S.F_BOLD, 50)
for i, (t, top, tag, tag_col, text, em) in enumerate(SLIDES, 1):
    frame = grab(t).crop((0, top, 1080, top + PH))
    im = Image.new("RGB", (W, H), S.INK)
    im.paste(frame, (0, BAND))
    d = ImageDraw.Draw(im)
    tag_spr = S.pill(tag, S.F_BLACK, 40, S.WHITE, tag_col + (255,), padx=24, pady=12, shadow=False)
    im.paste(tag_spr, (60 - 30, 40 - 30), tag_spr)
    lines = wrap(d, text, f_text, W - 130 - (70 if em else 0))
    y = 40 + tag_spr.height - 60 + 22
    for j, line in enumerate(lines):
        d.text((62, y), line, font=f_text, fill=S.WHITE)
        if em and j == len(lines) - 1:
            e = S.emoji_img(em, 52)
            im.paste(e, (int(62 + d.textlength(line, font=f_text) + 14), y + 4), e)
        y += 62
    # slide counter + swipe hint
    f_small = ImageFont.truetype(S.F_MED, 30)
    cnt = f"{i}/{len(SLIDES)}" + ("   swipe →" if i == 1 else "")
    d.text((W - 60 - d.textlength(cnt, font=f_small), 48), cnt, font=f_small, fill=(255, 255, 255, 150))
    im.save(OUT.format(i), quality=93)
    print("saved", OUT.format(i), "lines", len(lines))
