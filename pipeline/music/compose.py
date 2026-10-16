"""Compose a short calm-but-upbeat track (100 BPM, D major) as MIDI stems.

Bar grid (2.4 s per bar) is shared with the video edit:
 bar1 0.0  intro groove        | opening fold, fast-forward
 bar2 2.4  + clap, hook         | cobra, down dog
 bar3 4.8  crash, hook higher   | REACH UP
 bar4 7.2  16th energy          | round 2 time-lapse
 bar5 9.6  calmer + fill        | namaste, slow-mo high five
 bar6 12.0 full + hook          | freeze + call to action
 bar7 14.4 final chord          | fade out
"""
import random
import pretty_midi as pm

BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
random.seed(7)

def t(bar, beat):  # bar is 1-based
    return (bar - 1) * BAR + beat * BEAT

def hum(x, amt=0.008):
    return max(0.0, x + random.uniform(-amt, amt))

def add(inst, pitch, start, dur, vel, humanize=True):
    s = hum(start) if humanize else start
    inst.notes.append(pm.Note(velocity=int(max(1, min(127, vel + random.randint(-4, 4)))),
                              pitch=pitch, start=s, end=s + dur))

def cc(inst, num, val):
    inst.control_changes.append(pm.ControlChange(number=num, value=val, time=0.0))

# chords per bar: (bass root, EP voicing)
CHORDS = {
    1: (43, [59, 62, 66, 69]),      # Gmaj9
    2: (45, [61, 64, 66, 69]),      # A6
    3: (42, [57, 61, 64, 69]),      # F#m7
    4: (47, [57, 62, 66, 69]),      # Bm7
    5: (43, [59, 62, 66, 69]),      # Gmaj9
    6: (45, [55, 62, 64, 69]),      # A7sus4 (resolves mid-bar)
    7: (38, [50, 61, 64, 66, 69]),  # Dmaj9
}

def stem(program, is_drum=False, reverb=50, chorus=0, vol=100, name=""):
    mid = pm.PrettyMIDI(initial_tempo=BPM)
    inst = pm.Instrument(program=program, is_drum=is_drum, name=name)
    cc(inst, 91, reverb); cc(inst, 93, chorus); cc(inst, 7, vol)
    mid.instruments.append(inst)
    return mid, inst

# ---------- Electric piano ----------
ep_mid, ep = stem(4, reverb=70, chorus=40, vol=96, name="ep")
EP_PATTERN = [(0.0, 1.4, 72), (1.5, 0.45, 56), (2.5, 1.1, 66), (3.5, 0.4, 52)]
for bar in range(1, 7):
    root, voicing = CHORDS[bar]
    for i, (b, d, v) in enumerate(EP_PATTERN):
        notes = voicing
        if bar == 6 and b >= 2.0:
            notes = [55, 61, 64, 69]  # A7 resolution
        if bar == 5 and b > 0:
            v -= 8  # calmer bar
        for k, p in enumerate(notes):
            add(ep, p, t(bar, b) + k * 0.012, d * BEAT, v)  # tiny strum
for k, p in enumerate(CHORDS[7][1]):
    add(ep, p, t(7, 0) + k * 0.03, 2.2, 74, humanize=False)

# ---------- Bass ----------
bs_mid, bs = stem(33, reverb=5, vol=104, name="bass")
for bar in range(1, 7):
    root, _ = CHORDS[bar]
    nxt = CHORDS[bar + 1][0]
    add(bs, root, t(bar, 0), 0.9 * BEAT, 92)
    add(bs, root, t(bar, 1.5), 0.4 * BEAT, 70)
    add(bs, root + 7, t(bar, 2.5), 0.4 * BEAT, 74)
    add(bs, root + 12, t(bar, 3.0), 0.45 * BEAT, 72)
    add(bs, nxt + (1 if nxt < root else -1), t(bar, 3.5), 0.4 * BEAT, 66)  # approach
add(bs, 38, t(7, 0), 2.0, 96, humanize=False)

