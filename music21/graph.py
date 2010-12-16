#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         graph.py
# Purpose:      Classes for graphing in matplotlib and/or other graphing tools.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
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

import unittest, doctest
import random, math, sys, os

import music21
from music21 import note
from music21 import dynamics
from music21 import duration
from music21 import pitch
from music21 import common
from music21 import chord
from music21.analysis import windowed
from music21.analysis import discrete
from music21.analysis import correlate

from music21 import environment
_MOD = 'graph.py'
environLocal = environment.Environment(_MOD)

_missingImport = []
try:
    import matplotlib
    # backend can be configured from config file, matplotlibrc,
    # but an early test broke all processing
    #matplotlib.use('WXAgg')

    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib import collections
    from matplotlib import patches

    #from matplotlib.colors import colorConverter
    import matplotlib.pyplot as plt

except ImportError:
    _missingImport.append('matplotlib')


try:
    import numpy
except ImportError:
    _missingImport.append('numpy')

try:
    import networkx
except ImportError:
    # for now, this does nothing
    pass
    #_missingImport.append('networkx')


if len(_missingImport) > 0:
    if environLocal['warnings'] in [1, '1', True]:
        environLocal.warn(common.getMissingImportStr(_missingImport),
        header='music21:')


#-------------------------------------------------------------------------------
class GraphException(Exception):
    pass

class PlotStreamException(Exception):
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

#-------------------------------------------------------------------------------
class Graph(object):
    '''
    A music21.graph.Graph is an abstract object that represents a graph or 
    plot, automating the creation and configuration of this graph in matplotlib.
    It is a low-level object that most music21 users do not need to call directly
    but because it most graphs will take keyword arguments that specify the
    look of graphs, they are important to know about.

    The keyword arguments can be provided for configuration are: 
    alpha (which describes how transparent elements of the graph are), 
    colorBackgroundData, colorBackgroundFigure, colorGrid, title, 
    doneAction (see below), 
    figureSize, colors, tickFontSize, titleFontSize, labelFontSize, 
    fontFamily.

    Graph objects do not manipulate Streams or other music21 data; they only 
    manipulate raw data formatted for each Graph subclass, hence why it is
    unlikely that people will call this class directly.

    The doneAction argument determines what happens after the graph 
    has been processed. Currently there are three options, 'write' creates
    a file on disk (this is the default), while 'show' opens an 
    interactive GUI browser.  The
    third option, None, does the processing but does not write any output.
    '''

    def __init__(self, *args, **keywords):
        '''
        >>> a = Graph(title='a graph of some data to be given soon', tickFontSize = 9)
        >>> a.setData(['some', 'arbitrary', 'data', 14, 9.04, None])
        '''
        self.data = None
        # define a component dictionary for each axist
        self.axis = {}
        self.axisKeys = ['x', 'y']
        self.grid = True

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

        # define a list of one or more colors
        # these will be applied cyclically to data prsented
        if 'colors' in keywords:
            self.colors = keywords['colors']
        else:
            self.colors = ['#605C7F']

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
        '''pairs are positions and labels
        '''
        if pairs != None:
            positions = []
            labels = []
            # ticks are value, label pairs
            for value, label in pairs:
                positions.append(value)
                labels.append(label)
            self.axis[axisKey]['ticks'] = positions, labels

    def setAxisRange(self, axisKey, valueRange, pad=False):
        if axisKey not in self.axisKeys:
            raise GraphException('No such axis exists: %s' % axisKey)
        # find a shift
        if pad != False:
            range = valueRange[1] - valueRange[0]
            if pad == True: # use a default
                shift = range * .1 # add 10 percent of ragne
            else:
                shift = pad # provide a value directly
        else:
            shift = 0
        # set range with shift
        self.axis[axisKey]['range'] = (valueRange[0]-shift,
                                       valueRange[1]+shift)


    def setAxisLabel(self, axisKey, label):
        if axisKey not in self.axisKeys:
            raise GraphException('No such axis exists: %s' % axisKey)
        self.axis[axisKey]['label'] = label

    def _adjustAxisSpines(self, ax, leftBottom=False):
        '''Remove the right and left spines from the diagram
        '''
        for loc, spine in ax.spines.iteritems():
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
        rect.set_facecolor(self.colorBackgroundData)
        # this does not do anything yet
        # rect.set_edgecolor('red')

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

                    if 'ticks' in self.axis[axis].keys():
                        values, labels = self.axis[axis]['ticks']
                        #environLocal.printDebug(['x tick labels, x tick values', labels, values])
                        ax.set_xticks(values)
                        # using center alignment to account for odd spacing in 
                        # accidentals
                        ax.set_xticklabels(labels, fontsize=self.tickFontSize,
                            family=self.fontFamily, 
                            horizontalalignment='center', verticalalignment='center', y=-.01)

                elif axis == 'y':
                    # this is the old way ticks were set:
                    #plt.yticks(*self.axis[axis]['ticks'])
                    # new way:
                    if 'ticks' in self.axis[axis].keys():
                        values, labels = self.axis[axis]['ticks']
                        #environLocal.printDebug(['y tick labels, y tick values', labels, values])
                        ax.set_yticks(values)
                        ax.set_yticklabels(labels, fontsize=self.tickFontSize,
                            family=self.fontFamily,
                            horizontalalignment='right', verticalalignment='center')
            else: # apply some default formatting to default ticks
                ax.set_xticklabels(ax.get_xticks(),
                    fontsize=self.tickFontSize, family=self.fontFamily) 
                ax.set_yticklabels(ax.get_yticks(),
                    fontsize=self.tickFontSize, family=self.fontFamily) 

        if self.title:
            ax.set_title(self.title, fontsize=self.titleFontSize, family=self.fontFamily)

        if self.grid:
            if self.colorGrid is not None: # None is another way to hide grid
                ax.grid(True, color=self.colorGrid)


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
        plt.show()

    def write(self, fp=None):
        '''
        Writes the graph to a file. If no file path is given, a temporary file is used. 
        '''
        if fp == None:
            fp = environLocal.getTempFile('.png')
        #print _MOD, fp
        if self.dpi != None:
            self.fig.savefig(fp, facecolor=self.colorBackgroundFigure,      
                             edgecolor=self.colorBackgroundFigure,
                              dpi=self.dpi)
        else:
            self.fig.savefig(fp, facecolor=self.colorBackgroundFigure,      
                             edgecolor=self.colorBackgroundFigure)

        environLocal.launch('png', fp)




class GraphNetworxGraph(Graph):
    ''' 
    Grid a networkx graph -- which is a graph of nodes and edges.
    Requires the optional networkx module.
    
    >>> from music21 import *
    >>> #_DOCS_SHOW g = graph.GraphNetworxGraph()

    .. image:: images/GraphNetworxGraph.*
        :width: 600
    '''
    def __init__(self, *args, **keywords):
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

        if 'figureSize' not in keywords:
            self.setFigureSize([6, 6])
        if 'title' not in keywords:
            self.setTitle('Network Plot')

        if 'networkxGraph' in keywords.keys():
            self.networkxGraph = keywords['networkxGraph']
        else:
            # testing default; temporary
            ## TODO: Add import test.
            g = networkx.Graph()
