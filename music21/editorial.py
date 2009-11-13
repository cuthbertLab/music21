#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         editorial.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import music21

class EditorialException(Exception):
    pass

class CommentException(Exception):
    pass

class NoteEditorial(music21.Music21Object):
    '''EditorialComments that can be applied to notes'''
    def __init__(self):
        self.ficta = None  # Accidental object -- N.B. for PRINTING only not for determining intervals
        self.color = ""
        self.misc  = {}    # dict to hold anything you might like to store
        self.harmonicInterval = None
        self.melodicInterval = None
        self.melodicIntervals = []
        self.melodicIntervalOverRests = None
        self.melodicIntervalsOverRests = []
        self.comment = Comment()

    def lilyStart(self):
        baseRet = ""
        if self.ficta is not None:
            baseRet += self.fictaLilyStart()
        if self.color:
            baseRet += self.colorLilyStart()
        return baseRet

    def fictaLilyStart(self):
        return "\\ficta "

    def colorLilyStart(self):
        return "\\color \"" + self.color + "\" "

    def lilyAttached(self):
        if self.comment and self.comment.text:
            return self.comment.lily
        else:
            return ""
    
    def lilyEnd(self):
        return ""
        
class Comment(object):
    position = "below"
    text = None
    
    def _getLily(self):
        if self.text is None:
            return ""
        if self.position == 'below':
            return '_"' + self.text + '"'
        elif self.position == 'above':
            return '^"' + self.text + '"'
        else:
            raise CommentException("Cannot deal with position: " + self.position)
        
    lily = property(_getLily)