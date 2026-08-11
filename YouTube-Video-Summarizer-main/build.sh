#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
# torch's CPU-only wheels live on PyTorch's own index, not PyPI, so they
# have to be installed separately before the rest of requirements.txt
pip install -r requirements-torch.txt --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
