#!/usr/bin/env bash
set -euo pipefail

echo "==> Bootstrapping cloud agent environment"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not installed." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "node is required but not installed." >&2
  exit 1
fi

python_version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
node_major="$(node -p 'process.versions.node.split(\".\")[0]')"

if [[ "${python_version}" != "3.12" ]]; then
  echo "Warning: expected Python 3.12, found ${python_version}" >&2
fi

if [[ "${node_major}" != "20" ]]; then
  echo "Warning: expected Node.js 20.x, found $(node -v)" >&2
fi

echo "==> Installing Python dependencies"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt -r requirements-dev.txt

echo "==> Installing Node dependencies"
npm ci

echo "==> Environment bootstrap complete"
