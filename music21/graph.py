#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         graph.py
# Purpose:      Abstract utilities in matplotlib and/or other graphing tools.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest
import random, math

import music21

from music21 import note
from music21 import dynamics
from music21 import duration
from music21 import pitch

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
    environLocal.printWarn('no matplotlib available')





#-------------------------------------------------------------------------------
class GraphException(Exception):
    pass

class PlotStreamException(Exception):
    pass



#-------------------------------------------------------------------------------
class Graph(object):
    '''An object representing a graph or plot, automating the creation and configuration of this graph in matplotlib. 

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
            self.colorBackgroundFigure = '#cccccc'

        if 'colorGrid' in keywords:
            self.colorGrid = keywords['colorBackgroundFigure']
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
                        fontsize=self.labelFontSize, family=self.fontFamily)
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

        if self.title:
            ax.set_title(self.title, fontsize=self.titleFontSize, family=self.fontFamily)
        if self.grid:
            ax.grid(True, color=self.colorGrid)

        # this figure instance is created in the subclased process() method
        # set total size of figure
        self.fig.set_figwidth(self.figureSize[0]) 
        self.fig.set_figheight(self.figureSize[1]) 

#         ax.set_xscale('linear')
#         ax.set_yscale('linear')
#         ax.set_aspect('normal')

    def process(self):
        '''process data and prepare plt'''
        pass


    #---------------------------------------------------------------------------
    def done(self):
        '''Implement the desired doneAction, after data processing
        '''
        if self.doneAction == 'show':
            self.show()
        elif self.doneAction == 'write':
            self.write()
        elif self.doneAction == None:
            pass

    def show(self):
        plt.show()

    def write(self, fp=None):
        if fp == None:
            fp = environLocal.getTempFile('.png')
        #print _MOD, fp
        self.fig.savefig(fp, facecolor=self.colorBackgroundFigure,      
                             edgecolor=self.colorBackgroundFigure)
        environLocal.launch('png', fp)





class Graph2DBrokenHorizontalBar(Graph):
    def __init__(self, *args, **keywords):
        '''Numerous horizontal bars in discrete channels, where bars can be incomplete and/or overlap. 

        Data provided is a list of pairs, where the first value becomes the key, the second value is a list of x-start, x-end points. 

        >>> a = Graph2DBrokenHorizontalBar(doneAction=None)
        >>> data = [('a', [(10,20), (15, 40)]), ('b', [(5,15), (20,40)])]
        >>> a.setData(data)
        >>> a.process()
        '''
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

        self._barSpace = 10
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

        ax = self.fig.add_subplot(111)

        yPos = 0
        xPoints = [] # store all to find min/max
        yTicks = [] # a list of label, value pairs
        xTicks = []

        keys = []
        i = 0
        for key, points in self.data:
            keys.append(key)
            # provide a lost of start, end points; 
            # then start y position, bar height
            ax.broken_barh(points, (yPos+self._margin, self._barHeight),
                            facecolors=self.colors[i%len(self.colors)], alpha=self.alpha)
            for xStart, xEnd in points:
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

        self.setAxisRange('y', (0, len(keys) * self._barSpace))
        self.setAxisRange('x', (xMin, xMax))
        self.setTicks('y', yTicks)  

        for x in range(int(xMin+10), int(xMax), 10):
            xTicks.append([x, '%s' % x])
        self.setTicks('x', xTicks)  

        #environLocal.printDebug([yTicks])

        self._applyFormatting(ax)
        self.done()



class Graph2DScatterWeighted(Graph):
    '''A scatter plot where points are scaled in size to represent the number of values stored within.
    '''

    def __init__(self, *args, **keywords):
        '''A scatter plot where points are scaled in size to represent the number of values stored within.

        >>> a = Graph2DScatterWeighted(doneAction=None)
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
        ax = self.fig.add_subplot(111)

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
                zNorm.append(0)
            else:
                # this will make the minimum scalar 0 when z is zero
                scalar = (z-zMin) / zRange # shifted part / range
                zNorm.append(self._minDiameter + (self._rangeDiameter * scalar))

        # draw elipses
        for i in range(len(self.data)):
            x = xList[i]
            y = yList[i]
            z = zNorm[i] # normalized values

            width=z*xDistort
            height=z*yDistort
            e = patches.Ellipse(xy=(x, y), width=width, height=height)
            #e = patches.Circle(xy=(x, y), radius=z)
            ax.add_artist(e)

            e.set_clip_box(ax.bbox)
            e.set_alpha(self.alpha)
            e.set_facecolor(self.colors[i%len(self.colors)]) # can do this here
            #environLocal.printDebug([e])

            if z != 0:
                ax.text(x+(width*.7), y+.15, "%s" % zList[i], size=8,
                    va="baseline", ha="left", multialignment="left")

        self.setAxisRange('y', (yMin, yMax), pad=True)
        self.setAxisRange('x', (xMin, xMax), pad=True)

        self._applyFormatting(ax)
        self.done()


