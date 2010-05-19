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

import unittest, doctest
import random, math, sys

import music21

from music21 import note
from music21 import dynamics
from music21 import duration
from music21 import pitch
from music21 import common
from music21 import chord
from music21.analysis import windowedAnalysis

from music21 import environment
_MOD = 'graph.py'
environLocal = environment.Environment(_MOD)


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
    import numpy

except ImportError:
    environLocal.warn('no matplotlib available')





#-------------------------------------------------------------------------------
class GraphException(Exception):
    pass

class PlotStreamException(Exception):
    pass



#-------------------------------------------------------------------------------
class Graph(object):
    '''An object representing a graph or plot, automating the creation and configuration of this graph in matplotlib.

    Graph objects do not manipulate Streams or other music21 data; they only manipulate raw data formatted for each Graph subclass.

    Numerous keyword arguments can be provided for configuration: alpha,  colorBackgroundData, colorBackgroundFigure, colorGrid, title, doneAction, figureSize, colors, tickFontSize, titleFontSize, labelFontSize, fontFamily.

    The doneAction determines what happens after graph processing: either write a file ('write'), open an interactive GUI browser ('show') or None (do processing but do not write output.
    '''

    def __init__(self, *args, **keywords):
        '''Setup a basic graph with a dictionary for two or more axis values. Set options for grid and other parameters.

        Optional keyword arguments: title, doneAction

        >>> a = Graph()
        >>> a = Graph(title='green')
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
        '''Configure and return a figure object
        '''
        pass

    def setData(self, data):
        self.data = data

    def setTitle(self, title):
        self.title = title

    def setFigureSize(self, figSize):
        self.figureSize = figSize

    def setDoneAction(self, action):
        if action in ['show', 'write', None]:
            self.doneAction = action
        else:
            raise GraphException('not such done action: %s' % action)

    def setTicks(self, axisKey, pairs):
        '''paris are positions and labels
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

    def _adjustAxisSpines(self, ax):
        '''Remove the right and left spines from the diragmra
        '''
        for loc, spine in ax.spines.iteritems():
            if loc in ['left','bottom']:
                pass
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
                        ax.set_xticklabels(labels, fontsize=self.tickFontSize,
                            family=self.fontFamily)

                elif axis == 'y':
                    # this is the old way ticks were set:
                    #plt.yticks(*self.axis[axis]['ticks'])
                    # new way:
                    if 'ticks' in self.axis[axis].keys():
                        values, labels = self.axis[axis]['ticks']
                        #environLocal.printDebug(['y tick labels, y tick values', labels, values])
                        ax.set_yticks(values)
                        ax.set_yticklabels(labels, fontsize=self.tickFontSize,
                            family=self.fontFamily)
            else: # apply some default formatting to default ticks
                ax.set_xticklabels(ax.get_xticks(),
                    fontsize=self.tickFontSize, family=self.fontFamily) 
                ax.set_yticklabels(ax.get_yticks(),
                    fontsize=self.tickFontSize, family=self.fontFamily) 

        if self.title:
            ax.set_title(self.title, fontsize=self.titleFontSize, family=self.fontFamily)

        if self.grid:
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
        '''Calls the show() method of the matplotlib plot. For most matplotlib back ends, this will open a GUI window with the desired graph.
        '''
        plt.show()

    def write(self, fp=None):
        '''Writes the graph to a file. If no file path is given, a temporary file is used. 
        '''
        if fp == None:
            fp = environLocal.getTempFile('.png')
        #print _MOD, fp
        self.fig.savefig(fp, facecolor=self.colorBackgroundFigure,      
                             edgecolor=self.colorBackgroundFigure)
        environLocal.launch('png', fp)



