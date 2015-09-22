# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         featureExtractoMRJOB.py
# Purpose:      sample mrjob for use for feature extraction on entire corpus
#
# Authors:      Beth Hadley
#
# Copyright:    Copyright © 2011 The music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
A Sample mrjob. This mrjob is designed to extract all 91 features (jsymbolic and native)
from every corpus file (1,200 scores). This is a work in progress =)
'''
from mrjob.job import MRJob

from music21.demos.bhadley.mrjobaws import awsutility
from music21.features import base


class MRFeatureExtractor(MRJob):
    def mapper(self, key, fileName):
        data = awsutility.getStreamAndmd5(fileName.split()[0]) #.split()[0] because line is read in by protocol

        for dataList in data:
            streamObj, md5hash = dataList
            jsymb, nat = base.allFeaturesAsList(streamObj)   
            yield md5hash + '|' + streamObj.corpusFilepath + '|' + str(jsymb) + '|' + str(nat)

    #def reducer(self, word, occurrences):
    #    yield word, sum(occurrences)
    # reducer not needed, simply outputing data

if __name__ == '__main__':
    MRFeatureExtractor.run()
