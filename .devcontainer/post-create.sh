#!/usr/bin/env bash
set -euo pipefail


#python -m pip install --upgrade pip
#python -m pip install -r requirements-dev.txt

#echo "Vision runtime environment ready."
#echo "Tests: python -m unittest discover -s tests"
#echo "Demo: scripts/run_demo.sh"

bash scripts/setup_local.sh

.venv/bin/python -m pip install ruff openpyxl

echo "Vision environment ready."
echo "Activate it with: source .venv/bin/activate"
