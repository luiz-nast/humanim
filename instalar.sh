#!/usr/bin/env bash
# Instala o humanim no Ubuntu sem sudo: Cairo e Pango pelo Homebrew, Python pelo uv.
set -euo pipefail
cd "$(dirname "$0")"

HOMEBREW_NO_AUTO_UPDATE=1 brew install cairo pango pkgconf
export PKG_CONFIG="$(brew --prefix)/bin/pkgconf"
export PKG_CONFIG_PATH="$(brew --prefix)/lib/pkgconfig:$(brew --prefix)/share/pkgconfig"

uv venv -p 3.12 .venv
uv pip install -p .venv/bin/python -e .
echo "OK instalado. Use .venv/bin/humanim"
