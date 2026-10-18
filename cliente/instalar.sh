#!/usr/bin/env bash
# Cria venv local e instala o pycryptodome (crypto do login RSA/Blowfish).
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
./.venv/bin/pip install -q -r requirements.txt
echo "pronto. rode: ./.venv/bin/python entrar.py <usuario> <senha>"
