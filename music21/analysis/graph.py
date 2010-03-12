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



# visual apearance notes:

# can we make these defaults on our
# graphs: No top border, no right border, and (if possible) medium gray borders
# and ticks (and thinner if possible). If not easily possible, no worries.
# 

#-------------------------------------------------------------------------------
class Graph(object):

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
            self.setFigureSize([5,5])

        # define a list of one or more colors
        if 'colors' in keywords:
            self.colors = keywords['colors']
        else:
            self.colors = ['b']

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
        if pad:
            range = valueRange[1] - valueRange[0]
            shift = range * .1 # add 10 percent of ragne
        else: 
            shift = 0
        self.axis[axisKey]['range'] = (valueRange[0]-shift, 
                                       valueRange[1]+shift)

    def setAxisLabel(self, axisKey, label):
        if axisKey not in self.axisKeys:
            raise GraphException('No such axis exists: %s' % axisKey)
        self.axis[axisKey]['label'] = label

    def _applyFormatting(self, ax):
        '''Apply formatting to the Axes container     
        '''
        #environLocal.printDebug('calling _applyFormatting')

        rect = ax.axesPatch
        # this sets the color of the main data presentation window
        rect.set_facecolor(self.colorBackgroundData)
        # this does not do anything yet
        #rect.set_edgecolor('red')

        for axis in self.axisKeys:
            if self.axis[axis]['range'] != None:
                if axis == 'x' and len(self.axisKeys) == 2:
                    ax.set_xlim(*self.axis[axis]['range'])
                elif axis == 'y' and len(self.axisKeys) == 2:
                    ax.set_ylim(*self.axis[axis]['range'])
                elif axis == 'z' and len(self.axisKeys) == 2:
                    ax.set_zlim(*self.axis[axis]['range'])

                elif axis == 'x' and len(self.axisKeys) == 3:
                    ax.set_xlim3d(*self.axis[axis]['range'])
                elif axis == 'y' and len(self.axisKeys) == 3:
                    ax.set_ylim3d(*self.axis[axis]['range'])
                elif axis == 'z' and len(self.axisKeys) == 3:
                    ax.set_zlim3d(*self.axis[axis]['range'])

            if 'label' in self.axis[axis]:
                if self.axis[axis]['label'] != None:
                    if axis == 'x':
                        ax.set_xlabel(self.axis[axis]['label'])
                    elif axis == 'y':
                        ax.set_ylabel(self.axis[axis]['label'])
                    elif axis == 'z':
                        ax.set_zlabel(self.axis[axis]['label'])

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
                        ax.set_xticklabels(labels)

                elif axis == 'y':
                    # this is the old way ticks were set:
                    #plt.yticks(*self.axis[axis]['ticks'])
                    # new way:
                    if 'ticks' in self.axis[axis].keys():
                        values, labels = self.axis[axis]['ticks']
                        #environLocal.printDebug(['y tick labels, y tick values', labels, values])
                        ax.set_yticks(values)
                        ax.set_yticklabels(labels)

        if self.title:
            ax.set_title(self.title)
        if self.grid:
            ax.grid(True)

        # this works if we need to change size
        self.fig.set_figwidth(self.figureSize[0]) 
        self.fig.set_figheight(self.figureSize[1]) 

#         ax.set_xscale('linear')
#         ax.set_yscale('linear')
#         ax.set_aspect('normal')
#         if self.grid:
#             ax.grid()


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
        self.fig.savefig(fp)
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
            self.setFigureSize([10,5])
        if 'alpha' not in keywords:
            self.alpha = .6


    def process(self):
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()

        ax = self.fig.add_subplot(111)

        yPos = 0
        xPoints = [] # store all to find min/max
        yTicks = [] # a list of label, value pairs

        keys = []
        for key, points in self.data:
            keys.append(key)
            # provide a lost of start, end points; 
            # then start y position, bar height
            ax.broken_barh(points, (yPos+self._margin, self._barHeight),
                            facecolors='blue', alpha=self.alpha)
            for xStart, xEnd in points:
                for x in [xStart, xEnd]:
                    if x not in xPoints:
                        xPoints.append(x)
            # ticks are value, label
            yTicks.append([yPos + self._barSpace * .5, key])
            #yTicks.append([key, yPos + self._barSpace * .5])
            yPos += self._barSpace

        self.setAxisRange('y', (0, len(keys) * self._barSpace))
        self.setAxisRange('x', (min(xPoints), max(xPoints)))
        self.setTicks('y', yTicks)  
        #environLocal.printDebug([yTicks])

        self._applyFormatting(ax)
        self.done()



class Graph2DScatterWeighted(Graph):
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

        self._maxDiameter = 1
        self._minDiameter = .1
        self._rangeDiameter = self._maxDiameter - self._minDiameter

    def process(self):
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        ax = self.fig.add_subplot(111)

        # need to filter data to weight z values
        xList = [x for x, y, z in self.data]
        yList = [y for x, y, z in self.data]
        zList = [z for x, y, z in self.data]

        zMax = max(zList)
        zMin = min(zList)
        zRange = zMax - zMin

        zNorm = []
        for z in zList:
            scalar = (z-zMin) / zRange # shifted part / range
            zNorm.append(self._minDiameter + (self._rangeDiameter * scalar))

        for i in range(len(self.data)):
            x = xList[i]
            y = yList[i]
            z = zNorm[i] # normalized values

            e = patches.Ellipse(xy=(x, y), width=z, height=z)
            e.set_alpha(self.alpha)
            e.set_facecolor('b') # can do this here

            ax.add_artist(e)

            environLocal.printDebug([e])

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
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        ax = self.fig.add_subplot(111)
        for x, y in self.data:
            ax.plot(x, y, 'o', color='b', alpha=self.alpha)
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

        ax.bar(x, y, alpha=.8)

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

        #self._applyFormatting(ax)
        self.done()


