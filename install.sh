#!/usr/bin/env bash
set -e

echo "[Creating symlink] spotify.r.1s+.py -> ~/.config/argos/spotify.r.1s+.py"
ln -s spotify.r.1s+.py ~/.config/argos/spotify.r.1s+.py

echo "[Installing requirements]"
pip3 install -r requirements.txt

echo "Extension installed!"