class GraphColorGrid(Graph):
    ''' Grid of discrete colored "blocks" to visualize results of a windowed analysis routine.
    
        Data is provided as a list of lists of colors, based on analysis-specific mapping of colors to results
        
        
        >>> a = GraphColorGrid(doneAction=None)
        >>> data = [['#525252', '#5f5f5f', '#797979', '#858585', '#727272', '#6c6c6c', '#8c8c8c', '#8c8c8c', '#6c6c6c', '#999999', '#999999', '#797979', '#6c6c6c', '#5f5f5f', '#525252', '#464646', '#3f3f3f', '#3f3f3f', '#4c4c4c', '#4c4c4c', '#797979', '#797979', '#4c4c4c', '#4c4c4c', '#525252', '#5f5f5f', '#797979', '#858585', '#727272', '#6c6c6c'], ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#797979', '#6c6c6c', '#5f5f5f', '#5f5f5f', '#858585', '#797979', '#797979', '#797979', '#797979', '#797979', '#797979', '#858585', '#929292', '#999999'], ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#8c8c8c', '#8c8c8c', '#8c8c8c', '#858585', '#797979', '#858585', '#929292', '#999999'], ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#8c8c8c', '#929292', '#999999'], ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999', '#999999'], ['#999999', '#999999', '#999999', '#999999', '#999999']]
        >>> a.setData(data)
        >>> a.process()
    '''
    def __init__(self, *args, **keywords):
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()
        
        
        if 'minWindow' in keywords:
            self.minWindow = keywords['minWindow']
        else:
            self.minWindow = 5
        if 'maxWindow' in keywords:
            self.maxWindow = keywords['maxWindow']
        else:
            # if maxWindow is negative it will revert to maximum number of quarterNote lengths
            self.maxWindow = -1
        if 'windowStep' in keywords:
            self.windowStep = keywords['windowStep']
        else:
            self.windowStep = 3
        
        
    def setColors(self, colors):
        self.colors = colors
    
    def setMinWindow(self, minWindow):
        self.minWindow = minWindow
    
    def setMaxWindow(self, maxWindow):
        self.maxWindow = maxWindow
        
    def setWindowStep(self, windowStep):
        self.windowStep = windowStep

    def process(self):
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        
        axTop = self.fig.add_subplot(111)
        plt.ylabel('Window Size: from 1 quarter note to entire work')
        plt.xlabel('Progression of piece: from beginning to end')
        #plt.legend(('E', 'B', 'F', 'C', 'G', 'D'), 'upper-left')
        
        for i in range(len(self.data)):
            positions = []
            #correlations = []
            heights = []
            subColors = []
            
            for j in range(len(self.data[i])):
                positions.append((1/2)+j)
                subColors.append(self.data[i][j])
                #correlations.append(float(self.data[i][j][2]))
                heights.append(1)
                
            ax = self.fig.add_subplot(len(self.data), 1, len(self.data)-i)
            ax.bar(positions, heights, 1, color=subColors)
            
            for j, line in enumerate(ax.get_xticklines() + ax.get_yticklines()):
                line.set_visible(False)
            ax.set_yticklabels([""]*len(ax.get_yticklabels()))
            ax.set_xticklabels([""]*len(ax.get_xticklabels()))
            ax.set_xlim([0,len(self.data[i])])
            
        self.setAxisRange('x', range(len(self.data)), 0)
        self._adjustAxisSpines(axTop)
        self._applyFormatting(axTop)
        self.done()


