#!/usr/bin/env bash
# build_video.sh <account_dir> <slug>
# Assembles the single-voice landing page video from generated inputs. Runs in the cloud with ffmpeg only, no network.
# Required inputs (the generated media this session cannot make itself):
#   <dir>/assets/vo.wav            one continuous narrator clip, 8-scene script, about 208 words
#   <dir>/assets/broll.mp4         8 second opening b-roll, no on-screen text (its audio is discarded)
#   <dir>/assets/music_src.mp4     transcription-verified INSTRUMENTAL bed, no vocals
#   <dir>/assets/reference.mp4     real Airtable product footage (scenes 3 to 5 cut from it)
#   <dir>/cards/*.png              from make_cards.py
# Output: <dir>/<slug>_video.mp4 (1920x1080, 30 fps, H.264, AAC 48k stereo, 1.08x speedup applied last).
set -euo pipefail
DIR="$1"; SLUG="$2"
cd "$DIR"; mkdir -p segments
for f in assets/vo.wav assets/broll.mp4 assets/music_src.mp4 assets/reference.mp4 cards/s0_overlay.png cards/s1.png cards/s2.png cards/s6.png cards/s7.png cards/s8.png; do
  [ -s "$f" ] || { echo "MISSING INPUT: $DIR/$f" >&2; exit 3; }
done
ENC="-c:v libx264 -preset veryfast -pix_fmt yuv420p -r 30"
calc(){ awk "BEGIN{printf \"%.3f\", $1}"; }
VOD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 assets/vo.wav)
WT=208
d1=$(calc "40/$WT*$VOD"); d2=$(calc "40/$WT*$VOD"); d3=$(calc "19/$WT*$VOD")
d4=$(calc "27/$WT*$VOD"); d5=$(calc "29/$WT*$VOD"); d6=$(calc "30/$WT*$VOD"); d7=$(calc "23/$WT*$VOD")
S0=8.0; S8=5.5
echo "VOD=$VOD durs: $S0 $d1 $d2 $d3 $d4 $d5 $d6 $d7 $S8"

tmpmv(){ mv "segments/tmp_$1" "segments/$1"; }

ffmpeg -y -i assets/broll.mp4 -i cards/s0_overlay.png -filter_complex \
 "[0:v]scale=1920:1080,setsar=1,fps=30[bg];[bg][1:v]overlay=0:0,format=yuv420p" -t $S0 $ENC -an segments/tmp_seg0.mp4 -loglevel error && tmpmv seg0.mp4
cardseg(){ ffmpeg -y -loop 1 -i "$1" -t "$2" -vf "scale=1920:1080,fade=t=in:st=0:d=0.6,format=yuv420p" $ENC -an "segments/tmp_$3" -loglevel error && tmpmv "$3"; }
cardseg cards/s1.png $d1 seg1.mp4
cardseg cards/s2.png $d2 seg2.mp4
cardseg cards/s6.png $d6 seg6.mp4
cardseg cards/s7.png $d7 seg7.mp4
ffmpeg -y -loop 1 -i cards/s8.png -t $S8 -vf "scale=1920:1080,fade=t=in:st=0:d=0.6,fade=t=out:st=3.0:d=2.5,format=yuv420p" $ENC -an segments/tmp_seg8.mp4 -loglevel error && tmpmv seg8.mp4
prodseg(){ ffmpeg -y -ss "$1" -i assets/reference.mp4 -t "$2" -vf "scale=1920:1080,setsar=1,fps=30,format=yuv420p" $ENC -an "segments/tmp_$3" -loglevel error && tmpmv "$3"; }
prodseg 7  $d3 seg3.mp4
prodseg 70 $d4 seg4.mp4
prodseg 42 $d5 seg5.mp4

printf "file 'seg0.mp4'\nfile 'seg1.mp4'\nfile 'seg2.mp4'\nfile 'seg3.mp4'\nfile 'seg4.mp4'\nfile 'seg5.mp4'\nfile 'seg6.mp4'\nfile 'seg7.mp4'\nfile 'seg8.mp4'\n" > segments/list.txt
ffmpeg -y -f concat -safe 0 -i segments/list.txt -c copy segments/video_only.mp4 -loglevel error
VID=$(ffprobe -v error -show_entries format=duration -of csv=p=0 segments/video_only.mp4)
FADE=$(calc "$VID-3")

# AUDIO: narrator VO + verified-instrumental bed ONLY. Generated b-roll audio is never used, because generation tools can inject
# spoken taglines into it. music_src must have been checked by transcription to contain no speech.
ffmpeg -y -i assets/vo.wav -af "loudnorm=I=-16:LRA=11:TP=-1.5,volume=0.95" -ar 48000 -ac 2 assets/vo_norm.m4a -loglevel error
ffmpeg -y -i assets/music_src.mp4 -vn -ar 48000 -ac 2 assets/music8.m4a -loglevel error

ffmpeg -y -i segments/video_only.mp4 -stream_loop 25 -i assets/music8.m4a -i assets/vo_norm.m4a \
 -filter_complex "
   [1:a]volume='if(lt(t,10),0.20,0.13)':eval=frame[mus];
   [2:a]adelay=8000|8000,volume=1.0[vo];
   [mus][vo]amix=inputs=2:duration=longest:normalize=0,afade=t=out:st=$FADE:d=3,alimiter=limit=0.85[mix]" \
 -map 0:v -map "[mix]" -c:v copy -c:a aac -ar 48000 -ac 2 -b:a 192k -shortest final_unstretched.mp4 -loglevel error
ffmpeg -y -i final_unstretched.mp4 -filter_complex "[0:v]setpts=PTS/1.08[v];[0:a]atempo=1.08[a]" \
 -map "[v]" -map "[a]" -c:v libx264 -preset veryfast -pix_fmt yuv420p -r 30 -c:a aac -ar 48000 -ac 2 -b:a 192k "tmp_${SLUG}_video.mp4" -loglevel error
mv "tmp_${SLUG}_video.mp4" "${SLUG}_video.mp4"
echo "=== FINAL $SLUG ==="; ffprobe -v error -show_entries format=duration -of csv=p=0 "${SLUG}_video.mp4"
ffmpeg -i "${SLUG}_video.mp4" -af volumedetect -f null - 2>&1 | grep max_volume
