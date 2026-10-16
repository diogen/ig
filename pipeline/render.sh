#!/bin/bash
# usage: render.sh <src> <out> [title|notitle]
set -e
SRC="$1"; OUT="$2"; MODE="${3:-notitle}"
CROP="crop=990:1760:90:80,scale=1080:1920:flags=lanczos"
GRADE="eq=contrast=1.07:brightness=0.015:gamma=1.03:saturation=1.08,colorbalance=rs=0.02:bs=-0.03:rm=0.025:gm=0.005:bm=-0.03:rh=0.01:bh=-0.02,vibrance=intensity=0.18,curves=all='0/0 0.25/0.22 0.75/0.79 1/1',unsharp=5:5:0.5:5:5:0"
TITLE=""
if [ "$MODE" = "title" ]; then
  B=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf
  M=/usr/share/fonts/opentype/inter/Inter-Medium.otf
  # alpha: fade in 0.3-0.9s, hold, fade out 3.6-4.2s
  A="if(lt(t,0.3),0,if(lt(t,0.9),(t-0.3)/0.6,if(lt(t,3.6),1,if(lt(t,4.2),(4.2-t)/0.6,0))))"
  # slight upward drift while fading in
  Y1="250-if(lt(t,0.9),(0.9-max(t,0.3))*40,0)"
  Y2="370-if(lt(t,0.9),(0.9-max(t,0.3))*40,0)"
  TITLE=",drawtext=fontfile=$B:text='Morning flow':fontsize=92:fontcolor=0x1E1E1E:alpha='$A':x=64:y='$Y1',drawtext=fontfile=$M:text='SURYA NAMASKAR':fontsize=38:fontcolor=white:alpha='$A':x=78:y='$Y2':box=1:boxcolor=0xF26B1D@0.85:boxborderw=14"
fi
ffmpeg -v error -y -i "$SRC" -f lavfi -i anullsrc=r=44100:cl=stereo -filter_complex "\
[0:v]$CROP,$GRADE,split[v1][v2];\
[v1]trim=0:17.95,setpts=PTS-STARTPTS,fps=30[a];\
[v2]trim=17.95:18.55,setpts=2*(PTS-STARTPTS),fps=30[b];\
[a][b]concat=n=2:v=1:a=0,fade=t=in:st=0:d=0.3,fade=t=out:st=18.75:d=0.4${TITLE},format=yuv420p[v]" \
-map "[v]" -map 1:a -shortest -c:v libx264 -preset slow -crf 17 -profile:v high -level 4.1 \
-maxrate 15M -bufsize 30M -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
-c:a aac -b:a 128k -movflags +faststart "$OUT"