class Graph2DScatter(Graph):
    def __init__(self, *args, **keywords):
        '''Graph two parameters in a scatter plot

        >>> a = Graph2DScatter(doneAction=None)
        >>> data = [(x, x*x) for x in range(50)]
        >>> a.setData(data)
        >>> a.process()
        '''
        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

    def process(self):
        '''
        xValueLegit determines if index values or real values are used
        '''
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        ax = self.fig.add_subplot(111)
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

        self._applyFormatting(ax)
        self.done()

class Graph2DHistogram(Graph):
    def __init__(self, *args, **keywords):
        '''Graph the count of a single element.

        Data set is simply a list of x and y pairs, where there
        is only one of each x value, and y value is the count or magnitude
        of that value

        >>> a = Graph2DHistogram(doneAction=None)
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
        ax = self.fig.add_subplot(111)

        x = []
        y = []
        for a, b in self.data:
            x.append(a)
            y.append(b)
        ax.bar(x, y, alpha=.8, color=self.colors[0])
        self._applyFormatting(ax)
        self.done()

class Graph3DBars(Graph):
    def __init__(self, *args, **keywords):
        '''
        Graph multiple parallel bar graphs in 3D.

        Note: there is bug in matplotlib .99.0 that causes the units to be unusual here. this is supposed to fixed with a new release

        Data definition:
        A dictionary where each key forms an array sequence along the z 
        plane (which is depth)
        For each dictionary, a list of value pairs, where each pair is the 
        (x, y) coordinates. 
        
        >>> a = Graph3DBars()
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

        Note: Axis ticks do not seem to be adjustable without distorting the graph.

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
            self.barWidth = .4


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

        if self.axis['x']['range'] == None:
            self.axis['x']['range'] =  min(xVals), max(xVals)
        # swap y for z
        if self.axis['z']['range'] == None:
            self.axis['z']['range'] =  min(yVals), max(yVals)
        if self.axis['y']['range'] == None:
            self.axis['y']['range'] =  min(zVals), max(zVals)+1
            
        # this kinda works but does not adjust the ticks / scale range
        #self.axis['x']['scale'] = 'symlog'

        low, high = self.axis['y']['range']
        low = int(math.floor(low))
        high = int(math.ceil(high))
        zs = range(low, high)
        # colors are not working; not sure why
        #assert len(vertsColor) == len(zVals)
        #print _MOD, vertsColor

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

    id = None # string name used to access this class
    def __init__(self, streamObj, *args, **keywords):
        if not isinstance(streamObj, music21.stream.Stream):
            raise PlotStreamException('non-stream provided as argument')
        self.streamObj = streamObj
        self.graph = None  # store instance of graph class here

    def process(self):
        '''This will process all data, as well as call the done() method. This might be subclassed
        '''
        self.graph.process()

    def show(self):
        '''Call internal Graphs show() method independently of doneAction set and run with process()
        '''
        self.graph.show()

    def write(self, fp):
        '''Call internal Graphs write() method independently of doneAction set and run with process()
        '''
        self.graph.write()


    def ticksPitchClass(self, pcMin=0, pcMax=11):
        '''Utility method to get ticks in pitch classes

        >>> from music21 import stream; s = stream.Stream()
        >>> a = PlotStream(s)
        >>> a.ticksPitchClass()
        [[0, 'C'], [1, 'C#'], [2, 'D'], [3, 'D#'], [4, 'E'], [5, 'F'], [6, 'F#'], [7, 'G'], [8, 'G#'], [9, 'A'], [10, 'A#'], [11, 'B']]
        '''
        ticks = []
        for i in range(pcMin, pcMax+1):
            p = pitch.Pitch()
            p.ps = i
            ticks.append([i, '%s' % p.name])
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
            ticks.append([i, '%s%s%s' % (name, acc.modifier, oct)])
        return ticks

    def convertPsToNoteName(self, ps):
        name, acc = pitch.convertPsToStep(ps)
        oct = pitch.convertPsToOct(ps)
        return '%s%s%s' % (name, acc.modifier, oct)


    def ticksQuarterLength(self, qlList=None, labelStyle='type'):
        '''

        >>> from music21 import stream; s = stream.Stream()
        >>> a = PlotStream(s)
        >>> a.ticksQuarterLength()
        [[0.25, '16th'], [0.5, 'eighth'], [1, 'quarter'], [2, 'half'], [4, 'whole']]

        '''
        if qlList == None: # provide a default if not provided
            qlList = (.25, .5, 1, 2, 4)
        ticks = []
        for i in range(len(qlList)):
            qLen = qlList[i]
            # dtype, match = duration.
            # ticks.append([qLen, dc.convertQuarterLengthToType(qLen)]) 
            if labelStyle == 'type':
                ticks.append([qLen, duration.Duration(qLen).type]) 
            elif labelStyle == 'index':
                ticks.append([i, '%s' % qLen]) 
            else:
                raise PlotStreamException('bad label style: %s' % labelStyle)
        return ticks