# class Graph3DPolygon(Graph):
#     
#     def __init__(self):
#         '''This does not work
#         '''
#         Graph.__init__(self)
#         self.axisKeys = ['x', 'y', 'z']
#         self._axisInit()
# 
#     def process(self):
# 
#         self.fig = plt.figure()
#         ax = Axes3D(self.fig)
# 
#         colors = ['r', 'g', 'b', 'y']
#         verts = []
#         facecolors = []
#         i = 0
#         for key in range(*self.axis['y']['range']):
#             verts_i = []
# #             for i in range(len(self.data[key])):
# #                 verts_i.append(self.data[key][i])
#             verts.append(verts_i)       
#             facecolors.append(random.choice(colors))
#             i += 1
# 
#         zs = range(*self.axis['y']['range'])
#         #print _MOD, verts
# 
#   
#         poly = PolyCollection(verts, facecolors=facecolors)
#         poly.set_alpha(0.7)
#         ax.add_collection3d(poly, zs=zs, zdir='y')
#          
#         self._applyFormatting(ax)
#         self.write()
#         #self.show()        



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
            
        # this kinda works but does not adjust the ticks / scale range on this axis
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
    '''A base class from which Stream plotting Class inherit.
    '''

    def __init__(self, streamObj, *args, **keywords):
        if not isinstance(streamObj, music21.stream.Stream):
            raise CorrelateException, 'non-stream provided as argument'
        self.streamObj = streamObj
        # store instance of graph here
        self.graph = None
        self.id = 'plotStream' # string name used to access this class

    def process(self):
        '''This will process all data, as well as call the done() method
        '''
        self.graph.process()

    def show(self):
        self.graph.show()

    def write(self, fp):
        self.graph.write()


    def ticksPitchClass(self):
        ticks = []
        cVals = range(12)
        for i in cVals:
            p = pitch.Pitch()
            p.ps = i
            ticks.append([i, '%s' % p.name])
        return ticks
    
    def ticksPitchSpaceOctave(self, pitchMin=36, pitchMax=100):
        ticks = []
        cVals = range(pitchMin,pitchMax,12)
        for i in cVals:
            name, acc = pitch.convertPsToStep(i)
            oct = pitch.convertPsToOct(i)
            ticks.append([i, '%s%s' % (name, oct)])
        return ticks


    def ticksPitchSpaceChromatic(self, pitchMin=36, pitchMax=100):
        ticks = []
        cVals = range(pitchMin,pitchMax)
        for i in cVals:
            name, acc = pitch.convertPsToStep(i)
            oct = pitch.convertPsToOct(i)
            ticks.append([i, '%s%s%s' % (name, acc.modifier, oct)])
        return ticks

    
    def ticksQuarterLength(self):
        ticks = []
        for qLen in (.25, .5, 1, 2, 4):
            # dtype, match = duration.
            # ticks.append([qLen, dc.convertQuarterLengthToType(qLen)]) 
            ticks.append([qLen, duration.Duration(qLen).type]) 
        return ticks
    
    def ticksDynamics(self):
        ticks = []
        for i in range(len(dynamics.shortNames)):
            ticks.append([i, dynamics.shortNames[i]])
        return ticks
    



class PlotStreamPitchSpaceOffset(PlotStream):
    '''A graph of event, sorted by pitch, over time
    '''
    def __init__(self, streamObj, *args, **keywords):
        PlotStream.__init__(self, streamObj, *args, **keywords)
        self.id = 'pitchSpaceOffset' # string name used to access this class

        # find listing for any single pitch name
        dataUnique = {}
        # collect data
        for noteObj in self.streamObj.getElementsByClass(note.Note):
            ps = int(round(noteObj.ps)) # using midi for now
            if ps not in dataUnique.keys():
                dataUnique[ps] = []
            start = noteObj.offset
            end = noteObj.quarterLength
            dataUnique[ps].append((start, end))

        # create final data list
        data = []
        ticksPitchSpace = self.ticksPitchSpaceChromatic(min(dataUnique.keys()),
                                                        max(dataUnique.keys()))
        for ps, label in ticksPitchSpace:
            if ps in dataUnique.keys():
                data.append([label, dataUnique[ps]])
            else:
                data.append([label, []])

        self.graph = Graph2DBrokenHorizontalBar(*args, **keywords)
        self.graph.setData(data)




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


    def testPlotStreamTimeDomain(self):
        from music21 import corpus      
        a = corpus.parseWork('bach')
        b = PlotStreamPitchSpaceOffset(a[0].flat, title='bach soprano voice')
        b.process()


    def testScatterWeighted(self):
        import random
        data = []
        for i in range(50):
            points = []
            x = random.choice(range(50))
            y = random.choice(range(50))
            z = random.choice(range(50))
            data.append([x, y, z])
        
        a = Graph2DScatterWeighted()
        a.setData(data)
        a.process()



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



if __name__ == "__main__":
    #music21.mainTest(Test, TestExternal)
    music21.mainTest(Test)