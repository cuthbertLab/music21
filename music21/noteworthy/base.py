# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         noteworthy.base.py
# Purpose:      music21 classes and dicts for dealing with nwc data
#
# Authors:      Jordi Bartolome
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------



dictionaryNoteLength = {"Whole":4, "Half": 2, "4th":1, "8th":0.5, "16th":0.25, "32nd":0.125, "64th":0.0625, 0:0}
dictionaryrest = {"Whole\n":4, "Half\n": 2, "4th\n":1, "8th\n":0.5, "16th\n":0.25, "32nd\n":0.125, "64th\n":0.0625}
dictionarytrip = {4:"Whole", 2:"Half", 1:"4th", 0.5:"eighth", 0.25: "16th", 0.125: "32nd", 0.0625:"64th", 0:0}
dictionaryTreble = {1:"C", 2:"D", 3:"E", 4:"F", 5:"G", 6:"A", 7:"B", "octave":5}
dictionaryBass = {-1:"C", 0:"D", 1:"E", 2:"F", 3:"G", 4:"A", 5:"B", "octave":3}
dictionaryAlto = {0:"C", 1:"D", 2:"E", 3:"F", 4:"G", 5:"A", 6:"B", "octave":4}
dictionaryTenor = {-5:"C", -4:"D", -3:"E", -2:"F", -1:"G", 0:"A", 1:"B", "octave":3}
dictionarysharp = {1:"F", 2:"C", 3:"G", 4:"D", 5:"A", 6:"E", 7:"B"}
dictionarybemol = {1:"B", 2:"E", 3:"A", 4:"D", 5:"G", 6:"C", 7:"F"}
dictionaries = {"dictionaryNoteLength":dictionaryNoteLength, "dictionaryrest":dictionaryrest, "dictionarytrip": dictionarytrip, "dictionaryTreble":dictionaryTreble, "dictionaryAlto":dictionaryAlto, "dictionaryTenor":dictionaryTenor, "dictionaryBass":dictionaryBass, "dictionarysharp":dictionarysharp, "dictionarybemol":dictionarybemol}
