# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         graph.py
# Purpose:      Classes for graphing in matplotlib and/or other graphing tools.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               Evan Lynch
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Object definitions for graphing and 
plotting :class:`~music21.stream.Stream` objects. 
The :class:`~music21.graph.Graph` object subclasses 
abstract fundamental graphing archetypes using the 
matplotlib library. The :class:`~music21.graph.Plot` 
object subclasses provide reusable approaches 
to graphing data and structures in 
:class:`~music21.stream.Stream` objects.
'''
from __future__ import division

import unittest
import random, math, os

from music21 import base # for _missingImport

from music21 import note
from music21 import dynamics
from music21 import exceptions21

from music21 import pitch
from music21 import common
from music21 import chord
from music21 import corpus
from music21 import converter

from music21.analysis import windowed
from music21.analysis import discrete
from music21.analysis import correlate
from music21.analysis import reduction

from music21 import features
from music21.ext import webcolors

from collections import namedtuple

from music21 import environment
_MOD = 'graph.py'
environLocal = environment.Environment(_MOD)    

ExtendedModules = namedtuple('ExtendedModules', 'matplotlib Axes3D collections patches plt networkx')

def _getExtendedModules():
    '''
    this is done inside a def, so that the slow import of matplotlib is not done
    in ``from music21 import *`` unless it's actually needed.

    Returns a namedtuple: (matplotlib, Axes3D, collections, patches, plt, networkx)
    '''
    if 'matplotlib' in base._missingImport:
        raise GraphException('could not find matplotlib, graphing is not allowed') # pragma: no cover
    import matplotlib # @UnresolvedImport
    # backend can be configured from config file, matplotlibrc,
    # but an early test broke all processing
    #matplotlib.use('WXAgg')
    try:
        from mpl_toolkits.mplot3d import Axes3D # @UnresolvedImport
    except ImportError:
        Axes3D = None
        environLocal.warn("mpl_toolkits.mplot3d.Axes3D could not be imported -- likely cause is an old version of six.py (<1.9.0) on your system somewhere")
    
    from matplotlib import collections # @UnresolvedImport
    from matplotlib import patches # @UnresolvedImport

    #from matplotlib.colors import colorConverter
    import matplotlib.pyplot as plt # @UnresolvedImport
    
    try:
        import networkx
    except ImportError:
        networkx = None # use for testing
    
    return ExtendedModules(matplotlib, Axes3D, collections, patches, plt, networkx)

#-------------------------------------------------------------------------------
class GraphException(exceptions21.Music21Exception):
    pass

class PlotStreamException(exceptions21.Music21Exception):
    pass

# temporary
def _substituteAccidentalSymbols(label):
    if not common.isStr(label):
        return label
    if '-' in label:
        #label = label.replace('-', '&#x266d;')
        #label = label.replace('-', 'b')
        # this uses a tex-based italic
        #label = label.replace('-', '$b$')
        label = label.replace('-', r'$\flat$')
#             if '#' in label:
#                 label = label.replace('-', '&#x266f;')
    if '#' in label:
        label = label.replace('#', r'$\sharp$')
    return label

# define acceptable format and value strings
FORMATS = ['horizontalbar', 'histogram', 'scatter', 'scatterweighted', 
            '3dbars', 'colorgrid', 'horizontalbarweighted']

def userFormatsToFormat(value):
    '''
    Replace possible user format strings with defined format names as used herein. Returns string unaltered if no match.
    '''
    #environLocal.printDebug(['calling user userFormatsToFormat:', value])
    value = value.lower()
    value = value.replace(' ', '')
    if value in ['bar', 'horizontal', 'horizontalbar', 'pianoroll', 'piano']:
        return 'horizontalbar'
    elif value in ['histogram', 'histo', 'count']:
        return 'histogram'
    elif value in ['scatter', 'point']:
        return 'scatter'
    elif value in ['weightedscatter', 'weighted', 'scatterweighted']:
        return 'scatterweighted'
    elif value in ['3dbars', '3d']:
        return '3dbars'
    elif value in ['colorgrid', 'grid', 'window', 'windowed']:
        return 'colorgrid'
    elif value in ['horizontalbarweighted', 'barweighted', 'weightedbar']:
        return 'horizontalbarweighted'
    else: # return unaltered if no match
        #environLocal.printDebug(['userFormatsToFormat(): could not match value', value])
        return value

VALUES = ['pitch', 'pitchspace', 'ps', 'pitchclass', 'pc', 'duration', 'quarterlength', 'offset', 'time', 'dynamic', 'dynamics', 'instrument']

def userValuesToValues(valueList):
    '''Given a value list, replace string with synonymes. Let unmatched values pass.
    '''  
    post = []
    for value in valueList:
        value = value.lower()
        value = value.replace(' ', '')
        if value in ['pitch', 'pitchspace', 'ps']:
            post.append('pitch')
        elif value in ['pitchclass', 'pc']:
            post.append('pitchclass')
        elif value in ['duration', 'quarterlength']:
            post.append('quarterlength')
        elif value in ['offset', 'time']:
            post.append('offset')
        elif value in ['dynamic', 'dynamics']:
            post.append('dynamics')
        elif value in ['instrument', 'instruments', 'instrumentation']:
            post.append('instrument')
        else:
            post.append(value)
    return post


def getColor(color):
    '''Convert any specification of a color to a hexadecimal color used by matplotlib. 
    
    >>> graph.getColor('red')
    '#ff0000'
    >>> graph.getColor('r')
    '#ff0000'
    >>> graph.getColor('Steel Blue')
    '#4682b4'
    >>> graph.getColor('#f50')
    '#ff5500'
    >>> graph.getColor([.5, .5, .5])
    '#808080'
    >>> graph.getColor(.8)
    '#cccccc'
    >>> graph.getColor([255, 255, 255])
    '#ffffff'
    
    Invalid colors raise GraphExceptions:
    
    >>> graph.getColor('l')
    Traceback (most recent call last):
    GraphException: invalid color abbreviation: l

    >>> graph.getColor('chalkywhitebutsortofgreenish')
    Traceback (most recent call last):
    GraphException: invalid color name: chalkywhitebutsortofgreenish

    >>> graph.getColor(True)
    Traceback (most recent call last):
    GraphException: invalid color specification: True
    '''
    # expand a single value to three
    if common.isNum(color):
        color = [color, color, color]
    if common.isStr(color):
        if color[0] == '#': # assume is hex
            # this will expand three-value codes, and check for badly
            # formed codes
            return webcolors.normalize_hex(color)
        color = color.lower().replace(' ', '')
        # check for one character matplotlib colors
        if len(color) == 1:
            colorMap = {'b': 'blue',
                        'g': 'green',
                        'r': 'red',
                        'c': 'cyan',
                        'm': 'magenta',
                        'y': 'yellow',
                        'k': 'black',
                        'w': 'white'}
            try:
                color = colorMap[color]
            except KeyError:
                raise GraphException('invalid color abbreviation: %s' % color)
        try:
            return webcolors.css3_names_to_hex[color]
        except KeyError: # no color match
            raise GraphException('invalid color name: %s' % color)
    elif common.isListLike(color):
        percent = False
        for sub in color:
            if sub < 1:
                percent = True  
                break
        if percent:
            if len(color) == 1:
                color = [color, color, color]
            # convert to 0 100% values as strings with % symbol
            color = ['%s' % str(x*100) for x in color]
            color = [x + '%' for x in color]
            return webcolors.rgb_percent_to_hex(color)
        else: # assume integers
            return webcolors.rgb_to_hex(tuple(color))
    raise GraphException('invalid color specification: %s' % color)

#-------------------------------------------------------------------------------
class Graph(object):
    '''
    A music21.graph.Graph is an object that represents a visual graph or 
    plot, automating the creation and configuration of this graph in matplotlib.
    It is a low-level object that most music21 users do not need to call directly; 
    yet, as most graphs will take keyword arguments that specify the
    look of graphs, they are important to know about.

    The keyword arguments can be provided for configuration are: 
    alpha (which describes how transparent elements of the graph are), 
    colorBackgroundData, colorBackgroundFigure, colorGrid, title, 
    doneAction (see below), 
    figureSize, colors, tickFontSize, titleFontSize, labelFontSize, 
    fontFamily, marker, markerSize.

    Graph objects do not manipulate Streams or other music21 data; they only 
    manipulate raw data formatted for each Graph subclass, hence it is
    unlikely that users will call this class directly.

    The `doneAction` argument determines what happens after the graph 
    has been processed. Currently there are three options, 'write' creates
    a file on disk (this is the default), while 'show' opens an 
    interactive GUI browser.  The
    third option, None, does the processing but does not write any output.
    
    TODO: add color for individual points.
    '''

    def __init__(self, *args, **keywords):
        '''
        
        >>> a = graph.Graph(title='a graph of some data to be given soon', tickFontSize = 9)
        >>> a.setData(['some', 'arbitrary', 'data', 14, 9.04, None])
        '''
        _getExtendedModules()
        self.data = None
        self.fig = None
        # define a component dictionary for each axis
        self.axis = {}
        self.axisKeys = ['x', 'y']
        self.grid = True
        self._axisRangesAlreadySet = {}
        for axisKey in self.axisKeys:
            self._axisRangesAlreadySet[axisKey] = False

        if 'alpha' in keywords:
            self.alpha = keywords['alpha']
        else:
            self.alpha = .2

        if 'dpi' in keywords:
            self.dpi = keywords['dpi']
        else:
            self.dpi = None # do not set

        # set the color of the background data region
        if 'colorBackgroundData' in keywords:
            self.colorBackgroundData = keywords['colorBackgroundData']
        else:
            self.colorBackgroundData = '#ffffff'

        if 'colorBackgroundFigure' in keywords:
            self.colorBackgroundFigure = keywords['colorBackgroundFigure']
        else:
            # color options: #c7d2d4', '#babecf'
            self.colorBackgroundFigure = '#ffffff'

        if 'colorGrid' in keywords:
            self.colorGrid = keywords['colorGrid']
        else:
            self.colorGrid = '#666666'
        
        if 'title' in keywords:
            self.setTitle(keywords['title'])
        else:
            self.setTitle('Music21 Graph')
   
        if 'doneAction' in keywords:
            self.setDoneAction(keywords['doneAction'])
        else: # default is to write a file
            self.setDoneAction('write')

        if 'figureSize' in keywords:
            self.setFigureSize(keywords['figureSize'])
        else: # default is to write a file
            self.setFigureSize([6,6])

        if 'marker' in keywords:
            self.marker = keywords['marker']
        else:
            self.marker = 'o'
        
        if 'markerSize' in keywords:
            self.markerSize = keywords['marker']
        else:
            self.markerSize = 6
        
        # define a list of one or more colors
        # these will be applied cyclically to data prsented
        if 'colors' in keywords:
            self.colors = keywords['colors']
        else:
            self.colors = ['#605C7F', '#5c7f60', '#715c7f']

        # font info
        if 'tickFontSize' in keywords:
            self.tickFontSize = keywords['tickFontSize']
        else:
            self.tickFontSize = 8

        if 'titleFontSize' in keywords:
            self.titleFontSize = keywords['titleFontSize']
        else:
            self.titleFontSize = 12

        if 'labelFontSize' in keywords:
            self.labelFontSize = keywords['labelFontSize']
        else:
            self.labelFontSize = 10

        if 'fontFamily' in keywords:
            self.fontFamily = keywords['fontFamily']
        else:
            self.fontFamily = 'serif'

        self.hideXGrid = False
        if 'hideXGrid' in keywords:
            self.hideXGrid = keywords['hideXGrid']
        self.hideYGrid = False
        if 'hideYGrid' in keywords:
            self.hideYGrid = keywords['hideYGrid']

        self.xTickLabelRotation = 0
        self.xTickLabelHorizontalAlignment = 'center'
        self.xTickLabelVerticalAlignment = 'center'

        #self.hideYTick = True
        #self.hideXTick = True

    def _axisInit(self):
        for ax in self.axisKeys:
            self.axis[ax] = {}
            self.axis[ax]['range'] = None

    def _getFigure(self):
        '''
        Configure and return a figure object -- does nothing in the abstract class
        '''
        pass

    def setData(self, data):
        self.data = data

    def setTitle(self, title):
        self.title = title

    def setFigureSize(self, figSize):
        '''
        Set the figure size as an x,y pair. 
        
        Scales all graph components but because of matplotlib limitations
        (esp. on 3d graphs) no all labels scale properly. 
        '''
        self.figureSize = figSize

    def setDoneAction(self, action):
        '''
        sets what should happen when the graph is created (see docs above)
        default is 'write'.
        '''
        if action in ['show', 'write', None]:
            self.doneAction = action
        else:
            raise GraphException('not such done action: %s' % action)

    def setTicks(self, axisKey, pairs):
        '''
        Set the tick-labels for a given graph or plot's axisKey
        (generally 'x', and 'y') with a set of pairs
        
        Pairs are tuples of positions and labels.

        N.B. -- both 'x' and 'y' ticks have to be set in
        order to get matplotlib to display either...
        '''
        if pairs != None:
            positions = []
            labels = []
            # ticks are value, label pairs
            for value, label in pairs:
                positions.append(value)
                labels.append(label)
            #environLocal.printDebug(['got labels', labels])
            self.axis[axisKey]['ticks'] = positions, labels

    def setIntegerTicksFromData(self, unsortedData, axisKey = 'y', dataSteps = 8):
        '''
        Set the ticks for an axis (usually 'y') given the data
        '''
        maxData = max(unsortedData)
        yTicks = []
        yTickStep = int(round(maxData / (dataSteps+0.0)))
        if yTickStep <= 1:
            yTickStep = 2
        for y in range(0, maxData + 1, yTickStep):
            yTicks.append([y, '%s' % y])
        yTicks.sort()
        positions = []
        labels = []

        for value, label in yTicks:
            positions.append(value)
            labels.append(label)

        self.axis[axisKey]['ticks'] = positions, labels
        

    def setAxisRange(self, axisKey, valueRange, paddingFraction =.1):
        '''
        Set the range for the axis for a given axis key
        (generally, 'x', or 'y')
        
        ValueRange is a two-element tuple of the lowest
        number and the highest.
        
        By default there is a padding of 10% of the range
        in either direction.  Set paddingFraction = 0 to
        eliminate this shift
        '''
        
        if axisKey not in self.axisKeys:
            raise GraphException('No such axis exists: %s' % axisKey)
        # find a shift
        if paddingFraction != 0:
            totalRange = valueRange[1] - valueRange[0]
            shift = totalRange * paddingFraction # add 10 percent of range
        else:
            shift = 0
        # set range with shift
        self.axis[axisKey]['range'] = (valueRange[0]-shift,
                                       valueRange[1]+shift)
        
        self._axisRangesAlreadySet[axisKey] = True

    def setAxisLabel(self, axisKey, label):
        if axisKey not in self.axisKeys:
            raise GraphException('No such axis exists: %s' % axisKey)
        self.axis[axisKey]['label'] = label

    def _adjustAxisSpines(self, ax, leftBottom=False):
        '''Remove the right and left spines from the diagram
        '''
        for loc, spine in ax.spines.items():
            if loc in ['left','bottom']:
                if leftBottom:
                    spine.set_color('none') # don't draw spine
                # this pushes them outward in an interesting way
                #spine.set_position(('outward',10)) # outward by 10 points
            elif loc in ['right','top']:
                spine.set_color('none') # don't draw spine
            else:
                raise ValueError('unknown spine location: %s'%loc)

        # remove top and right ticks
        for i, line in enumerate(ax.get_xticklines() + ax.get_yticklines()):
            if i % 2 == 1:   # odd indices
                line.set_visible(False)
            else:
                if leftBottom:
                    line.set_visible(False)

    def _applyFormatting(self, ax):
        '''Apply formatting to the Axes container and Figure instance.  
        '''
        #environLocal.printDebug('calling _applyFormatting')

        rect = ax.axesPatch
        # this sets the color of the main data presentation window
        rect.set_facecolor(getColor(self.colorBackgroundData))
        # this does not do anything yet
        # rect.set_edgecolor(getColor('red'))

        for axis in self.axisKeys:
            if self.axis[axis]['range'] != None:
                # for 2d graphs
                if axis == 'x' and len(self.axisKeys) == 2:
                    ax.set_xlim(*self.axis[axis]['range'])
                elif axis == 'y' and len(self.axisKeys) == 2:
                    ax.set_ylim(*self.axis[axis]['range'])
                elif axis == 'z' and len(self.axisKeys) == 2:
                    ax.set_zlim(*self.axis[axis]['range'])
                # for 3d graphs
                elif axis == 'x' and len(self.axisKeys) == 3:
                    ax.set_xlim3d(*self.axis[axis]['range'])
                elif axis == 'y' and len(self.axisKeys) == 3:
                    ax.set_ylim3d(*self.axis[axis]['range'])
                elif axis == 'z' and len(self.axisKeys) == 3:
                    ax.set_zlim3d(*self.axis[axis]['range'])

            if 'label' in self.axis[axis]:
                if self.axis[axis]['label'] != None:
                    if axis == 'x':
                        ax.set_xlabel(self.axis[axis]['label'],
                        fontsize=self.labelFontSize, family=self.fontFamily)
                    elif axis == 'y':
                        ax.set_ylabel(self.axis[axis]['label'],
                        fontsize=self.labelFontSize, family=self.fontFamily,
                        rotation='horizontal')
                    elif axis == 'z':
                        ax.set_zlabel(self.axis[axis]['label'],
                        fontsize=self.labelFontSize, family=self.fontFamily)

            if 'scale' in self.axis[axis]:
                if self.axis[axis]['scale'] != None:
                    if axis == 'x':
                        ax.set_xscale(self.axis[axis]['scale'])
                    elif axis == 'y':
                        ax.set_yscale(self.axis[axis]['scale'])
                    elif axis == 'z':
                        ax.set_zscale(self.axis[axis]['scale'])

            if 'ticks' in self.axis[axis]:
                if axis == 'x':
                    # note: this problem needs to be update to use the
                    # same format as y, below
                    #plt.xticks(*self.axis[axis]['ticks'], fontsize=7)

                    if 'ticks' in self.axis[axis]:
                        values, labels = self.axis[axis]['ticks']
                        #environLocal.printDebug(['x tick labels, x tick values', labels, values])
                        ax.set_xticks(values)
                        # using center alignment to account for odd spacing in 
                        # accidentals
                        #environLocal.printDebug(['setting labels', labels])
                        ax.set_xticklabels(labels, fontsize=self.tickFontSize,
                            family=self.fontFamily, 
                            horizontalalignment=self.xTickLabelHorizontalAlignment, verticalalignment=self.xTickLabelVerticalAlignment, 
                            rotation=self.xTickLabelRotation,
                            y=-.01)

                elif axis == 'y':
                    # this is the old way ticks were set:
                    #plt.yticks(*self.axis[axis]['ticks'])
                    # new way:
                    if 'ticks' in self.axis[axis]:
                        values, labels = self.axis[axis]['ticks']
                        #environLocal.printDebug(['y tick labels, y tick values', labels, values])
                        ax.set_yticks(values)
                        ax.set_yticklabels(labels, fontsize=self.tickFontSize,
                            family=self.fontFamily,
                            horizontalalignment='right', verticalalignment='center')
            else: # apply some default formatting to default ticks
                if axis == 'x':
                    ax.set_xticklabels(ax.get_xticks(),
                        fontsize=self.tickFontSize, family=self.fontFamily) 
                elif axis == 'y':
                    ax.set_yticklabels(ax.get_yticks(),
                        fontsize=self.tickFontSize, family=self.fontFamily) 


        if self.title:
            ax.set_title(self.title, fontsize=self.titleFontSize, family=self.fontFamily)

        if self.grid:
            if self.colorGrid is not None: # None is another way to hide grid
                ax.grid(True, which='major', color=getColor(self.colorGrid))
        # provide control for each grid line
        if self.hideYGrid:
            ax.yaxis.grid(False)
        if self.hideXGrid:
            ax.xaxis.grid(False)

        # right and top must be larger
        # this does not work right yet
        #self.fig.subplots_adjust(left=1, bottom=1, right=2, top=2)

        # this figure instance is created in the subclased process() method
        # set total size of figure
        self.fig.set_figwidth(self.figureSize[0])
        self.fig.set_figheight(self.figureSize[1])

#         ax.set_xscale('linear')
#         ax.set_yscale('linear')
#         ax.set_aspect('normal')

    def process(self):
        '''process data and prepare plot'''
        pass

    #---------------------------------------------------------------------------
    def done(self, fp=None):
        '''Implement the desired doneAction, after data processing
        '''
        if self.doneAction == 'show':
            self.show()
        elif self.doneAction == 'write':
            self.write(fp)
        elif self.doneAction == None:
            pass

    def show(self):
        '''
        Calls the show() method of the matplotlib plot. 
        For most matplotlib back ends, this will open 
        a GUI window with the desired graph.
        '''
        extm = _getExtendedModules() #@UnusedVariable
        extm.plt.show()

    def write(self, fp=None):
        '''
        Writes the graph to a file. If no file path is given, a temporary file is used. 
        '''
        if fp == None:
            fp = environLocal.getTempFile('.png')
        #print _MOD, fp
        if self.dpi != None:
            self.fig.savefig(fp, facecolor=getColor(self.colorBackgroundFigure),      
                             edgecolor=getColor(self.colorBackgroundFigure),
                              dpi=self.dpi)
        else:
            self.fig.savefig(fp, facecolor=getColor(self.colorBackgroundFigure),      
                             edgecolor=getColor(self.colorBackgroundFigure))

        if common.runningUnderIPython() is not True:
            environLocal.launch('png', fp)




class GraphNetworxGraph(Graph):
    ''' 
    Grid a networkx graph -- which is a graph of nodes and edges.
    Requires the optional networkx module.
    
    '''
    _DOC_ATTR = {
        'networkxGraph' : '''An instance of a networkx graph object.'''
    }

#     
#     >>> #_DOCS_SHOW g = graph.GraphNetworxGraph()
# 
#     .. image:: images/GraphNetworxGraph.*
#         :width: 600

    def __init__(self, *args, **keywords):
        Graph.__init__(self, *args, **keywords)
        extm = _getExtendedModules() 
        self.axisKeys = ['x', 'y']
        self._axisInit()

        if 'figureSize' not in keywords:
            self.setFigureSize([6, 6])
        if 'title' not in keywords:
            self.setTitle('Network Plot')

        self.networkxGraph = None
        if 'networkxGraph' in keywords:
            self.networkxGraph = keywords['networkxGraph']            
        elif extm.networkx is not None: # if we have this module
            # testing default; temporary
            try:
                g = extm.networkx.Graph()
#             g.add_edge('a','b',weight=1.0)
#             g.add_edge('b','c',weight=0.6)
#             g.add_edge('c','d',weight=0.2)
#             g.add_edge('d','e',weight=0.6)
                self.networkxGraph = g
            except NameError: 
                pass # keep as None

    def process(self):
        extm = _getExtendedModules()
        plt = extm.plt
        networkx = extm.networkx
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        ax = self.fig.add_subplot(1, 1, 1)

        # positions for all nodes
        # positions are stored in the networkx graph as a pos attribute
        posNodes = {}
        posNodeLabels = {}
        # returns a data dictionary
        for nId, nData in self.networkxGraph.nodes(data=True):
            posNodes[nId] = nData['pos']
            # shift labels off center of nodes
            posNodeLabels[nId] = (nData['pos'][0]+.125, nData['pos'][1])

        #environLocal.printDebug(['get position', posNodes])
        #posNodes = networkx.spring_layout(self.networkxGraph, weighted=True) 
        # draw nodes
        networkx.draw_networkx_nodes(self.networkxGraph, posNodes, 
            node_size=300, ax=ax, node_color='#605C7F', alpha=.5)

        for (u,v,d) in self.networkxGraph.edges(data=True):
            environLocal.printDebug(['GraphNetworxGraph', (u,v,d)])
            #print (u,v,d)
            # adding one at a time to permit individual alpha settings
            edgelist = [(u,v)]
            networkx.draw_networkx_edges(self.networkxGraph, posNodes, edgelist=edgelist, width=2, style=d['style'], 
            edge_color='#666666', alpha=d['weight'], ax=ax)
        
        # labels
        networkx.draw_networkx_labels(self.networkxGraph, posNodeLabels, 
            font_size=self.labelFontSize, 
            font_family=self.fontFamily, font_color='#000000',
            ax=ax)

        #remove all labels
        self.setAxisLabel('y', '')
        self.setAxisLabel('x', '')
        self.setTicks('y', [])
        self.setTicks('x', [])
        # turn off grid
        self.grid = False
        # standard procedures
        self._adjustAxisSpines(ax, leftBottom=True)
        self._applyFormatting(ax)
        self.done()





class GraphColorGrid(Graph):
    ''' Grid of discrete colored "blocks" to visualize results of a windowed analysis routine.
    
    Data is provided as a list of lists of colors, where colors are specified as a hex triplet, or the common HTML color codes, and based on analysis-specific mapping of colors to results.
    
    
    
    >>> #_DOCS_SHOW g = graph.GraphColorGrid()
    >>> g = graph.GraphColorGrid(doneAction=None) #_DOCS_HIDE
    >>> data = [['#55FF00', '#9b0000', '#009b00'], ['#FFD600', '#FF5600'], ['#201a2b', '#8f73bf', '#a080d5', '#403355', '#999999']]
    >>> g.setData(data)
    >>> g.process()

    .. image:: images/GraphColorGrid.*
        :width: 600
    '''
    def __init__(self, *args, **keywords):
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

        if 'figureSize' not in keywords:
            self.setFigureSize([9, 6])
                
    def process(self):
        extm = _getExtendedModules() 
        plt = extm.plt

        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        self.fig.subplots_adjust(left=0.15)   
        axTop = self.fig.add_subplot(1, 1, 1)
        # do not need grid for outer container

        # these approaches do not work:
        # adjust face color of axTop independently
        # this sets the color of the main data presentation window
        #axTop.axesPatch.set_facecolor('#000000')

        # axTop.bar([.5], [1], 1, color=['#000000'], linewidth=.5, edgecolor='#111111')
        
        rowCount = len(self.data)

        for i in range(rowCount):
            positions = []
            heights = []
            subColors = []
            
            for j in range(len(self.data[i])):
                positions.append((1/2)+j)
                # collect colors in a list to set all at once
                subColors.append(self.data[i][j])
                #correlations.append(float(self.data[i][j][2]))
                heights.append(1)
            
            # add a new subplot for each row    
            ax = self.fig.add_subplot(rowCount, 1, len(self.data)-i)

            # linewidth: .1 is the thinnest possible
            # antialiased = false, for small diagrams, provides tighter images
            ax.bar(positions, heights, 1, color=subColors, linewidth=.3, edgecolor='#000000', antialiased=False)

            # remove spines from each bar plot; cause excessive thickness
            for unused_loc, spine in ax.spines.items():
                #spine.set_color('none') # don't draw spine
                spine.set_linewidth(.3) 
                spine.set_color('#000000') 
                spine.set_alpha(1) 

            # remove all ticks for subplots
            for j, line in enumerate(ax.get_xticklines() + ax.get_yticklines()):
                line.set_visible(False)
            ax.set_yticklabels([""]*len(ax.get_yticklabels()))
            ax.set_xticklabels([""]*len(ax.get_xticklabels()))
            # this is the shifting the visible bars; may not be necessary
            ax.set_xlim([0,len(self.data[i])])
            
            # these do not seem to do anything
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)


        # adjust space between the bars
        # .1 is about the smallest that gives some space
        if rowCount > 12:
            self.fig.subplots_adjust(hspace=0)
        else:
            self.fig.subplots_adjust(hspace=.1)

        self.setAxisRange('x', range(rowCount), 0)
        # turn off grid
        self.grid = False
        # standard procedures
        self._adjustAxisSpines(axTop, leftBottom=True)
        self._applyFormatting(axTop)
        self.done()


class GraphColorGridLegend(Graph):
    ''' Grid of discrete colored "blocks" where each block can be labeled
    
    Data is provided as a list of lists of colors, where colors are specified as a hex triplet, or the common HTML color codes, and based on analysis-specific mapping of colors to results.
    
    
    >>> #_DOCS_SHOW g = graph.GraphColorGridLegend()
    >>> g = graph.GraphColorGridLegend(doneAction=None) #_DOCS_HIDE
    >>> data = []
    >>> data.append(('Major', [('C#', '#00AA55'), ('D-', '#5600FF'), ('G#', '#2B00FF')]))
    >>> data.append(('Minor', [('C#', '#004600'), ('D-', '#00009b'), ('G#', '#00009B')]))
    >>> g.setData(data)
    >>> g.process()

    .. image:: images/GraphColorGridLegend.*
        :width: 600

    '''

#     >>> data = [('a', [('q', '#525252'), ('r', '#5f5f5f'), ('s', '#797979')]),
#                 ('b', [('t', '#858585'), ('u', '#00ff00'), ('v', '#6c6c6c')]), ('c', [('w', '#8c8c8c'), ('x', '#8c8c8c'), ('y', '#6c6c6c')])

    def __init__(self, *args, **keywords):
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

        if 'figureSize' not in keywords:
            self.setFigureSize([5, 1.5])
        if 'title' not in keywords:
            self.setTitle('Legend')
                
    def process(self):
        extm = _getExtendedModules()
        plt = extm.plt

        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()

        axTop = self.fig.add_subplot(1, 1, 1)
        
        for i in range(len(self.data)):
            rowLabel = self.data[i][0]
            rowData = self.data[i][1]
            #environLocal.printDebug(['rowLabel', rowLabel, i])

            positions = []
            heights = []
            subColors = []
            
            for j in range(len(rowData)):
                positions.append(.5+j)
                subColors.append(rowData[j][1]) # second value is colors
                heights.append(1)
            
            # add a new subplot for each row    
            posTriple = (len(self.data), 1, i+1)
            #environLocal.printDebug(['posTriple', posTriple])
            ax = self.fig.add_subplot(*posTriple)
            # 1 here is width
            ax.bar(positions, heights, 1, color=subColors, linewidth=.3, edgecolor='#000000')
            
            # remove spines from each bar plot; cause excessive thickness
            for unused_loc, spine in ax.spines.items():
                #spine.set_color('none') # don't draw spine
                spine.set_linewidth(.3) 
                spine.set_color('#000000') 

            # remove all ticks for subplots
            for j, line in enumerate(ax.get_xticklines() + ax.get_yticklines()):
                line.set_visible(False)

            # need one label for each left side; .5 is in the middle
            ax.set_yticks([.5])
            ax.set_yticklabels([rowLabel], fontsize=self.tickFontSize, 
                family=self.fontFamily, horizontalalignment='right', 
                verticalalignment='center') # one label for one tick

            # need a label for each bars
            ax.set_xticks([x + 1 for x in range(len(rowData))])
            # get labels from row data; first of pair
            # need to push y down as need bottom alignment for lower case
            ax.set_xticklabels(
                [_substituteAccidentalSymbols(x) for x, unused_y in rowData], 
                fontsize=self.tickFontSize, family=self.fontFamily, horizontalalignment='center', verticalalignment='center', 
                y=-.4)
            # this is the scaling to see all bars; not necessary
            ax.set_xlim([.5, len(rowData)+.5])
            
        self.setAxisRange('x', range(len(self.data)), 0)

        for j, line in enumerate(axTop.get_xticklines() + axTop.get_yticklines()):
            line.set_visible(False)

        # sets the space between subplots
        # top and bottom here push diagram more toward center of frame
        # may be useful in other graphs
        # , 
        self.fig.subplots_adjust(hspace=1.5, top=.75, bottom=.2)

        self.setAxisLabel('y', '')
        self.setAxisLabel('x', '')
        self.setTicks('y', [])
        self.setTicks('x', [])

        # standard procedures
        self._adjustAxisSpines(axTop, leftBottom=True)
        self._applyFormatting(axTop)
        self.done()



class GraphHorizontalBar(Graph):
    def __init__(self, *args, **keywords):
        '''Numerous horizontal bars in discrete channels, where bars can be incomplete and/or overlap.

        Data provided is a list of pairs, where the first value becomes the key, the second value is a list of x-start, x-length values.

        
        >>> #_DOCS_SHOW a = graph.GraphHorizontalBar(doneAction='show')
        >>> a = graph.GraphHorizontalBar(doneAction=None)  #_DOCS_HIDE
        >>> data = [('Chopin', [(1810, 1849-1810)]), ('Schumanns', [(1810, 1856-1810), (1819, 1896-1819)]), ('Brahms', [(1833, 1897-1833)])]
        >>> a.setData(data)
        >>> a.process()

        .. image:: images/GraphHorizontalBar.*
            :width: 600

        '''
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

        self._barSpace = 8
        self._margin = 2
        self._barHeight = self._barSpace - (self._margin * 2)

        # if figure size has not been defined, configure
        if 'figureSize' not in keywords:
            self.setFigureSize([10,4])
        if 'alpha' not in keywords:
            self.alpha = .6

    def process(self):
        extm  = _getExtendedModules()
        plt = extm.plt

        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        self.fig.subplots_adjust(left=0.15)   
        ax = self.fig.add_subplot(1, 1, 1)

        yPos = 0
        xPoints = [] # store all to find min/max
        yTicks = [] # a list of label, value pairs
        xTicks = []

        keys = []
        i = 0
        # TODO: check data orientation; flips in some cases
        for key, points in self.data:
            keys.append(key)
            # provide a list of start, end points;
            # then start y position, bar height
            faceColor = getColor(self.colors[i % len(self.colors)])            
            
            ax.broken_barh(points, (yPos + self._margin, self._barHeight),
                        facecolors=faceColor, alpha=self.alpha)
            for xStart, xLen in points:
                xEnd = xStart + xLen
                for x in [xStart, xEnd]:
                    if x not in xPoints:
                        xPoints.append(x)
            # ticks are value, label
            yTicks.append([yPos + self._barSpace * .5, key])
            #yTicks.append([key, yPos + self._barSpace * .5])
            yPos += self._barSpace
            i += 1

        xMin = min(xPoints)
        xMax = max(xPoints) 
        xRange = xMax - xMin
        #environLocal.printDebug(['got xMin, xMax for points', xMin, xMax, ])

        self.setAxisRange('y', (0, len(keys) * self._barSpace))
        self.setAxisRange('x', (xMin, xMax))
        self.setTicks('y', yTicks)  

        # first, see if ticks have been set externally
        if 'ticks' in self.axis['x'] and len(self.axis['x']['ticks']) == 0:
            rangeStep = int(xMin+int(round(xRange/10)))
            if rangeStep == 0:
                rangeStep = 1
            for x in range(int(math.floor(xMin)), 
                           int(round(math.ceil(xMax))), 
                           rangeStep):
                xTicks.append([x, '%s' % x])
            self.setTicks('x', xTicks)  

        #environLocal.printDebug([yTicks])
        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()



class GraphHorizontalBarWeighted(Graph):
    def __init__(self, *args, **keywords):
        '''
        Numerous horizontal bars in discrete channels, 
        where bars can be incomplete and/or overlap, and 
        can have different heights and colors within their 
        respective channel.
        '''
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

        self._barSpace = 8 
        self._margin = .25 # was 8; determines space between channels
        # this is a maximum value
        self._barHeight = self._barSpace - (self._margin * 2)

        # if figure size has not been defined, configure
        if 'figureSize' not in keywords:
            self.setFigureSize([10,4])
        # this default alpha is used if not specified per bar
        if 'alpha' not in keywords:
            self.alpha = 1

# example data
#         data =  [
#         ('Violins',  [(3, 5, 1, '#fff000'), (1, 12, .2, '#3ff203')]  ), 
#         ('Celli',    [(2, 7, .2, '#0ff302'), (10, 3, .6, '#ff0000', 1)]  ), 
#         ('Clarinet', [(5, 1, .5, '#3ff203')]  ),
#         ('Flute',    [(5, 1, .1, '#00ff00'), (7, 20, .3, '#00ff88')]  ),
#                 ]

    def process(self):
        extm = _getExtendedModules()
        plt = extm.plt

        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        # might need more space here for larger y-axis labels
        self.fig.subplots_adjust(left=0.15)   
        ax = self.fig.add_subplot(1, 1, 1)

        yPos = 0
        xPoints = [] # store all to find min/max
        yTicks = [] # a list of label, value pairs
        #xTicks = []

        keys = []
        i = 0
        # reversing data to present in order
        self.data = list(self.data)
        self.data.reverse()
        for key, points in self.data:
            keys.append(key)
            xRanges = []
            yRanges = []
            alphas = []
            colors = []
            for i, data in enumerate(points):
                if len(data) == 3:
                    x, span, heightScalar = data
                    color = self.colors[i%len(self.colors)]
                    alpha = self.alpha
                    yShift = 0 # between -1 and 1
                elif len(data) == 4:
                    x, span, heightScalar, color = data
                    alpha = self.alpha
                    yShift = 0 # between -1 and 1
                elif len(data) == 5:
                    x, span, heightScalar, color, alpha = data
                    yShift = 0 # between -1 and 1
                elif len(data) == 6:
                    x, span, heightScalar, color, alpha, yShift = data
                # filter color value
                color = getColor(color)
                # add to x ranges
                xRanges.append((x, span))
                colors.append(color)
                alphas.append(alpha)
                # x points used to get x ticks
                if x not in xPoints:
                    xPoints.append(x)
                if x+span not in xPoints:
                    xPoints.append(x+span)

                # TODO: add high/low shift to position w/n range
                # provide a list of start, end points;
                # then start y position, bar height
                h = self._barHeight*heightScalar
                yAdjust = (self._barHeight-h) * .5
                yShiftUnit = self._barHeight * (1-heightScalar) * .5
                yRanges.append((yPos + 
                    self._margin + yAdjust + (yShiftUnit*yShift), h))

            for i, xRange in enumerate(xRanges):
                # note: can get ride of bounding lines by providing
                # linewidth=0, however, this may leave gaps in adjacent regions
                ax.broken_barh([xRange], yRanges[i],
                        facecolors=colors[i], alpha=alphas[i], 
                        edgecolor=colors[i])

            # ticks are value, label
            yTicks.append([yPos + self._barSpace * .5, key])
            #yTicks.append([key, yPos + self._barSpace * .5])
            yPos += self._barSpace
            i += 1

        xMin = min(xPoints)
        xMax = max(xPoints) 
        xRange = xMax - xMin
        #environLocal.printDebug(['got xMin, xMax for points', xMin, xMax, ])

        # NOTE: these pad values determine extra space inside the graph that
        # is not filled with data, a sort of inner margin
        self.setAxisRange('y', (0, len(keys) * self._barSpace), paddingFraction=.05)
        self.setAxisRange('x', (xMin, xMax), paddingFraction=.01)
        self.setTicks('y', yTicks)  

        # first, see if ticks have been set externally
#         if 'ticks' in self.axis['x'] and len(self.axis['x']['ticks']) == 0:
#             rangeStep = int(xMin+int(round(xRange/10)))
#             if rangeStep == 0:
#                 rangeStep = 1
#             for x in range(int(math.floor(xMin)), 
#                            int(round(math.ceil(xMax))), 
#                            rangeStep):
#                 xTicks.append([x, '%s' % x])
#                 self.setTicks('x', xTicks)  
#         environLocal.printDebug(['xTicks', xTicks])

        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()



class GraphScatterWeighted(Graph):
    '''A scatter plot where points are scaled in size to represent the number of values stored within.

    
    >>> #_DOCS_SHOW g = graph.GraphScatterWeighted()
    >>> g = graph.GraphScatterWeighted(doneAction=None) #_DOCS_HIDE
    >>> data = [(23, 15, 234), (10, 23, 12), (4, 23, 5), (15, 18, 120)]
    >>> g.setData(data)
    >>> g.process()

    .. image:: images/GraphScatterWeighted.*
        :width: 600

    '''

    def __init__(self, *args, **keywords):
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

        # if figure size has not been defined, configure
        if 'figureSize' not in keywords:
            self.setFigureSize([5,5])
        if 'alpha' not in keywords:
            self.alpha = .6

        self._maxDiameter = 1.25
        self._minDiameter = .25
        self._rangeDiameter = self._maxDiameter - self._minDiameter

    def process(self):
        extm = _getExtendedModules()
        plt = extm.plt
        patches = extm.patches

        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        # these need to be equal to maintain circle scatter points
        self.fig.subplots_adjust(left=0.15, bottom=0.15)
        ax = self.fig.add_subplot(1, 1, 1)

        # need to filter data to weight z values
        xList = [x for x, unused_y, unused_z in self.data]
        yList = [y for unused_x, y, unused_z in self.data]
        zList = [z for unused_x, unused_y, z in self.data]

        xMax = max(xList)
        xMin = min(xList)
        xRange = float(xMax - xMin)

        yMax = max(yList)
        yMin = min(yList)
        yRange = float(yMax - yMin)

        zMax = max(zList)
        zMin = min(zList)
        zRange = float(zMax - zMin)

        # if xRange and yRange are not the same, the resulting circle,
        # when drawn, will be distorted into an ellipse. to counter this
        # we need to get a ratio to scale the width of the elips
        xDistort = 1
        yDistort = 1
        if xRange > yRange:
            yDistort = float(yRange)/xRange
        elif yRange > xRange:
            xDistort = float(xRange)/yRange
        #environLocal.printDebug(['xDistort, yDistort', xDistort, yDistort])

        zNorm = []
        for z in zList:
            if z == 0:
                zNorm.append([0, 0])
            else:
                # this will make the minimum scalar 0 when z is zero
                if zRange != 0:
                    scalar = (z-zMin) / zRange # shifted part / range
                else:
                    scalar = .5 # if all the same size, use .5
                scaled = self._minDiameter + (self._rangeDiameter * scalar)
                zNorm.append([scaled, scalar])

        # draw elipses
        for i in range(len(self.data)):
            x = xList[i]
            y = yList[i]
            z, unused_zScalar = zNorm[i] # normalized values

            width=z*xDistort
            height=z*yDistort
            e = patches.Ellipse(xy=(x, y), width=width, height=height)
            #e = patches.Circle(xy=(x, y), radius=z)
            ax.add_artist(e)

            e.set_clip_box(ax.bbox)
            #e.set_alpha(self.alpha*zScalar)
            e.set_alpha(self.alpha)
            e.set_facecolor(getColor(self.colors[i%len(self.colors)])) 
            # can do this here
            #environLocal.printDebug([e])

            # only show label if min if greater than zNorm min
            if zList[i] > 1:
                # xdistort does not seem to
                # width shift can be between .1 and .25
                # width is already shifted by distort
                # use half of width == radius
                ax.text(x+((width*.5)+(.05*xDistort)),
                        y+.10,
                        "%s" % zList[i], size=6,
                        va="baseline", ha="left", multialignment="left")

        self.setAxisRange('y', (yMin, yMax),)
        self.setAxisRange('x', (xMin, xMax),)

        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()


class GraphScatter(Graph):
    '''Graph two parameters in a scatter plot. Data representation is a list of points of values. 

    
    >>> #_DOCS_SHOW g = graph.GraphScatter()
    >>> g = graph.GraphScatter(doneAction=None) #_DOCS_HIDE
    >>> data = [(x, x*x) for x in range(50)]
    >>> g.setData(data)
    >>> g.process()

    .. image:: images/GraphScatter.*
        :width: 600
    '''

    def __init__(self, *args, **keywords):
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

    def process(self):
        '''
        runs the data through the processor and if doneAction == 'show' (default), show the graph
        '''
        extm = _getExtendedModules()
        plt = extm.plt

        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        self.fig.subplots_adjust(left=0.15)
        ax = self.fig.add_subplot(1, 1, 1)
        xValues = []
        yValues = []
        i = 0
        for row in self.data:
            if len(row) < 2:
                raise GraphException("Need at least two points for a graph data object!")
            x = row[0]
            y = row[1]
            xValues.append(x)
            yValues.append(y)
        xValues.sort()
        yValues.sort()

        for row in self.data:
            x = row[0]
            y = row[1]
            marker = self.marker
            color = getColor(self.colors[i%len(self.colors)])
            alpha = self.alpha
            markerSize = self.markerSize
            if len(row) >= 3:
                displayData = row[2]
                if 'color' in displayData:
                    color = displayData['color']
                if 'marker' in displayData:
                    marker = displayData['marker']
                if 'alpha' in displayData:
                    alpha = displayData['alpha']
                if 'markerSize' in displayData:
                    markerSize = displayData['markerSize']
                    
            ax.plot(x, y, marker, color=color, alpha=alpha, ms=markerSize)
            i += 1
        # values are sorted, so no need to use max/min
        if not self._axisRangesAlreadySet['y']:
            self.setAxisRange('y', (yValues[0], yValues[-1]))
        if not self._axisRangesAlreadySet['x']:
            self.setAxisRange('x', (xValues[0], xValues[-1]))

        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()

class GraphHistogram(Graph):
    '''Graph the count of a single element.

    Data set is simply a list of x and y pairs, where there
    is only one of each x value, and y value is the count or magnitude
    of that value

    
    >>> import random
    >>> #_DOCS_SHOW g = graph.GraphHistogram()
    >>> g = graph.GraphHistogram(doneAction=None) #_DOCS_HIDE
    >>> data = [(x, random.choice(range(30))) for x in range(50)]
    >>> g.setData(data)
    >>> g.process()

    .. image:: images/GraphHistogram.*
        :width: 600

    '''

    def __init__(self, *args, **keywords):

        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()
        if 'binWidth' in keywords:
            self.binWidth = keywords['binWidth']
        else:
            self.binWidth = 0.8
            
        if 'alpha' in keywords:
            self.alpha = keywords['alpha']
        else:
            self.alpha = 0.8

    def process(self):
        extm = _getExtendedModules()
        plt = extm.plt

        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        self.fig.subplots_adjust(left=0.15)
        ax = self.fig.add_subplot(1, 1, 1)

        x = []
        y = []
        binWidth = self.binWidth
        color = getColor(self.colors[0])
        alpha = self.alpha
        for a,b in self.data:
            x.append(a)
            y.append(b)
        ax.bar(x, y, width = binWidth, alpha=alpha, color=color)

        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()



class GraphGroupedVerticalBar(Graph):
    '''Graph the count of on or more elements in vertical bars

    Data set is simply a list of x and y pairs, where there
    is only one of each x value, and y value is a list of values

    >>> from collections import OrderedDict
    >>> #_DOCS_SHOW g = graph.GraphGroupedVerticalBar()
    >>> g = graph.GraphGroupedVerticalBar(doneAction=None) #_DOCS_HIDE
    >>> lengths = OrderedDict( [('a', 3), ('b', 2), ('c', 1)] )
    >>> data = [('bar' + str(x), lengths) for x in range(3)]
    >>> data
    [('bar0', OrderedDict([('a', 3), ('b', 2), ('c', 1)])), ('bar1', OrderedDict([('a', 3), ('b', 2), ('c', 1)])), ('bar2', OrderedDict([('a', 3), ('b', 2), ('c', 1)]))]    
    >>> g.setData(data)
    >>> g.process()
    '''
    def __init__(self, *args, **keywords):
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()
        if 'roundDigits' in keywords:
            self.roundDigits = keywords['roundDigits']
        else:
            self.roundDigits = 1
        
        if 'groupLabelHeight' in keywords:
            self.groupLabelHeight = keywords['groupLabelHeight']
        else:
            self.groupLabelHeight = 0.0
            
        if 'binWidth' in keywords:
            self.binWidth = keywords['binWidth']
        else:
            self.binWidth = 1

    def labelBars(self, ax, rects):
        # attach some text labels
        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x()+rect.get_width()/2., height, '%s'%str(round(height, self.roundDigits)), ha='center', va='bottom', 
            fontsize=self.tickFontSize, family=self.fontFamily)

    def process(self):
        extm = _getExtendedModules()
        plt = extm.plt
        matplotlib = extm.matplotlib

        self.fig = plt.figure()
        self.fig.subplots_adjust(bottom=.3)
        ax = self.fig.add_subplot(1, 1, 1)

        # b value is a list of values for each bar
        for unused_a, b in self.data:
            barsPerGroup = len(b)
            # get for legend
            subLabels = sorted(b.keys())
            break
        
        binWidth = self.binWidth
        widthShift = binWidth / float(barsPerGroup)

        xVals = []
        yBundles = []
        for i, (unused_a, b) in enumerate(self.data):
            # create x vals from index values 
            xVals.append(i)
            yBundles.append([b[key] for key in sorted(b.keys())])

        rects = []
        for i in range(barsPerGroup):
            yVals = []
            for j, x in enumerate(xVals):
                # get position, then get bar group
                yVals.append(yBundles[j][i])
            xValsShifted = []
            #xLabels = []
            for x in xVals:
                xValsShifted.append(x + (widthShift * i))

            rect = ax.bar(xValsShifted, yVals, width=widthShift, alpha=.8,
                    color=getColor(self.colors[i % len(self.colors)]))
            rects.append(rect)

        colors = []
        for rect in rects:
            self.labelBars(ax, rect)
            colors.append(rect[0])

        font = matplotlib.font_manager.FontProperties(size=self.tickFontSize,
                         family=self.fontFamily) 
        ax.legend(colors, subLabels, prop=font)

        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()


class _Graph3DBars(Graph):
    '''Not functioning in all matplotlib versions
    '''
    def __init__(self, *args, **keywords):
        '''
        Graph multiple parallel bar graphs in 3D.

        Note: there is bug in matplotlib .99.0 that causes the units to be unusual here. 
        This is supposed to be fixed in a forthcoming release.

        Data definition:
        A dictionary where each key forms an array sequence along the z
        plane (which is depth)
        For each dictionary, a list of value pairs, where each pair is the
        (x, y) coordinates.
       
        >>> a = graph._Graph3DBars()
        '''
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y', 'z']
        self._axisInit()

    def process(self):
        extm = _getExtendedModules()
        plt = extm.plt
        
        self.fig = plt.figure()
        ax = extm.Axes3D(self.fig)

        zVals = self.data.keys()
        zVals.sort()

        yVals = []
        xVals = []
        for key in zVals:
            for i in range(len(self.data[key])):
                x, y = self.data[key][i]
                yVals.append(y)
                xVals.append(x)
        #environLocal.printDebug(['yVals', yVals])
        #environLocal.printDebug(['xVals', xVals])

        if self.axis['x']['range'] == None:
            self.axis['x']['range'] =  min(xVals), max(xVals)
        # swap y for z
        if self.axis['z']['range'] == None:
            self.axis['z']['range'] =  min(yVals), max(yVals)
        if self.axis['y']['range'] == None:
            self.axis['y']['range'] =  min(zVals), max(zVals)+1

        for z in range(*self.axis['y']['range']):
            #c = ['b', 'g', 'r', 'c', 'm'][z%5]
            # list of x values
            xs = [x for x, y in self.data[z]]
            # list of y values
            ys = [y for x, y in self.data[z]]
            # width=.1, color=c, alpha=self.alpha
            ax.bar(xs, ys, zs=z, zdir='y')

        self.setAxisLabel('x', 'x')
        self.setAxisLabel('y', 'y')
        self.setAxisLabel('z', 'z')

        #ax.set_xlabel('X')
        #ax.set_ylabel('Y')
        #ax.set_zlabel('Z')
        self._applyFormatting(ax)
        self.done()
   

class Graph3DPolygonBars(Graph):
    '''Graph multiple parallel bar graphs in 3D.

    This draws bars with polygons, a temporary alternative to using Graph3DBars, above.

    Note: Due to matplotib issue Axis ticks do not seem to be adjustable without distorting the graph.

    >>> import random
    >>> #_DOCS_SHOW g = graph.Graph3DPolygonBars()
    >>> g = graph.Graph3DPolygonBars(doneAction=None) #_DOCS_HIDE
    >>> data = {1:[], 2:[], 3:[]}
    >>> dk = list(data.keys())
    >>> for i in range(len(dk)):
    ...    q = [(x, random.choice(range(10*(i+1)))) for x in range(20)]
    ...    data[dk[i]] = q
    >>> g.setData(data)
    >>> g.process()

    .. image:: images/Graph3DPolygonBars.*
        :width: 600

    '''
    def __init__(self, *args, **keywords):
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y', 'z']
        self._axisInit()

        if 'barWidth' in keywords:
            self.barWidth = keywords['barWidth']
        else:
            self.barWidth = .1
        
        if 'useKeyValues' in keywords:
            self.useKeyValues = keywords['useKeyValues']
        else:
            self.useKeyValues = False
            
        if 'zeroFloor' in keywords:
            self.zeroFloor = keywords['zeroFloor']
        else:
            self.zeroFloor = False

    def process(self):
        extm = _getExtendedModules()
        plt = extm.plt
        matplotlib = extm.matplotlib
        Axes3D = extm.Axes3D
        collections = extm.collections
        
        cc = lambda arg: matplotlib.colors.colorConverter.to_rgba(getColor(arg),
                                alpha=self.alpha)
        self.fig = plt.figure()
        ax = Axes3D(self.fig)

        verts = []
        vertsColor = []
        q = 0
        zVals = list(self.data.keys())
        zVals.sort()

        colors = []
        while len(colors) < len(zVals):
            colors += self.colors
        colors = colors[:len(zVals)] # snip at length

        yVals = []
        xVals = []
        for key in zVals: 
            verts_i = []
            for i in range(len(self.data[key])):
                x, y = self.data[key][i]
                yVals.append(y)
                xVals.append(x)
                # this draws the bar manually
                verts_i.append([x-(self.barWidth*.5),0])
                verts_i.append([x-(self.barWidth*.5),y])
                verts_i.append([x+(self.barWidth*.5),y])
                verts_i.append([x+(self.barWidth*.5),0])
            verts.append(verts_i)      
            vertsColor.append(cc(colors[q%len(colors)]))
            q += 1

        # this actually appears as the w
        #g.setAxisRange('x', (xValues[0], xValues[-1]))
        self.setAxisRange('x', (min(xVals), max(xVals)))
        #environLocal.printDebug(['3d axis range, x:', min(xVals), max(xVals)])

        # z values here end up being height of the graph
        if self.zeroFloor is True:
            self.setAxisRange('z', (0, max(yVals)))
        else:
            self.setAxisRange('z', (min(yVals), max(yVals)))
        #environLocal.printDebug(['3d axis range, z (from y):', min(yVals), max(yVals)])

        # y values are the z of the graph, the depth
        self.setAxisRange('y', (min(zVals), max(zVals)))
        #environLocal.printDebug(['3d axis range, y (from z):', min(zVals), max(zVals)])

#         self.axis['x']['range'] =  min(xVals), max(xVals)
#         # swap y for z
#         self.axis['z']['range'] =  min(yVals), max(yVals)
#         # set y range for z here
#         self.axis['y']['range'] =  min(zVals), max(zVals)
           
        # this kinda works but does not adjust the ticks / scale range
        #self.axis['x']['scale'] = 'symlog'

        low, high = self.axis['y']['range']
        low = int(math.floor(low))
        high = int(math.ceil(high))
        
        if self.useKeyValues is True:
            zs = zVals
        else:
            zs = range(low, high+1)

        poly = collections.PolyCollection(verts, facecolors=vertsColor)
        poly.set_alpha(self.alpha)

        ax.add_collection3d(poly, zs=zs, zdir='y')
        self._applyFormatting(ax)
        self.done()






#-------------------------------------------------------------------------------
# graphing utilities that operate on streams

class PlotStream(object):
    '''Approaches to plotting and graphing a Stream. A base class from which Stream plotting Classes inherit.

    This class has a number of public attributes, but these are generally not intended for direct user application. The `data` attribute, for example, exposes the internal data format of this plotting routine for testing, but no effort is made to make this data useful outside of the context of the Plot.
    '''
    # the following static parameters are used to for matching this
    # plot based on user-requested string aguments
    # a string representation of the type of graph
    format = ''
    # store a list of parameters that are graphed
    values = []

    def __init__(self, streamObj, flatten=True, *args, **keywords):
        '''Provide a Stream as an arguement. If `flatten` is True, the Stream will automatically be flattened.
        '''
        #if not isinstance(streamObj, music21.stream.Stream):
        if not hasattr(streamObj, 'elements'):
            raise PlotStreamException('non-stream provided as argument: %s' % streamObj)
        self.streamObj = streamObj
        self.flatten = flatten
        self.data = None # store native data representation, useful for testing
        self.graph = None  # store instance of graph class here

        # store axis label type for time-based plots
        # either measure or offset
        self._axisLabelUsesMeasures = None

    #---------------------------------------------------------------------------
    def _extractChordDataOneAxis(self, fx, c):
        '''
        Look for Note-like attributes in a Chord. This is done by first 
        looking at the Chord, and then, if attributes are not found, looking at each pitch. 
        '''
        values = []
        value = None
        try:
            value = fx(c)
        except AttributeError:
            pass # do not try others
        if value is not None:
            values.append(value)

        if values == []: # still not set, get form chord
            for n in c:
                # try to get get values from note inside chords
                value = None
                try:
                    value = fx(n)
                except AttributeError:
                    break # do not try others
                if value is not None:
                    values.append(value)
        return values


    def _extractChordDataTwoAxis(self, fx, fy, c, matchPitchCount=False):
        xValues = []
        yValues = []
        x = None
        y = None

        for b in [(fx, x, xValues), (fy, y, yValues)]:
            #environLocal.printDebug(['b', b])
            f, target, dst = b
            try:
                target = f(c)
            except AttributeError:
                pass 
            if target is not None:
                dst.append(target)

        #environLocal.printDebug(['after looking at Chord:', 'xValues', xValues, 'yValues', yValues])
        # get form pitches only if cannot be gotten from chord;
        # this is necessary as pitches have an offset, but here we are likley
        # looking for chord offset, etc.

        if (xValues == [] and yValues == []): # still not set, get form chord
            bundleGroups = [(fx, x, xValues), (fy, y, yValues)]
            environLocal.printDebug(['trying to fill x + y'])
        # x values not set from pitch; get form chord
        elif (xValues == [] and yValues != []): # still not set, get form chord
            bundleGroups = [(fx, x, xValues)]
            #environLocal.printDebug(['trying to fill x'])
        # y values not set from pitch; get form chord
        elif (yValues == [] and xValues != []):
            bundleGroups = [(fy, y, yValues)]
            #environLocal.printDebug(['trying to fill y'])
        else:
            bundleGroups = []

        for b in bundleGroups:
            for n in c:
                x = None
                y = None
                f, target, dst = b
                try:
                    target = f(n)
                except AttributeError:
                    pass # must try others
                if target is not None:
                    dst.append(target)

        #environLocal.printDebug(['after looking at Pitch:', 'xValues', xValues, 'yValues', yValues])

        # if we only have one attribute form the Chord, and many from the 
        # Pitches, need to make the number of data points equal by 
        # duplicating data
        if matchPitchCount: 
            if len(xValues) == 1 and len(yValues) > 1:
                #environLocal.printDebug(['balancing x'])
                for i in range(len(yValues) - 1):
                    xValues.append(xValues[0])
            elif len(yValues) == 1 and len(xValues) > 1:
                #environLocal.printDebug(['balancing y'])
                for i in range(len(xValues) - 1):
                    yValues.append(yValues[0])

        return xValues, yValues




    def _extractData(self):
        '''Override in subclass
        '''
        return None

    def process(self):
        '''This will process all data, as well as call the done() method. 
        What happens when the done() is called is determined by the keyword argument `doneAction`; 
        options are 'show' (display immediately), 'write' (write the file to a supplied file path), 
        and None (do processing but do not write or show a graph).

        Subclass dependent data extracted is stored in the self.data attribute. 
        '''
        self.graph.process()

    def show(self):
        '''Call internal Graphs show() method independently of doneAction set and run with process()
        '''
        self.graph.show()

    def write(self, fp=None):
        '''Call internal Graphs write() method independently of doneAction set and run with process()
        '''
        self.graph.write(fp)


    #---------------------------------------------------------------------------
    def _getId(self):
        return '%s-%s' % (self.format, '-'.join(self.values))


    id = property(_getId, doc='''
        Each PlotStream has a unique id that consists of its format and a string that defines the parameters that are graphed.
        ''')

    #---------------------------------------------------------------------------
    def _axisLabelMeasureOrOffset(self):
        '''Return an axis label for measure or offset, depending on if measures are available.
        '''
        # look for this attribute; only want to do ticksOffset procedure once
        if self._axisLabelUsesMeasures is None:
            raise GraphException('call ticksOffset() first')
        # this parameter is set in 
        if self._axisLabelUsesMeasures:
            return 'Measure Number'
        else:
            return 'Offset'

    def _axisLabelQuarterLength(self, remap):
        '''Return an axis label for quarter length, showing whether or not values are remapped.
        '''
        if remap:
            return 'Quarter Length ($log_2$)'
        else:
            return 'Quarter Length'


    #---------------------------------------------------------------------------



    def _filterPitchLabel(self, ticks):
        '''Given a list of ticks, replace all labels with alternative/unicode symbols where necessary.

        '''
        #environLocal.printDebug(['calling filterPitchLabel', ticks])
        # this uses tex mathtext, which happens to define harp and flat
        # http://matplotlib.sourceforge.net/users/mathtext.html
        post = []
        for value, label in ticks:
            label = _substituteAccidentalSymbols(label)
            post.append([value, label])
            #post.append([value, unicode(label)])
        return post


    def ticksPitchClassUsage(self, pcMin=0, pcMax=11, showEnharmonic=True,
            blankLabelUnused=True, hideUnused=False):
        r'''
        Get ticks and labels for pitch classes.
        
        If `showEnharmonic` is `True` (default) then 
        when choosing whether to display as sharp or flat use
        the most commonly used enharmonic.

        
        >>> s = corpus.parse('bach/bwv324.xml')
        >>> s.analyze('key')
        <music21.key.Key of G major>
        >>> a = graph.PlotStream(s)
        >>> for position, noteName in a.ticksPitchClassUsage(hideUnused=True):
        ...            print (str(position) + " " + noteName)
        0 C
        2 D
        3 D$\sharp$
        4 E
        6 F$\sharp$
        7 G
        9 A
        11 B
        
        >>> s = corpus.parse('bach/bwv281.xml')
        >>> a = graph.PlotStream(s)
        >>> [x for x, y in a.ticksPitchClassUsage(showEnharmonic=True, hideUnused=True)]
        [0, 2, 3, 4, 5, 7, 9, 10, 11]
        >>> [x for x, y in a.ticksPitchClassUsage(showEnharmonic=True, blankLabelUnused=False)]
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        >>> s = stream.Stream()
        >>> for i in range(60, 84):
        ...    n = note.Note()
        ...    n.ps = i
        ...    s.append(n)
        >>> a = graph.PlotStream(s)
        >>> [x for x, y in a.ticksPitchClassUsage(showEnharmonic=True)]
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        OMIT_FROM_DOCS
        TODO: this ultimately needs to look at key signature/key to determine defaults for undefined notes.

        '''
        # keys are integers
        # pcCount = self.streamObj.pitchAttributeCount('pitchClass')
        # name strings are keys, and enharmonic are thus different
        nameCount = self.streamObj.pitchAttributeCount('name')
        ticks = []
        for i in range(pcMin, pcMax+1):
            p = pitch.Pitch()
            p.ps = i
            weights = [] # a list of pairs of count/label
            for key in nameCount:
                if pitch.Pitch(key).pitchClass == i:
                    weights.append((nameCount[key], key))
            weights.sort()
            label = []
            if len(weights) == 0: # get a default
                if hideUnused:
                    continue
                if not blankLabelUnused:
                    label.append(p.name)
                else: # use an empty label to maintain spacing
                    label.append('')
            elif not showEnharmonic: # get just the first weighted
                label.append(weights[0][1]) # second value is label
            else:      
                sub = []
                for unused_w, name in weights:
                    sub.append(name)
                label.append('/'.join(sub))
            ticks.append([i, ''.join(label)])
        ticks = self._filterPitchLabel(ticks)
        return ticks

    def ticksPitchClass(self, pcMin=0, pcMax=11):
        r'''
        Utility method to get ticks in pitch classes

        Uses the default label for each pitch class regardless of what is in the `Stream`
        (unlike `ticksPitchClassUsage()`)

        
        >>> s = stream.Stream()
        >>> a = graph.PlotStream(s)
        >>> a.ticksPitchClass()
        [[0, 'C'], [1, 'C$\\sharp$'], [2, 'D'], [3, 'E$\\flat$'], [4, 'E'], [5, 'F'], [6, 'F$\\sharp$'], [7, 'G'], [8, 'G$\\sharp$'], [9, 'A'], [10, 'B$\\flat$'], [11, 'B']]
        '''
        ticks = []
        for i in range(pcMin, pcMax+1):
            p = pitch.Pitch()
            p.ps = i
            ticks.append([i, '%s' % p.name])
        ticks = self._filterPitchLabel(ticks)
        return ticks
   
    def ticksPitchSpaceOctave(self, pitchMin=36, pitchMax=100):
        '''
        Utility method to get ticks in pitch space only for every octave.

        
        >>> s = stream.Stream()
        >>> a = graph.PlotStream(s)
        >>> a.ticksPitchSpaceOctave()
        [[36, 'C2'], [48, 'C3'], [60, 'C4'], [72, 'C5'], [84, 'C6'], [96, 'C7']]
        '''
        ticks = []
        cVals = range(pitchMin, pitchMax, 12)
        for i in cVals:
            p = pitch.Pitch(ps = i)
            ticks.append([i, '%s' % (p.nameWithOctave)])
        ticks = self._filterPitchLabel(ticks)
        return ticks


    def ticksPitchSpaceChromatic(self, pitchMin=36, pitchMax=100):
        r'''Utility method to get ticks in pitch space values.

        
        >>> s = stream.Stream()
        >>> a = graph.PlotStream(s)
        >>> a.ticksPitchSpaceChromatic(20, 24)
        [[20, 'G$\\sharp$0'], [21, 'A0'], [22, 'B$\\flat$0'], [23, 'B0'], [24, 'C1']]
        >>> [x for x,y in a.ticksPitchSpaceChromatic(60, 72)]
        [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
        '''
        ticks = []
        cVals = range(pitchMin, pitchMax+1)
        for i in cVals:
            p = pitch.Pitch(ps = i)
            ticks.append([i, '%s' % (p.nameWithOctave)])
        ticks = self._filterPitchLabel(ticks)
        return ticks

    def ticksPitchSpaceQuartertone(self, pitchMin=36, pitchMax=100):
        '''
        Utility method to get ticks in quarter-tone pitch space values.
        '''
        ticks = []
        cVals = []
        for i in range(pitchMin, pitchMax+1):
            cVals.append(i)
            if i != pitchMax: # if not last
                cVals.append(i+.5)        
        for i in cVals:
            p = pitch.Pitch(ps = i)
            # should be able to just use nameWithOctave
            ticks.append([i, '%s' % (p.nameWithOctave)])
        ticks = self._filterPitchLabel(ticks)
        environLocal.printDebug(['ticksPitchSpaceQuartertone', ticks])
        return ticks

    def ticksPitchSpaceUsage(self, pcMin=36, pcMax=72,
            showEnharmonic=False, blankLabelUnused=True, hideUnused=False):
        '''Get ticks and labels for pitch space based on usage. That is, show the most commonly used enharmonic first.
        
        >>> s = corpus.parse('bach/bwv324.xml')
        >>> a = graph.PlotStream(s.parts[0])
        >>> [x for x, y in a.ticksPitchSpaceUsage(hideUnused=True)]
        [64, 66, 67, 69, 71, 72]

        >>> s = corpus.parse('corelli/opus3no1/1grave')
        >>> a = graph.PlotStream(s)
        >>> [x for x, y in a.ticksPitchSpaceUsage(showEnharmonic=True, hideUnused=True)]
        [36, 41, 43, 45, 46, 47, 48, 49, 50, 52, 53, 55, 57, 58, 60, 62, 64, 65, 67, 69, 70, 71, 72]

        OMIT_FROM_DOCS
        TODO: this needs to look at key signature/key to determine defaults
        for undefined notes.

        '''
        # keys are integers
        # pcCount = self.streamObj.pitchAttributeCount('pitchClass')
        # name strings are keys, and enharmonic are thus different
        nameWithOctaveCount = self.streamObj.pitchAttributeCount(
                             'nameWithOctave')
        ticks = []
        for i in range(int(math.floor(pcMin)), int(math.ceil(pcMax+1))):
            p = pitch.Pitch()
            p.ps = i # set pitch space value
            weights = [] # a list of pairs of count/label
            for key in nameWithOctaveCount:
                if pitch.Pitch(key).ps == i:
                    weights.append((nameWithOctaveCount[key], key))
            weights.sort()
            label = []
            if len(weights) == 0: # get a default
                if hideUnused:
                    continue
                if not blankLabelUnused:
                    label.append(p.nameWithOctave)
                else: # provide an empty label
                    label.append('')
            elif not showEnharmonic: # get just the first weighted
                label.append(weights[0][1]) # second value is label
            else:      
                sub = []
                for unused_w, name in weights:
                    sub.append(name)
                label.append('/'.join(sub))
            ticks.append([i, ''.join(label)])
        ticks = self._filterPitchLabel(ticks)
        return ticks


    def ticksPitchSpaceQuartertoneUsage(self, pcMin=36, pcMax=72,
            showEnharmonic=False, blankLabelUnused=True, hideUnused=False):
        '''
        Get ticks and labels for pitch space based on usage. 
        That is, show the most commonly used enharmonic first.
        '''
        # keys are integers
        # pcCount = self.streamObj.pitchAttributeCount('pitchClass')
        # name strings are keys, and enharmonic are thus different
        nameWithOctaveCount = self.streamObj.pitchAttributeCount(
                             'nameWithOctave')
        vals = []
        for i in range(int(math.floor(pcMin)), int(math.ceil(pcMax+1))):
            vals.append(i)
            vals.append(i+.5)
        vals = vals[:-1]

        ticks = []
        for i in vals:
            p = pitch.Pitch()
            p.ps = i # set pitch space value
            weights = [] # a list of pairs of count/label
            for key in nameWithOctaveCount:
                if pitch.Pitch(key).ps == i:
                    weights.append((nameWithOctaveCount[key], key))
            weights.sort()
            label = []
            if len(weights) == 0: # get a default
                if hideUnused:
                    continue
                if not blankLabelUnused:
                    label.append(p.nameWithOctave)
                else: # provide an empty label
                    label.append('')
            elif not showEnharmonic: # get just the first weighted
                label.append(weights[0][1]) # second value is label
            else:      
                sub = []
                for unused_w, name in weights:
                    sub.append(name)
                label.append('/'.join(sub))
            ticks.append([i, ''.join(label)])
        ticks = self._filterPitchLabel(ticks)
        return ticks




    def ticksOffset(self, offsetMin=None, offsetMax=None, offsetStepSize=None,
                    displayMeasureNumberZero=False, minMaxOnly=False, 
                    remap=False):
        '''
        Get offset ticks. If `Measure` objects are found, they will be used to 
        create ticks. If not, `offsetStepSize` will be used to create 
        offset ticks between min and max. 

        If `minMaxOnly` is True, only the first and last values will be provided.

        The `remap` parameter is not yet used.

        
        >>> s = corpus.parse('bach/bwv281.xml')
        >>> a = graph.PlotStream(s)
        >>> a.ticksOffset() # on whole score, showing anacrusis spacing
        [[0.0, '0'], [1.0, '1'], [5.0, '2'], [9.0, '3'], [13.0, '4'], [17.0, '5'], [21.0, '6'], [25.0, '7'], [29.0, '8']]

        >>> a = graph.PlotStream(s.parts[0].flat) # on a Part
        >>> a.ticksOffset() # on whole score, showing anacrusis spacing
        [[0.0, '0'], [1.0, '1'], [5.0, '2'], [9.0, '3'], [13.0, '4'], [17.0, '5'], [21.0, '6'], [25.0, '7'], [29.0, '8']]
        >>> a.ticksOffset(8, 12, 2)
        [[9.0, '3']]

        >>> a = graph.PlotStream(s.parts[0].flat) # on a Flat collection
        >>> a.ticksOffset(8, 12, 2)
        [[9.0, '3']]

        >>> n = note.Note('a') # on a raw collection of notes with no measures
        >>> s = stream.Stream()
        >>> s.repeatAppend(n, 10)
        >>> a = graph.PlotStream(s) # on a Part
        >>> a.ticksOffset() # on whole score
        [[0, '0'], [10, '10']]
        '''
        from music21 import stream
        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        if offsetMin == None:
            offsetMin = sSrc.lowestOffset
        if offsetMax == None:
            offsetMax = sSrc.highestTime
   
        # see if this stream has any Measures, or has any references to
        # Measure obtained through contexts
        # look at measures first, as this will always be faster
        #environLocal.printDebug(['ticksOffset: about to call measure offset', self.streamObj])
        offsetMap = {}
        if self.streamObj.hasPartLikeStreams():
            # if we have part-like sub streams; we can assume that all parts
            # have parallel measures start times here for simplicity
            # take the top part 
            offsetMap = self.streamObj.getElementsByClass(
                'Stream')[0].measureOffsetMap(['Measure'])
        elif self.streamObj.hasMeasures():
            offsetMap = self.streamObj.measureOffsetMap([stream.Measure])
        else:
            offsetMap = self.streamObj.measureOffsetMap([note.Note])
        if len(offsetMap) > 0:
            self._axisLabelUsesMeasures = True
        else:
            self._axisLabelUsesMeasures = False
        #environLocal.printDebug(['ticksOffset: got offset map keys', offsetMap.keys(), self._axisLabelUsesMeasures])

        ticks = [] # a list of graphed value, string label pairs
        if len(offsetMap) > 0:
            #environLocal.printDebug(['using measures for offset ticks'])
            # store indices in offsetMap
            mNoToUse = []
            sortedKeys = sorted(list(offsetMap.keys()))
            for key in sortedKeys:
                if key >= offsetMin and key <= offsetMax:
#                     if key == 0.0 and not displayMeasureNumberZero:
#                         continue # skip
                    #if key == sorted(offsetMap.keys())[-1]:
                    #    continue # skip last
                    # assume we can get the first Measure in the lost if
                    # measurers; this may not always be True
                    mNoToUse.append(key)
            #environLocal.printDebug(['ticksOffset():', 'mNotToUse', mNoToUse])

            # just get the min and the max
            if minMaxOnly:
                for i in [0, len(mNoToUse)-1]:
                    offset = mNoToUse[i]
                    mNumber = offsetMap[offset][0].number
                    ticks.append([offset, '%s' % mNumber])
            else: # get all of them
                if len(mNoToUse) > 20:
                    # get about 10 ticks
                    mNoStepSize = int(len(mNoToUse) / 10.)
                else:
                    mNoStepSize = 1    
                #for i in range(0, len(mNoToUse), mNoStepSize):
                i = 0 # always start with first
                while i < len(mNoToUse):
                    offset = mNoToUse[i]
                    mNumber = offsetMap[offset][0].number
                    ticks.append([offset, '%s' % mNumber])
                    i += mNoStepSize
        else: # generate numeric ticks
            if offsetStepSize == None:
                offsetStepSize = 10
            #environLocal.printDebug(['using offsets for offset ticks'])
            # get integers for range calculation
            oMin = int(math.floor(offsetMin))
            oMax = int(math.ceil(offsetMax))
            for i in range(oMin, oMax+1, offsetStepSize):
                ticks.append([i, '%s' % i])

        #environLocal.printDebug(['ticksOffset():', 'final ticks', ticks])
        return ticks

    def remapQuarterLength(self, x):
        '''
        Remap a quarter length as its log2.  Essentially it's
        just math.log(x, 2), but 0 gives 0.
        '''
        if x == 0: # not expected but does happen
            return 0
        try:
            return math.log(x, 2)
        except ValueError:
            raise GraphException('cannot take log of x value: %s' %  x)
        #return pow(x, .5)

    def ticksQuarterLength(self, min=None, max=None, remap=True): #@ReservedAssignment
        '''
        Get ticks for quarterLength. 
        
        If `remap` is `True` (the default), the `remapQuarterLength()`
        method will be used to scale displayed quarter lengths 
        by log base 2. 

        Note that mix and max do nothing, but must be included
        in order to set the tick style.

         
        >>> s = stream.Stream()
        >>> for t in ['32nd', '16th', 'eighth', 'quarter', 'half']:
        ...     n = note.Note()
        ...     n.duration.type = t
        ...     s.append(n)
        
        >>> a = graph.PlotStream(s)
        >>> a.ticksQuarterLength()
        [[-3.0, '0.1...'], [-2.0, '0.25'], [-1.0, '0.5'], [0.0, '1.0'], [1.0, '2.0']]

        >>> a.ticksQuarterLength(remap = False)
        [[0.125, '0.1...'], [0.25, '0.25'], [0.5, '0.5'], [1.0, '1.0'], [2.0, '2.0']]

        The second entry is 0.125 but gets rounded differently in python 2 (1.3) and python 3
        (1.2)
        '''
        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj
        # get all quarter lengths
        mapping = sSrc.attributeCount([note.Note, chord.Chord], 'quarterLength')

        ticks = []
        for ql in sorted(mapping.keys()):
            if remap:
                x = self.remapQuarterLength(ql)
            else:
                x = ql
            ticks.append([x, '%s' % round(ql, 2)])

        return ticks

   
    def ticksDynamics(self, minNameIndex=None, maxNameIndex=None):
        '''
        Utility method to get ticks in dynamic values:

        
        >>> s = stream.Stream()
        >>> a = graph.PlotStream(s)
        >>> a.ticksDynamics()
        [[0, '$pppppp$'], [1, '$ppppp$'], [2, '$pppp$'], [3, '$ppp$'], [4, '$pp$'], [5, '$p$'], [6, '$mp$'], [7, '$mf$'], [8, '$f$'], [9, '$fp$'], [10, '$sf$'], [11, '$ff$'], [12, '$fff$'], [13, '$ffff$'], [14, '$fffff$'], [15, '$ffffff$']]

        A minimum and maximum dynamic index can be specified:

        >>> a.ticksDynamics(3, 6)
        [[3, '$ppp$'], [4, '$pp$'], [5, '$p$'], [6, '$mp$']]

        '''
        if minNameIndex == None:
            minNameIndex = 0
        if maxNameIndex == None:
            # will add one in range()
            maxNameIndex = len(dynamics.shortNames)-1

        ticks = []
        for i in range(minNameIndex, maxNameIndex+1):
            # place string in tex format for italic display
            ticks.append([i, r'$%s$' % dynamics.shortNames[i]])
        return ticks
    

#-------------------------------------------------------------------------------
# base class for multi-stream displays

class PlotMultiStream(object):
    '''
    Approaches to plotting and graphing multiple Streams. 
    A base class from which Stream plotting Classes inherit.

    '''
    # the following static parameters are used to for matching this
    # plot based on user-requested string aguments
    # a string representation of the type of graph
    format = ''
    # store a list of parameters that are graphed
    values = []

    def __init__(self, streamList, labelList=None, *args, **keywords):
        '''
        Provide a list of Streams as an argument. Optionally 
        provide an additional list of labels for each list. 
        
        If `flatten` is True, the Streams will automatically be flattened.
        '''
        if labelList is None:
            labelList = []

        self.streamList = []
        foundPaths = []
        for s in streamList:
            # could be corpus or file path
            if common.isStr(s):
                foundPaths.append(os.path.basename(s))
                if os.path.exists(s):
                    s = converter.parse(s)
                else: # assume corpus
                    s = corpus.parse(s)
            # otherwise assume a parsed stream
            self.streamList.append(s)

        # use found paths if no labels are provided
        if len(labelList) == 0 and len(foundPaths) == len(streamList):
            self.labelList = foundPaths
        else:
            self.labelList = labelList

        self.data = None # store native data representation, useful for testing
        self.graph = None  # store instance of graph class here


    def process(self):
        '''
        This will process all data, as well as call 
        the done() method. What happens when the done() is 
        called is determined by the keyword argument `doneAction`; 
        options are 'show' (display immediately), 
        'write' (write the file to a supplied file path), 
        and None (do processing but do not write or show a graph).

        Subclass dependent data extracted is stored in the self.data attribute. 
        '''
        self.graph.process()

    def show(self):
        '''Call internal Graphs show() method independently of doneAction set and run with process()
        '''
        self.graph.show()

    def write(self, fp=None):
        '''Call internal Graphs write() method independently of doneAction set and run with process()
        '''
        self.graph.write(fp)







#-------------------------------------------------------------------------------
# color grids    

class PlotWindowedAnalysis(PlotStream):
    '''Base Plot for windowed analysis routines.

    ''' 
    format = 'colorGrid'
    def __init__(self, streamObj, processor=None, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)
        
        # store process for getting title
        self.processor = processor
        self.graphLegend = None

        if 'title' not in keywords:
            # pass to Graph instance
            keywords['title'] = 'Windowed Analysis'

        if 'minWindow' in keywords:
            self.minWindow = keywords['minWindow']
        else:
            self.minWindow = 1

        if 'maxWindow' in keywords:
            self.maxWindow = keywords['maxWindow']
        else: # max window of None gets larges
            self.maxWindow = None

        if 'windowStep' in keywords:
            self.windowStep = keywords['windowStep']
        else:
            self.windowStep = 'pow2'

        if 'windowType' in keywords:
            self.windowType = keywords['windowType']
        else:
            self.windowType = 'overlap'

        if 'compressLegend' in keywords:
            self.compressLegend = keywords['compressLegend']
        else:
            self.compressLegend = True

        # create a color grid
        self.graph = GraphColorGrid(*args, **keywords)
        # uses self.processor
        data, yTicks = self._extractData()
        xTicks = self.ticksOffset(minMaxOnly=True)
        
        self.graph.setData(data)
        self.graph.setAxisLabel('y', 'Window Size\n(Quarter Lengths)')
        self.graph.setAxisLabel('x', 'Windows (%s Span)' %
                                 self._axisLabelMeasureOrOffset())
        self.graph.setTicks('y', yTicks)

        # replace offset values with 0 and 1, as proportional here
        if len(xTicks) == 2:
            xTicks = [(0, xTicks[0][1]), (1, xTicks[1][1])]
        else:
            environLocal.printDebug(['raw xTicks', xTicks])
            xTicks = []
        self.graph.setTicks('x', xTicks)

        
    def _extractData(self):
        '''Extract data actually calls the processing routine. 
        '''
        wa = windowed.WindowedAnalysis(self.streamObj, self.processor)
        unused_solutionMatrix, colorMatrix, metaMatrix = wa.process(self.minWindow, 
            self.maxWindow, self.windowStep, windowType=self.windowType)
                
        # get dictionaries of meta data for each row
        pos = 0
        yTicks = []

        # if more than 12 bars, reduce the number of ticks
        if len(metaMatrix) > 12:
            tickRange = range(0, len(metaMatrix), int(len(metaMatrix) / 12))
        else:
            tickRange = range(len(metaMatrix))
        environLocal.printDebug(['tickRange', tickRange])
        for y in tickRange:        
            # pad three ticks for each needed
            yTicks.append([pos, '']) # pad first
            yTicks.append([pos+1, '%s' % metaMatrix[y]['windowSize']])
            yTicks.append([pos+2, '']) # pad last
            pos += 3

        return colorMatrix, yTicks
    
    def _getLegend(self):
        title = (self.processor.name + 
                ' (%s)' % self.processor.solutionUnitString())
        graphLegend = GraphColorGridLegend(doneAction=self.graph.doneAction, 
                           title=title)
        graphLegend.setData(self.processor.solutionLegend(
                           compress=self.compressLegend))
        return graphLegend

    def process(self):
        '''Process method here overridden to provide legend.
        '''
        # call the process routine in the base graph
        self.graph.process()
        # create a new graph of the legend
        self.graphLegend = self._getLegend()
        self.graphLegend.process()

    def write(self, fp=None):
        '''Process method here overridden to provide legend.
        '''
        if fp == None:
            fp = environLocal.getTempFile('.png')

        directory, fn = os.path.split(fp)
        fpLegend = os.path.join(directory, 'legend-' + fn)
        # call the process routine in the base graph
        self.graph.write(fp)
        # create a new graph of the legend

        self.graphLegend = self._getLegend()
        self.graphLegend.process()
        self.graphLegend.write(fpLegend)

    
class PlotWindowedKrumhanslSchmuckler(PlotWindowedAnalysis):
    '''Stream plotting of windowed version of Krumhansl-Schmuckler analysis routine. See :class:`~music21.analysis.discrete.KrumhanslSchmuckler` for more details.

    
    >>> s = corpus.parse('bach/bwv66.6')
    >>> p = graph.PlotWindowedKrumhanslSchmuckler(s.parts[0], doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW p = graph.PlotWindowedKrumhanslSchmuckler(s.parts[0])
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotWindowedKrumhanslSchmuckler.*
        :width: 600

    .. image:: images/legend-PlotWindowedKrumhanslSchmuckler.*

    '''
    values = discrete.KrumhanslSchmuckler.identifiers
    def __init__(self, streamObj, *args, **keywords):
        PlotWindowedAnalysis.__init__(self, streamObj, 
            discrete.KrumhanslSchmuckler(streamObj), *args, **keywords)
    
class PlotWindowedKrumhanslKessler(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Krumhansl-Kessler 
    analysis routine. See :class:`~music21.analysis.discrete.KrumhanslKessler` for more details.
    '''
    values = discrete.KrumhanslKessler.identifiers
    def __init__(self, streamObj, *args, **keywords):
        PlotWindowedAnalysis.__init__(self, streamObj, 
            discrete.KrumhanslKessler(streamObj), *args, **keywords)

class PlotWindowedAardenEssen(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Aarden-Essen 
    analysis routine. 
    See :class:`~music21.analysis.discrete.AardenEssen` for more details.
    '''
    values = discrete.AardenEssen.identifiers
    def __init__(self, streamObj, *args, **keywords):
        PlotWindowedAnalysis.__init__(self, streamObj, 
            discrete.AardenEssen(streamObj), *args, **keywords)

class PlotWindowedSimpleWeights(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Simple Weights analysis 
    routine. See :class:`~music21.analysis.discrete.SimpleWeights` for more details.
    '''
    values = discrete.SimpleWeights.identifiers
    def __init__(self, streamObj, *args, **keywords):
        PlotWindowedAnalysis.__init__(self, streamObj, 
            discrete.SimpleWeights(streamObj), *args, **keywords)

class PlotWindowedBellmanBudge(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Bellman-Budge analysis 
    routine. See :class:`~music21.analysis.discrete.BellmanBudge` for more details.
    '''
    values = discrete.BellmanBudge.identifiers
    def __init__(self, streamObj, *args, **keywords):
        PlotWindowedAnalysis.__init__(self, streamObj, 
            discrete.BellmanBudge(streamObj), *args, **keywords)

class PlotWindowedTemperleyKostkaPayne(PlotWindowedAnalysis):
    '''
    Stream plotting of windowed version of Temperley-Kostka-Payne 
    analysis routine. 
    See :class:`~music21.analysis.discrete.TemperleyKostkaPayne` for more details.
    '''
    values = discrete.TemperleyKostkaPayne.identifiers
    def __init__(self, streamObj, *args, **keywords):
        PlotWindowedAnalysis.__init__(self, streamObj, 
            discrete.TemperleyKostkaPayne(streamObj), *args, **keywords)

    

class PlotWindowedAmbitus(PlotWindowedAnalysis):
    '''Stream plotting of basic pitch span. 

    
    >>> s = corpus.parse('bach/bwv66.6')
    >>> p = graph.PlotWindowedAmbitus(s.parts[0], doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW p = graph.PlotWindowedAmbitus(s.parts[0])
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotWindowedAmbitus.*
        :width: 600

    .. image:: images/legend-PlotWindowedAmbitus.*

    '''
    values = discrete.Ambitus.identifiers
    def __init__(self, streamObj, *args, **keywords):
        # provide the stream to both the window and processor in this case
        PlotWindowedAnalysis.__init__(self, streamObj, 
            discrete.Ambitus(streamObj), *args, **keywords)
        

#-------------------------------------------------------------------------------
# histograms

class PlotHistogram(PlotStream):
    '''
    Base class for Stream plotting classes.

    Plots take a Stream as their arguments, Graphs take any data.

    '''
    format = 'histogram'
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

    def _extractData(self, dataValueLegit=True):
        data = {}
        dataTick = {}
        #countMin = 0 # could be the lowest value found
        countMax = 0

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        # first, collect all unique data values
        dataValues = []
        for noteObj in sSrc.getElementsByClass(note.Note):
            value = self.fx(noteObj)
            if value not in dataValues:
                dataValues.append(value)
        for chordObj in sSrc.getElementsByClass(chord.Chord):
            values = self._extractChordDataOneAxis(self.fx, chordObj)
            for value in values:
                if value not in dataValues:
                    dataValues.append(value)

        dataValues.sort()

        # second, count instances
        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                values = self._extractChordDataOneAxis(self.fx, obj)
                ticks = self._extractChordDataOneAxis(self.fxTick, obj)
            else: # simulate a list
                values = [self.fx(obj)]            
                ticks = [self.fxTick(obj)]            

            for i, value in enumerate(values):
                if not dataValueLegit: 
                    # get the index position, not the value
                    value = dataValues.index(value)
    
                if value not in data:
                    data[value] = 0
                    # this is the offset that is used to shift labels
                    # into bars; this only is .5 if x values are integers
                    dataTick[value+.4] = ticks[i]
                data[value] += 1
                if data[value] >= countMax:
                    countMax = data[value]

        data = list(data.items())
        data.sort()
        dataTick = list(dataTick.items())
        dataTick.sort()
        xTicks = dataTick
        # alway have min and max
        yTicks = []
        yTickStep = int(round(countMax / 8.))
        if yTickStep <= 1:
            yTickStep = 2
        for y in range(0, countMax+1, yTickStep):
            yTicks.append([y, '%s' % y])
        yTicks.sort()
        return data, xTicks, yTicks


class PlotHistogramPitchSpace(PlotHistogram):
    '''A histogram of pitch space.

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHistogramPitchSpace(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotHistogramPitchSpace(s)
    >>> p.id
    'histogram-pitch'
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHistogramPitchSpace.*
        :width: 600
    '''
    values = ['pitch']
    def __init__(self, streamObj, *args, **keywords):
        PlotHistogram.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n: n.pitch.midi
        self.fxTick = lambda n: n.nameWithOctave
        # replace with self.ticksPitchSpaceUsage

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData()

        # filter xTicks to remove - in flat lables
        xTicks = self._filterPitchLabel(xTicks)

        self.graph = GraphHistogram(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)

        self.graph.setAxisLabel('y', 'Count')
        self.graph.setAxisLabel('x', 'Pitch')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([9,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Histogram')

        # make smaller for axis display
        if 'tickFontSize' not in keywords:
            self.graph.tickFontSize = 7



class PlotHistogramPitchClass(PlotHistogram):
    '''A histogram of pitch class

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHistogramPitchClass(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotHistogramPitchClass(s)
    >>> p.id
    'histogram-pitchClass'
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHistogramPitchClass.*
        :width: 600

    '''
    values = ['pitchClass']
    def __init__(self, streamObj, *args, **keywords):
        PlotHistogram.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n: n.pitch.pitchClass
        self.fxTick = lambda n: n.name
        # replace with self.ticksPitchClassUsage

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData()

        # filter xTicks to remove - in flat lables
        xTicks = self._filterPitchLabel(xTicks)

        self.graph = GraphHistogram(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)

        self.graph.setAxisLabel('y', 'Count')
        self.graph.setAxisLabel('x', 'Pitch Class')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Class Histogram')




class PlotHistogramQuarterLength(PlotHistogram):
    '''A histogram of pitch class

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHistogramQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotHistogramQuarterLength(s)
    >>> p.id
    'histogram-quarterLength'
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHistogramQuarterLength.*
        :width: 600

    '''
    values = ['quarterLength']
    def __init__(self, streamObj, *args, **keywords):
        PlotHistogram.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n:n.quarterLength
        self.fxTick = lambda n: n.quarterLength

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData(dataValueLegit=False)

        self.graph = GraphHistogram(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)

        self.graph.setAxisLabel('y', 'Count')
        self.graph.setAxisLabel('x', 'Quarter Length')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Quarter Length Histogram')



#-------------------------------------------------------------------------------
# scatter plots

class PlotScatter(PlotStream):
    '''Base class for 2D Scatter plots.
    '''
    format = 'scatter'
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

        if 'xLog' not in keywords:
            self.xLog = True
        else:
            self.xLog = keywords['xLog']

        # sample values; customize in subclass
        self.fy = lambda n: n.pitch.ps
        self.fyTicks = self.ticksPitchSpaceUsage

        self.fx = lambda n: n.quarterLength
        self.fxTicks = self.ticksQuarterLength


    def _extractData(self, xLog=False):
        data = []
        xValues = []
        yValues = []

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        # get all unique values for both x and y
        for noteObj in sSrc.getElementsByClass(note.Note):
            x = self.fx(noteObj)
            if xLog:
                x = self.remapQuarterLength(x)
            y = self.fy(noteObj)
            if x not in xValues:
                xValues.append(x)            
            if y not in xValues:
                yValues.append(x)            
        for chordObj in sSrc.getElementsByClass(chord.Chord):
            xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, 
                         chordObj, matchPitchCount=False)
            for x in xSrc:
                if x not in xValues:
                    xValues.append(x)            
            for y in ySrc:
                if y not in xValues:
                    yValues.append(y)     

        xValues.sort()
        yValues.sort()

        # count the frequency of each item
        for noteObj in sSrc.getElementsByClass(note.Note):
            x = self.fx(noteObj)
            if xLog:
                x = self.remapQuarterLength(x)
            y = self.fy(noteObj)
            data.append([x, y])

        for chordObj in sSrc.getElementsByClass(chord.Chord):
            # here, need an x for every y, so match pitch count
            xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, 
                         chordObj, matchPitchCount=True)
            #environLocal.printDebug(['xSrc', xSrc, 'ySrc', ySrc])
            for i, x in enumerate(xSrc):
                y = ySrc[i]
                if xLog:
                    x = self.remapQuarterLength(x)
                data.append([x, y])

        #environLocal.printDebug(['data', data])

        xVals = [x for x,y in data]
        yVals = [y for x,y in data]

        xTicks = self.fxTicks(min(xVals), max(xVals), remap=xLog)
        yTicks = self.fyTicks(min(yVals), max(yVals))

        return data, xTicks, yTicks


class PlotScatterPitchSpaceQuarterLength(PlotScatter):
    '''A scatter plot of pitch space and quarter length

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterPitchSpaceQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotScatterPitchSpaceQuarterLength(s)
    >>> p.id
    'scatter-pitch-quarterLength'
    >>> p.process()

    .. image:: images/PlotScatterPitchSpaceQuarterLength.*
        :width: 600
    '''
    values = ['pitch', 'quarterLength']
    def __init__(self, streamObj, *args, **keywords):
        PlotScatter.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.ps
        self.fyTicks = self.ticksPitchSpaceUsage
        self.fx = lambda n: n.quarterLength
        self.fxTicks = self.ticksQuarterLength

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData(xLog=self.xLog)

        self.graph = GraphScatter(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Pitch')
        self.graph.setAxisLabel('x', self._axisLabelQuarterLength(
                                remap=self.xLog))

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch by Quarter Length Scatter')
        if 'alpha' not in keywords:
            self.graph.alpha = .7


class PlotScatterPitchClassQuarterLength(PlotScatter):
    '''A scatter plot of pitch class and quarter length

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterPitchClassQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotScatterPitchClassQuarterLength(s)
    >>> p.id
    'scatter-pitchClass-quarterLength'
    >>> p.process()

    .. image:: images/PlotScatterPitchClassQuarterLength.*
        :width: 600
    '''
    # string name used to access this class
    values = ['pitchClass', 'quarterLength']
    def __init__(self, streamObj, *args, **keywords):
        PlotScatter.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.pitchClass
        self.fyTicks = self.ticksPitchClassUsage

        self.fx = lambda n: n.quarterLength
        self.fxTicks = self.ticksQuarterLength

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData(xLog=self.xLog)

        self.graph = GraphScatter(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Pitch Class')
        self.graph.setAxisLabel('x', self._axisLabelQuarterLength(
                                remap=self.xLog))

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Class by Quarter Length Scatter')
        if 'alpha' not in keywords:
            self.graph.alpha = .7


class PlotScatterPitchClassOffset(PlotScatter):
    '''A scatter plot of pitch class and offset

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterPitchClassOffset(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotScatterPitchClassOffset(s)
    >>> p.id
    'scatter-pitchClass-offset'
    >>> p.process()

    .. image:: images/PlotScatterPitchClassOffset.*
        :width: 600
    '''
    values = ['pitchClass', 'offset']
    def __init__(self, streamObj, *args, **keywords):
        PlotScatter.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.pitchClass
        self.fyTicks = self.ticksPitchClassUsage

        self.fx = lambda n: n.offset
        self.fxTicks = self.ticksOffset

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData()

        self.graph = GraphScatter(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Pitch Class')
        self.graph.setAxisLabel('x', self._axisLabelMeasureOrOffset())

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([10,5])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Class by Offset Scatter')
        if 'alpha' not in keywords:
            self.graph.alpha = .7


class PlotScatterPitchSpaceDynamicSymbol(PlotScatter):
    '''A graph of dynamics used by pitch space.

    
    >>> s = converter.parse('tinynotation: 4/4 C4 d E f', makeNotation=False) #_DOCS_HIDE
    >>> s.insert(0.0, dynamics.Dynamic('pp')) #_DOCS_HIDE
    >>> s.insert(2.0, dynamics.Dynamic('ff')) #_DOCS_HIDE
    >>> p = graph.PlotScatterPitchSpaceDynamicSymbol(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = converter.parse('/Desktop/schumann/opus41no1/movement2.xml')
    >>> #_DOCS_SHOW p = graph.PlotScatterPitchSpaceDynamicSymbol(s)
    >>> p.process()

    .. image:: images/PlotScatterPitchSpaceDynamicSymbol.*
        :width: 600
    '''
    # string name used to access this class
    values = ['pitchClass', 'dynamics']
    def __init__(self, streamObj, *args, **keywords):
        PlotScatter.__init__(self, streamObj, *args, **keywords)

        self.fxTicks = self.ticksPitchSpaceUsage
        self.fyTicks = self.ticksDynamics

        # get data from correlate object
        am = correlate.ActivityMatch(self.streamObj)
        self.data  = am.pitchToDynamic(dataPoints=True)

        xVals = [x for x, unused_y in self.data]
        yVals = [y for unused_x, y in self.data]

        xTicks = self.fxTicks(min(xVals), max(xVals))
        # ticks dynamics takes no args
        yTicks = self.fyTicks(min(yVals), max(yVals))

        self.graph = GraphScatter(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Dynamics')
        self.graph.setAxisLabel('x', 'Pitch')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([12,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Class by Quarter Length Scatter')
        if 'alpha' not in keywords:
            self.graph.alpha = .7
        # make smaller for axis display
        if 'tickFontSize' not in keywords:
            self.graph.tickFontSize = 7




#-------------------------------------------------------------------------------
# horizontal bar graphs

class PlotHorizontalBar(PlotStream):
    '''A graph of events, sorted by pitch, over time
    '''
    format = 'horizontalbar'
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.ps
        self.fyTicks = self.ticksPitchSpaceChromatic
        self.fxTicks = self.ticksOffset

    def _extractData(self):
        dataUnique = {}
        xValues = []
        # collect data
        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj
        for obj in sSrc.getElementsByClass((note.Note, chord.Chord)):
            if 'Chord' in obj.classes:
                values = self._extractChordDataOneAxis(self.fy, obj)
                valueObjPairs = [(v, obj) for v in values]
            else: # its a Note
                valueObjPairs = [(self.fy(obj), obj)]
            for v, objSub in valueObjPairs:
                # rounding to nearest quarter tone
                numericValue = common.roundToHalfInteger(v) #int(v)

                if numericValue not in dataUnique:
                    dataUnique[numericValue] = []
                # all work with offset
                start = objSub.offset
                # this is not the end, but instead the length
                end = objSub.quarterLength
                xValues.append(start)
                xValues.append(end)
                dataUnique[numericValue].append((start, end))
        # create final data list
        # get labels from ticks
        data = []
        # y ticks are auto-generated in lower-level routines
        # this is used just for creating labels
        yTicks = self.fyTicks(min(dataUnique.keys()),
                                       max(dataUnique.keys()))
        for numericValue, label in yTicks:
            if numericValue in dataUnique:
                data.append([label, dataUnique[numericValue]])
            else:
                data.append([label, []])
        # use default args for now
        xTicks = self.fxTicks()
        # yTicks are returned, even though they are not used after this method
        return data, xTicks, yTicks


class PlotHorizontalBarPitchClassOffset(PlotHorizontalBar):
    '''A graph of events, sorted by pitch class, over time

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHorizontalBarPitchClassOffset(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotHorizontalBarPitchClassOffset(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHorizontalBarPitchClassOffset.*
        :width: 600

    '''
    values = ['pitchClass', 'offset', 'pianoroll']
    def __init__(self, streamObj, *args, **keywords):
        PlotHorizontalBar.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n: n.pitch.pitchClass
        self.fyTicks = self.ticksPitchClassUsage
        self.fxTicks = self.ticksOffset # this a method

        self.data, xTicks, unused_yTicks = self._extractData()

        #environLocal.printDebug(['PlotHorizontalBarPitchClassOffset', 'post processing xTicks', xTicks])

        self.graph = GraphHorizontalBar(*args, **keywords)
        self.graph.setData(self.data)

        # only need to add x ticks; y ticks added from data labels
        #environLocal.printDebug(['PlotHorizontalBarPitchClassOffset:', 'xTicks before setting to self.graph', xTicks])
        self.graph.setTicks('x', xTicks)  

        self.graph.setAxisLabel('x', self._axisLabelMeasureOrOffset())
        self.graph.setAxisLabel('y', 'Pitch Class')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([10,4])
        if 'title' not in keywords:
            self.graph.setTitle('Note Quarter Length and Offset by Pitch Class')


class PlotHorizontalBarPitchSpaceOffset(PlotHorizontalBar):
    '''A graph of events, sorted by pitch space, over time

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHorizontalBarPitchSpaceOffset(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotHorizontalBarPitchSpaceOffset(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        :width: 600
    '''

    values = ['pitch', 'offset', 'pianoroll']
    def __init__(self, streamObj, *args, **keywords):
        PlotHorizontalBar.__init__(self, streamObj, *args, **keywords)
       
        self.fy = lambda n: n.pitch.ps
        self.fxTicks = self.ticksOffset

        if self.streamObj.isTwelveTone():
            self.fyTicks = self.ticksPitchSpaceUsage
        else:
            self.fyTicks = self.ticksPitchSpaceQuartertoneUsage

        self.data, xTicks, unused_yTicks = self._extractData()

        self.graph = GraphHorizontalBar(*args, **keywords)
        self.graph.setData(self.data)

        # only need to add x ticks; y ticks added from data labels
        self.graph.setTicks('x', xTicks)  

        if self.streamObj.recurse().getElementsByClass('Measure'):
            self.graph.setAxisLabel('x', 'Measure Number')
        else:
            self.graph.setAxisLabel('x', 'Offset')
        self.graph.setAxisLabel('y', 'Pitch')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([10,6])
        if 'title' not in keywords:
            self.graph.setTitle('Note Quarter Length by Pitch')




#-------------------------------------------------------------------------------
class PlotHorizontalBarWeighted(PlotStream):
    '''A base class for plots of Scores with weighted (by height) horizontal bars. 
    Many different weighted segments can provide a 
    representation of a dynamic parameter of a Part.


    '''
    format = 'horizontalbarweighted'
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)
        # will get Measure numbers if appropraite
        self.fxTicks = self.ticksOffset

        self.fillByMeasure = False
        if 'fillByMeasure' in keywords:
            self.fillByMeasure = keywords['fillByMeasure']
        self.segmentByTarget = True
        if 'segmentByTarget' in keywords:
            self.segmentByTarget = keywords['segmentByTarget']
        self.normalizeByPart = False
        if 'normalizeByPart' in keywords:
            self.normalizeByPart = keywords['normalizeByPart']
        self.partGroups = None
        if 'partGroups' in keywords:
            self.partGroups = keywords['partGroups']


    def _extractData(self):
        '''Extract the data from the Stream.
        '''
        if 'Score' not in self.streamObj.classes:
            raise GraphException('provided Stream must be Score')
        # parameters: x, span, heightScalar, color, alpha, yShift
        pr = reduction.PartReduction(self.streamObj, partGroups=self.partGroups, 
                fillByMeasure=self.fillByMeasure, 
                segmentByTarget=self.segmentByTarget, 
                normalizeByPart=self.normalizeByPart)
        pr.process()
        data = pr.getGraphHorizontalBarWeightedData()
        #environLocal.printDebug(['data', data])
        uniqueOffsets = []
        for unused_key, value in data:
            for dataList in value:
                start = dataList[0]
                dur = dataList[1]
                if start not in uniqueOffsets:
                    uniqueOffsets.append(start)
                if start+dur not in uniqueOffsets:
                    uniqueOffsets.append(start+dur)
        yTicks = []
        # use default args for now
        xTicks = self.fxTicks(min(uniqueOffsets), max(uniqueOffsets))
        # yTicks are returned, even though they are not used after this method
        return data, xTicks, yTicks


class PlotDolan(PlotHorizontalBarWeighted):
    '''A graph of the activity of a parameter of a part (or a group of parts) over time. The default parameter graphed is Dynamics. Dynamics are assumed to extend activity to the next change in dynamics.

    Numerous parameters can be configured based on functionality encoded in the :class:`~music21.analysis.reduction.PartReduction` object.


    If the `fillByMeasure` parameter is True, and if measures are available, each part will segment by Measure divisions, and look for the target activity only once per Measure. If more than one target is found in the Measure, values will be averaged. If `fillByMeasure` is False, the part will be segmented by each Note. 

    The `segmentByTarget` parameter is True, segments, which may be Notes or Measures, will be divided if necessary to show changes that occur over the duration of the segment by a target object. 

    If the `normalizeByPart` parameter is True, each part will be normalized within the range only of that part. If False, all parts will be normalized by the max of all parts. The default is True. 

    >>> s = corpus.parse('bwv66.6')
    >>> dyn = ['p', 'mf', 'f', 'ff', 'mp', 'fff', 'ppp']
    >>> i = 0
    >>> for p in s.parts:
    ...     for m in p.getElementsByClass('Measure'):
    ...         m.insert(0, dynamics.Dynamic(dyn[i % len(dyn)]))
    ...         i += 1
    ...
    >>> #_DOCS_SHOW s.plot('dolan', fillByMeasure=True, segmentByTarget=True)

    .. image:: images/PlotDolan.*
        :width: 600

    '''
    values = ['instrument']
    def __init__(self, streamObj, *args, **keywords):
        PlotHorizontalBarWeighted.__init__(self, streamObj, *args, **keywords)

        #self.fy = lambda n: n.pitch.pitchClass
        #self.fyTicks = self.ticksPitchClassUsage
        self.fxTicks = self.ticksOffset # this is a method

        # must set part groups if not defined here
        self._getPartGroups()
        self.data, xTicks, unused_yTicks = self._extractData()

        self.graph = GraphHorizontalBarWeighted(*args, **keywords)
        self.graph.setData(self.data)

        # only need to add x ticks; y ticks added from data labels
        #environLocal.printDebug(['PlotHorizontalBarPitchClassOffset:', 'xTicks before setting to self.graph', xTicks])
        self.graph.setTicks('x', xTicks)  
        self.graph.setAxisLabel('x', self._axisLabelMeasureOrOffset())
        #self.graph.setAxisLabel('y', '')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([10,4])
        if 'title' not in keywords:
            self.graph.setTitle('Instrumentation')
            if self.streamObj.metadata is not None:
                if self.streamObj.metadata.title is not None:
                    self.graph.setTitle(self.streamObj.metadata.title)
        if 'hideYGrid' not in keywords:
            self.graph.hideYGrid = True


    def _getPartGroups(self):
        '''Examine the instruments in the Score and determine if there is a good match for a default configuration of parts. 
        '''
        if self.partGroups is not None:
            return # keep what the user set

        instStream = self.streamObj.flat.getElementsByClass('Instrument')
        if len(instStream) == 0:
            return # do not set anything
        
        if len(instStream) == 4 and self.streamObj.getElementById('Soprano') is not None:
            pgOrc = [
                {'name':'Soprano', 'color':'purple', 'match':['soprano', '0']},
                {'name':'Alto', 'color':'orange', 'match':['alto', '1']},
                {'name':'Tenor', 'color':'lightgreen', 'match':['tenor']},
                {'name':'Bass', 'color':'mediumblue', 'match':['bass']}, 
            ]
            self.partGroups = pgOrc
            
        elif len(instStream) == 4 and self.streamObj.getElementById('Viola') is not None:
            pgOrc = [
                {'name':'1st Violin', 'color':'purple', 'match':['1st violin', '0', 'violin 1']},
                {'name':'2nd Violin', 'color':'orange', 'match':['2nd violin', '1', 'violin 2']},
                {'name':'Viola', 'color':'lightgreen', 'match':['viola']},
                {'name':'Cello', 'color':'mediumblue', 'match':['cello', 'violoncello', "'cello"]}, 
            ]
            self.partGroups = pgOrc

        elif len(instStream) > 10:
            pgOrc = [
            {'name':'Timpani', 'color':'#5C3317', 'match':None},
            {'name':'Trumpet', 'color':'red', 'match':['tromba']},
            {'name':'Horns', 'color':'orange', 'match':['corno']},

            {'name':'Flute', 'color':'#C154C1', 'match':['flauto']}, 
            {'name':'Oboe', 'color':'blue', 'match':['oboe']}, 
            {'name':'Clarinet', 'color':'mediumblue', 'match':['clarinetto']}, 
            {'name':'Bassoon', 'color':'purple', 'match':['fagotto']}, 

            {'name':'Violin I', 'color':'lightgreen', 'match':['violino i']},
            {'name':'Violin II', 'color':'green', 'match':['violino ii']},
            {'name':'Viola', 'color':'forestgreen', 'match':None},
            {'name':'Violoncello & CB', 'color':'dark green', 
                'match':['violoncello', 'contrabasso']}, 
#            {'name':'CB', 'color':'#003000', 'match':['contrabasso']},
                    ]
            self.partGroups = pgOrc



#-------------------------------------------------------------------------------
# weighted scatter

class PlotScatterWeighted(PlotStream):

    format = 'scatterWeighted'
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

        if 'xLog' not in keywords:
            self.xLog = True
        else:
            self.xLog = keywords['xLog']

        # specialize in sub-class
        self.fx = lambda n: n.quarterLength
        self.fy = lambda n: n.pitch.midi
        self.fxTicks = self.ticksQuarterLength
        self.fyTicks = self.ticksPitchClassUsage

    def _extractData(self, xLog=True):
        '''If `xLog` is true, x values will be remapped using the remapQuarterLength() function.

        Ultimately, this will need to be madularized
        '''
        environLocal.printDebug([self, 'xLog', xLog])

        dataCount = {}
        xValues = []
        yValues = []

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, obj, matchPitchCount=False)
            else: # Note, just one value
                xSrc = [self.fx(obj)]
                ySrc = [self.fy(obj)]
            for x in xSrc:
                if xLog:
                    x = self.remapQuarterLength(x)
                if x not in xValues:
                    xValues.append(x)
            for y in ySrc:
                if y not in yValues:
                    yValues.append(y)


        xValues.sort()
        yValues.sort()
        yMin = min(yValues)
        yMax = max(yValues)
        # create a count slot for all possibilities of x/y
        # y is the pitch axis; get all contiguous pirches
        for y, unused_label in self.fyTicks(yMin, yMax):
        #for y in yValues:
            dataCount[y] = [[x, 0] for x in xValues]

        maxCount = 0 # this is the max z value

        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, obj, matchPitchCount=True)
            else: # Note, just one value
                xSrc = [self.fx(obj)]
                ySrc = [self.fy(obj)]
            for i, x in enumerate(xSrc):
                y = ySrc[i]
                if xLog:
                    x = self.remapQuarterLength(x)
                indexToIncrement = xValues.index(x)
                # second position stores increment
                dataCount[y][indexToIncrement][1] += 1
                if dataCount[y][indexToIncrement][1] > maxCount:
                    maxCount = dataCount[y][indexToIncrement][1]


#         for noteObj in sSrc.getElementsByClass(note.Note):
#             x = self.fx(noteObj)
#             if xLog:
#                 x = self.remapQuarterLength(x)
#             indexToIncrement = xValues.index(x)
# 
#             # second position stores increment
#             dataCount[self.fy(noteObj)][indexToIncrement][1] += 1
#             if dataCount[self.fy(noteObj)][indexToIncrement][1] > maxCount:
#                 maxCount = dataCount[self.fy(noteObj)][indexToIncrement][1]

        xTicks = self.fxTicks(min(xValues), max(xValues), remap=xLog)
        # create final data list using fy ticks to get values
        data = []
        for y, unused_label in self.fyTicks(yMin, yMax):
            yIndex = y
            for x, z in dataCount[y]:
                data.append([x, yIndex, z])

        # only label y values that are defined
        yTicks = self.fyTicks(yMin, yMax)
        return data, xTicks, yTicks


class PlotScatterWeightedPitchSpaceQuarterLength(PlotScatterWeighted):
    '''A graph of event, sorted by pitch, over time

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterWeightedPitchSpaceQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotScatterWeightedPitchSpaceQuarterLength(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotScatterWeightedPitchSpaceQuarterLength.*
        :width: 600
    '''

    values = ['pitch', 'quarterLength']
    def __init__(self, streamObj, *args, **keywords):
        PlotScatterWeighted.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n: n.quarterLength
        self.fy = lambda n: n.pitch.midi
        self.fxTicks = self.ticksQuarterLength
        self.fyTicks = self.ticksPitchSpaceUsage

        self.data, xTicks, yTicks = self._extractData(xLog=self.xLog)

        self.graph = GraphScatterWeighted(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setAxisLabel('x', self._axisLabelQuarterLength(
                                remap=self.xLog))
        self.graph.setAxisLabel('y', 'Pitch')

        self.graph.setTicks('y', yTicks)  
        self.graph.setTicks('x', xTicks)  

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([7,7])
        if 'title' not in keywords:
            self.graph.setTitle('Count of Pitch and Quarter Length')
        if 'alpha' not in keywords:
            self.graph.alpha = .8


class PlotScatterWeightedPitchClassQuarterLength(PlotScatterWeighted):
    '''A graph of event, sorted by pitch class, over time.

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterWeightedPitchClassQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotScatterWeightedPitchClassQuarterLength(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotScatterWeightedPitchClassQuarterLength.*
        :width: 600

    '''

    values = ['pitchClass', 'quarterLength']
    def __init__(self, streamObj, *args, **keywords):
        PlotScatterWeighted.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n: n.quarterLength
        self.fy = lambda n: n.pitch.pitchClass
        self.fxTicks = self.ticksQuarterLength
        self.fyTicks = self.ticksPitchClassUsage

        self.data, xTicks, yTicks = self._extractData(xLog = self.xLog)

        self.graph = GraphScatterWeighted(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setAxisLabel('x', self._axisLabelQuarterLength(
                                remap=self.xLog))
        self.graph.setAxisLabel('y', 'Pitch Class')

        self.graph.setTicks('y', yTicks)  
        self.graph.setTicks('x', xTicks)  

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([7,7])
        if 'title' not in keywords:
            self.graph.setTitle('Count of Pitch Class and Quarter Length')
        if 'alpha' not in keywords:
            self.graph.alpha = .8



class PlotScatterWeightedPitchSpaceDynamicSymbol(PlotScatterWeighted):
    '''A graph of dynamics used by pitch space.

    >>> #_DOCS_SHOW s = converter.parse('/Desktop/schumann/opus41no1/movement2.xml')
    >>> s = converter.parse('tinynotation: 4/4 C4 d E f', makeNotation=False) #_DOCS_HIDE
    >>> s.insert(0.0, dynamics.Dynamic('pp')) #_DOCS_HIDE
    >>> s.insert(2.0, dynamics.Dynamic('ff')) #_DOCS_HIDE
    >>> p = graph.PlotScatterWeightedPitchSpaceDynamicSymbol(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW p = graph.PlotScatterWeightedPitchSpaceDynamicSymbol(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotScatterWeightedPitchSpaceDynamicSymbol.*
        :width: 600
        
    '''

    values = ['pitchClass', 'dynamicSymbol']
    def __init__(self, streamObj, *args, **keywords):
        PlotScatterWeighted.__init__(self, streamObj, *args, **keywords)

        self.fxTicks = self.ticksPitchSpaceUsage
        self.fyTicks = self.ticksDynamics

        # get data from correlate object
        am = correlate.ActivityMatch(self.streamObj)
        self.data = am.pitchToDynamic(dataPoints=False)

        xVals = [x for x, unused_y, unused_z in self.data]
        yVals = [y for unused_x, y, unused_z in self.data]

        xTicks = self.fxTicks(min(xVals), max(xVals))
        # ticks dynamics takes no args
        yTicks = self.fyTicks(min(yVals), max(yVals))


        self.graph = GraphScatterWeighted(*args, **keywords)
        self.graph.setData(self.data)

        self.graph.setAxisLabel('x', 'Pitch')
        self.graph.setAxisLabel('y', 'Dynamics')

        self.graph.setTicks('y', yTicks)  
        self.graph.setTicks('x', xTicks)  

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([10,10])
        if 'title' not in keywords:
            self.graph.setTitle('Count of Pitch Class and Quarter Length')
        if 'alpha' not in keywords:
            self.graph.alpha = .8
        # make smaller for axis display
        if 'tickFontSize' not in keywords:
            self.graph.tickFontSize = 7




class Plot3DBars(PlotStream):
    '''Base class for Stream plotting classes.
    '''
    format = '3dBars'
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

    def _extractData(self):
        # TODO: add support for chords
        data = {}
        xValues = []
        yValues = []

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, 
                         obj, matchPitchCount=False)
            else: # Note, just one value
                xSrc = [self.fx(obj)]
                ySrc = [self.fy(obj)]
            for x in xSrc:
                if x not in xValues:
                    xValues.append(x)
            for y in ySrc:
                if y not in yValues:
                    yValues.append(y)

#         for noteObj in sSrc.getElementsByClass(note.Note):
#             x = self.fx(noteObj)
#             if x not in xValues:
#                 xValues.append(x)
#             y = self.fy(noteObj)
#             if y not in yValues:
#                 yValues.append(y)
        xValues.sort()
        yValues.sort()
        # prepare data dictionary; need to pack all values
        # need to provide spacings even for zero values
        #for y in range(yValues[0], yValues[-1]+1):
        # better to use actual y values
        for y, unused_label in self.fyTicks(min(yValues), max(yValues)):
        #for y in yValues:
            data[y] = [[x, 0] for x in xValues]
        #print _MOD, 'data keys', data.keys()

        maxCount = 0

        for obj in sSrc.getElementsByClass([note.Note, chord.Chord]):
            if 'Chord' in obj.classes:
                xSrc, ySrc = self._extractChordDataTwoAxis(self.fx, self.fy, obj, matchPitchCount=True)
            else: # Note, just one value
                xSrc = [self.fx(obj)]
                ySrc = [self.fy(obj)]

            for i, x in enumerate(xSrc):
                y = ySrc[i]
                indexToIncrement = xValues.index(x)
                # second position stores increment
                data[y][indexToIncrement][1] += 1
                if data[y][indexToIncrement][1] > maxCount:
                    maxCount = data[y][indexToIncrement][1]


#         for noteObj in sSrc.getElementsByClass(note.Note):
#             indexToIncrement = xValues.index(self.fx(noteObj))
#             # second position stores increment
#             #print _MOD, fy(noteObj), indexToIncrement
# 
#             data[self.fy(noteObj)][indexToIncrement][1] += 1
#             if data[self.fy(noteObj)][indexToIncrement][1] > maxCount:
#                 maxCount = data[self.fy(noteObj)][indexToIncrement][1]

        # setting of ticks does not yet work in matplotlib
        xTicks = [(40, 'test')]
        yTicks = self.fyTicks(min(yValues), max(yValues))
        zTicks = []
        return data, xTicks, yTicks, zTicks


class Plot3DBarsPitchSpaceQuarterLength(Plot3DBars):
    '''A scatter plot of pitch and quarter length

    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.Plot3DBarsPitchSpaceQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW from music21.musicxml import testFiles
    >>> #_DOCS_SHOW s = converter.parse(testFiles.mozartTrioK581Excerpt)
    >>> #_DOCS_SHOW p = graph.Plot3DBarsPitchSpaceQuarterLength(s) 
    >>> p.id
    '3dBars-pitch-quarterLength'
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/Plot3DBarsPitchSpaceQuarterLength.*
        :width: 600
    '''

    values = ['pitch', 'quarterLength']
    def __init__(self, streamObj, *args, **keywords):
        Plot3DBars.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n: n.quarterLength
        self.fy = lambda n: n.pitch.ps
        self.fyTicks = self.ticksPitchSpaceUsage

        # will use self.fx and self.fxTick to extract data
        self.data, unused_xTicks, unused_yTicks, unused_zTicks = self._extractData()

        self.graph = Graph3DPolygonBars(*args, **keywords)
        self.graph.setData(self.data)

        #self.graph.setTicks('y', yTicks)
        #self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'MIDI Note Number')
        self.graph.setAxisLabel('x', 'Quarter Length')
        self.graph.setAxisLabel('z', '')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch by Quarter Length Count')
        if 'barWidth' not in keywords:
            self.graph.barWidth = .1
        if 'alpha' not in keywords:
            self.graph.alpha = .5




#-------------------------------------------------------------------------------
# plot multi stream

class PlotFeatures(PlotMultiStream):
    '''
    FeatureExtractors can be ids or classes. 
    '''
    format = 'features'

    def __init__(self, streamList, featureExtractors, labelList=None, *args, **keywords):
        if labelList is None:
            labelList = []
        PlotMultiStream.__init__(self, streamList, labelList, *args, **keywords)

        self.featureExtractors = featureExtractors

        # will use self.fx and self.fxTick to extract data
        self.data, xTicks, yTicks = self._extractData()

        self.graph = GraphGroupedVerticalBar(*args, **keywords)
        self.graph.grid = False
        self.graph.setData(self.data)

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)


        self.graph.xTickLabelRotation = 90
        self.graph.xTickLabelHorizontalAlignment = 'left'
        self.graph.xTickLabelVerticalAlignment = 'top'

        #self.graph.setAxisLabel('y', 'Count')
        #self.graph.setAxisLabel('x', 'Streams')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([10,6])
        if 'title' not in keywords:
            self.graph.setTitle(None)


    def _extractData(self):
        if len(self.labelList) != len(self.streamList):
            labelList = [x+1 for x in range(len(self.streamList))]
        else:
            labelList = self.labelList

        feList = []
        for fe in self.featureExtractors:
            if common.isStr(fe):
                post = features.extractorsById(fe)
                for sub in post:
                    feList.append(sub())
            else: # assume a class
                feList.append(fe())

        # store each stream in a data instance
        diList = []
        for s in self.streamList:
            di = features.DataInstance(s)
            diList.append(di)

        data = []
        for i, di in enumerate(diList):
            sub = {}
            for fe in feList:
                fe.setData(di)
                v = fe.extract().vector
                if len(v) == 1:
                    sub[fe.name] = v[0]
                # average all values?
                else:
                    sub[fe.name] = sum(v)/float(len(v))
            dataPoint = [labelList[i], sub]
            data.append(dataPoint)

        #environLocal.printDebug(['data', data])

        xTicks = []
        for x, label in enumerate(labelList):
            # first value needs to be center of bar
            # value of tick is the string entry
            xTicks.append([x+.5, '%s' % label])
        # alway have min and max
        yTicks = []
        return data, xTicks, yTicks






#-------------------------------------------------------------------------------
# public function
def _getPlotsToMake(*args, **keywords):
    '''
    Given `format` and `values` arguments, return a list of plot classes.
    '''
    plotClasses = [
        # histograms
        PlotHistogramPitchSpace, PlotHistogramPitchClass, PlotHistogramQuarterLength,
        # scatters
        PlotScatterPitchSpaceQuarterLength, 
        PlotScatterPitchClassQuarterLength, 
        PlotScatterPitchClassOffset,
        PlotScatterPitchSpaceDynamicSymbol,
        # offset based horizontal
        PlotHorizontalBarPitchSpaceOffset, PlotHorizontalBarPitchClassOffset,
        # weighted scatter
        PlotScatterWeightedPitchSpaceQuarterLength, PlotScatterWeightedPitchClassQuarterLength,
        PlotScatterWeightedPitchSpaceDynamicSymbol,
        # 3d graphs
        Plot3DBarsPitchSpaceQuarterLength,
        # windowed plots
        PlotWindowedKrumhanslSchmuckler,
        PlotWindowedKrumhanslKessler,
        PlotWindowedAardenEssen,
        PlotWindowedSimpleWeights,
        PlotWindowedBellmanBudge,
        PlotWindowedTemperleyKostkaPayne,
        PlotWindowedAmbitus,
        # instrumentation and part graphs
        PlotDolan,
    ]

    showFormat = ''
    values = []

    # can match by format
    if 'format' in keywords:
        showFormat = keywords['format']
    elif 'showFormat' in keywords:
        showFormat = keywords['showFormat']

    if 'values' in keywords:
        values = keywords['values'] # should be a list

    #environLocal.printDebug(['got args pre conversion', args])
    # if no args, use pianoroll
    foundClassName = None
    if len(args) == 0 and showFormat == '' and values == []:
        showFormat = 'horizontalbar'
        values = 'pitch'
    elif len(args) == 1:
        formatCandidate = userFormatsToFormat(args[0])
        #environLocal.printDebug(['formatCandidate', formatCandidate])
        match = False
        if formatCandidate in FORMATS:
            showFormat = formatCandidate
            values = 'pitch'
            match = True
        # if one arg, assume it is a histogram value
        if formatCandidate in VALUES:
            showFormat = 'histogram'
            values = [args[0]]
            match = True
        # permit directly matching the class name
        if not match:
            for className in plotClasses:
                if formatCandidate in str(className).lower():
                    match = True
                    foundClassName = className
                    break
    elif len(args) > 1:
        showFormat = userFormatsToFormat(args[0])
        values = args[1:] # get all remaining
    if not common.isListLike(values):
        values = [values]
    # make sure we have a list
    values = list(values)

    #environLocal.printDebug(['got args post conversion', 'format', showFormat, 'values', values, 'foundClassName', foundClassName])

    # clean data and process synonyms
    # will return unaltered if no change
    showFormat = userFormatsToFormat(showFormat) 
    values = userValuesToValues(values)
    #environLocal.printDebug(['plotStream: format, values', showFormat , values])

    plotMake = []
    if showFormat.lower() == 'all':
        plotMake = plotClasses
    elif foundClassName is not None:
        plotMake = [foundClassName] # place in a list
    else:
        plotMakeCandidates = [] # store pairs of score, class
        for plotClassName in plotClasses:
            # try to match by complete class name
            if plotClassName.__name__.lower() == showFormat.lower():
                #environLocal.printDebug(['got plot class:', plotClassName])
                plotMake.append(plotClassName)

            # try direct match of format and values
            plotClassNameValues = [x.lower() for x in plotClassName.values]
            plotClassNameFormat = plotClassName.format.lower()
            if plotClassNameFormat == showFormat.lower():
                #environLocal.printDebug(['matching format', showFormat])
                # see if a matching set of values is specified
                # normally plots need to match all values 
                match = []
                for requestedValue in values:
                    if requestedValue is None: 
                        continue
                    if (requestedValue.lower() in plotClassNameValues):
                        # do not allow the same value to be requested
                        if requestedValue not in match:
                            match.append(requestedValue)
                if len(match) == len(values):
                    plotMake.append(plotClassName)
                else:
                    sortTuple = (len(match), plotClassName)
                    plotMakeCandidates.append(sortTuple)

        # if no matches, try something more drastic:
        if len(plotMake) == 0:
            if len(plotMakeCandidates) > 0:
                plotMakeCandidates.sort(key=lambda x: (x[0], x[1].__name__.lower()) )
                # last in list has highest score; second item is class
                plotMake.append(plotMakeCandidates[-1][1])
            else:
                for plotClassName in plotClasses:
                    # create a list of all possible identifiers
                    plotClassIdentifiers = [plotClassName.format.lower()]
                    plotClassIdentifiers += [x.lower() for x in 
                                            plotClassName.values]
                    # combine format and values args
                    for requestedValue in [showFormat] + values:
                        if requestedValue.lower() in plotClassIdentifiers:
                            plotMake.append(plotClassName)
                            break
                    if len(plotMake) > 0: # found a match
                        break
    #environLocal.printDebug(['plotMake', plotMake])
    return plotMake

def plotStream(streamObj, *args, **keywords):
    '''Given a stream and any keyword configuration arguments, create and display a plot.

    Note: plots requires matplotib to be installed.

    Plot methods can be specified as additional arguments or by keyword. 
    Two keyword arguments can be given: `format` and `values`. 
    If positional arguments are given, the first is taken as `format` 
    and the rest are collected as `values`. If `format` is the class 
    name, that class is collected. Additionally, every 
    :class:`~music21.graph.PlotStream` subclass defines one `format` 
    string and a list of `values` strings. The `format` parameter 
    defines the type of Graph (e.g. scatter, histogram, colorGrid). The 
    `values` list defines what values are graphed 
    (e.g. quarterLength, pitch, pitchClass). 

    If a user provides a `format` and one or more `values` strings, a plot with the corresponding profile, if found, will be generated. If not, the first Plot to match any of the defined specifiers will be created. 

    In the case of :class:`~music21.graph.PlotWindowedAnalysis` subclasses, the :class:`~music21.analysis.discrete.DiscreteAnalysis` subclass :attr:`~music21.analysis.discrete.DiscreteAnalysis.indentifiers` list is added to the Plot's `values` list. 

    Available plots include the following:

    * :class:`~music21.graph.PlotHistogramPitchSpace`
    * :class:`~music21.graph.PlotHistogramPitchClass`
    * :class:`~music21.graph.PlotHistogramQuarterLength`
    * :class:`~music21.graph.PlotScatterPitchSpaceQuarterLength`
    * :class:`~music21.graph.PlotScatterPitchClassQuarterLength`
    * :class:`~music21.graph.PlotScatterPitchClassOffset`
    * :class:`~music21.graph.PlotScatterPitchSpaceDynamicSymbol`
    * :class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`
    * :class:`~music21.graph.PlotHorizontalBarPitchClassOffset`
    * :class:`~music21.graph.PlotScatterWeightedPitchSpaceQuarterLength`
    * :class:`~music21.graph.PlotScatterWeightedPitchClassQuarterLength`
    * :class:`~music21.graph.PlotScatterWeightedPitchSpaceDynamicSymbol`
    * :class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`
    * :class:`~music21.graph.PlotWindowedKrumhanslSchmuckler`
    * :class:`~music21.graph.PlotWindowedKrumhanslKessler`
    * :class:`~music21.graph.PlotWindowedAardenEssen`
    * :class:`~music21.graph.PlotWindowedSimpleWeights`
    * :class:`~music21.graph.PlotWindowedBellmanBudge`
    * :class:`~music21.graph.PlotWindowedTemperleyKostkaPayne`
    * :class:`~music21.graph.PlotWindowedAmbitus`
    * :class:`~music21.graph.PlotDolan`


    
    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> s.plot('histogram', 'pitch', doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW s.plot('histogram', 'pitch')

    .. image:: images/PlotHistogramPitchSpace.*
        :width: 600


    >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
    >>> s.plot('pianoroll', doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
    >>> #_DOCS_SHOW s.plot('pianoroll')

    .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        :width: 600

    '''
    plotMake = _getPlotsToMake(*args, **keywords)
    #environLocal.printDebug(['plotClassName found', plotMake])
    for plotClassName in plotMake:
        obj = plotClassName(streamObj, *args, **keywords)
        obj.process()

        

#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
   
    def runTest(self):
        pass
   
    def testBasic(self):
        '''Tests of graph primitives. These are used for producing exaple graphics.
        '''
        a = GraphScatter(doneAction='write', title='x to x*x', alpha=1)
        data = [(x, x*x) for x in range(50)]
        a.setData(data)
        a.process()
        
        del a

        a = GraphHistogram(doneAction='write', title='50 x with random(30) y counts')
        data = [(x, random.choice(range(30))) for x in range(50)]
        a.setData(data)
        a.process()
        
        del a

        a = Graph3DPolygonBars(doneAction='write', title='50 x with random values increase by 10 per x', alpha=.8, colors=['b', 'g'])
        data = {1:[], 2:[], 3:[], 4:[], 5:[]}
        for i in range(len(data.keys())):
            q = [(x, random.choice(range(10*i, 10*(i+1)))) for x in range(50)]
            dk = list(data.keys())
            data[dk[i]] = q
        a.setData(data)
        a.process()
        
        del a


    def test3DGraph(self):
        a = Graph3DPolygonBars(doneAction='write', title='50 x with random values increase by 10 per x', alpha=.8, colors=['b', 'g'])
        data = {1:[], 2:[], 3:[], 4:[], 5:[]}
        for i in range(len(data.keys())):
            q = [(x, random.choice(range(10*i, 10*(i+1)))) for x in range(50)]
            data[data.keys()[i]] = q
        a.setData(data)


        xPoints = []
        xTicks = []
        for unused_key, value in data.items():
            for x, unused_y in value:
                if x not in xPoints:
                    xPoints.append(x)
                    xTicks.append(['r', x])

        # this does not work, and instead causes massive distortion
        #a.setTicks('x', xTicks)
        a.process()
        


    def testBrokenHorizontal(self):
        data = []
        for label in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']:
            points = []
            for unused_pairs in range(10):
                start = random.choice(range(150))
                end = start + random.choice(range(50))
                points.append((start, end))
            data.append([label, points])
        #environLocal.printDebug(['data points', data])
       
        a = GraphHorizontalBar()
        a.setData(data)
        a.process()
        


    def testPlotHorizontalBarPitchSpaceOffset(self):
        a = corpus.parse('bach/bwv57.8')
        # do not need to call flat version
        b = PlotHorizontalBarPitchSpaceOffset(a.parts[0], title='Bach (soprano voice)')
        b.process()
        

        b = PlotHorizontalBarPitchSpaceOffset(a, title='Bach (all parts)')
        b.process()
        



    def testPlotHorizontalBarPitchClassOffset(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHorizontalBarPitchClassOffset(a.parts[0], title='Bach (soprano voice)')
        b.process()
        

        a = corpus.parse('bach/bwv57.8')
        b = PlotHorizontalBarPitchClassOffset(a.parts[0].measures(3,6), title='Bach (soprano voice, mm 3-6)')
        b.process()
        



    def testScatterWeighted(self):
        data = []
        for i in range(50):
            x = random.choice(range(20))
            y = random.choice(range(20))
            z = random.choice(range(1, 20))
            data.append([x, y, z])
       
        a = GraphScatterWeighted()
        a.setData(data)
        a.process()

    def testPlotScatterWeightedPitchSpaceQuarterLength(self):
        for xLog in [True, False]:
            a = corpus.parse('bach/bwv57.8')
            b = PlotScatterWeightedPitchSpaceQuarterLength(a.parts[0].flat,
                            title='Pitch Space Bach (soprano voice)',
                            xLog=xLog)
            b.process()
    
            a = corpus.parse('bach/bwv57.8')
            b = PlotScatterWeightedPitchClassQuarterLength(a.parts[0].flat,
                            title='Pitch Class Bach (soprano voice)',
                            xLog=xLog)
            b.process()


    def testPlotPitchSpace(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramPitchSpace(a.parts[0].flat, title='Bach (soprano voice)')
        b.process()
        

    def testPlotPitchClass(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramPitchClass(a.parts[0].flat, title='Bach (soprano voice)')
        b.process()

    def testPlotQuarterLength(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramQuarterLength(a.parts[0].flat, title='Bach (soprano voice)')
        b.process()


    def testPlotScatterPitchSpaceQuarterLength(self):
        for xLog in [True, False]:

            a = corpus.parse('bach/bwv57.8')
            b = PlotScatterPitchSpaceQuarterLength(a.parts[0].flat, title='Bach (soprano voice)', xLog=xLog)
            b.process()
    
            b = PlotScatterPitchClassQuarterLength(a.parts[0].flat, title='Bach (soprano voice)', xLog=xLog)
            b.process()

    def testPlotScatterPitchClassOffset(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotScatterPitchClassOffset(a.parts[0].flat, title='Bach (soprano voice)')
        b.process()


    def testPlotScatterPitchSpaceDynamicSymbol(self):
        a = corpus.parse('schumann/opus41no1', 2)
        b = PlotScatterPitchSpaceDynamicSymbol(a.parts[0].flat, title='Schumann (soprano voice)')
        b.process()
        

        b = PlotScatterWeightedPitchSpaceDynamicSymbol(a.parts[0].flat, title='Schumann (soprano voice)')
        b.process()
        



    def testPlot3DPitchSpaceQuarterLengthCount(self):
        a = corpus.parse('bach/bwv57.8')
        b = Plot3DBarsPitchSpaceQuarterLength(a.flat, title='Bach (soprano voice)')
        b.process()
        



    def testAll(self):
        a = corpus.parse('bach/bwv57.8')
        plotStream(a.flat, 'all')


    def writeAllGraphs(self):
        '''
        Write a graphic file for all graphs, 
        naming them after the appropriate class. 
        This is used to generate documentation samples.
        '''

        # get some data
        data3DPolygonBars = {1:[], 2:[], 3:[]}
        for i in range(len(data3DPolygonBars.keys())):
            q = [(x, random.choice(range(10*(i+1)))) for x in range(20)]
            data3DPolygonBars[data3DPolygonBars.keys()[i]] = q

        # pair data with class name
        graphClasses = [
        (GraphHorizontalBar, 
            [('Chopin', [(1810, 1849-1810)]), ('Schumanns', [(1810, 1856-1810), (1819, 1896-1819)]), ('Brahms', [(1833, 1897-1833)])]
        ),
        (GraphScatterWeighted, 
            [(23, 15, 234), (10, 23, 12), (4, 23, 5), (15, 18, 120)]),
        (GraphScatter, 
            [(x, x*x) for x in range(50)]),
        (GraphHistogram, 
            [(x, random.choice(range(30))) for x in range(50)]),
        (Graph3DPolygonBars, data3DPolygonBars),
        (GraphColorGridLegend, 
        [('Major', [('C', '#00AA55'), ('D', '#5600FF'), ('G', '#2B00FF')]),
         ('Minor', [('C', '#004600'), ('D', '#00009b'), ('G', '#00009B')]),]
        ),
        (GraphColorGrid, [['#8968CD', '#96CDCD', '#CD4F39'], 
                ['#FFD600', '#FF5600'], 
                ['#201a2b', '#8f73bf', '#a080d5', '#6495ED', '#FF83FA'],
               ]
        ),

        ]

        for graphClassName, data in graphClasses:
            obj = graphClassName(doneAction=None)
            obj.setData(data) # add data here
            obj.process()
            fn = obj.__class__.__name__ + '.png'
            fp = os.path.join(environLocal.getRootTempDir(), fn)
            environLocal.printDebug(['writing fp:', fp])
            obj.write(fp)


    def writeGraphColorGrid(self):
        # this is temporary
        a = GraphColorGrid(doneAction=None)
        data = [['#525252', '#5f5f5f', '#797979', '#858585', '#727272', '#6c6c6c', '#8c8c8c', '#8c8c8c', '#6c6c6c', '#999999', '#999999', '#797979', '#6c6c6c', '#5f5f5f', '#525252', '#464646', '#3f3f3f', '#3f3f3f', '#4c4c4c', '#4c4c4c', '#797979', '#797979', '#4c4c4c', '#4c4c4c', '#525252', '#5f5f5f', '#797979', '#858585', '#727272', '#6c6c6c'], ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#797979', '#6c6c6c', '#5f5f5f', '#5f5f5f', '#858585', '#797979', '#797979', '#797979', '#797979', '#797979', '#797979', '#858585', '#929292', '#999999'], ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#8c8c8c', '#8c8c8c', '#8c8c8c', '#858585', '#797979', '#858585', '#929292', '#999999'], ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#8c8c8c', '#929292', '#999999'], ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999'], ['#999999', '#999999', '#999999', '#999999', '#999999']]
        a.setData(data)
        a.process()
        fn = a.__class__.__name__ + '.png'
        fp = os.path.join(environLocal.getRootTempDir(), fn)

        a.write(fp)
        



    def writeAllPlots(self):
        '''Write a graphic file for all graphs, naming them after the appropriate class. This is used to generate documentation samples.
        '''
        # TODO: need to add strip() ties here; but need stripTies on Score
        from music21.musicxml import testFiles 

        plotClasses = [
        # histograms
        (PlotHistogramPitchSpace, None, None), 
        (PlotHistogramPitchClass, None, None), 
        (PlotHistogramQuarterLength, None, None),
        # scatters
        (PlotScatterPitchSpaceQuarterLength, None, None), 
        (PlotScatterPitchClassQuarterLength, None, None), 
        (PlotScatterPitchClassOffset, None, None),
        (PlotScatterPitchSpaceDynamicSymbol, corpus.getWork('schumann/opus41no1', 2), 'Schumann Opus 41 No 1'),

        # offset based horizontal
        (PlotHorizontalBarPitchSpaceOffset, None, None), 
        (PlotHorizontalBarPitchClassOffset, None, None),
        # weighted scatter
        (PlotScatterWeightedPitchSpaceQuarterLength, None, None), (PlotScatterWeightedPitchClassQuarterLength, None, None),
        (PlotScatterWeightedPitchSpaceDynamicSymbol, corpus.getWork('schumann/opus41no1', 2), 'Schumann Opus 41 No 1'),


        # 3d graphs
        (Plot3DBarsPitchSpaceQuarterLength, testFiles.mozartTrioK581Excerpt, 'Mozart Trio K581 Excerpt'), # @UndefinedVariable

        (PlotWindowedKrumhanslSchmuckler, corpus.getWork('bach/bwv66.6.xml'), 'Bach BWV 66.6'),
        (PlotWindowedAmbitus, corpus.getWork('bach/bwv66.6.xml'), 'Bach BWV 66.6'),

        ]



        sDefault = corpus.parse('bach/bwv57.8')

        for plotClassName, work, titleStr in plotClasses:
            if work == None:
                s = sDefault

            else: # expecting data
                s = converter.parse(work)

            if titleStr != None:
                obj = plotClassName(s, doneAction=None, title=titleStr)
            else:
                obj = plotClassName(s, doneAction=None)

            obj.process()
            fn = obj.__class__.__name__ + '.png'
            fp = os.path.join(environLocal.getRootTempDir(), fn)
            environLocal.printDebug(['writing fp:', fp])
            obj.write(fp)


    def writeGraphingDocs(self):
        '''Write graphing examples for the docs
        '''
        post = []

        a = GraphScatter(doneAction=None)
        data = [(x, x*x) for x in range(50)]
        a.setData(data)
        post.append([a, 'graphing-01'])

        a = GraphScatter(title='Exponential Graph', alpha=1, doneAction=None)
        data = [(x, x*x) for x in range(50)]
        a.setData(data)
        post.append([a, 'graphing-02'])

        a = GraphHistogram(doneAction=None)
        data = [(x, random.choice(range(30))) for x in range(50)]
        a.setData(data)
        post.append([a, 'graphing-03'])

        a = Graph3DPolygonBars(doneAction=None) 
        data = {1:[], 2:[], 3:[]}
        for i in range(len(data.keys())):
            q = [(x, random.choice(range(10*(i+1)))) for x in range(20)]
            data[data.keys()[i]] = q
        a.setData(data) 
        post.append([a, 'graphing-04'])


        b = Graph3DPolygonBars(title='Random Data', alpha=.8,\
        barWidth=.2, doneAction=None, colors=['b','r','g']) 
        b.setData(data)
        post.append([b, 'graphing-05'])


        for obj, name in post:
            obj.process()
            fn = name + '.png'
            fp = os.path.join(environLocal.getRootTempDir(), fn)
            environLocal.printDebug(['writing fp:', fp])
            obj.write(fp)
            



class Test(unittest.TestCase):
   
    def runTest(self):
        pass
   

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)



    def testBasic(self):
        a = GraphScatter(doneAction=None, title='x to x*x', alpha=1)
        data = [(x, x*x) for x in range(50)]
        a.setData(data)
        a.process()
        
        del a

        a = GraphHistogram(doneAction=None, title='50 x with random(30) y counts')
        data = [(x, random.choice(range(30))) for x in range(50)]
        a.setData(data)
        a.process()
        
        del a


        a = Graph3DPolygonBars(doneAction=None, title='50 x with random values increase by 10 per x', alpha=.8, colors=['b', 'g'])
        data = {1:[], 2:[], 3:[], 4:[], 5:[]}
        for i in range(len(data.keys())):
            q = [(x, random.choice(range(10*i, 10*(i+1)))) for x in range(50)]
            dk = list(data.keys())
            data[dk[i]] = q
        a.setData(data)
        a.process()
        
        del a

    def testBrokenHorizontal(self):
        data = []
        for label in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']:
            points = []
            for i in range(10):
                start = random.choice(range(150))
                end = start + random.choice(range(50))
                points.append((start, end))
            data.append([label, points])
       
        a = GraphHorizontalBar(doneAction=None)
        a.setData(data)
        a.process()
        



    def testPlotPitchSpaceDurationCount(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotScatterWeightedPitchSpaceQuarterLength(a.parts[0].flat, doneAction=None,
                        title='Bach (soprano voice)')
        b.process()
        

    def testPlotPitchSpace(self):
        a = corpus.parse('bach')
        b = PlotHistogramPitchSpace(a.parts[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()
        

    def testPlotPitchClass(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramPitchClass(a.parts[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()
        

    def testPlotQuarterLength(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotHistogramQuarterLength(a.parts[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()
        

    def testPitchDuration(self):
        a = corpus.parse('schoenberg/opus19', 2)
        b = PlotScatterPitchSpaceDynamicSymbol(a.parts[0].flat, doneAction=None, title='Schoenberg (piano)')
        b.process()
        

        b = PlotScatterWeightedPitchSpaceDynamicSymbol(a.parts[0].flat, doneAction=None, title='Schoenberg (piano)')
        b.process()
        

        
    def testPlotWindowed(self, doneAction=None):
        if doneAction != None:
            fp = random.choice(corpus.getBachChorales('.xml'))
            unused_directory, fn = os.path.split(fp)
            a = corpus.parse(fp)
            windowStep = 3 #'2'
            #windowStep = random.choice([1,2,4,8,16,32])
            #a.show()
        else:
            a = corpus.parse('bach/bwv66.6')
            fn = 'bach/bwv66.6'
            windowStep = 20 # set high to be fast

#         b = PlotWindowedAmbitus(a.parts, title='Bach Ambitus',
#             minWindow=1, maxWindow=8, windowStep=3,
#             doneAction=doneAction)
#         b.process()

        b = PlotWindowedKrumhanslSchmuckler(a, title=fn,
            minWindow=1, windowStep=windowStep, 
            doneAction=doneAction, dpi=300)
        b.process()
        



    def testAll(self):
        a = corpus.parse('bach/bwv57.8')
        plotStream(a.flat, doneAction=None)


    
    def testColorGridLegend(self, doneAction=None):
        ks = discrete.KrumhanslSchmuckler()
        data = ks.solutionLegend()
        #print data
        a = GraphColorGridLegend(doneAction=doneAction, dpi=300)
        a.setData(data)
        a.process()
        

    def testPianoRollFromOpus(self):
        o = corpus.parse('josquin/laDeplorationDeLaMorteDeJohannesOckeghem')
        s = o.mergeScores()

        b = PlotHorizontalBarPitchClassOffset(s, doneAction=None)
        b.process()
        



    def testGraphNetworxGraph(self):
        extm = _getExtendedModules() #@UnusedVariable

        if extm.networkx is not None:
            b = GraphNetworxGraph(doneAction=None)
            #b = GraphNetworxGraph()
            b.process()
            


    def testPlotChordsA(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        b = PlotHistogram(stream.Stream(), doneAction=None)
        c = chord.Chord(['b', 'c', 'd'])
        fx = lambda n: n.pitch.midi
        self.assertEqual(b._extractChordDataOneAxis(fx, c), [71, 60, 62])


        s = stream.Stream()
        s.append(chord.Chord(['b', 'c#', 'd']))
        s.append(note.Note('c3'))
        s.append(note.Note('c5'))
        b = PlotHistogramPitchSpace(s, doneAction=None)
        b.process()
        
        #b.write()
        self.assertEqual(b.data, [(48, 1), (61, 1), (62, 1), (71, 1), (72, 1)])

        s = stream.Stream()
        s.append(sc.getChord('e3','a3'))
        s.append(note.Note('c3'))
        b = PlotHistogramPitchClass(s, doneAction=None)
        b.process()
        
        #b.write()
        self.assertEqual(b.data, [(0, 1), (4, 1), (5, 1), (7, 1), (9, 1)])

        s = stream.Stream()
        s.append(sc.getChord('e3','a3', quarterLength=2))
        s.append(note.Note('c3', quarterLength=.5))
        b = PlotHistogramQuarterLength(s, doneAction=None)
        b.process()
        
        #b.write()
        self.assertEqual(b.data, [(0, 1), (1, 1)])


        # test scatter plots


        b = PlotScatter(stream.Stream(), doneAction=None)
        c = chord.Chord(['b', 'c', 'd'], quarterLength=.5)
        fx = lambda n: n.pitch.midi
        fy = lambda n: n.quarterLength
        self.assertEqual(b._extractChordDataTwoAxis(fx, fy, c), ([71, 60, 62], [0.5]))
        c = chord.Chord(['b', 'c', 'd'], quarterLength=.5)
        # matching the number of pitches for each data point may be needed
        self.assertEqual(b._extractChordDataTwoAxis(fx, fy, c, matchPitchCount=True), ([71, 60, 62], [0.5, 0.5, 0.5]) )

    def testPlotChordsA2(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        s.append(sc.getChord('b3','c5', quarterLength=1.5))
        s.append(note.Note('c3', quarterLength=2))
        b = PlotScatterPitchSpaceQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data, [[2, 48], [0.5, 52], [0.5, 53], [0.5, 55], [0.5, 57], 
                                  [1.5, 59], [1.5, 60], [1.5, 62], [1.5, 64], [1.5, 65], 
                                  [1.5, 67], [1.5, 69], [1.5, 71], [1.5, 72]])
        #b.write()

    def testPlotChordsA3(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        s.append(sc.getChord('b3','c5', quarterLength=1.5))
        s.append(note.Note('c3', quarterLength=2))
        b = PlotScatterPitchClassQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data, [[2, 0], [0.5, 4], [0.5, 5], [0.5, 7], [0.5, 9], [1.5, 11], 
                                  [1.5, 0], [1.5, 2], [1.5, 4], [1.5, 5], [1.5, 7], [1.5, 9], 
                                  [1.5, 11], [1.5, 0]] )
        #b.write()

    def testPlotChordsA4(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3','e4', quarterLength=1.5))
        s.append(note.Note('d3', quarterLength=2))
        self.assertEqual([e.offset for e in s], [0.0, 0.5, 2.5, 4.0])

        #s.show()
        b = PlotScatterPitchClassOffset(s, doneAction=None)
        b.process()
        
        self.assertEqual(b.data, [[0.5, 0], [4.0, 2], [0.0, 4], [0.0, 5], [0.0, 7], 
                                  [0.0, 9], [2.5, 11], [2.5, 0], [2.5, 2], [2.5, 4]] )
        #b.write()

    def testPlotChordsA5(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(dynamics.Dynamic('f'))
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(dynamics.Dynamic('p'))
        s.append(sc.getChord('b3','e4', quarterLength=1.5))
        #s.append(note.Note('d3', quarterLength=2))

        #s.show()
        b = PlotScatterPitchSpaceDynamicSymbol(s, doneAction=None)
        b.process()
        
        self.assertEqual(b.data, [[52, 8], [53, 8], [55, 8], [57, 8], [59, 8], [59, 5], 
                                  [60, 8], [60, 5], [62, 8], [62, 5], [64, 8], [64, 5]])
        #b.write()


    def testPlotChordsB(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3','e4', quarterLength=1.5))

        b = PlotHorizontalBarPitchClassOffset(s, doneAction=None)
        b.process()
        
        self.assertEqual(b.data, [['C', [(0.0, 1.0), (1.5, 1.5)]], ['', []], 
                                  ['D', [(1.5, 1.5)]], ['', []], ['E', [(1.0, 0.5), (1.5, 1.5)]],
                                   ['F', [(1.0, 0.5)]], ['', []], ['G', [(1.0, 0.5)]], 
                                   ['', []], ['A', [(1.0, 0.5)]], ['', []], ['B', [(1.5, 1.5)]]] )
        #b.write()


        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3','e4', quarterLength=1.5))

        b = PlotHorizontalBarPitchSpaceOffset(s, doneAction=None)
        b.process()
        
        self.assertEqual(b.data, [['C3', [(0.0, 1.0)]], ['', []], ['', []], ['', []], 
                                  ['E3', [(1.0, 0.5)]], ['F3', [(1.0, 0.5)]], ['', []], 
                                  ['G3', [(1.0, 0.5)]], ['', []], ['A3', [(1.0, 0.5)]], ['', []], 
                                  ['B3', [(1.5, 1.5)]], ['C4', [(1.5, 1.5)]], ['', []], 
                                  ['D4', [(1.5, 1.5)]], ['', []], ['E4', [(1.5, 1.5)]]] )
        #b.write()


        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3','e4', quarterLength=1.5))
        s.append(sc.getChord('f4','g5', quarterLength=3))
        s.append(sc.getChord('f4','g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))

        b = PlotScatterWeightedPitchSpaceQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data, [[0.5, 48, 0], [1.0, 48, 1], [1.5, 48, 0], [3, 48, 0], [0.5, 49, 0], [1.0, 49, 0], [1.5, 49, 0], [3, 49, 0], [0.5, 50, 0], [1.0, 50, 0], [1.5, 50, 0], [3, 50, 0], [0.5, 51, 0], [1.0, 51, 0], [1.5, 51, 0], [3, 51, 0], [0.5, 52, 1], [1.0, 52, 0], [1.5, 52, 0], [3, 52, 0], [0.5, 53, 1], [1.0, 53, 0], [1.5, 53, 0], [3, 53, 0], [0.5, 54, 0], [1.0, 54, 0], [1.5, 54, 0], [3, 54, 0], [0.5, 55, 1], [1.0, 55, 0], [1.5, 55, 0], [3, 55, 0], [0.5, 56, 0], [1.0, 56, 0], [1.5, 56, 0], [3, 56, 0], [0.5, 57, 1], [1.0, 57, 0], [1.5, 57, 0], [3, 57, 0], [0.5, 58, 0], [1.0, 58, 0], [1.5, 58, 0], [3, 58, 0], [0.5, 59, 0], [1.0, 59, 0], [1.5, 59, 1], [3, 59, 0], [0.5, 60, 0], [1.0, 60, 0], [1.5, 60, 1], [3, 60, 0], [0.5, 61, 0], [1.0, 61, 0], [1.5, 61, 0], [3, 61, 0], [0.5, 62, 0], [1.0, 62, 0], [1.5, 62, 1], [3, 62, 0], [0.5, 63, 0], [1.0, 63, 0], [1.5, 63, 0], [3, 63, 0], [0.5, 64, 0], [1.0, 64, 0], [1.5, 64, 1], [3, 64, 0], [0.5, 65, 0], [1.0, 65, 0], [1.5, 65, 0], [3, 65, 2], [0.5, 66, 0], [1.0, 66, 0], [1.5, 66, 0], [3, 66, 0], [0.5, 67, 0], [1.0, 67, 0], [1.5, 67, 0], [3, 67, 2], [0.5, 68, 0], [1.0, 68, 0], [1.5, 68, 0], [3, 68, 0], [0.5, 69, 0], [1.0, 69, 0], [1.5, 69, 0], [3, 69, 2], [0.5, 70, 0], [1.0, 70, 0], [1.5, 70, 0], [3, 70, 0], [0.5, 71, 0], [1.0, 71, 0], [1.5, 71, 0], [3, 71, 2], [0.5, 72, 0], [1.0, 72, 0], [1.5, 72, 0], [3, 72, 3], [0.5, 73, 0], [1.0, 73, 0], [1.5, 73, 0], [3, 73, 0], [0.5, 74, 0], [1.0, 74, 0], [1.5, 74, 0], [3, 74, 2], [0.5, 75, 0], [1.0, 75, 0], [1.5, 75, 0], [3, 75, 0], [0.5, 76, 0], [1.0, 76, 0], [1.5, 76, 0], [3, 76, 2], [0.5, 77, 0], [1.0, 77, 0], [1.5, 77, 0], [3, 77, 2], [0.5, 78, 0], [1.0, 78, 0], [1.5, 78, 0], [3, 78, 0], [0.5, 79, 0], [1.0, 79, 0], [1.5, 79, 0], [3, 79, 2]] )
        #b.write()



        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(sc.getChord('b3','e4', quarterLength=1.5))
        s.append(sc.getChord('f4','g5', quarterLength=3))
        s.append(sc.getChord('f4','g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))

        b = PlotScatterWeightedPitchClassQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data, [[0.5, 0, 0], [1.0, 0, 1], [1.5, 0, 1], [3, 0, 3], [0.5, 1, 0], [1.0, 1, 0], [1.5, 1, 0], [3, 1, 0], [0.5, 2, 0], [1.0, 2, 0], [1.5, 2, 1], [3, 2, 2], [0.5, 3, 0], [1.0, 3, 0], [1.5, 3, 0], [3, 3, 0], [0.5, 4, 1], [1.0, 4, 0], [1.5, 4, 1], [3, 4, 2], [0.5, 5, 1], [1.0, 5, 0], [1.5, 5, 0], [3, 5, 4], [0.5, 6, 0], [1.0, 6, 0], [1.5, 6, 0], [3, 6, 0], [0.5, 7, 1], [1.0, 7, 0], [1.5, 7, 0], [3, 7, 4], [0.5, 8, 0], [1.0, 8, 0], [1.5, 8, 0], [3, 8, 0], [0.5, 9, 1], [1.0, 9, 0], [1.5, 9, 0], [3, 9, 2], [0.5, 10, 0], [1.0, 10, 0], [1.5, 10, 0], [3, 10, 0], [0.5, 11, 0], [1.0, 11, 0], [1.5, 11, 1], [3, 11, 2]])
        #b.write()

    def testPlotChordsB2(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(dynamics.Dynamic('f'))
        #s.append(note.Note('c3'))
        c = sc.getChord('e3','a3', quarterLength=.5)
        self.assertEqual(repr(c), '<music21.chord.Chord E3 F3 G3 A3>')
        self.assertEqual([n.pitch.ps for n in c], [52.0, 53.0, 55.0, 57.0])
        s.append(c)
        #s.append(note.Note('c3', quarterLength=2))
        s.append(dynamics.Dynamic('mf'))
        s.append(sc.getChord('b3','e4', quarterLength=1.5))
        s.append(dynamics.Dynamic('pp'))
        s.append(sc.getChord('f4','g5', quarterLength=3))
        s.append(sc.getChord('f4','g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))

        b = PlotScatterWeightedPitchSpaceDynamicSymbol(s, doneAction=None, xLog=False)
        b.process()
        
        self.maxDiff = 2048
        # TODO: Is this right? why are the old dynamics still active?
        self.assertEqual(b.data, [(52.0, 8, 1), (53.0, 8, 1), (55.0, 8, 1), (57.0, 8, 1), 
                                  (59.0, 8, 1), (59.0, 7, 1), (60.0, 8, 1), (60.0, 7, 1), 
                                  (62.0, 8, 1), (62.0, 7, 1), (64.0, 8, 1), (64.0, 7, 1), 
                                  (65.0, 7, 1), (65.0, 4, 2), 
                                  (67.0, 7, 1), (67.0, 4, 2), (69.0, 7, 1), (69.0, 4, 2), 
                                  (71.0, 7, 1), (71.0, 4, 2), (72.0, 7, 1), (72.0, 4, 3), # C x 3
                                  (74.0, 7, 1), (74.0, 4, 2), (76.0, 7, 1), (76.0, 4, 2), 
                                  (77.0, 7, 1), (77.0, 4, 2), (79.0, 7, 1), (79.0, 4, 2)])
        #b.write()

    def testPlotChordsB3(self):
        from music21 import stream, scale
        sc = scale.MajorScale('c4')


        s = stream.Stream()
        s.append(dynamics.Dynamic('f'))
        s.append(note.Note('c3'))
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        s.append(dynamics.Dynamic('mf'))
        s.append(sc.getChord('b3','e4', quarterLength=1.5))
        s.append(dynamics.Dynamic('pp'))
        s.append(sc.getChord('f4','g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))

        b = Plot3DBarsPitchSpaceQuarterLength(s, doneAction=None, xLog=False)
        b.process()
        
        self.assertEqual(b.data, {48: [[0.5, 0], [1.0, 1], [1.5, 0], [3, 0]], 49: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 50: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 51: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 52: [[0.5, 1], [1.0, 0], [1.5, 0], [3, 0]], 53: [[0.5, 1], [1.0, 0], [1.5, 0], [3, 0]], 54: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 55: [[0.5, 1], [1.0, 0], [1.5, 0], [3, 0]], 56: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 57: [[0.5, 1], [1.0, 0], [1.5, 0], [3, 0]], 58: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 59: [[0.5, 0], [1.0, 0], [1.5, 1], [3, 0]], 60: [[0.5, 0], [1.0, 0], [1.5, 1], [3, 0]], 61: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 62: [[0.5, 0], [1.0, 0], [1.5, 1], [3, 0]], 63: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 64: [[0.5, 0], [1.0, 0], [1.5, 1], [3, 0]], 65: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 1]], 66: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 67: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 1]], 68: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 69: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 1]], 70: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 71: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 1]], 72: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 2]], 73: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 74: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 1]], 75: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 76: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 1]], 77: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 1]], 78: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 0]], 79: [[0.5, 0], [1.0, 0], [1.5, 0], [3, 1]]})
        #b.write()



    def testPlotChordsC(self):
        from music21 import stream, scale

        sc = scale.MajorScale('c4')

        s = stream.Stream()
        s.append(dynamics.Dynamic('f'))
        s.append(note.Note('c4'))
        s.append(sc.getChord('e3','a3', quarterLength=.5))
        #s.append(note.Note('c3', quarterLength=2))
        s.append(dynamics.Dynamic('mf'))
        s.append(sc.getChord('b3','e4', quarterLength=1.5))
        s.append(dynamics.Dynamic('pp'))
        s.append(sc.getChord('f4','g5', quarterLength=3))
        s.append(sc.getChord('f4','g5', quarterLength=3))
        s.append(note.Note('c5', quarterLength=3))
        
        for args in [
            ('histogram', 'pitch'),
            ('histogram', 'pitchclass'), 
            ('histogram', 'quarterlength'), 
            ('scatter', 'pitch', 'quarterlength'), 
            ('scatter', 'pitchspace', 'offset'), 
            ('scatter', 'pitch', 'offset'), 
            ('scatter', 'dynamics'), 
            ('bar', 'pitch'), 
            ('bar', 'pc'), 
            ('weighted', 'pc', 'duration'), 
            ('weighted', 'dynamics'), 
                    ]:
            #s.plot(*args, doneAction='write')
            s.plot(*args, doneAction=None)
        

    def testGetPlotsToMakeA(self):
        post = _getPlotsToMake(format='grid', values='krumhansl-schmuckler')
        self.assertEqual(post, [PlotWindowedKrumhanslSchmuckler])
        post = _getPlotsToMake(format='grid', values='aarden')
        self.assertEqual(post, [PlotWindowedAardenEssen])
        post = _getPlotsToMake(format='grid', values='simple')
        self.assertEqual(post, [PlotWindowedSimpleWeights])
        post = _getPlotsToMake(format='grid', values='bellman')
        self.assertEqual(post, [PlotWindowedBellmanBudge])
        post = _getPlotsToMake(format='grid', values='kostka')
        self.assertEqual(post, [PlotWindowedTemperleyKostkaPayne])
        post = _getPlotsToMake(format='grid', values='KrumhanslKessler')
        self.assertEqual(post, [PlotWindowedKrumhanslKessler])


        # no args get pitch space piano roll
        post = _getPlotsToMake()
        self.assertEqual(post, [PlotHorizontalBarPitchSpaceOffset])

        # one arg gives a histogram of that parameters
        post = _getPlotsToMake('duration')
        self.assertEqual(post, [PlotHistogramQuarterLength])
        post = _getPlotsToMake('quarterLength')
        self.assertEqual(post, [PlotHistogramQuarterLength])
        post = _getPlotsToMake('ps')
        self.assertEqual(post, [PlotHistogramPitchSpace])
        post = _getPlotsToMake('pitch')
        self.assertEqual(post, [PlotHistogramPitchSpace])
        post = _getPlotsToMake('pitchspace')
        self.assertEqual(post, [PlotHistogramPitchSpace])
        post = _getPlotsToMake('pc')
        self.assertEqual(post, [PlotHistogramPitchClass])

        post = _getPlotsToMake('scatter', 'ps')
        self.assertEqual(post, [PlotScatterPitchSpaceQuarterLength])
        post = _getPlotsToMake('scatter', 'ps', 'duration')
        self.assertEqual(post, [PlotScatterPitchSpaceQuarterLength])

        post = _getPlotsToMake('scatter', 'pc', 'offset')
        self.assertEqual(post, [PlotScatterPitchClassOffset])


    def testGetPlotsToMakeB(self):
        post = _getPlotsToMake('dolan')
        self.assertEqual(post, [PlotDolan])
        post = _getPlotsToMake(values='instrument')
        self.assertEqual(post, [PlotDolan])
        post = _getPlotsToMake(format='horizontalbarweighted')
        self.assertEqual(post, [PlotDolan])



    def testGraphVerticalBar(self):
        from music21 import graph
        
        g = graph.GraphGroupedVerticalBar(doneAction=None)
        data = [('bar%s' % x, {'a':3,'b':2,'c':1}) for x in range(10)]
        g.setData(data)
        g.process()
        streamList = ['bach/bwv66.6', 'schoenberg/opus19/movement2', 'corelli/opus3no1/1grave']
        feList = ['ql1', 'ql2', 'ql3']

        p = PlotFeatures(streamList, featureExtractors=feList, doneAction=None)
        p.process()
        


    def testColors(self):
        from music21 import graph
        self.assertEqual(graph.getColor([.5, .5, .5]), '#808080')
        self.assertEqual(graph.getColor(.5), '#808080')
        self.assertEqual(graph.getColor(255), '#ffffff')
        self.assertEqual(graph.getColor('Steel Blue'), '#4682b4')

#     def testMeasureNumbersA(self):
#         from music21 import corpus, graph
#         s = corpus.parse('bwv66.6')
#         p = graph.PlotHorizontalBarPitchClassOffset(s)
#         #p.process()


    def testPlotDolanA(self):
        a = corpus.parse('bach/bwv57.8')
        b = PlotDolan(a, title='Bach', doneAction=None)
        b.process()
        
        #b.show()


    def xtestGraphVerticalBar(self):

        #streamList = corpus.parse('essenFolksong/han1')
        streamList = corpus.getBachChorales()[100:108]
        feList = ['m17', 'm18', 'm19', 'ql1']
        #labelList = [os.path.basename(fp) for fp in streamList]
        p = PlotFeatures(streamList, feList)
        p.process()
        


#     def testHorizontalInstrumentationA(self):
#         s = corpus.parse('symphony94/02')
#         unused_g = PlotDolan(s, fillByMeasure=False, segmentByTarget=True, 
#             normalizeByPart = False, title='Haydn, Symphony No. 94 in G major, Movement II',
#             hideYGrid=True, hideXGrid=True, alpha=1, figureSize=[60,4], dpi=300, )


    def testHorizontalInstrumentationB(self):
        s = corpus.parse('bwv66.6')
        dyn = ['p', 'mf', 'f', 'ff', 'mp', 'fff', 'ppp']
        i = 0
        for p in s.parts:
            for m in p.getElementsByClass('Measure'):
                m.insert(0, dynamics.Dynamic(dyn[i % len(dyn)]))
                i += 1
        s.plot('dolan', fillByMeasure = True, segmentByTarget=True, doneAction=None)





#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [
        PlotHistogramPitchSpace, PlotHistogramPitchClass, PlotHistogramQuarterLength,
        # windowed
        PlotWindowedKrumhanslSchmuckler, PlotWindowedAmbitus,
        # scatters
        PlotScatterPitchSpaceQuarterLength, PlotScatterPitchClassQuarterLength, PlotScatterPitchClassOffset,
        PlotScatterPitchSpaceDynamicSymbol,
        # offset based horizontal
        PlotHorizontalBarPitchSpaceOffset, PlotHorizontalBarPitchClassOffset,
        PlotDolan,
        # weighted scatter
        PlotScatterWeightedPitchSpaceQuarterLength, PlotScatterWeightedPitchClassQuarterLength,
        PlotScatterWeightedPitchSpaceDynamicSymbol,
        # 3d graphs
        Plot3DBarsPitchSpaceQuarterLength,
]

if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
