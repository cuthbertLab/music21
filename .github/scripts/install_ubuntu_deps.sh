#!/bin/bash
set -e  # error if anything returns non-zero exit code

# needed for some tests that add Desktop
mkdir ~/Desktop

sudo apt-get install -y libpng-dev
# sudo apt-get install -y python-qt4
wget -q https://lilypond.org/download/binaries/linux-64/lilypond-2.22.0-1.linux-64.sh
sh lilypond-2.22.0-1.linux-64.sh --batch
export PATH=/home/runner/bin:$PATH
pip3 install -r requirements.txt
pip3 install coveralls
pip3 install scipy
pip3 install python-Levenshtein
pip3 install setuptools
pip3 install coverage
cd music21
python -m compileall music21
