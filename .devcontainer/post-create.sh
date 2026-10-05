#!/usr/bin/env bash
set -euo pipefail


python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

echo "Vision runtime environment ready."
echo "Tests: python -m unittest discover -s tests"
echo "Demo: scripts/run_demo.sh"
