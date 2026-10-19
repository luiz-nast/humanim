#!/usr/bin/env bash
# Instala o humanim no Ubuntu sem sudo: Cairo e Pango pelo Homebrew, Python pelo uv.
set -euo pipefail
cd "$(dirname "$0")"

HOMEBREW_NO_AUTO_UPDATE=1 brew install cairo pango pkgconf
export PKG_CONFIG="$(brew --prefix)/bin/pkgconf"
export PKG_CONFIG_PATH="$(brew --prefix)/lib/pkgconfig:$(brew --prefix)/share/pkgconfig"

uv venv -p 3.12 .venv
uv pip install -p .venv/bin/python -e .
mkdir -p ~/.local/bin
ln -sf "$PWD/.venv/bin/humanim" ~/.local/bin/humanim  # ~/.local/bin já está no PATH do Ubuntu
echo "OK instalado: humanim (link em ~/.local/bin; se o terminal não achar, abra um novo ou use .venv/bin/humanim)"
