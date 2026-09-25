#!/usr/bin/env bash
# Run the pytest suite in a throwaway Python container (Home Assistant's test
# harness needs a newer Python than most hosts ship). CI runs this same script.
set -euo pipefail

# Pinned by digest for reproducible runs. To update it:
#   docker pull python:3.14-slim
#   docker image inspect python:3.14-slim --format '{{index .RepoDigests 0}}'
PYTHON_IMAGE="python:3.14-slim@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker run --rm -e AUDIT -e PYTHONDONTWRITEBYTECODE=1 -v "$repo_root":/src -w /src "$PYTHON_IMAGE" bash -c '
  set -euo pipefail
  pip install --quiet --root-user-action=ignore --disable-pip-version-check -r requirements_test.txt
  # homeassistant pins cryptography==48.0.1, which has open advisories
  # (CVE-2026-69247/69248/69249). Test with the fixed release until HA bumps it.
  pip install --quiet --root-user-action=ignore --disable-pip-version-check cryptography==50.0.1 2>&1 \
    | grep -v "dependency conflicts\|requires cryptography" || true
  if [ "${AUDIT:-0}" = 1 ]; then
    pip install --quiet --root-user-action=ignore --disable-pip-version-check pip-audit
    pip-audit --progress-spinner off
  fi
  python -m pytest -q -p no:cacheprovider "$@"
' test "$@"