class GraphHorizontalBar(Graph):
    def __init__(self, *args, **keywords):
        '''Numerous horizontal bars in discrete channels, where bars can be incomplete and/or overlap.

        Data provided is a list of pairs, where the first value becomes the key, the second value is a list of x-start, x-length values.

    .. image:: images/GraphHorizontalBar.*
        :width: 600

        >>> a = GraphHorizontalBar(doneAction=None)
        >>> data = [('a', [(15, 40)]), ('b', [(5,25), (20,40)]), ('c', [(0,60)])]
        >>> a.setData(data)
        >>> a.process()

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

        for x in range(int(math.floor(xMin)), 
                       int(round(math.ceil(xMax))), int(xMin+int(round(xRange/10)))) + [int(round(xMax))]:
            xTicks.append([x, '%s' % x])
        self.setTicks('x', xTicks)  

        #environLocal.printDebug([yTicks])
        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()



class GraphScatterWeighted(Graph):
    '''A scatter plot where points are scaled in size to represent the number of values stored within.

    .. image:: images/GraphScatterWeighted.*
        :width: 600

    '''

    def __init__(self, *args, **keywords):
        '''A scatter plot where points are scaled in size to represent the number of values stored within.

        >>> a = GraphScatterWeighted(doneAction=None)
        >>> data = [(23, 15, 234), (10, 23, 12), (4, 23, 5)]
        >>> a.setData(data)
        >>> a.process()
        '''
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
    def __init__(self, *args, **keywords):
        '''Graph two parameters in a scatter plot

    .. image:: images/GraphScatter.*
        :width: 600

        >>> a = GraphScatter(doneAction=None)
        >>> data = [(x, x*x) for x in range(50)]
        >>> a.setData(data)
        >>> a.process()

        '''
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
    def __init__(self, *args, **keywords):
        '''Graph the count of a single element.

        Data set is simply a list of x and y pairs, where there
        is only one of each x value, and y value is the count or magnitude
        of that value

    .. image:: images/GraphHistogram.*
        :width: 600

        >>> a = GraphHistogram(doneAction=None)
        >>> data = [(x, random.choice(range(30))) for x in range(50)]
        >>> a.setData(data)
        >>> a.process()

        '''
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

    def process(self):
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        # added extra .1 in middle param to permit space on right 
        ax = self.fig.add_subplot(1, 1.1, 1.1)

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
    def __init__(self, *args, **keywords):
        '''Graph multiple parallel bar graphs in 3D.

        This draws bars with polygons, a temporary alternative to using Graph3DBars, above.

        Note: Due to matplotib issue Axis ticks do not seem to be adjustable without distorting the graph.

    .. image:: images/Graph3DPolygonBars.*
        :width: 600

        >>> a = Graph3DPolygonBars(doneAction=None)
        >>> data = {1:[], 2:[], 3:[]}
        >>> for i in range(len(data.keys())):
        ...    q = [(x, random.choice(range(10*(i+1)))) for x in range(20)]
        ...    data[data.keys()[i]] = q
        >>> a.setData(data)
        >>> a.process()


        '''
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
        return '%s-%s' % (self.format, ''.join(self.values))


    id = property(_getId, doc='''
        Each PlotStream has a unique id that consists of its format and a string that defines the parameters that are graphed.
        ''')

    #---------------------------------------------------------------------------
    def _axisLabelMeasureOrOffset(self):
        '''Return an axis label for measure or offset, depending on if measures are available.
        '''
        from music21 import stream

        # generate an offset map to see if we can find measure numbers, either
        # by looking at keys or by looking at Notes
        offsetMap = self.streamObj.measureOffsetMap([stream.Measure, note.Note])
        if len(offsetMap.keys()) > 0:
            return 'Measure Numbers'
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
        #TODO: this is not yet working!

        post = []
        for value, label in ticks:
            if '-' in label:
                #label = label.replace('-', '&#x266d;')
                label = label.replace('-', 'b')
#             if '#' in label:
#                 label = label.replace('-', '&#x266f;')
            post.append([value, label])
            #post.append([value, unicode(label)])
        return post


    def ticksPitchClassUsage(self, pcMin=0, pcMax=11, showEnharmonic=True,
            blankLabelUnused=True, hideUnused=False):
        '''Get ticks and labels for pitch classes based on usage. That is, show the most commonly used enharmonic first.

        >>> from music21 import corpus
        >>> s = corpus.parseWork('bach/bwv324.xml')
        >>> a = PlotStream(s)
        >>> a.ticksPitchClassUsage(hideUnused=True)
        [[0, u'C'], [2, u'D'], [3, u'D#'], [4, u'E'], [6, u'F#'], [7, u'G'], [9, u'A'], [11, u'B']]

        >>> s = corpus.parseWork('bach/bwv281.xml')
        >>> a = PlotStream(s)
        >>> a.ticksPitchClassUsage(showEnharmonic=True, hideUnused=True)
        [[0, u'C'], [2, u'D'], [3, u'Eb'], [4, u'E'], [5, u'F'], [7, u'G'], [9, u'A'], [10, u'Bb'], [11, u'B']]
        >>> a.ticksPitchClassUsage(showEnharmonic=True, blankLabelUnused=False)
        [[0, u'C'], [1, 'C#'], [2, u'D'], [3, u'Eb'], [4, u'E'], [5, u'F'], [6, 'F#'], [7, u'G'], [8, 'G#'], [9, u'A'], [10, u'Bb'], [11, u'B']]

        >>> s = corpus.parseWork('schumann/opus41no1/movement2.xml')
        >>> a = PlotStream(s)
        >>> a.ticksPitchClassUsage(showEnharmonic=True)
        [[0, u'C'], [1, u'Db/C#'], [2, u'D'], [3, u'Eb/D#'], [4, u'E'], [5, u'F'], [6, u'F#'], [7, u'G'], [8, u'Ab/G#'], [9, u'A'], [10, u'Bb'], [11, u'B']]

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
        >>> a.ticksPitchClass()
        [[0, 'C'], [1, 'C#'], [2, 'D'], [3, 'D#'], [4, 'E'], [5, 'F'], [6, 'F#'], [7, 'G'], [8, 'G#'], [9, 'A'], [10, 'A#'], [11, 'B']]
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
        >>> a.ticksPitchSpaceChromatic(60,72)
        [[60, 'C4'], [61, 'C#4'], [62, 'D4'], [63, 'D#4'], [64, 'E4'], [65, 'F4'], [66, 'F#4'], [67, 'G4'], [68, 'G#4'], [69, 'A4'], [70, 'A#4'], [71, 'B4'], [72, 'C5']]
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
        >>> a.ticksPitchSpaceUsage(hideUnused=True)
        [[64, u'E4'], [66, u'F#4'], [67, u'G4'], [69, u'A4'], [71, u'B4'], [72, u'C5']]

        >>> s = corpus.parseWork('schumann/opus41no1/movement2.xml')
        >>> a = PlotStream(s)
        >>> a.ticksPitchSpaceUsage(showEnharmonic=True, hideUnused=True)
        [[36, u'C2'], [38, u'D2'], [40, u'E2'], [41, u'F2'], [43, u'G2'], [44, u'Ab2'], [45, u'A2'], [47, u'B2'], [48, u'C3'], [50, u'D3'], [51, u'Eb3/D#3'], [52, u'E3'], [53, u'F3'], [54, u'F#3'], [55, u'G3'], [56, u'Ab3/G#3'], [57, u'A3'], [58, u'Bb3'], [59, u'B3'], [60, u'C4'], [61, u'Db4/C#4'], [62, u'D4'], [63, u'Eb4/D#4'], [64, u'E4'], [65, u'F4'], [66, u'F#4'], [67, u'G4'], [68, u'Ab4/G#4'], [69, u'A4'], [70, u'Bb4'], [71, u'B4'], [72, u'C5']]

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
                    displayMeasureNumberZero=False, remap=False):
        '''Get offset ticks. If Measures are found, they will be used to create ticks. If not, `offsetStepSize` will be used to create offset ticks between min and max. The `remap` parameter is not yet used. 

        >>> from music21 import corpus, stream, note
        >>> s = corpus.parseWork('bach/bwv281.xml')
        >>> a = PlotStream(s)
        >>> a.ticksOffset() # on whole score
        [[4.0, '1'], [8.0, '2'], [12.0, '3'], [16.0, '4'], [20.0, '5'], [24.0, '6'], [28.0, '7'], [32.0, '8']]

        >>> a = PlotStream(s[0]) # on a Part
        >>> a.ticksOffset() # on whole score
        [[4.0, '1'], [8.0, '2'], [12.0, '3'], [16.0, '4'], [20.0, '5'], [24.0, '6'], [28.0, '7'], [32.0, '8']]
        >>> a.ticksOffset(8, 12, 2)
        [[8.0, '2'], [12.0, '3']]

        >>> a = PlotStream(s[0].flat) # on a Flat collection
        >>> a.ticksOffset(8, 12, 2)
        [[8.0, '2'], [12.0, '3']]

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
        offsetMap = self.streamObj.measureOffsetMap([stream.Measure, note.Note])
        ticks = [] # a lost of graphed value, string label pairs
        if len(offsetMap.keys()) > 0:
            #environLocal.printDebug(['using measures for offset ticks'])

            # store indices in offsetMap
            mNoToUse = []
            for key in sorted(offsetMap.keys()):
                if key >= offsetMin and key <= offsetMax:
                    if key == 0 and not displayMeasureNumberZero:
                        continue # skip
                    #if key == sorted(offsetMap.keys())[-1]:
                    #    continue # skip last
                    # assume we can get the first Measure in the lost if
                    # measurers; this may not always be True
                    mNoToUse.append(key)

            if len(mNoToUse) > 20:
                # get about 10 ticks
                mNoStepSize = int(len(mNoToUse) / 10.)
            else:
                mNoStepSize = 1

            for i in range(0, len(mNoToUse), mNoStepSize):
                offset = mNoToUse[i]
                mNumber = offsetMap[offset][0].measureNumber
                ticks.append([offset, '%s' % mNumber])

        else: # generate numeric ticks
            if offsetStepSize == None:
                offsetStepSize = 10
            #environLocal.printDebug(['using offsets for offset ticks'])
            for i in range(offsetMin, offsetMax+1, offsetStepSize):
                ticks.append([i, '%s' % i])

        #environLocal.printDebug(['final ticks', ticks])
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

   
    def ticksDynamics(self):
        '''Utility method to get ticks in dynamic values.

        >>> from music21 import stream; s = stream.Stream()
        >>> a = PlotStream(s)
        >>> a.ticksDynamics()
        [[0, 'pppppp'], [1, 'ppppp'], [2, 'pppp'], [3, 'ppp'], [4, 'pp'], [5, 'p'], [6, 'mp'], [7, 'mf'], [8, 'f'], [9, 'fp'], [10, 'sf'], [11, 'ff'], [12, 'fff'], [13, 'ffff'], [14, 'fffff'], [15, 'ffffff']]
        '''
        ticks = []
        for i in range(len(dynamics.shortNames)):
            ticks.append([i, dynamics.shortNames[i]])
        return ticks
    
    
    
    
    


#-------------------------------------------------------------------------------
# color grids    

class PlotColorGrid(PlotStream):
    format = ''
    
    def __init__(self, streamObj, AnalysisProcessor, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)
        
        self.graph = GraphColorGrid(*args, **keywords)
        
        data, yTicks = self._extractData(AnalysisProcessor)
        
        self.graph.setData(data)
        
        self.graph.setAxisLabel('y', 'Window Size')
        self.graph.setAxisLabel('x', 'Time')
        
        self.graph.setTicks('y', yTicks)
        
        
    def _extractData(self, AnalysisProcessor, dataValueLegit=True):
        b = AnalysisProcessor
        a = windowedAnalysis.WindowedAnalysis(self.streamObj, b)
        soln = a.process(self.graph.minWindow, self.graph.maxWindow, self.graph.windowStep)
        
        
        yTicks = []
        for y in range(self.graph.minWindow, len(soln[1]), ((len(soln[1])-self.graph.minWindow)/10)+1):
            yTicks.append([y, '%s' % y])
        
        print yTicks
        return soln[1], yTicks
    
    
class PlotColorGridKrumhanslSchmuckler(PlotColorGrid):
    '''Subclass for plotting Krumhansl-Schmuckler analysis routine
    '''
    format = 'colorGrid'
    
    def __init__(self, streamObj, *args, **keywords):
        PlotColorGrid.__init__(self, streamObj, windowedAnalysis.KrumhanslSchmuckler(), *args, **keywords)
    
    
class PlotColorGridSadoianAmbitus(PlotColorGrid):
    '''Subclass for plotting basic pitch span over a windowed analysis
    '''
    format = 'colorGrid'
    
    def __init__(self, streamObj, *args, **keywords):
        PlotColorGrid.__init__(self, streamObj, windowedAnalysis.SadoianAmbitus(), *args, **keywords)
        

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
        for y in range(0, countMax, 10):
            yTicks.append([y, '%s' % y])
        yTicks.sort()
        return data, xTicks, yTicks


class PlotHistogramPitchSpace(PlotHistogram):
    '''A histogram of pitch space.

    .. image:: images/PlotHistogramPitchSpace.*
        :width: 600


    >>> from music21 import corpus
    >>> s = corpus.parseWork('bach/bwv324.xml')
    >>> a = PlotHistogramPitchSpace(s)
    >>> a.id
    'histogram-pitch'
    '''
    values = ['pitch']
    def __init__(self, streamObj, *args, **keywords):
        PlotHistogram.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n:n.midi
        self.fxTick = lambda n: n.nameWithOctave
        # replace with self.ticksPitchSpaceUsage


        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData()

        self.graph = GraphHistogram(*args, **keywords)
        self.graph.setData(data)

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)

        self.graph.setAxisLabel('y', 'Count')
        self.graph.setAxisLabel('x', 'Pitch')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([8,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Histogram')


class PlotHistogramPitchClass(PlotHistogram):
    '''A histogram of pitch class

    .. image:: images/PlotHistogramPitchClass.*
        :width: 600

    >>> from music21 import corpus
    >>> s = corpus.parseWork('bach/bwv324.xml')
    >>> a = PlotHistogramPitchClass(s)
    >>> a.id
    'histogram-pitchClass'
    '''
    values = ['pitchClass']
    def __init__(self, streamObj, *args, **keywords):
        PlotHistogram.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n:n.pitchClass
        self.fxTick = lambda n: n.nameWithOctave
        # replace with self.ticksPitchClassUsage

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData()

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

    .. image:: images/PlotHistogramQuarterLength.*
        :width: 600

    >>> from music21 import corpus
    >>> s = corpus.parseWork('bach/bwv324.xml')
    >>> a = PlotHistogramQuarterLength(s)
    >>> a.id
    'histogram-quarterLength'
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

#             if not xValueLegit: # get index number, not actual value
#                 x = xValues.index(x)
            data.append([x, y])

        xVals = [x for x,y in data]
        yVals = [y for x,y in data]

        xTicks = self.fxTicks(min(xVals), max(xVals), remap=xLog)
        yTicks = self.fyTicks(min(yVals), max(yVals))

        return data, xTicks, yTicks


class PlotScatterPitchSpaceQuarterLength(PlotScatter):
    '''A scatter plot of pitch space and quarter length

    .. image:: images/PlotScatterPitchSpaceQuarterLength.*
        :width: 600

    >>> from music21 import corpus
    >>> s = corpus.parseWork('bach/bwv324.xml')
    >>> a = PlotHistogramQuarterLength(s)
    >>> a.id
    'histogram-quarterLength'
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

        if 'xLog' not in keywords:
            xLog = True
        else:
            xLog = keywords['xLog']

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData(xLog=xLog)

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

    .. image:: images/PlotHorizontalBarPitchClassOffset.*
        :width: 600
    '''

    values = ['pitchClass', 'offset']
    def __init__(self, streamObj, *args, **keywords):
        PlotHorizontalBar.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n:n.pitchClass
        self.fyTicks = self.ticksPitchClassUsage
        self.fxTicks = self.ticksOffset

        data, xTicks, yTicks = self._extractData()

        self.graph = GraphHorizontalBar(*args, **keywords)
        self.graph.setData(data)

        # only need to add x ticks; y ticks added from data labels
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

    .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        :width: 600
    '''


    values = ['pitch', 'offset']
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

        if len(self.streamObj.measures) > 0 or len(self.streamObj.semiFlat.measures) > 0:
            self.graph.setAxisLabel('x', 'Measure Numbers')
        else:
            self.graph.setAxisLabel('x', 'Offset')
        self.graph.setAxisLabel('y', 'Pitch')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([10,5])

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
        xTicks = []
        yTicks = self.fyTicks(min(yValues), max(yValues))
        zTicks = []
        return data, xTicks, yTicks, zTicks


