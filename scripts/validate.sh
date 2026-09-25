#!/usr/bin/env bash
# Validate the integration: Python syntax, JSON files, and Home Assistant's hassfest.
# Run locally before pushing; CI runs this same script.
set -euo pipefail

# hassfest is pinned by digest so a run is reproducible. To update it:
#   docker pull ghcr.io/home-assistant/hassfest:latest
#   docker image inspect ghcr.io/home-assistant/hassfest:latest --format '{{index .RepoDigests 0}}'
HASSFEST_IMAGE="ghcr.io/home-assistant/hassfest@sha256:66b55a8ce14cdcf0c200dd4dab1f3228ac8d3f6e0404ec710a0d8a79b296eba4"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "==> Python syntax"
for f in custom_components/dockge/*.py; do
  python3 -c 'import sys; compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec")' "$f"
done

echo "==> JSON files"
for f in hacs.json custom_components/dockge/manifest.json custom_components/dockge/strings.json; do
  python3 -m json.tool "$f" > /dev/null
done

echo "==> hassfest"
docker run --rm -v "$repo_root":/github/workspace:ro "$HASSFEST_IMAGE"