#             g.add_edge('a','b',weight=1.0)
#             g.add_edge('b','c',weight=0.6)
#             g.add_edge('c','d',weight=0.2)
#             g.add_edge('d','e',weight=0.6)
            
            self.networkxGraph = g

    def process(self):

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

        environLocal.printDebug(['get position', posNodes])
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
    
    
    >>> from music21 import *
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
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()

        plotShift = .08 # shift to make room for y axis label        
        axTop = self.fig.add_subplot(1, 1, 1+plotShift)
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
            ax = self.fig.add_subplot(rowCount, 1,
                 len(self.data)-i+plotShift)

            # linewidth: .1 is the thinnest possible
            # antialiased = false, for small diagrams, provides tighter images
            ax.bar(positions, heights, 1, color=subColors, linewidth=.3, edgecolor='#000000', antialiased=False)

            # remove spines from each bar plot; cause excessive thickness
            for loc, spine in ax.spines.iteritems():
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
    
    >>> from music21 import *
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
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()

        plotShift = 0        
        axTop = self.fig.add_subplot(1, 1, 1+plotShift)
        
        for i in range(len(self.data)):
            rowLabel = self.data[i][0]
            rowData = self.data[i][1]

            environLocal.printDebug(['rowLabel', rowLabel, i])

            positions = []
            heights = []
            subColors = []
            
            for j in range(len(rowData)):
                positions.append(.5+j)
                subColors.append(rowData[j][1]) # second value is colors
                heights.append(1)
            
            # add a new subplot for each row    
            posTriple = (len(self.data), 1, i+1+plotShift)
            #environLocal.printDebug(['posTriple', posTriple])
            ax = self.fig.add_subplot(*posTriple)
            # 1 here is width
            ax.bar(positions, heights, 1, color=subColors, linewidth=.3, edgecolor='#000000')
            
            # remove spines from each bar plot; cause excessive thickness
            for loc, spine in ax.spines.iteritems():
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
                [_substituteAccidentalSymbols(x) for x, y in rowData], 
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

        >>> from music21 import *
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
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()

        ax = self.fig.add_subplot(1, 1, 1.1)

        yPos = 0
        xPoints = [] # store all to find min/max
        yTicks = [] # a list of label, value pairs
        xTicks = []

        keys = []
        i = 0
        for key, points in self.data:
            keys.append(key)
            # provide a list of start, end points;
            # then start y position, bar height
            ax.broken_barh(points, (yPos+self._margin, self._barHeight),
                            facecolors=self.colors[i%len(self.colors)], alpha=self.alpha)
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

        environLocal.printDebug(['got xMin, xMax for points', xMin, xMax, ])

        self.setAxisRange('y', (0, len(keys) * self._barSpace))
        self.setAxisRange('x', (xMin, xMax), pad=True)
        self.setTicks('y', yTicks)  

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



