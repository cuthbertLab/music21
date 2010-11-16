#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         spanner.py
# Purpose:      The Spanner base-class and subclasses
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import music21
from music21 import spanners



class Spanner(music21.Music21Object):
    '''
    Spanner objects live on Streams as other Music21Objects, but store connections between one ore more Music21Objects.


    '''
    def __init__(self, *arguments, **keywords):
        music21.Music21Object.__init__(self)

        # store a spanners instance; each instances shares a single
        # storage dictionary and wraps all components in weak refs
        self._spanners = spanners.Spanners()


        # let all *arguments be a list of object to be 
        # components of this Spanner

    def getComponents(self):
        pass
        # get components form _spanners

    def addComponents(self):
        pass

    def clearComponents(self):
        pass





# connect two or more notes anywhere in the score
class Slur(Spanner):
    pass

# crescendo
class Crescendo(Spanner):
    pass


# first/second repeat bracket
class RepeatBracket(Spanner):
    pass




# association of staffs
# designates bracket or brace or combination of many
class StaffGroup(Spanner):
    pass




# optionally define one or more Streams as a staff
# provide settings for staff presentation such as bar lines
class Staff(Spanner):
    pass



# association of all measures or streams on a page
class Page(Spanner):
    pass