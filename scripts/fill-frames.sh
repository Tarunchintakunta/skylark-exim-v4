#!/usr/bin/env bash
# Fill the frames a stepped render skipped: <dir> <first> <last> <step>. Rendered PNGs are never touched; the gaps
# come from ffmpeg motion-compensated interpolation (minterpolate) between the rendered neighbours.
set -euo pipefail
dir=$1 F=$2 L=$3 S=$4
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
k=0; for ((f=F; f<=L; f+=S)); do ln -s "$(cd "$dir" && pwd)/$(printf "%04d.png" "$f")" "$(printf "%s/%05d.png" "$tmp" "$k")"; k=$((k+1)); done
last=$((F+(k-1)*S))
ffmpeg -v error -y -framerate "$(awk "BEGIN{print 24/$S}")" -i "$tmp/%05d.png" -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -start_number "$F" "$tmp/i_%04d.png"
for ((f=F; f<=L; f++)); do
  dst=$(printf "%s/%04d.png" "$dir" "$f"); [ -f "$dst" ] && continue
  src=$(printf "%s/i_%04d.png" "$tmp" "$f"); [ "$f" -gt "$last" ] && src=$(printf "%s/%04d.png" "$dir" "$L")
  [ -f "$src" ] || src=$(printf "%s/%04d.png" "$dir" "$last")
  cp "$src" "$dst"
done
echo "filled $dir $F-$L (step $S, $k rendered)"