class GraphScatterWeighted(Graph):
    '''A scatter plot where points are scaled in size to represent the number of values stored within.

    >>> from music21 import *
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
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        ax = self.fig.add_subplot(1, 1, 1.1)

        # need to filter data to weight z values
        xList = [x for x, y, z in self.data]
        yList = [y for x, y, z in self.data]
        zList = [z for x, y, z in self.data]

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
                scalar = (z-zMin) / zRange # shifted part / range
                scaled = self._minDiameter + (self._rangeDiameter * scalar)
                zNorm.append([scaled, scalar])

        # draw elipses
        for i in range(len(self.data)):
            x = xList[i]
            y = yList[i]
            z, zScalar = zNorm[i] # normalized values

            width=z*xDistort
            height=z*yDistort
            e = patches.Ellipse(xy=(x, y), width=width, height=height)
            #e = patches.Circle(xy=(x, y), radius=z)
            ax.add_artist(e)

            e.set_clip_box(ax.bbox)
            #e.set_alpha(self.alpha*zScalar)
            e.set_alpha(self.alpha)
            e.set_facecolor(self.colors[i%len(self.colors)]) # can do this here
            #environLocal.printDebug([e])

            # only show label if min if greater than zNorm min
            if zList[i] > 1:
                # xdistort does not seem to
                # width shift can be between .1 and .25
                # width is already shifted by by distort
                # use half of width == radius
                ax.text(x+((width*.5)+(.05*xDistort)),
                        y+.10,
                        "%s" % zList[i], size=6,
                        va="baseline", ha="left", multialignment="left")

        self.setAxisRange('y', (yMin, yMax), pad=True)
        self.setAxisRange('x', (xMin, xMax), pad=True)

        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()


class GraphScatter(Graph):
    '''Graph two parameters in a scatter plot. Data representation is a list of points of values. 

    >>> from music21 import *
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
        '''
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        ax = self.fig.add_subplot(1, 1, 1.1)
        xValues = []
        yValues = []
        i = 0
        for x, y in self.data:
            if x not in xValues:
                xValues.append(x)
            if y not in yValues:
                yValues.append(y)
        xValues.sort()
        yValues.sort()

        for x, y in self.data:
            ax.plot(x, y, 'o', color=self.colors[i%len(self.colors)], alpha=self.alpha)
            i += 1

        self.setAxisRange('y', (min(yValues), max(yValues)), pad=True)
        self.setAxisRange('x', (min(xValues), max(xValues)), pad=True)

        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()

class GraphHistogram(Graph):
    '''Graph the count of a single element.

    Data set is simply a list of x and y pairs, where there
    is only one of each x value, and y value is the count or magnitude
    of that value

    >>> from music21 import *
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

    def process(self):
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        # added extra .1 in middle param to permit space on right 
        ax = self.fig.add_subplot(1, 1.1, 1.05)

        x = []
        y = []
        for a, b in self.data:
            x.append(a)
            y.append(b)
        ax.bar(x, y, alpha=.8, color=self.colors[0])

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
       
        >>> a = _Graph3DBars()
        '''
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y', 'z']
        self._axisInit()

    def process(self):
        self.fig = plt.figure()
        ax = Axes3D(self.fig)

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

    >>> from music21 import *
    >>> #_DOCS_SHOW g = graph.Graph3DPolygonBars()
    >>> g = graph.Graph3DPolygonBars(doneAction=None) #_DOCS_HIDE
    >>> data = {1:[], 2:[], 3:[]}
    >>> for i in range(len(data.keys())):
    ...    q = [(x, random.choice(range(10*(i+1)))) for x in range(20)]
    ...    data[data.keys()[i]] = q
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

    def process(self):
        cc = lambda arg: matplotlib.colors.colorConverter.to_rgba(arg,
                                alpha=self.alpha)
        self.fig = plt.figure()
        ax = Axes3D(self.fig)

        verts = []
        vertsColor = []
        q = 0
        zVals = self.data.keys()
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
        environLocal.printDebug(['3d axis range, x:', min(xVals), max(xVals)])

        # z values here end up being height of the graph
        self.setAxisRange('z', (min(yVals), max(yVals)))
        environLocal.printDebug(['3d axis range, z (from y):', min(yVals), max(yVals)])

        # y values are the z of the graph, the depth
        self.setAxisRange('y', (min(zVals), max(zVals)))
        environLocal.printDebug(['3d axis range, y (from z):', min(zVals), max(zVals)])

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
        zs = range(low, high+1)

        poly = collections.PolyCollection(verts, facecolors=vertsColor)
        poly.set_alpha(self.alpha)

        ax.add_collection3d(poly, zs=zs, zdir='y')
        self._applyFormatting(ax)
        self.done()






#-------------------------------------------------------------------------------
# graphing utilities that operate on streams

class PlotStream(object):
    '''Approaches to plotting and graphing a stream. A base class from which Stream plotting Classes inherit.
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
        self.graph = None  # store instance of graph class here

        # store axis label type for time-based plots
        # either measure or offset
        self._axisLabelUsesMeasures = None

    def process(self):
        '''This will process all data, as well as call the done() method. What happens when the done() is called is determined by the the keyword argument `doneAction`; options are 'show' (display immediately), 'write' (write the file to a supplied file path), and None (do processing but do not write or show a graph).
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
        '''Get ticks and labels for pitch classes based on usage. That is, show the most commonly used enharmonic first.

        >>> from music21 import corpus
        >>> s = corpus.parseWork('bach/bwv324.xml')
        >>> a = PlotStream(s)
        >>> [x for x, y in a.ticksPitchClassUsage(hideUnused=True)]
        [0, 2, 3, 4, 6, 7, 9, 11]

        >>> s = corpus.parseWork('bach/bwv281.xml')
        >>> a = PlotStream(s)
        >>> [x for x, y in a.ticksPitchClassUsage(showEnharmonic=True, hideUnused=True)]
        [0, 2, 3, 4, 5, 7, 9, 10, 11]
        >>> [x for x, y in a.ticksPitchClassUsage(showEnharmonic=True, blankLabelUnused=False)]
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        >>> s = corpus.parseWork('schumann/opus41no1/movement2.xml')
        >>> a = PlotStream(s)
        >>> [x for x, y in a.ticksPitchClassUsage(showEnharmonic=True)]
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        OMIT_FROM_DOCS
        TODO: this ultimately needs to look at key signature/key to determine defaults for undefined notes.

        '''
        # keys are integers
        pcCount = self.streamObj.pitchAttributeCount('pitchClass')
        # name strings are keys, and enharmonic are thus different
        nameCount = self.streamObj.pitchAttributeCount('name')
        ticks = []
        for i in range(pcMin, pcMax+1):
            p = pitch.Pitch()
            p.ps = i
            weights = [] # a list of pairs of count/label
            for key in nameCount.keys():
                if pitch.convertNameToPitchClass(key) == i:
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
                for w, name in weights:
                    sub.append(name)
                label.append('/'.join(sub))
            ticks.append([i, ''.join(label)])
        ticks = self._filterPitchLabel(ticks)
        return ticks

    def ticksPitchClass(self, pcMin=0, pcMax=11):
        '''Utility method to get ticks in pitch classes

        >>> from music21 import corpus
        >>> s = corpus.parseWork('bach/bwv324.xml')
        >>> a = PlotStream(s)
        >>> [x for x,y in a.ticksPitchClass()]
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        '''
        ticks = []
        for i in range(pcMin, pcMax+1):
            p = pitch.Pitch()
            p.ps = i
            ticks.append([i, '%s' % p.name])
        ticks = self._filterPitchLabel(ticks)
        return ticks
   
    def ticksPitchSpaceOctave(self, pitchMin=36, pitchMax=100):
        '''Utility method to get ticks in pitch space only for every octave.

        >>> from music21 import stream; s = stream.Stream()
        >>> a = PlotStream(s)
        >>> a.ticksPitchSpaceOctave()
        [[36, 'C2'], [48, 'C3'], [60, 'C4'], [72, 'C5'], [84, 'C6'], [96, 'C7']]
        '''
        ticks = []
        cVals = range(pitchMin,pitchMax,12)
        for i in cVals:
            name, acc = pitch.convertPsToStep(i)
            oct = pitch.convertPsToOct(i)
            ticks.append([i, '%s%s' % (name, oct)])
        ticks = self._filterPitchLabel(ticks)
        return ticks


    def ticksPitchSpaceChromatic(self, pitchMin=36, pitchMax=100):
        '''Utility method to get ticks in pitch space values.

        >>> from music21 import stream; s = stream.Stream()
        >>> a = PlotStream(s)
        >>> [x for x,y in a.ticksPitchSpaceChromatic(60,72)]
        [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]
        '''
        ticks = []
        cVals = range(pitchMin, pitchMax+1)
        for i in cVals:
            name, acc = pitch.convertPsToStep(i)
            oct = pitch.convertPsToOct(i)
            # should be able to just use nameWithOctave
            ticks.append([i, '%s%s%s' % (name, acc.modifier, oct)])
        ticks = self._filterPitchLabel(ticks)
        return ticks

    def ticksPitchSpaceUsage(self, pcMin=36, pcMax=72,
            showEnharmonic=False, blankLabelUnused=True, hideUnused=False):
        '''Get ticks and labels for pitch space based on usage. That is, show the most commonly used enharmonic first.

        >>> from music21 import corpus
        >>> s = corpus.parseWork('bach/bwv324.xml')
        >>> a = PlotStream(s[0])
        >>> [x for x, y in a.ticksPitchSpaceUsage(hideUnused=True)]
        [64, 66, 67, 69, 71, 72]

        >>> s = corpus.parseWork('schumann/opus41no1/movement2.xml')
        >>> a = PlotStream(s)
        >>> [x for x, y in a.ticksPitchSpaceUsage(showEnharmonic=True, hideUnused=True)]
        [36, 38, 40, 41, 43, 44, 45, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72]

        OMIT_FROM_DOCS
        TODO: this needs to look at key signature/key to determine defaults
        for undefined notes.

        '''
        # keys are integers
        pcCount = self.streamObj.pitchAttributeCount('pitchClass')
        # name strings are keys, and enharmonic are thus different
        nameWithOctaveCount = self.streamObj.pitchAttributeCount(
                             'nameWithOctave')
        ticks = []
        for i in range(int(pcMin), int(pcMax+1)):
            p = pitch.Pitch()
            p.ps = i # set pitch space value
            weights = [] # a list of pairs of count/label
            for key in nameWithOctaveCount.keys():
                if pitch.convertNameToPs(key) == i:
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
                for w, name in weights:
                    sub.append(name)
                label.append('/'.join(sub))
            ticks.append([i, ''.join(label)])
        ticks = self._filterPitchLabel(ticks)
        return ticks



    def ticksOffset(self, offsetMin=None, offsetMax=None, offsetStepSize=None,
                    displayMeasureNumberZero=False, minMaxOnly=False, 
                    remap=False):
        '''Get offset ticks. If Measures are found, they will be used to create ticks. If not, `offsetStepSize` will be used to create offset ticks between min and max. The `remap` parameter is not yet used. 

        If `minMaxOnly` is True, only the first and last values will be provided.

        >>> from music21 import corpus, stream, note
        >>> s = corpus.parseWork('bach/bwv281.xml')
        >>> a = PlotStream(s)
        >>> a.ticksOffset() # on whole score, showing anacrusis spacing
        [[1.0, '1'], [5.0, '2'], [9.0, '3'], [13.0, '4'], [17.0, '5'], [21.0, '6'], [25.0, '7'], [29.0, '8']]

        >>> a = PlotStream(s.parts[0].flat) # on a Part
        >>> a.ticksOffset() # on whole score, showing anacrusis spacing
        [[1.0, '1'], [5.0, '2'], [9.0, '3'], [13.0, '4'], [17.0, '5'], [21.0, '6'], [25.0, '7'], [29.0, '8']]
        >>> a.ticksOffset(8, 12, 2)
        [[9.0, '3']]

        >>> a = PlotStream(s.parts[0].flat) # on a Flat collection
        >>> a.ticksOffset(8, 12, 2)
        [[9.0, '3']]

        >>> n = note.Note('a') # on a raw collection of notes with no measures
        >>> s = stream.Stream()
        >>> s.repeatAppend(n, 10)
        >>> a = PlotStream(s) # on a Part
        >>> a.ticksOffset() # on whole score
        [[0, '0'], [10, '10']]
        '''
        # importing stream only within method here
        # need stream.Measure to match measure numbers
        # may be a better way
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
        environLocal.printDebug(['ticksOffset: about to call measure offset', self.streamObj])

        if self.streamObj.hasPartLikeStreams():
            # if we have part-like sub streams; we can assume that all parts
            # have parallel measures start times here for simplicity
            # take the top part 
            environLocal.printDebug(['found partLikeStreams', self.streamObj.parts[0]])

            offsetMap = self.streamObj.parts[0].measureOffsetMap(
                        ['Measure'])
        elif self.streamObj.hasMeasures():
            offsetMap = self.streamObj.measureOffsetMap([stream.Measure])
        else:
            offsetMap = self.streamObj.measureOffsetMap([note.Note])

        if len(offsetMap.keys()) > 0:
            self._axisLabelUsesMeasures = True
        else:
            self._axisLabelUsesMeasures = False

        environLocal.printDebug(['ticksOffset: got offset map keys', offsetMap.keys(), self._axisLabelUsesMeasures])


        ticks = [] # a list of graphed value, string label pairs
        if len(offsetMap.keys()) > 0:
            #environLocal.printDebug(['using measures for offset ticks'])
            # store indices in offsetMap
            mNoToUse = []
            sortedKeys = sorted(offsetMap.keys())
            for key in sortedKeys:
                if key >= offsetMin and key <= offsetMax:
                    if key == 0.0 and not displayMeasureNumberZero:
                        continue # skip
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
                for i in range(0, len(mNoToUse), mNoStepSize):
                    offset = mNoToUse[i]
                    mNumber = offsetMap[offset][0].number
                    ticks.append([offset, '%s' % mNumber])

        else: # generate numeric ticks
            if offsetStepSize == None:
                offsetStepSize = 10
            #environLocal.printDebug(['using offsets for offset ticks'])
            # get integers for range calculation
            oMin = int(math.floor(offsetMin))
            oMax = int(math.ceil(offsetMax))
            for i in range(oMin, oMax+1, offsetStepSize):
                ticks.append([i, '%s' % i])

        environLocal.printDebug(['ticksOffset():', 'final ticks', ticks])
        return ticks

    def remapQuarterLength(self, x):
        '''Remap all quarter lengths.
        '''
        if x == 0: # not expected but does happne
            return 0
        try:
            return math.log(x, 2)
        except ValueError:
            raise GraphException('cannot take log of x value: %s' %  x)
        #return pow(x, .5)

    def ticksQuarterLength(self, min=.25, max=4, remap=True):
        '''Get ticks for quarterLength. If `remap` is True, the remapQuarterLength() function will be used to scale displayed quarter lengths by log base 2. 

        >>> from music21 import stream; s = stream.Stream()
        >>> a = PlotStream(s)
        '''
        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        # get all quarter lengths
        map = sSrc.attributeCount([note.Note, chord.Chord], 'quarterLength')

        ticks = []

        for ql in sorted(map.keys()):
#        for i in range(len(qlList)):
            #qLen = qlList[i]
            # dtype, match = duration.
            # ticks.append([qLen, dc.convertQuarterLengthToType(qLen)])

            if remap:
                x = self.remapQuarterLength(ql)
            else:
                x = ql
            ticks.append([x, '%s' % round(ql, 2)])

#             if labelStyle == 'type':
#                 ticks.append([qLen, duration.Duration(qLen).type])
#             elif labelStyle == 'quarterLength':
#                 ticks.append([i, '%s' % qLen])
#             elif labelStyle == 'index':
#                 ticks.append([i, '%s' % i])
#             else:
#                 raise PlotStreamException('bad label style: %s' % labelStyle)
        return ticks

   
    def ticksDynamics(self, minNameIndex=None, maxNameIndex=None):
        '''Utility method to get ticks in dynamic values.

        >>> from music21 import stream; s = stream.Stream()
        >>> a = PlotStream(s)
        >>> a.ticksDynamics()
        [[0, '$pppppp$'], [1, '$ppppp$'], [2, '$pppp$'], [3, '$ppp$'], [4, '$pp$'], [5, '$p$'], [6, '$mp$'], [7, '$mf$'], [8, '$f$'], [9, '$fp$'], [10, '$sf$'], [11, '$ff$'], [12, '$fff$'], [13, '$ffff$'], [14, '$fffff$'], [15, '$ffffff$']]

        >>> a.ticksDynamics(3,6)
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
# color grids    

