"""Render a Reel cover: the "Reach up" moment with the hook text, no other labels.

Usage: python3 cover.py OUT.jpg [time_seconds]
Always pass the result to Instagram as cover_url (or pick it in the app) so the
cover is never the first frame by accident.
"""
import shutil, sys, glob, os
import reel  # sets up Reel labels on the shared story module
S = reel.S

out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/work/out/reel_cover.jpg"
t = float(sys.argv[2]) if len(sys.argv) > 2 else 5.6
lines = [("Couples who", 88, S.INK, S.WHITE, None), ("stretch together...", 88, S.WHITE, S.ORANGE, None)]
S.LABELS = [reel.Stack(t - 2.0, t + 10, lines, cy=300)]
S.CTA_T = 999
S.PREVIEW_TIMES = [t]
for f in glob.glob("/home/claude/work/frames/pv_*.jpg"):
    os.remove(f)
S.render()
shutil.move(glob.glob("/home/claude/work/frames/pv_*.jpg")[0], out)
print("cover saved", out)
