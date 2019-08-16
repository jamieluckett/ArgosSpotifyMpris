#!/usr/bin/env bash
echo "[Creating symlink] spotify.r.1s+.py -> ~/.config/argos/spotify.r.1s+.py"
ln -s spotify.r.1s+.py ~/.config/argos/spotify.r.1s+.py

if [ $? -eq 0 ]
then
    echo "Extension installed!"
fi