#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from music21.ext import xlrd
from music21.ext import six
#sys.path.append('/mit/cuthbert/www/music21')


if len(sys.argv) != 3:
    raise Exception("Need two arguments to diff!")

if (sys.argv[1].count(':') == 1):
    (book1name, sheetname1) = sys.argv[1].split(':')
    if (book1name.count('.xls') == 0):
        book1name += ".xls"
else:
    raise ("First name must be in form filename:sheetname")

if (sys.argv[2].count(':') == 1):
    (book2name, sheetname2) = sys.argv[2].split(':')
else:
    (book2name, sheetname2) = (sys.argv[2], sheetname1)

if (book2name.count('.xls') == 0):
    book2name += ".xls"
    
book1 = xlrd.open_workbook(book1name)
book2 = xlrd.open_workbook(book2name)

sheet1 = book1.sheet_by_name(sheetname1)
sheet2 = book2.sheet_by_name(sheetname2)

totalRows1 = sheet1.nrows
totalRows2 = sheet2.nrows
extraRows = 0
longsheet = 0

if (totalRows1 > totalRows2):
    longsheet = 1
    extraRows = (totalRows1 - totalRows2)
    minRows = totalRows2
elif (totalRows1 < totalRows2):
    longsheet = 2
    extraRows = (totalRows2 - totalRows1)
    minRows = totalRows1
else:
    minRows = totalRows1 # doesnt matter which

for i in range(0, minRows):
    rowvalues1 = sheet1.row_values(i)
    rowvalues2 = sheet2.row_values(i)
    longrow = 0
    totalCells1 = len(rowvalues1)
    totalCells2 = len(rowvalues2)
    extraCells = 0
    if (totalCells1 > totalCells2):
        longrow = 1
        extraCells = (totalCells1 - totalCells2)
        minCells = totalCells2
    elif (totalCells1 > totalCells2):
        longrow = 2
        extraCells = (totalCells2 - totalCells1)
        minCells = totalCells1
    else:
        minCells = totalCells1 # doesnt matter which
    for j in range(0, minCells):
        if (rowvalues1[j] != rowvalues2[j]):
            print("%3d,%2s--%34s : %34s" % (i+1,xlrd.colname(j),
                                               six.u(rowvalues1[j]).encode('utf-8')[:34],
                                               six.u(rowvalues2[j]).encode('utf-8')[:34]))
    if (extraCells > 0):
        print("%3d extra cells in row %3d in" % (extraCells, i+1),)
        if (longrow == 1): 
            print(book1name + ":" + sheetname1)
        elif (longrow == 2): 
            print(book2name + ":" + sheetname2)
        else: 
            raise Exception("What?  longrow was not set!")

if (extraRows > 0):
    print("%3d extra rows in" % extraRows,)
    if (longsheet == 1): 
        print(book1name + ":" + sheetname1)
    elif (longsheet == 2): 
        print(book2name + ":" + sheetname2)
    else: 
        raise Exception("What?  longsheet was not set!")



#------------------------------------------------------------------------------
# eof

