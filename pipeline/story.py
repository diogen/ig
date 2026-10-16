"""Render the dynamic IG story: retimed edit + zoom punch-ins + animated labels + music."""
import subprocess, sys, math
from collections import OrderedDict
import numpy as np
import cv2
from scipy.interpolate import PchipInterpolator
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = "/home/claude/work/src.mp4"
MUSIC = "/home/claude/work/music/music.wav"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/work/out/story_v2.mp4"
PREVIEW_TIMES = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None

W, H = 1080, 1920
FPS_OUT = 30
FPS_SRC = 60
DUR = 15.6
FRAME_BYTES = W * H * 3

CROP = "crop=990:1760:90:80,scale=1080:1920:flags=lanczos"
GRADE = ("eq=contrast=1.07:brightness=0.015:gamma=1.03:saturation=1.08,"
         "colorbalance=rs=0.02:bs=-0.03:rm=0.025:gm=0.005:bm=-0.03:rh=0.01:bh=-0.02,"
         "vibrance=intensity=0.18,curves=all='0/0 0.25/0.22 0.75/0.79 1/1',unsharp=5:5:0.5:5:5:0")

# ---------------- time map (output seconds -> source seconds) ----------------
KEYS = [(0.0, 0.0), (1.2, 1.2), (1.8, 3.0), (3.0, 4.0), (4.2, 5.2), (4.8, 7.2),
        (6.6, 9.0), (9.0, 15.8), (10.8, 17.95), (12.0, 18.33), (DUR, 18.33)]
tmap = PchipInterpolator([k[0] for k in KEYS], [k[1] for k in KEYS])
dmap = tmap.derivative()

# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_out_cubic(p):
    return 1 - (1 - p) ** 3

def ease_in_out(p):
    return p * p * (3 - 2 * p)

def ease_out_back(p, c1=1.9):
    c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2

# ---------------- zoom ----------------
PUNCHES = [(1.8, 0.035, 0.5), (3.0, 0.035, 0.5), (4.8, 0.075, 1.0), (10.8, 0.05, 0.7)]

def zoom_at(t):
    z = 1.0
    for t0, amp, dec in PUNCHES:
        if t >= t0:
            u = t - t0
            z += amp * (ease_out_cubic(clamp(u / 0.12)) if u < 0.12 else math.exp(-(u - 0.12) / (dec / 3)))
    if 6.6 <= t < 9.0:
        z += 0.03 * ease_in_out((t - 6.6) / 2.4)
    elif 9.0 <= t < 9.4:
        z += 0.03 * (1 - ease_in_out((t - 9.0) / 0.4))
    cx, cy = 540, 1000
    if t >= 12.0:
        p = ease_in_out(clamp((t - 12.0) / (DUR - 12.0)))
        z += 0.11 * p
        cx, cy = 540 + 20 * p, 1000 - 220 * p
    return z, cx, cy