class Plot3DBarsPitchSpaceQuarterLength(Plot3DBars):
    '''A scatter plot of pitch and quarter length

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
        #self.graph.setAxisLabel('z', 'Count')

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

    Plot method can be specified as a second argument or by keyword. Available plots include the following:

    pitchSpace (:class:`~music21.graph.PlotHistogramPitchSpace`)
    pitchClass (:class:`~music21.graph.PlotHistogramPitchClass`)
    quarterLength (:class:`~music21.graph.PlotHistogramQuarterLength`)

    scatterPitchSpaceQuarterLength (:class:`~music21.graph.PlotScatterPitchSpaceQuarterLength`)
    scatterPitchClassQuarterLength (:class:`~music21.graph.PlotScatterPitchClassQuarterLength`)
    scatterPitchClassOffset (':class:`~graph.PlotScatterPitchClassOffset`)

    pitchClassOffset (:class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`)
    pitchSpaceOffset (:class:`~music21.graph.PlotHorizontalBarPitchClassOffset`)

    pitchSpaceQuarterLengthCount (:class:`~music21.graph.PlotScatterWeightedPitchSpaceQuarterLength`)
    pitchClassQuarterLengthCount (:class:`~music21.graph.PlotScatterWeightedPitchClassQuarterLength`)

    3DPitchSpaceQuarterLengthCount (:class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`)

    '''
    plotClasses = [
        # histograms
        PlotHistogramPitchSpace, PlotHistogramPitchClass, PlotHistogramQuarterLength,
        # scatters
        PlotScatterPitchSpaceQuarterLength, PlotScatterPitchClassQuarterLength, PlotScatterPitchClassOffset,
        # offset based horizontal
        PlotHorizontalBarPitchSpaceOffset, PlotHorizontalBarPitchClassOffset,
        # weighted scatter
        PlotScatterWeightedPitchSpaceQuarterLength, PlotScatterWeightedPitchClassQuarterLength,
        # 3d graphs
        Plot3DBarsPitchSpaceQuarterLength,
    ]


    if 'format' in keywords:
        format = keywords['format']
    else:
        format = None
    if 'values' in keywords:
        values = keywords['values'] # should be a list
    else:
        values = None

    if len(args) > 0:
        format = args[0]
    if len(args) > 1:
        values = args[1] # get all remaining

    if not common.isListLike(values):
        values = [values]

    #plotRequest = 'PlotHorizontalBarPitchSpaceOffset'
    if format == None and values == None:
        format = 'horizontalBar'
        values = ['pitch', 'offset']
    if format == None:
        format = 'histogram'
    if values == None or values == [None]:
        values = ['pitch']

    environLocal.printDebug(['plotStream: stream', streamObj, 'format, values', format, values])


    plotMake = []
    if format.lower() == 'all':
        plotMake = plotClasses
    else:
        for plotClassName in plotClasses:
            if plotClassName.__name__.lower() == format.lower():
                plotMake.append(plotClassName)

            # try direct match
            plotClassNameValues = [x.lower() for x in plotClassName.values]
            if plotClassName.format.lower() == format.lower():
                match = 0
                for requestedValue in values:
                    if requestedValue == None: continue
                    if (requestedValue.lower() in plotClassNameValues):
                        match += 1
                if match == len(values):
                    plotMake.append(plotClassName)

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
        b = PlotHorizontalBarPitchClassOffset(a[0].getMeasureRange(3,6), title='Bach (soprano voice, mm 3-6)')
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
            [('a', [(15, 40)]), ('b', [(5,25), (20,40)]), ('c', [(0,60)])]),
        (GraphScatterWeighted, 
            [(23, 15, 234), (10, 23, 12), (4, 23, 5), (15, 18, 120)]),
        (GraphScatter, 
            [(x, x*x) for x in range(50)]),
        (GraphHistogram, 
            [(x, random.choice(range(30))) for x in range(50)]),
        (Graph3DPolygonBars, data3DPolygonBars),
        ]

        for graphClassName, data in graphClasses:
            obj = graphClassName(doneAction=None)
            obj.setData(data) # add data here
            obj.process()
            fn = obj.__class__.__name__ + '.png'
            fp = os.path.join(environLocal.getRootTempDir(), fn)
            environLocal.printDebug(['writing fp:', fp])
            obj.write(fp)


    def writeAllPlots(self):
        '''Write a graphic file for all graphs, naming them after the appropriate class. This is used to generate documentation samples.
        '''
        import os

        plotClasses = [
        # histograms
        PlotHistogramPitchSpace, PlotHistogramPitchClass, PlotHistogramQuarterLength,
        # scatters
        PlotScatterPitchSpaceQuarterLength, PlotScatterPitchClassQuarterLength, PlotScatterPitchClassOffset,
        # offset based horizontal
        PlotHorizontalBarPitchSpaceOffset, PlotHorizontalBarPitchClassOffset,
        # weighted scatter
        PlotScatterWeightedPitchSpaceQuarterLength, PlotScatterWeightedPitchClassQuarterLength,
        # 3d graphs
        Plot3DBarsPitchSpaceQuarterLength,
        ]

        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')

        for plotClassName in plotClasses:
            obj = plotClassName(a, doneAction=None)
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
        
    def testPlotColorGridSadoianAmbitus(self):
        from music21 import corpus
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotColorGridSadoianAmbitus(a, doneAction=None, title='Bach')
        b.process()


    def testAll(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        plotStream(a.flat, doneAction=None)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [PlotHistogramPitchSpace, PlotHistogramPitchClass, PlotHistogramQuarterLength,
        # scatters
        PlotScatterPitchSpaceQuarterLength, PlotScatterPitchClassQuarterLength, PlotScatterPitchClassOffset,
        # offset based horizontal
        PlotHorizontalBarPitchSpaceOffset, PlotHorizontalBarPitchClassOffset,
        # weighted scatter
        PlotScatterWeightedPitchSpaceQuarterLength, PlotScatterWeightedPitchClassQuarterLength,
        # 3d graphs
        Plot3DBarsPitchSpaceQuarterLength,
]



if __name__ == "__main__":
    #music21.mainTest(Test, TestExternal)

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        a = TestExternal()
        a.testPlotScatterWeightedPitchSpaceQuarterLength()

        #a.testPlotQuarterLength()
        a.testPlotScatterPitchSpaceQuarterLength()