# ---------- Kalimba hook ----------
mel_mid, mel = stem(108, reverb=85, chorus=20, vol=92, name="kalimba")
MEL = {
    1: [(3.0, 81, 0.5, 50), (3.5, 83, 0.5, 56)],
    2: [(0, 78, .5, 80), (.5, 81, 1, 74), (1.5, 83, .5, 78), (2, 81, 1, 72), (3, 78, .5, 74), (3.5, 76, .5, 68)],
    3: [(0, 78, .5, 82), (.5, 81, 1, 76), (1.5, 85, .5, 84), (2, 83, 1, 76), (3, 81, .5, 74), (3.5, 78, .5, 70)],
    5: [(0, 86, 1.5, 70), (2, 83, 1, 62), (3, 81, 1, 58)],
    6: [(0, 78, .5, 84), (.5, 81, 1, 78), (1.5, 83, .5, 82), (2, 86, 1, 84), (3, 88, .5, 86), (3.5, 90, .5, 88)],
}
for bar, notes in MEL.items():
    for b, p, d, v in notes:
        add(mel, p, t(bar, b), d * BEAT, v)
# bar 4: rising 16th arpeggio for the time-lapse
arp = [71, 74, 78, 81]
for i in range(16):
    p = arp[i % 4] + (12 if i >= 8 else 0)
    add(mel, p, t(4, i * 0.25), 0.3 * BEAT, 52 + i * 2)
add(mel, 86, t(7, 0), 2.2, 84, humanize=False)
add(mel, 90, t(7, 0) + 0.02, 2.2, 60, humanize=False)

# ---------- Warm pad ----------
pad_mid, pad = stem(89, reverb=100, chorus=60, vol=70, name="pad")
for bar in range(1, 8):
    root, voicing = CHORDS[bar]
    dur = BAR if bar < 7 else 2.6
    for p in voicing:
        add(pad, p - 12 if p > 64 else p, t(bar, 0), dur, 46 if bar > 1 else 36, humanize=False)

# ---------- Drums ----------
dr_mid, dr = stem(0, is_drum=True, reverb=25, vol=100, name="drums")
KICK, SNARE, CLAP, RIM, HAT, OPEN, SHAKER, CRASH, TAMB = 36, 38, 39, 37, 42, 46, 70, 49, 54
SW = 0.06  # swing amount in beats for off-8ths
for bar in range(1, 7):
    full = bar in (2, 3, 4, 6)
    # kick
    kicks = [0, 2] if bar in (1, 5) else [0, 1.5, 2, 3.5] if bar != 4 else [0, 1.5, 2, 2.75, 3.5]
    for b in kicks:
        add(dr, KICK, t(bar, b), 0.2, 100 if b in (0, 2) else 80)
    # backbeat
    if full:
        for b in (1, 3):
            add(dr, CLAP, t(bar, b), 0.2, 84)
            add(dr, SNARE, t(bar, b) + 0.004, 0.2, 52)
    elif bar == 5:
        add(dr, RIM, t(bar, 1), 0.1, 70)
        add(dr, RIM, t(bar, 3), 0.1, 64)
    # hats
    if bar == 4:
        for i in range(16):
            add(dr, HAT, t(bar, i * 0.25), 0.1, 70 if i % 2 == 0 else 50)
        add(dr, TAMB, t(bar, 1), 0.2, 60); add(dr, TAMB, t(bar, 3), 0.2, 60)
    else:
        for i in range(8):
            b = i * 0.5 + (SW if i % 2 else 0)
            v = 64 if i % 2 == 0 else 48
            if bar == 1:
                v -= 12
            add(dr, HAT, t(bar, b), 0.1, v)
        if full:
            add(dr, OPEN, t(bar, 3.5 + SW), 0.3, 46)
    # shaker 16ths
    for i in range(16):
        add(dr, SHAKER, t(bar, i * 0.25), 0.08, 40 if i % 4 else 52)
# crashes on the big moments
add(dr, CRASH, t(3, 0), 1.0, 70)   # reach up
add(dr, CRASH, t(6, 0), 1.0, 76)   # call to action
add(dr, CRASH, t(7, 0), 1.5, 72); add(dr, KICK, t(7, 0), 0.2, 104)
# fill at end of bar 5 into the end card
for i in range(4):
    add(dr, SNARE, t(5, 3 + i * 0.25), 0.1, 50 + i * 14)

for name, mid in [("ep", ep_mid), ("bass", bs_mid), ("mel", mel_mid), ("pad", pad_mid), ("drums", dr_mid)]:
    mid.write(f"/home/claude/work/music/{name}.mid")
print("bar", BAR, "total", t(7, 0) + 2.6)