def apply_zoom(img, z, cx, cy):
    if abs(z - 1) < 1e-3:
        return img
    cw, ch = W / z, H / z
    x0 = clamp(cx - cw / 2, 0, W - cw)
    y0 = clamp(cy - ch / 2, 0, H - ch)
    M = np.array([[z, 0, -x0 * z], [0, z, -y0 * z]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ---------------- sprites ----------------
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
F_MED = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
F_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
ORANGE = (242, 107, 29)
INK = (24, 24, 27)
WHITE = (255, 255, 255)

def emoji_img(ch, height):
    f = ImageFont.truetype(F_EMOJI, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((8, 8), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    r = height / im.height
    return im.resize((max(1, int(im.width * r)), int(height)), Image.LANCZOS)

def pill(text, font_path, size, fg, bg, padx=34, pady=20, radius=None, emoji=None, shadow=True, rot=0.0):
    font = ImageFont.truetype(font_path, size)
    asc, desc = font.getmetrics()
    tw = font.getlength(text)
    th = asc + desc
    em = emoji_img(emoji, size * 1.05) if emoji else None
    gap = int(size * 0.28) if em else 0
    w = int(tw + (em.width + gap if em else 0) + 2 * padx)
    h = int(th * 0.82 + 2 * pady)
    radius = radius if radius is not None else h // 2
    m = 30  # margin for shadow / rotation
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([m, m + 8, m + w, m + h + 8], radius, fill=(0, 0, 0, 70))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([m, m, m + w, m + h], radius, fill=bg)
    ty = m + pady - int(th * 0.12)
    d.text((m + padx, ty), text, font=font, fill=fg)
    if em:
        im.alpha_composite(em, (int(m + padx + tw + gap), int(m + (h - em.height) / 2)))
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    return im

def to_np(im):
    a = np.asarray(im).astype(np.float32) / 255.0
    return a  # RGBA float

# ---------------- labels ----------------
class Label:
    def __init__(self, start, end, main, sub, x, y, sub_emoji=None, sub_variants=None, main_bg=ORANGE):
        self.start, self.end, self.x, self.y = start, end, x, y
        self.main = pill(main, F_BLACK, 84, WHITE, main_bg + (255,), padx=36, pady=22)
        subs = sub_variants or [sub]
        self.subs = [pill(s, F_SEMI, 46, INK, WHITE + (245,), padx=26, pady=16, emoji=sub_emoji, rot=3.0)
                     for s in subs]

    def draw(self, frame, t):
        if not (self.start <= t <= self.end):
            return
        u = t - self.start
        v = self.end - t
        out_p = clamp(v / 0.2)
        exit_a = out_p
        exit_dy = -(1 - out_p) * 30
        # main pill: pop
        p = clamp(u / 0.32)
        sc = (0.55 + 0.45 * ease_out_back(p)) * (0.92 + 0.08 * out_p)
        a = clamp(u / 0.1) * exit_a
        bob = 5 * math.sin(2 * math.pi * u / 1.7)
        mw, mh = self.main.size
        blit(frame, self.main, self.x + mw / 2, self.y + mh / 2 + bob + exit_dy, sc, a)
        # sub pill: slide in from the left, slightly later
        u2 = u - 0.16
        if u2 > 0:
            sub = self.subs[int(u2 / 0.28) % len(self.subs)] if len(self.subs) > 1 else self.subs[0]
            q = ease_out_cubic(clamp(u2 / 0.32))
            sw, shh = sub.size
            sx = self.x + 22 + sw / 2 - 70 * (1 - q)
            sy = self.y + mh - 22 + shh / 2 + bob * 0.6 + exit_dy
            blit(frame, sub, sx, sy, 1.0, clamp(u2 / 0.14) * exit_a)

_cache = {}
def blit(frame, sprite, cx, cy, scale, alpha):
    if alpha <= 0.01 or scale <= 0.05:
        return
    key = (id(sprite), round(scale, 3))
    arr = _cache.get(key)
    if arr is None:
        im = sprite if abs(scale - 1) < 1e-3 else sprite.resize(
            (max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale))), Image.BICUBIC)
        arr = to_np(im)
        if len(_cache) > 400:
            _cache.clear()
        _cache[key] = arr
    h, w = arr.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    fx0, fy0 = max(0, x0), max(0, y0)
    fx1, fy1 = min(W, x0 + w), min(H, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    s = arr[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0]
    al = s[..., 3:4] * alpha
    roi = frame[fy0:fy1, fx0:fx1]
    roi[:] = roi * (1 - al) + s[..., :3] * al

LX, LY, LB = 64, 300, 1385
LABELS = [
    Label(0.12, 1.72, "MORNING FLOW", "before coffee. brave.", LX, LY, sub_emoji="☕"),
    Label(1.98, 2.98, "COBRA", "sssss...", LX, LY, sub_emoji="\U0001F40D"),
    Label(3.06, 4.16, "DOWN DOG", "good boy", LX, LY, sub_emoji="\U0001F436"),
    Label(4.95, 6.48, "REACH UP", "looking for better wifi", LX, LB, sub_emoji="\U0001F4F6"),
    Label(6.66, 8.92, "ROUND 2", "speedrun mode", LX, LY, sub_emoji="⏩", main_bg=INK),
    Label(9.25, 10.74, "NAMASTE", None, LX, LB, sub_emoji="\U0001F64F",
          sub_variants=["inner peace: loading.  ", "inner peace: loading.. ", "inner peace: loading..."]),
    Label(10.86, 11.96, "HIGH FIVE!", "partners in stretch", LX, LB, sub_emoji="✋"),
]

# ---------------- call to action card ----------------
CTA_T = 12.15
card_w, card_h = 920, 400
card = Image.new("RGBA", (card_w + 60, card_h + 60), (0, 0, 0, 0))
sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([30, 42, 30 + card_w, 42 + card_h], 48, fill=(0, 0, 0, 110))
card = Image.alpha_composite(card, sh.filter(ImageFilter.GaussianBlur(16)))
ImageDraw.Draw(card).rounded_rectangle([30, 30, 30 + card_w, 30 + card_h], 48, fill=INK + (236,))

def text_sprite(text, font_path, size, fill, emoji=None):
    font = ImageFont.truetype(font_path, size)
    asc, desc = font.getmetrics()
    tw = font.getlength(text)
    em = emoji_img(emoji, size * 1.1) if emoji else None
    gap = int(size * 0.3) if em else 0
    im = Image.new("RGBA", (int(tw + (em.width + gap if em else 0)) + 8, asc + desc + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4, 4), text, font=font, fill=fill)
    if em:
        im.alpha_composite(em, (int(4 + tw + gap), int((im.height - em.height) / 2)))
    return im

cta_lines = [
    (text_sprite("YOUR TURN.", F_BLACK, 124, ORANGE + (255,)), 0.18),
    (text_sprite("Stretch first. Scroll later.", F_BOLD, 60, WHITE + (255,)), 0.38),
    (text_sprite("Tomorrow, 10 minutes. You in?", F_MED, 44, (255, 255, 255, 200), emoji="\U0001F64C"), 0.58),
]
CARD_CX, CARD_TOP = W / 2, 1180

def draw_cta(frame, t):
    u = t - CTA_T
    if u < 0:
        return
    q = ease_out_cubic(clamp(u / 0.45))
    fade_out = clamp((DUR - t) / 0.45)
    dy = 140 * (1 - q)
    blit(frame, card, CARD_CX, CARD_TOP + card.height / 2 + dy, 1.0, clamp(u / 0.25) * fade_out)
    y = CARD_TOP + 30 + 50 + dy
    for spr, delay in cta_lines:
        uu = u - delay
        if uu > 0:
            s = 0.8 + 0.2 * ease_out_back(clamp(uu / 0.35)) if spr is cta_lines[0][0] else 1.0
            ddy = 24 * (1 - ease_out_cubic(clamp(uu / 0.3)))
            blit(frame, spr, CARD_CX, y + spr.height / 2 + ddy, s, clamp(uu / 0.2) * fade_out)
        y += spr.height + 14

# ---------------- source reader ----------------
class Source:
    def __init__(self):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"{CROP},{GRADE}",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.buf = OrderedDict()
        self.next_idx = 0
        self.last = None

    def get(self, idx):
        while self.next_idx <= idx:
            raw = self.p.stdout.read(FRAME_BYTES)
            if len(raw) < FRAME_BYTES:
                break
            if self.next_idx >= idx - 8:
                self.last = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32) / 255.0
                self.buf[self.next_idx] = self.last
            self.next_idx += 1
        for k in list(self.buf):
            if k < idx - 8:
                del self.buf[k]
            else:
                break
        return self.buf.get(idx, self.last)

def source_frame(src, t):
    s = float(tmap(t))
    speed = float(dmap(t))
    if speed > 1.3:  # motion blur: average frames across a 180-degree shutter
        span = speed / FPS_OUT * 0.5
        i1 = int(round(s * FPS_SRC))
        i0 = int(round((s - span) * FPS_SRC))
        idxs = list(range(max(0, i0), i1 + 1)) or [i1]
        acc = sum(src.get(i) for i in idxs)
        return acc / len(idxs)
    f = s * FPS_SRC
    i = int(math.floor(f)); fr = f - i
    a = src.get(i)
    if fr < 0.05:
        return a.copy()
    b = src.get(i + 1)
    return a * (1 - fr) + b * fr

def render():
    n = int(round(DUR * FPS_OUT))
    times = [i / FPS_OUT for i in range(n)]
    if PREVIEW_TIMES:
        times = PREVIEW_TIMES
    src = Source()
    enc = None
    if not PREVIEW_TIMES:
        enc = subprocess.Popen([
            "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
            "-r", str(FPS_OUT), "-i", "-", "-i", MUSIC, "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.1",
            "-maxrate", "15M", "-bufsize", "30M", "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
            stdin=subprocess.PIPE)
    for t in times:
        fr = source_frame(src, t)
        z, cx, cy = zoom_at(t)
        fr = apply_zoom(fr, z, cx, cy)
        if t >= 12.0:  # gentle dim behind the call to action
            fr *= 1 - 0.28 * ease_in_out(clamp((t - 12.0) / 0.5))
        for lb in LABELS:
            lb.draw(fr, t)
        draw_cta(fr, t)
        if t < 0.2:
            fr *= t / 0.2
        if t > DUR - 0.5:
            fr *= clamp((DUR - t) / 0.5)
        out = (np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8)
        if enc:
            enc.stdin.write(out.tobytes())
        else:
            Image.fromarray(out).save(f"/home/claude/work/frames/pv_{t:05.2f}.jpg", quality=88)
    if enc:
        enc.stdin.close(); enc.wait()
    src.p.kill()

if __name__ == "__main__":
    render()
