#!/bin/bash

set -e

for i in sounds/orig/*.wav; do
    echo $i
    ffmpeg -y -i "$i" -ac 1 -ar 22050 -sample_fmt s16 -af "volume=0.95" "sounds/wav/`basename $i .wav`.wav"
    ffmpeg -y -i "$i" -ac 1 -ar 22050 -b:a 64k -codec:a libmp3lame -write_xing 0 -af "volume=0.95" "sounds/low/`basename $i .wav`.mp3"
    ffmpeg -y -i "$i" -ac 1 -b:a 128k -af "volume=0.95" "sounds/hi/`basename $i .wav`.mp3"
done

# cp -v sounds/low/*mp3 /media/`whoami`/CIRCUITPY/sounds
