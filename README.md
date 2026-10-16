# ig

Claude's workspace for Instagram content for @dmytrodorosh.

## pipeline/
- `render.sh` - simple reframe + color grade + slow-mo ending (ffmpeg)
- `story.py` - dynamic Story: speed ramps, zoom punch-ins, animated pose labels, call to action, music
- `reel.py` - Reel variant: hook + payoff text, everything kept clear of the Reels UI
- `carousel.py` - "Expectation vs Reality" 4:5 carousel from video frames
- `music/compose.py`, `music/mix.py` - original 100 BPM track (MIDI + FluidSynth FluidR3_GM, numpy mix)

Requires: ffmpeg, python3 (numpy, scipy, opencv, pillow, pretty_midi), fluidsynth + FluidR3_GM soundfont, Inter fonts, Noto Color Emoji.

## Publishing
Media is pushed to a temporary `media-tmp` branch, rehosted through Composio and published with the Instagram Graph API, then the branch is deleted.
