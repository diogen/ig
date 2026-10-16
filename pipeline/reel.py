"""Reel variant of the story render: hook + payoff text, labels and CTA kept clear of Reels UI."""
import sys
from PIL import Image, ImageDraw, ImageFilter
import story as S

# Reels UI: caption/username covers roughly the bottom 22% (y > ~1500), buttons sit on the right edge.
LB = 1170

class Stack:
    """Two stacked pills, centered, popping in one after the other."""
    def __init__(self, start, end, lines, cy, cx=S.W / 2 - 40):
        self.start, self.end, self.cx, self.cy = start, end, cx, cy
        self.sprites = [S.pill(txt, S.F_BLACK, size, fg, bg + (255,), padx=34, pady=20, emoji=em)
                        for txt, size, fg, bg, em in lines]

    def draw(self, frame, t):
        if not (self.start <= t <= self.end):
            return
        u, v = t - self.start, self.end - t
        out_p = S.clamp(v / 0.2)
        y = self.cy
        for i, spr in enumerate(self.sprites):
            ui = u - i * 0.28
            if ui > 0:
                p = S.clamp(ui / 0.32)
                sc = (0.55 + 0.45 * S.ease_out_back(p)) * (0.92 + 0.08 * out_p)
                rot_bob = 4 * S.math.sin(2 * S.math.pi * ui / 1.7)
                S.blit(frame, spr, self.cx, y + spr.height / 2 + rot_bob - (1 - out_p) * 30, sc,
                       S.clamp(ui / 0.1) * out_p)
            y += spr.height - 34

HOOK = Stack(0.08, 1.74, [("Couples who", 88, S.INK, S.WHITE, None),
                          ("stretch together...", 88, S.WHITE, S.ORANGE, None)], cy=300)
PAYOFF = Stack(10.84, 11.98, [("...high-five", 80, S.INK, S.WHITE, None),
                              ("together", 80, S.WHITE, S.ORANGE, "✋")], cy=LB - 40, cx=S.W / 2 - 60)

def relabel(lb, y):
    lb.y = y
    return lb

old = S.LABELS
S.LABELS = [
    HOOK,
    old[1],                      # COBRA (top)
    old[2],                      # DOWN DOG (top)
    relabel(old[3], LB),         # REACH UP
    old[4],                      # ROUND 2 (top)
    relabel(old[5], LB),         # NAMASTE
    PAYOFF,
]

# ---- call to action card, narrower and higher than the story version ----
card_w, card_h = 860, 400
card = Image.new("RGBA", (card_w + 60, card_h + 60), (0, 0, 0, 0))
sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([30, 42, 30 + card_w, 42 + card_h], 48, fill=(0, 0, 0, 110))
card = Image.alpha_composite(card, sh.filter(ImageFilter.GaussianBlur(16)))
ImageDraw.Draw(card).rounded_rectangle([30, 30, 30 + card_w, 30 + card_h], 48, fill=S.INK + (236,))
S.card = card
S.cta_lines = [
    (S.text_sprite("YOUR TURN.", S.F_BLACK, 124, S.ORANGE + (255,)), 0.18),
    (S.text_sprite("Send this to your stretch buddy", S.F_BOLD, 50, S.WHITE + (255,)), 0.38),
    (S.text_sprite("& save it for tomorrow, 6 am", S.F_MED, 44, (255, 255, 255, 205), emoji="\U0001F516"), 0.58),
]
S.CARD_CX, S.CARD_TOP = S.W / 2 - 40, 960

if __name__ == "__main__":
    S.render()