# this does not get dots
#     def convertQuarterLengthToType(self, qLen):
#         return '%s' % duration.Duration(qLen).type

    
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
# stream plotting

class PlotHistogram(PlotStream):
    '''Base class for Stream plotting classes.
    '''
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

    def _extractData(self, dataValueLegit=True):
        data = {}
        dataTick = {}
        countMin = 0 # could be the lowest value found
        countMax = 0

        dataValues = []
        for noteObj in self.streamObj.getElementsByClass(note.Note):
            value = self.fx(noteObj)
            if value not in dataValues:
                dataValues.append(value)
        dataValues.sort()

        for noteObj in self.streamObj.getElementsByClass(note.Note):
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


#-------------------------------------------------------------------------------
# histograms

class PlotPitchSpace(PlotHistogram):
    '''A histogram of pitch space

    '''
    id = 'pitchSpace' # string name used to access this class
    def __init__(self, streamObj, *args, **keywords):
        PlotHistogram.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n:n.midi
        self.fxTick = lambda n: n.nameWithOctave

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData()

        self.graph = Graph2DHistogram(*args, **keywords)
        self.graph.setData(data)

        self.graph.setTicks('x', xTicks)
        self.graph.setTicks('y', yTicks)

        self.graph.setAxisLabel('y', 'Count')
        self.graph.setAxisLabel('x', 'Pitch Space')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([8,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Space Histogram')


class PlotPitchClass(PlotHistogram):
    '''A histogram of pitch class

    '''
    id = 'pitchClass' # string name used to access this class
    def __init__(self, streamObj, *args, **keywords):
        PlotHistogram.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n:n.pitchClass
        self.fxTick = lambda n: n.nameWithOctave

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData()

        self.graph = Graph2DHistogram(*args, **keywords)
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


class PlotQuarterLength(PlotHistogram):
    '''A histogram of pitch class

    '''
    id = 'quarterLength' # string name used to access this class
    def __init__(self, streamObj, *args, **keywords):
        PlotHistogram.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n:n.quarterLength
        self.fxTick = lambda n: n.quarterLength

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData(dataValueLegit=False)

        self.graph = Graph2DHistogram(*args, **keywords)
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
    '''Base class for scatter plots.
    '''
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

        # sample values; customize in subclass
        self.fy = lambda n:n.ps
        self.fyTicks = self.ticksPitchSpaceChromatic

        self.fx = lambda n:n.quarterLength
        self.fxTicks = self.ticksQuarterLength

    def _extractData(self, xValueLegit=True):
        data = []
        xValues = []
        yValues = []

        for noteObj in self.streamObj.getElementsByClass(note.Note):
            x = self.fx(noteObj)
            y = self.fy(noteObj)
            if x not in xValues:
                xValues.append(x)            
            if y not in xValues:
                yValues.append(x)            
    
        xValues.sort()
        yValues.sort()
        for noteObj in self.streamObj.getElementsByClass(note.Note):
            x = self.fx(noteObj)
            y = self.fy(noteObj)

            if not xValueLegit: # get index number, not actual value
                x = xValues.index(x)
            data.append([x, y])

        xVals = [x for x,y in data]
        yVals = [y for x,y in data]
        # xTicks expects a list of values
        if self.fxTicks != None:
            if xValueLegit:
                xTicks = self.fxTicks(xValues)
            else:
                xTicks = self.fxTicks(xValues, labelStyle='index')
        else: # if None, create ticks manually
            xTicks = []
            for x in range(min(xVals), max(xVals), 10):
                xTicks.append([x, '%s' % x])

        yTicks = self.fyTicks(min(yVals), max(yVals))

        return data, xTicks, yTicks


class PlotScatterPitchSpaceQuarterLength(PlotScatter):
    '''A scatter plot of pitch space and quarter length

    '''
    id = 'scatterPitchSpaceQuarterLength' # string name used to access this class
    def __init__(self, streamObj, *args, **keywords):
        PlotScatter.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n:n.ps
        self.fyTicks = self.ticksPitchSpaceChromatic

        self.fx = lambda n:n.quarterLength
        self.fxTicks = self.ticksQuarterLength

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData(xValueLegit=False)

        self.graph = Graph2DScatter(*args, **keywords)
        self.graph.setData(data)

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Pitch Space')
        self.graph.setAxisLabel('x', 'Qaurter Length')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Space by Quarter Length Scatter')


class PlotScatterPitchClassQuarterLength(PlotScatter):
    '''A scatter plot of pitch class and quarter length
    '''
    # string name used to access this class
    id = 'scatterPitchClassQuarterLength' 
    def __init__(self, streamObj, *args, **keywords):
        PlotScatter.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n:n.pitchClass
        self.fyTicks = self.ticksPitchClass

        self.fx = lambda n:n.quarterLength
        self.fxTicks = self.ticksQuarterLength

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData(xValueLegit=False)

        self.graph = Graph2DScatter(*args, **keywords)
        self.graph.setData(data)

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Pitch Space')
        self.graph.setAxisLabel('x', 'Qaurter Length')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Space by Quarter Length Scatter')


class PlotScatterPitchClassOffset(PlotScatter):
    '''A scatter plot of pitch class and offset

    '''
    id = 'scatterPitchClassOffset' # string name used to access this class
    def __init__(self, streamObj, *args, **keywords):
        PlotScatter.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n:n.pitchClass
        self.fyTicks = self.ticksPitchClass

        self.fx = lambda n:n.offset
        self.fxTicks = None

        # will use self.fx and self.fxTick to extract data
        data, xTicks, yTicks = self._extractData(xValueLegit=False)

        self.graph = Graph2DScatter(*args, **keywords)
        self.graph.setData(data)

        self.graph.setTicks('y', yTicks)
        self.graph.setTicks('x', xTicks)
        self.graph.setAxisLabel('y', 'Pitch Space')
        self.graph.setAxisLabel('x', 'Offset')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Pitch Class by Offset Scatter')



#-------------------------------------------------------------------------------
# horizontal bar graphs

class PlotBrokenHorizontalBar(PlotStream):
    '''A graph of events, sorted by pitch, over time

    '''
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n:n.ps
        self.fyTicks = self.ticksPitchSpaceChromatic

    def _extractData(self):
        # find listing for any single pitch name
        dataUnique = {}
        xValues = []
        # collect data
        for noteObj in self.streamObj.getElementsByClass(note.Note):
            # numeric value here becomes y axis
            numericValue = int(round(self.fy(noteObj)))
            if numericValue not in dataUnique.keys():
                dataUnique[numericValue] = []
            # all work with offset
            start = noteObj.offset
            end = noteObj.quarterLength
            xValues.append(start)
            xValues.append(end)
            dataUnique[numericValue].append((start, end))

        # create final data list
        # get labels from ticks
        data = []
        # ticks are auto-generated in lower-level routines
        # this is used just for creating labels
        yTicks = self.fyTicks(min(dataUnique.keys()),
                                       max(dataUnique.keys()))

        for numericValue, label in yTicks:
            if numericValue in dataUnique.keys():
                data.append([label, dataUnique[numericValue]])
            else:
                data.append([label, []])
        xTicks = []
        yTicks = []
        return data


class PlotPitchClassOffset(PlotBrokenHorizontalBar):
    '''A graph of events, sorted by pitch class, over time

    '''
    id = 'pitchClassOffset' # string name used to access this class

    def __init__(self, streamObj, *args, **keywords):
        PlotBrokenHorizontalBar.__init__(self, streamObj, *args, **keywords)

        self.fy = lambda n:n.pitchClass
        self.fyTicks = self.ticksPitchClass

        data = self._extractData()

        self.graph = Graph2DBrokenHorizontalBar(*args, **keywords)
        self.graph.setData(data)

        # do not need to add ticks; happens at lower level 

        self.graph.setAxisLabel('x', 'Offset')
        self.graph.setAxisLabel('y', 'Pitch Space')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([10,4])

        if 'title' not in keywords:
            self.graph.setTitle('Note Quarter Length and Offset by Pitch Class')



class PlotPitchSpaceOffset(PlotBrokenHorizontalBar):
    '''A graph of events, sorted by pitch space, over time

    '''
    id = 'pitchSpaceOffset' # string name used to access this class

    def __init__(self, streamObj, *args, **keywords):
        PlotBrokenHorizontalBar.__init__(self, streamObj, *args, **keywords)
        
        self.fy = lambda n:n.ps
        self.fyTicks = self.ticksPitchSpaceChromatic

        data = self._extractData()

        self.graph = Graph2DBrokenHorizontalBar(*args, **keywords)
        self.graph.setData(data)

        # do not need to add ticks; happens at lower level 

        self.graph.setAxisLabel('x', 'Offset')
        self.graph.setAxisLabel('y', 'Pitch Space')

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([10,5])

        if 'title' not in keywords:
            self.graph.setTitle('Note Quarter Length and Offset by Pitch')



#-------------------------------------------------------------------------------
# weighted scatter

class PlotScatterWeighted(PlotStream):
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)

        # specialize in sub-class
        self.fx = lambda n:n.quarterLength
        self.fy = lambda n: n.midi
        self.fyTicks = self.ticksPitchClass

    def _extractData(self):
        dataCount = {}
        xValues = []
        yValues = []
        # find all combinations of x/y
        for noteObj in self.streamObj.getElementsByClass(note.Note):
            x = self.fx(noteObj)
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
        for noteObj in self.streamObj.getElementsByClass(note.Note):
            indexToIncrement = xValues.index(self.fx(noteObj))

            # second position stores increment
            dataCount[self.fy(noteObj)][indexToIncrement][1] += 1
            if dataCount[self.fy(noteObj)][indexToIncrement][1] > maxCount:
                maxCount = dataCount[self.fy(noteObj)][indexToIncrement][1] 

        # create final data list
        data = []
        for y, label in self.fyTicks(yMin, yMax):

        #for y in dataCount.keys():
                
            #yIndex = yValues.index(y)      
            yIndex = y
            for x, z in dataCount[y]:
                xIndex = xValues.index(x)
                data.append([xIndex, yIndex, z])

        # set ticks
        xTicks = []
        for i in range(len(xValues)):
            x = xValues[i]
            xTicks.append([i, '%s' % x])
        # only label y values that are defined
        yTicks = []
        for y, label in self.fyTicks(yMin, yMax):

        #for i in range(len(yValues)):
            #y = yValues[i]
            # y is a midi pitch value; find its name
            #nn = self.convertPsToNoteName(y)
            yTicks.append([y, '%s' % label])
        return data, xTicks, yTicks


class PlotPitchSpaceQuarterLengthCount(PlotScatterWeighted):
    '''A graph of event, sorted by pitch, over time
    '''
    id = 'pitchSpaceQuarterLengthCount'
    def __init__(self, streamObj, *args, **keywords):
        PlotScatterWeighted.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n:n.quarterLength
        self.fy = lambda n: n.midi
        self.fyTicks = self.ticksPitchSpaceChromatic

        data, xTicks, yTicks = self._extractData()

        self.graph = Graph2DScatterWeighted(*args, **keywords)
        self.graph.setData(data)

        self.graph.setAxisLabel('x', 'Quarter Length')
        self.graph.setAxisLabel('y', 'Pitch Space')

        self.graph.setTicks('y', yTicks)  
        self.graph.setTicks('x', xTicks)  

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Count of Pitch and Quarter Length')


class PlotPitchClassQuarterLengthCount(PlotScatterWeighted):
    '''A graph of event, sorted by pitch class, over time
    '''
    id = 'pitchClassQuarterLengthCount'
    def __init__(self, streamObj, *args, **keywords):
        PlotScatterWeighted.__init__(self, streamObj, *args, **keywords)

        self.fx = lambda n:n.quarterLength
        self.fy = lambda n: n.pitchClass
        self.fyTicks = self.ticksPitchClass

        data, xTicks, yTicks = self._extractData()

        self.graph = Graph2DScatterWeighted(*args, **keywords)
        self.graph.setData(data)

        self.graph.setAxisLabel('x', 'Quarter Length')
        self.graph.setAxisLabel('y', 'Pitch Class')

        self.graph.setTicks('y', yTicks)  
        self.graph.setTicks('x', xTicks)  

        # need more space for pitch axis labels
        if 'figureSize' not in keywords:
            self.graph.setFigureSize([6,6])
        if 'title' not in keywords:
            self.graph.setTitle('Count of Pitch Class and Quarter Length')



#-------------------------------------------------------------------------------
# public function 

def plotStream(streamObj, *args, **keywords):
    '''Public interface to Stream plotting methods. 
    '''
    plotClasses = [
        # histograms
        PlotPitchSpace, PlotPitchClass, PlotQuarterLength, 
        # scatters
        PlotScatterPitchSpaceQuarterLength, PlotScatterPitchClassQuarterLength, PlotScatterPitchClassOffset,
        # offset based horizontal
        PlotPitchSpaceOffset, PlotPitchClassOffset,
        # weighted scatter
        PlotPitchSpaceQuarterLengthCount, PlotPitchClassQuarterLengthCount,
    ]


    if 'method' in keywords:
        plotType = keywords['method']
    elif len(args) > 0:
        plotType = args[0]
    else:
        plotType = 'PlotPitchSpaceOffset'

    plotMake = []
    if plotType.lower() == 'all':
        plotMake = plotClasses
    else:
        for plotClassName in plotClasses:
            if (plotClassName.id.lower() == plotType.lower() or
                plotClassName.__name__.lower() == plotType.lower()):
                plotMake.append(plotClassName)

    for plotClassName in plotMake:
        obj = plotClassName(streamObj, *args, **keywords)
        obj.process()



#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testBasic(self):
        a = Graph2DScatter(doneAction='write', title='x to x*x', alpha=1)
        data = [(x, x*x) for x in range(50)]
        a.setData(data)
        a.process()
        del a

        a = Graph2DHistogram(doneAction='write', title='50 x with random(30) y counts')
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
        
        a = Graph2DBrokenHorizontalBar()
        a.setData(data)
        a.process()


    def testPlotPlotPitchSpaceOffset(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotPitchSpaceOffset(a[0].flat, title='Bach (soprano voice)')
        b.process()


    def testPlotPlotPitchClassOffset(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotPitchClassOffset(a[0].flat, title='Bach (soprano voice)')
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
        
        a = Graph2DScatterWeighted()
        a.setData(data)
        a.process()

    def testPlotPitchSpaceQuarterLengthCount(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotPitchSpaceQuarterLengthCount(a[0].flat, 
                        title='Bach (soprano voice)')
        b.process()

    def testPlotPitchClassQuarterLengthCount(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotPitchClassQuarterLengthCount(a[0].flat, 
                        title='Bach (soprano voice)')
        b.process()


    def testPlotPitchSpace(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotPitchSpace(a[0].flat, title='Bach (soprano voice)')
        b.process()

    def testPlotPitchClass(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotPitchClass(a[0].flat, title='Bach (soprano voice)')
        b.process()

    def testPlotQuarterLength(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotQuarterLength(a[0].flat, title='Bach (soprano voice)')
        b.process()


    def testPlotPitchSpaceQuarterLength(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotScatterPitchSpaceQuarterLength(a[0].flat, title='Bach (soprano voice)')
        b.process()

    def testPlotScatterPitchClassOffset(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotScatterPitchClassOffset(a[0].flat, title='Bach (soprano voice)')
        b.process()


    def testAll(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        plotStream(a.flat, 'all')



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
        a = Graph2DScatter(doneAction=None, title='x to x*x', alpha=1)
        data = [(x, x*x) for x in range(50)]
        a.setData(data)
        a.process()
        del a

        a = Graph2DHistogram(doneAction=None, title='50 x with random(30) y counts')
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
        
        a = Graph2DBrokenHorizontalBar(doneAction=None)
        a.setData(data)
        a.process()



    def testPlotPitchSpaceDurationCount(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotPitchSpaceQuarterLengthCount(a[0].flat, doneAction=None,
                        title='Bach (soprano voice)')
        b.process()

    def testPlotPitchSpace(self):
        from music21 import corpus      
        a = corpus.parseWork('bach')
        b = PlotPitchSpace(a[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()

    def testPlotPitchClass(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotPitchClass(a[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()

    def testPlotQuarterLength(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        b = PlotQuarterLength(a[0].flat, doneAction=None, title='Bach (soprano voice)')
        b.process()


    def testAll(self):
        from music21 import corpus      
        a = corpus.parseWork('bach/bwv57.8')
        plotStream(a.flat, doneAction=None)


if __name__ == "__main__":
    #music21.mainTest(Test, TestExternal)
    music21.mainTest(Test)