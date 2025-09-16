#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

# Config
TARGET_I=-14      # target integrated loudness (LUFS)
TARGET_TP=-1.5    # target true peak (dBTP)
TARGET_LRA=11     # target loudness range
BOOST=16dB         # uniform boost applied after normalization
OUTDIR="sounds/wav"

mkdir -p "$OUTDIR"

for f in sounds/orig/*.wav; do
  [ -f "$f" ] || continue
  echo "----------------------------------------"
  echo "Processing: $f"

  # Pass 1: measure loudness (print JSON to stderr -> capture)
  JSON=$(ffmpeg -hide_banner -v info -i "$f" -af "loudnorm=I=$TARGET_I:TP=$TARGET_TP:LRA=$TARGET_LRA:print_format=json" -f null - 2>&1)

  # Extract measured values (capture between the quotes) with sed -> this strips quotes reliably
  MEASURED_I=$(echo "$JSON" | sed -nE 's/.*"input_i"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p')
  MEASURED_TP=$(echo "$JSON" | sed -nE 's/.*"input_tp"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p')
  MEASURED_LRA=$(echo "$JSON" | sed -nE 's/.*"input_lra"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p')
  MEASURED_THRESH=$(echo "$JSON" | sed -nE 's/.*"input_thresh"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p')
  OFFSET=$(echo "$JSON" | sed -nE 's/.*"target_offset"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p')

  # If parsing failed, fall back to single-pass loudnorm + boost
  if [ -z "${MEASURED_I:-}" ] || [ -z "${MEASURED_TP:-}" ]; then
    echo "Warning: failed to parse loudnorm measurement for '$f'. Falling back to 1-pass loudnorm + boost."
    ffmpeg -hide_banner -y -i "$f" -af "loudnorm=I=$TARGET_I:TP=$TARGET_TP:LRA=$TARGET_LRA,volume=$BOOST" -ar 44100 -ac 2 -c:a pcm_s16le "$OUTDIR/`basename $f .wav`.wav"
    continue
  fi

  echo "Measured_I = $MEASURED_I   Measured_TP = $MEASURED_TP   Offset = $OFFSET"

  # Pass 2: apply measured normalization + boost
  ffmpeg -hide_banner -y -i "$f" -af "loudnorm=I=$TARGET_I:TP=$TARGET_TP:LRA=$TARGET_LRA:measured_I=$MEASURED_I:measured_TP=$MEASURED_TP:measured_LRA=$MEASURED_LRA:measured_thresh=$MEASURED_THRESH:offset=$OFFSET:linear=true,volume=$BOOST" -ar 44100 -ac 2 -c:a pcm_s16le "$OUTDIR/`basename $f .wav`.wav"
done

echo "✅ Done. Outputs in: $OUTDIR"


# cp -v sounds/wav/*.wav /media/`whoami`/CIRCUITPY/sounds