class PlotWindowedAnalysis(PlotStream):
    '''Base Plot for windowed analysis routines.

    ''' 
    format = 'colorGrid'
    def __init__(self, streamObj, processor=None, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)
        
        # store process for getting title
        self.processor = processor

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
        solutionMatrix, colorMatrix, metaMatrix = wa.process(self.minWindow, 
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

        dir, fn = os.path.split(fp)
        fpLegend = os.path.join(dir, 'legend-' + fn)
        # call the process routine in the base graph
        self.graph.write(fp)
        # create a new graph of the legend

        self.graphLegend = self._getLegend()
        self.graphLegend.process()
        self.graphLegend.write(fpLegend)

    
class PlotWindowedKrumhanslSchmuckler(PlotWindowedAnalysis):
    '''Stream plotting of windowed version of Krumhansl-Schmuckler analysis routine.

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv66.6.xml') #_DOCS_HIDE
    >>> p = graph.PlotWindowedKrumhanslSchmuckler(s.parts[0], doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv66.6')
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
    

class PlotWindowedAmbitus(PlotWindowedAnalysis):
    '''Stream plotting of basic pitch span.

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv66.6.xml') #_DOCS_HIDE
    >>> p = graph.PlotWindowedAmbitus(s.parts[0], doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv66.6')
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
    '''Base class for Stream plotting classes.

    '''
    format = 'histogram'
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

    def _extractData(self, dataValueLegit=True):
        data = {}
        dataTick = {}
        countMin = 0 # could be the lowest value found
        countMax = 0

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        dataValues = []
        for noteObj in sSrc.getElementsByClass(note.Note):
            value = self.fx(noteObj)
            if value not in dataValues:
                dataValues.append(value)
        dataValues.sort()

        for noteObj in sSrc.getElementsByClass(note.Note):
            if dataValueLegit: # use the real values
                value = self.fx(noteObj)
            else:
                value = dataValues.index(self.fx(noteObj))

            if value not in data.keys():
                data[value] = 0
                # this is the offset that is used to shift labels
                # into bars; this only is .5 if x values are integers
                dataTick[value+.4] = self.fxTick(noteObj)
            data[value] += 1
            if data[value] >= countMax:
                countMax = data[value]

        data = data.items()
        data.sort()
        dataTick = dataTick.items()
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

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHistogramPitchSpace(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
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

        self.fx = lambda n:n.midi
        self.fxTick = lambda n: n.nameWithOctave
        # replace with self.ticksPitchSpaceUsage

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData()

        # filter xTicks to remove - in flat lables
        xTicks = self._filterPitchLabel(xTicks)

        self.graph = GraphHistogram(*args, **keywords)
        self.graph.setData(data)

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

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHistogramPitchClass(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
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

        self.fx = lambda n:n.pitchClass
        self.fxTick = lambda n: n.name
        # replace with self.ticksPitchClassUsage

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData()

        # filter xTicks to remove - in flat lables
        xTicks = self._filterPitchLabel(xTicks)

        self.graph = GraphHistogram(*args, **keywords)
        self.graph.setData(data)

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

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHistogramQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
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
        data, xTicks, yTicks = self._extractData(dataValueLegit=False)

        self.graph = GraphHistogram(*args, **keywords)
        self.graph.setData(data)

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
        self.fy = lambda n:n.ps
        self.fyTicks = self.ticksPitchSpaceUsage

        self.fx = lambda n:n.quarterLength
        self.fxTicks = self.ticksQuarterLength

    def _extractData(self, xLog=False):
        data = []
        xValues = []
        yValues = []

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        for noteObj in sSrc.getElementsByClass(note.Note):
            x = self.fx(noteObj)
            if xLog:
                x = self.remapQuarterLength(x)

            y = self.fy(noteObj)
            if x not in xValues:
                xValues.append(x)            
            if y not in xValues:
                yValues.append(x)            
   
        xValues.sort()
        yValues.sort()
        for noteObj in sSrc.getElementsByClass(note.Note):
            x = self.fx(noteObj)
            if xLog:
                x = self.remapQuarterLength(x)
            y = self.fy(noteObj)
            data.append([x, y])

        xVals = [x for x,y in data]
        yVals = [y for x,y in data]

        xTicks = self.fxTicks(min(xVals), max(xVals), remap=xLog)
        yTicks = self.fyTicks(min(yVals), max(yVals))

        return data, xTicks, yTicks


class PlotScatterPitchSpaceQuarterLength(PlotScatter):
    '''A scatter plot of pitch space and quarter length

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterPitchSpaceQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
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

        self.fy = lambda n:n.ps
        self.fyTicks = self.ticksPitchSpaceUsage
        self.fx = lambda n:n.quarterLength
        self.fxTicks = self.ticksQuarterLength

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData(xLog=self.xLog)

        self.graph = GraphScatter(*args, **keywords)
        self.graph.setData(data)

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

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterPitchClassQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
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

        self.fy = lambda n:n.pitchClass
        self.fyTicks = self.ticksPitchClassUsage

        self.fx = lambda n:n.quarterLength
        self.fxTicks = self.ticksQuarterLength

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData(xLog=self.xLog)

        self.graph = GraphScatter(*args, **keywords)
        self.graph.setData(data)

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

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterPitchClassOffset(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
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

        self.fy = lambda n:n.pitchClass
        self.fyTicks = self.ticksPitchClassUsage

        self.fx = lambda n:n.offset
        self.fxTicks = self.ticksOffset

#         if 'xLog' not in keywords:
#             xLog = False
#         else:
#             xLog = keywords['xLog']

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData()

        self.graph = GraphScatter(*args, **keywords)
        self.graph.setData(data)

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

    >>> from music21 import *
    >>> s = corpus.parseWork('schumann/opus41no1', 2) #_DOCS_HIDE
    >>> p = graph.PlotScatterPitchSpaceDynamicSymbol(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('schumann/opus41no1', 2)
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
        data  = am.pitchToDynamic(dataPoints=True)

        xVals = [x for x,y in data]
        yVals = [y for x,y in data]

        xTicks = self.fxTicks(min(xVals), max(xVals))
        # ticks dynamics takes no args
        yTicks = self.fyTicks(min(yVals), max(yVals))

        self.graph = GraphScatter(*args, **keywords)
        self.graph.setData(data)

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
    format = 'horizontalBar'
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n:n.ps
        self.fyTicks = self.ticksPitchSpaceChromatic
        self.fxTicks = self.ticksOffset

    def _extractData(self):
        # find listing for any single pitch name
        dataUnique = {}
        xValues = []
        # collect data

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        for noteObj in sSrc.getElementsByClass(note.Note):
            # numeric value here becomes y axis
            numericValue = int(round(self.fy(noteObj)))
            if numericValue not in dataUnique.keys():
                dataUnique[numericValue] = []
            # all work with offset
            start = noteObj.offset
            # this is not the end, but instead the length
            end = noteObj.quarterLength
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
            if numericValue in dataUnique.keys():
                data.append([label, dataUnique[numericValue]])
            else:
                data.append([label, []])

        # use default args for now
        xTicks = self.fxTicks()

        # yTicks are returned, even though they are not used after this method
        return data, xTicks, yTicks


class PlotHorizontalBarPitchClassOffset(PlotHorizontalBar):
    '''A graph of events, sorted by pitch class, over time

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHorizontalBarPitchClassOffset(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotHorizontalBarPitchClassOffset(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHorizontalBarPitchClassOffset.*
        :width: 600

    '''

    values = ['pitchClass', 'offset', 'pianoroll']
    def __init__(self, streamObj, *args, **keywords):
        PlotHorizontalBar.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n:n.pitchClass
        self.fyTicks = self.ticksPitchClassUsage
        self.fxTicks = self.ticksOffset

        data, xTicks, yTicks = self._extractData()

        self.graph = GraphHorizontalBar(*args, **keywords)
        self.graph.setData(data)

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

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotHorizontalBarPitchSpaceOffset(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotHorizontalBarPitchSpaceOffset(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        :width: 600
    '''

    values = ['pitch', 'offset', 'pianoroll']
    def __init__(self, streamObj, *args, **keywords):
        PlotHorizontalBar.__init__(self, streamObj, *args, **keywords)
       
        self.fy = lambda n:n.ps
        self.fyTicks = self.ticksPitchSpaceUsage
        self.fxTicks = self.ticksOffset

        data, xTicks, yTicks = self._extractData()

        self.graph = GraphHorizontalBar(*args, **keywords)
        self.graph.setData(data)

        # only need to add x ticks; y ticks added from data labels
        self.graph.setTicks('x', xTicks)  

        if len(self.streamObj.getElementsByClass('Measure')) > 0 or len(self.streamObj.semiFlat.getElementsByClass('Measure')) > 0:
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
        self.fx = lambda n:n.quarterLength
        self.fy = lambda n: n.midi
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

        # find all combinations of x/y
        for noteObj in sSrc.getElementsByClass(note.Note):
            x = self.fx(noteObj)
            if xLog:
                x = self.remapQuarterLength(x)
            if x not in xValues:
                xValues.append(x)
            y = self.fy(noteObj)
            if y not in yValues:
                yValues.append(y)

        xValues.sort()
        yValues.sort()
        yMin = min(yValues)
        yMax = max(yValues)
        # create a count slot for all possibilities of x/y
        # y is the pitch axis; get all contiguous pirches
        for y, label in self.fyTicks(yMin, yMax):
        #for y in yValues:
            dataCount[y] = [[x, 0] for x in xValues]

        maxCount = 0 # this is the max z value
        for noteObj in sSrc.getElementsByClass(note.Note):
            x = self.fx(noteObj)
            if xLog:
                x = self.remapQuarterLength(x)
            indexToIncrement = xValues.index(x)

            # second position stores increment
            dataCount[self.fy(noteObj)][indexToIncrement][1] += 1
            if dataCount[self.fy(noteObj)][indexToIncrement][1] > maxCount:
                maxCount = dataCount[self.fy(noteObj)][indexToIncrement][1]

        xTicks = self.fxTicks(min(xValues), max(xValues), remap=xLog)

        # create final data list using fy ticks to get values
        data = []
        for y, label in self.fyTicks(yMin, yMax):
            yIndex = y
            for x, z in dataCount[y]:
                data.append([x, yIndex, z])

        # only label y values that are defined
        yTicks = self.fyTicks(yMin, yMax)
        return data, xTicks, yTicks


class PlotScatterWeightedPitchSpaceQuarterLength(PlotScatterWeighted):
    '''A graph of event, sorted by pitch, over time

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterWeightedPitchSpaceQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotScatterWeightedPitchSpaceQuarterLength(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotScatterWeightedPitchSpaceQuarterLength.*
        :width: 600
    '''

    values = ['pitch', 'quarterLength']
    def __init__(self, streamObj, *args, **keywords):
        PlotScatterWeighted.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n: n.quarterLength
        self.fy = lambda n: n.midi
        self.fxTicks = self.ticksQuarterLength
        self.fyTicks = self.ticksPitchSpaceUsage

        data, xTicks, yTicks = self._extractData(xLog=self.xLog)

        self.graph = GraphScatterWeighted(*args, **keywords)
        self.graph.setData(data)

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

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> p = graph.PlotScatterWeightedPitchClassQuarterLength(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
    >>> #_DOCS_SHOW p = graph.PlotScatterWeightedPitchClassQuarterLength(s)
    >>> p.process() # with defaults and proper configuration, will open graph

    .. image:: images/PlotScatterWeightedPitchClassQuarterLength.*
        :width: 600

    '''

    values = ['pitchClass', 'quarterLength']
    def __init__(self, streamObj, *args, **keywords):
        PlotScatterWeighted.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n:n.quarterLength
        self.fy = lambda n: n.pitchClass
        self.fxTicks = self.ticksQuarterLength
        self.fyTicks = self.ticksPitchClassUsage

        data, xTicks, yTicks = self._extractData(xLog = self.xLog)

        self.graph = GraphScatterWeighted(*args, **keywords)
        self.graph.setData(data)

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


    >>> from music21 import *
    >>> s = corpus.parseWork('schumann/opus41no1', 2) #_DOCS_HIDE
    >>> p = graph.PlotScatterWeightedPitchSpaceDynamicSymbol(s, doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('schumann/opus41no1', 2)
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
        data  = am.pitchToDynamic(dataPoints=False)

        xVals = [x for x,y,z in data]
        yVals = [y for x,y,z in data]

        xTicks = self.fxTicks(min(xVals), max(xVals))
        # ticks dynamics takes no args
        yTicks = self.fyTicks(min(yVals), max(yVals))


        self.graph = GraphScatterWeighted(*args, **keywords)
        self.graph.setData(data)

        self.graph.setAxisLabel('x', 'Pitch')
        self.graph.setAxisLabel('y', 'Dynamics')

        self.graph.setTicks('y', yTicks)  
        self.graph.setTicks('x', xTicks)  

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([12,12])
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
        data = {}
        xValues = []
        yValues = []

        if self.flatten:
            sSrc = self.streamObj.flat
        else:
            sSrc = self.streamObj

        for noteObj in sSrc.getElementsByClass(note.Note):
            x = self.fx(noteObj)
            if x not in xValues:
                xValues.append(x)
            y = self.fy(noteObj)
            if y not in yValues:
                yValues.append(y)
        xValues.sort()
        yValues.sort()
        # prepare data dictionary; need to pack all values
        # need to provide spacings even for zero values
        #for y in range(yValues[0], yValues[-1]+1):
        # better to use actual y values
        for y, label in self.fyTicks(min(yValues), max(yValues)):
        #for y in yValues:
            data[y] = [[x, 0] for x in xValues]
        #print _MOD, 'data keys', data.keys()

        maxCount = 0
        for noteObj in sSrc.getElementsByClass(note.Note):
            indexToIncrement = xValues.index(self.fx(noteObj))
            # second position stores increment
            #print _MOD, fy(noteObj), indexToIncrement

            data[self.fy(noteObj)][indexToIncrement][1] += 1
            if data[self.fy(noteObj)][indexToIncrement][1] > maxCount:
                maxCount = data[self.fy(noteObj)][indexToIncrement][1]

        # setting of ticks does not yet work in matplotlib
        xTicks = [(40, 'test')]
        yTicks = self.fyTicks(min(yValues), max(yValues))
        zTicks = []
        return data, xTicks, yTicks, zTicks


class Plot3DBarsPitchSpaceQuarterLength(Plot3DBars):
    '''A scatter plot of pitch and quarter length

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
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

        self.fx = lambda n:n.quarterLength
        self.fy = lambda n:n.ps
        self.fyTicks = self.ticksPitchSpaceUsage

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks, zTicks = self._extractData()

        self.graph = Graph3DPolygonBars(*args, **keywords)
        self.graph.setData(data)

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
# public function

def plotStream(streamObj, *args, **keywords):
    '''Given a stream and any keyword configuration arguments, create and display a plot.

    Note: plots requires matplotib to be installed.

    Plot methods can be specified as additional arguments or by keyword. Two keyword arguments can be given: `format` and `values`. If positional arguments are given, the first is taken as `format` and the rest are collected as `values`. If `format` is the class name, that class is collected. Additionally, every :class:`~music21.graph.PlotStream` subclass defines one `format` string and a list of `values` strings. The `format` parameter defines the type of Graph (e.g. scatter, histogram, colorGrid). The `values` list defines what values are graphed (e.g. quarterLength, pitch, pitchClass). 

    If a user provides a `format` and one or more `values` strings, a plot with the corresponding profile, if found, will be generated. If not, the first Plot to match any of the defined specifiers will be created. 

    In the case of :class:`~music21.graph.PlotWindowedAnalysis` subclasses, the :class:`~music21.analysis.discrete.DiscreteAnalysis` subclass :attr:`~music21.analysis.discrete.DiscreteAnalysis.indentifiers` list is added to the Plot's `values` list. 

    Available plots include the following:

    :class:`~music21.graph.PlotHistogramPitchSpace`
    :class:`~music21.graph.PlotHistogramPitchClass`
    :class:`~music21.graph.PlotHistogramQuarterLength`

    :class:`~music21.graph.PlotScatterPitchSpaceQuarterLength`
    :class:`~music21.graph.PlotScatterPitchClassQuarterLength`
    :class:`~music21.graph.PlotScatterPitchClassOffset`
    :class:`~music21.graph.PlotScatterPitchSpaceDynamicSymbol`

    :class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`
    :class:`~music21.graph.PlotHorizontalBarPitchClassOffset`

    :class:`~music21.graph.PlotScatterWeightedPitchSpaceQuarterLength`
    :class:`~music21.graph.PlotScatterWeightedPitchClassQuarterLength`
    :class:`~music21.graph.PlotScatterWeightedPitchSpaceDynamicSymbol`

    :class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`

    :class:`~music21.graph.PlotWindowedKrumhanslSchmuckler`
    :class:`~music21.graph.PlotWindowedAmbitus`

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> s.plot('histogram', 'pitch', doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
    >>> #_DOCS_SHOW s.plot('histogram', 'pitch')

    .. image:: images/PlotHistogramPitchSpace.*
        :width: 600


    >>> s = corpus.parseWork('bach/bwv324.xml') #_DOCS_HIDE
    >>> s.plot('pianoroll', doneAction=None) #_DOCS_HIDE
    >>> #_DOCS_SHOW s = corpus.parseWork('bach/bwv57.8')
    >>> #_DOCS_SHOW s.plot('pianoroll')

    .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        :width: 600

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
        PlotWindowedAmbitus,
    ]

    format = ''
    values = []

    # can match by format
    if 'format' in keywords:
        format = keywords['format']
    if 'values' in keywords:
        values = keywords['values'] # should be a list

    if len(args) > 0:
        format = args[0]
    if len(args) > 1:
        values = args[1:] # get all remaining

    if not common.isListLike(values):
        values = [values]
    # make sure we have a list
    values = list(values)

    environLocal.printDebug(['plotStream: stream', streamObj, 
                             'format, values', format, values])

    plotMake = []
    if format.lower() == 'all':
        plotMake = plotClasses
    else:
        for plotClassName in plotClasses:
            # try to match by complete class name
            if plotClassName.__name__.lower() == format.lower():
                plotMake.append(plotClassName)

            # try direct match of format and values
            plotClassNameValues = [x.lower() for x in plotClassName.values]
            plotClassNameFormat = plotClassName.format.lower()
            if plotClassNameFormat == format.lower():
                # see if a matching set of values is specified
                # normally plots need to match all values 
                match = []
                for requestedValue in values:
                    if requestedValue == None: continue
                    if (requestedValue.lower() in plotClassNameValues):
                        # do not allow the same value to be requested
                        if requestedValue not in match:
                            match.append(requestedValue)
                if len(match) == len(values):
                    plotMake.append(plotClassName)

        # if no matches, try something more drastic:
        if len(plotMake) == 0:
            for plotClassName in plotClasses:
                # create a lost of all possible identifiers
                plotClassIdentifiers = [plotClassName.format.lower()]
                plotClassIdentifiers += [x.lower() for x in 
                                        plotClassName.values]
                # combine format and values args
                for requestedValue in [format] + values:
                    if requestedValue.lower() in plotClassIdentifiers:
                        plotMake.append(plotClassName)
                        break
                if len(plotMake) > 0: # found a match
                    break


    environLocal.printDebug(['plotClassName found', plotMake])
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
            data[data.keys()[i]] = q
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
        for key, value in data.items():
            for x, y in value:
                if x not in xPoints:
                    xPoints.append(x)
                    xTicks.append(['r', x])

        # this does not work, and instead causes massive distortion
        #a.setTicks('x', xTicks)
        a.process()


    def testBrokenHorizontal(self):
        import random
        data = []
        for label in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']:
            points = []
            for pairs in range(10):
                start = random.choice(range(150))
                end = start + random.choice(range(50))
                points.append((start, end))
            data.append([label, points])
        #environLocal.printDebug(['data points', data])
       
        a = GraphHorizontalBar()
        a.setData(data)
        a.process()


    def testPlotHorizontalBarPitchSpaceOffset(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        # do not need to call flat version
        b = PlotHorizontalBarPitchSpaceOffset(a[0], title='Bach (soprano voice)')
        b.process()

        b = PlotHorizontalBarPitchSpaceOffset(a, title='Bach (all parts)')
        b.process()



    def testPlotHorizontalBarPitchClassOffset(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotHorizontalBarPitchClassOffset(a[0], title='Bach (soprano voice)')
        b.process()

        a = corpus.parseWork('bach/bwv57.8')
        b = PlotHorizontalBarPitchClassOffset(a[0].measures(3,6), title='Bach (soprano voice, mm 3-6)')
        b.process()



    def testScatterWeighted(self):
        import random
        data = []
        for i in range(50):
            points = []
            x = random.choice(range(20))
            y = random.choice(range(20))
            z = random.choice(range(1, 20))
            data.append([x, y, z])
       
        a = GraphScatterWeighted()
        a.setData(data)
        a.process()

    def testPlotScatterWeightedPitchSpaceQuarterLength(self):
        from music21 import corpus      

        for xLog in [True, False]:
            a = corpus.parseWork('bach/bwv57.8')
            b = PlotScatterWeightedPitchSpaceQuarterLength(a[0].flat,
                            title='Pitch Space Bach (soprano voice)',
                            xLog=xLog)
            b.process()
    
            a = corpus.parseWork('bach/bwv57.8')
            b = PlotScatterWeightedPitchClassQuarterLength(a[0].flat,
                            title='Pitch Class Bach (soprano voice)',
                            xLog=xLog)
            b.process()


    def testPlotPitchSpace(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotHistogramPitchSpace(a[0].flat, title='Bach (soprano voice)')
        b.process()

    def testPlotPitchClass(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotHistogramPitchClass(a[0].flat, title='Bach (soprano voice)')
        b.process()

    def testPlotQuarterLength(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotHistogramQuarterLength(a[0].flat, title='Bach (soprano voice)')
        b.process()


    def testPlotScatterPitchSpaceQuarterLength(self):
        from music21 import corpus      

        for xLog in [True, False]:

            a = corpus.parseWork('bach/bwv57.8')
            b = PlotScatterPitchSpaceQuarterLength(a[0].flat, title='Bach (soprano voice)', xLog=xLog)
            b.process()
    
            b = PlotScatterPitchClassQuarterLength(a[0].flat, title='Bach (soprano voice)', xLog=xLog)
            b.process()

    def testPlotScatterPitchClassOffset(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotScatterPitchClassOffset(a[0].flat, title='Bach (soprano voice)')
        b.process()


    def testPlotScatterPitchSpaceDynamicSymbol(self):
        from music21 import corpus      
        a = corpus.parseWork('schumann/opus41no1', 2)
        b = PlotScatterPitchSpaceDynamicSymbol(a[0].flat, title='Schumann (soprano voice)')
        b.process()

        b = PlotScatterWeightedPitchSpaceDynamicSymbol(a[0].flat, title='Schumann (soprano voice)')
        b.process()



    def testPlot3DPitchSpaceQuarterLengthCount(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = Plot3DBarsPitchSpaceQuarterLength(a.flat, title='Bach (soprano voice)')
        b.process()



    def testAll(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        plotStream(a.flat, 'all')


    def writeAllGraphs(self):
        '''Write a graphic file for all graphs, naming them after the appropriate class. This is used to generate documentation samples.
        '''
        import os

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
        import os
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
        import os
        from music21 import corpus, converter      
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
        (Plot3DBarsPitchSpaceQuarterLength, testFiles.mozartTrioK581Excerpt, 'Mozart Trio K581 Excerpt'),

        (PlotWindowedKrumhanslSchmuckler, corpus.getWork('bach/bwv66.6.xml'), 'Bach BWV 66.6'),
        (PlotWindowedAmbitus, corpus.getWork('bach/bwv66.6.xml'), 'Bach BWV 66.6'),

        ]



        sDefault = corpus.parseWork('bach/bwv57.8')

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
        import random, os
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
        for part in sys.modules[self.__module__].__dict__.keys():
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
                a = copy.copy(obj)
                b = copy.deepcopy(obj)



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
            data[data.keys()[i]] = q
        a.setData(data)
        a.process()
        del a

    def testBrokenHorizontal(self):
        import random
        data = []
        for label in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']:
            points = []
            for pairs in range(10):
                start = random.choice(range(150))
                end = start + random.choice(range(50))
                points.append((start, end))
            data.append([label, points])
       
        a = GraphHorizontalBar(doneAction=None)
        a.setData(data)
        a.process()



    def testPlotPitchSpaceDurationCount(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotScatterWeightedPitchSpaceQuarterLength(a[0].flat, doneAction=None,
                        title='Bach (soprano voice)')
        b.process()

    def testPlotPitchSpace(self):
        from music21 import corpus      
        a = corpus.parseWork('bach')
        b = PlotHistogramPitchSpace(a[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()

    def testPlotPitchClass(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotHistogramPitchClass(a[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()

    def testPlotQuarterLength(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotHistogramQuarterLength(a[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()

    def testPitchDuration(self):
        from music21 import corpus      
        a = corpus.parseWork('schumann/opus41no1', 2)
        b = PlotScatterPitchSpaceDynamicSymbol(a[0].flat, doneAction=None, title='Schumann (soprano voice)')
        b.process()

        b = PlotScatterWeightedPitchSpaceDynamicSymbol(a[0].flat, doneAction=None, title='Schumann (soprano voice)')
        b.process()

        
    def testPlotWindowed(self, doneAction=None):
        from music21 import corpus
        if doneAction != None:
            fp = random.choice(corpus.getBachChorales('.xml'))
            dir, fn = os.path.split(fp)
            a = corpus.parseWork(fp)
            windowStep = 3 #'2'
            #windowStep = random.choice([1,2,4,8,16,32])
            #a.show()
        else:
            a = corpus.parseWork('bach/bwv66.6')
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
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        plotStream(a.flat, doneAction=None)


    
    def testColorGridLegend(self, doneAction=None):

        from music21.analysis import discrete
        ks = discrete.KrumhanslSchmuckler()
        data = ks.solutionLegend()
        #print data
        a = GraphColorGridLegend(doneAction=doneAction, dpi=300)
        a.setData(data)
        a.process()

    def testPianoRollFromOpus(self):
        from music21 import corpus
        o = corpus.parseWork('josquin/laDeplorationDeLaMorteDeJohannesOckeghem')
        s = o.mergeScores()

        b = PlotHorizontalBarPitchClassOffset(s, doneAction=None)
        b.process()



    def testGraphNetworxGraph(self):
        
        b = GraphNetworxGraph(doneAction=None)
        #b = GraphNetworxGraph()
        b.process()



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [PlotHistogramPitchSpace, PlotHistogramPitchClass, PlotHistogramQuarterLength,
        # windowed
        PlotWindowedKrumhanslSchmuckler, PlotWindowedAmbitus,
        # scatters
        PlotScatterPitchSpaceQuarterLength, PlotScatterPitchClassQuarterLength, PlotScatterPitchClassOffset,
        PlotScatterPitchSpaceDynamicSymbol,
        # offset based horizontal
        PlotHorizontalBarPitchSpaceOffset, PlotHorizontalBarPitchClassOffset,
        # weighted scatter
        PlotScatterWeightedPitchSpaceQuarterLength, PlotScatterWeightedPitchClassQuarterLength,
        PlotScatterWeightedPitchSpaceDynamicSymbol,
        # 3d graphs
        Plot3DBarsPitchSpaceQuarterLength,
]



if __name__ == "__main__":
    #music21.mainTest(Test, TestExternal)

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()
        te = TestExternal()
        #a.testPlotScatterWeightedPitchSpaceQuarterLength()

        #t.testPlotQuarterLength()
        #t.testPlotScatterPitchSpaceQuarterLength()
        #t.testPlotScatterPitchSpaceDynamicSymbol()

        #t.writeGraphColorGrid()
        #t.writeAllGraphs()
        #t.writeAllPlots()

        #te.testColorGridLegend('write')
        #te.testPlotWindowed('write')

        #t.testPianoRollFromOpus()

        t.testGraphNetworxGraph()


#------------------------------------------------------------------------------
# eof


