

import os, sys

print "Starting music21 Configuration Assistant, this could take 10-60 seconds, please wait..."

if 'music21' in os.listdir(os.getcwd()):
    p1 = os.path.join(os.getcwd(), 'music21')
    if p1 not in sys.path:
        sys.path.append(p1)
    if 'music21' in os.listdir(p1):
        p2 = os.path.join(p1, 'music21')
        if p2 not in sys.path:
            sys.path.append(os.path.join(p2, 'music21'))

run = False
try:
    from music21 import configure
    run = True
except ImportError:
    pass


# need to be sure that we have the configure.py file found in the right place

if run:
    ca = configure.ConfigurationAssistant()
    ca.run()






