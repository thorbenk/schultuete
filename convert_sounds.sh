#!/bin/bash

set -e

for i in sounds/orig/*.wav; do
    echo $i
    ffmpeg -y -i "$i" -ac 1 -ar 22050 -sample_fmt s16 -af "volume=0.95" "sounds/`basename $i .wav`.wav"
done

cp -v sounds/*.wav /media/`whoami`/CIRCUITPY/sounds
