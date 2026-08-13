#!/usr/bin/env bash
# Régénère img/manifest.json à partir des fichiers présents dans img/.
# Nomme tes fichiers d'après le slug du personnage : monkey-d-luffy.png, roronoa-zoro.jpg…
# (le slug est le nom en minuscules, sans accent, espaces et points remplacés par des tirets)
set -euo pipefail
cd "$(dirname "$0")/.."
{
  echo "{"
  first=1
  for f in img/*.png img/*.jpg img/*.jpeg img/*.webp; do
    [ -e "$f" ] || continue
    b=$(basename "$f")
    s="${b%.*}"
    [ $first -eq 1 ] || echo ","
    printf '  "%s": "%s"' "$s" "$b"
    first=0
  done
  echo ""
  echo "}"
} > img/manifest.json
n=$(grep -c '": "' img/manifest.json || true)
echo "img/manifest.json régénéré — $n image(s)."
