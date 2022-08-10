#!/bin/bash
set -e  # error if anything returns non-zero exit code

# needed for some tests that add Desktop
mkdir ~/Desktop

sudo apt-get install -y libpng-dev
# sudo apt-get install -y python3-pyqt5
wget -q https://lilypond.org/download/binaries/linux-64/lilypond-2.22.1-1.linux-64.sh
sh lilypond-2.22.1-1.linux-64.sh --batch
export PATH=/home/runner/bin:$PATH
pip3 install -r requirements_dev.txt
python3 -m compileall music21
