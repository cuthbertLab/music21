# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         graph/primitives.py
# Purpose:      Classes for graphing in matplotlib and/or other graphing tools.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               Evan Lynch
#
# Copyright:    Copyright © 2009-2012, 2017 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Object definitions for graphing and plotting :class:`~music21.stream.Stream` objects.

The :class:`~music21.graph.primitives.Graph` object subclasses primitive, abstract fundamental
graphing archetypes using the matplotlib library.
'''
import math
import random
import unittest

from music21 import common
from music21.graph.utilities import (getExtendedModules,
                                     GraphException,
                                     getColor,
                                     accidentalLabelToUnicode,
                                     )
from music21 import prebase
from music21.converter.subConverters import SubConverter

from music21 import environment
_MOD = 'graph.primitives'
environLocal = environment.Environment(_MOD)


# ------------------------------------------------------------------------------
class Graph(prebase.ProtoM21Object):
    '''
    A music21.graph.primitives.Graph is an object that represents a visual graph or
    plot, automating the creation and configuration of this graph in matplotlib.
    It is a low-level object that most music21 users do not need to call directly;
    yet, as most graphs will take keyword arguments that specify the
    look of graphs, they are important to know about.

    The keyword arguments can be provided for configuration are:

    *    doneAction (see below)
    *    alpha (which describes how transparent elements of the graph are)
    *    dpi
    *    colorBackgroundData
    *    colorBackgroundFigure
    *    colorGrid,
    *    title (a string)
    *    figureSize (a tuple of two ints)
    *    colors (a list of colors to cycle through)
    *    tickFontSize
    *    tickColors (a dict of 'x': '#color', 'y': '#color')
    *    titleFontSize
    *    labelFontSize
    *    fontFamily
    *    hideXGrid
    *    hideYGrid
    *    xTickLabelRotation
    *    marker
    *    markersize

    Graph objects do not manipulate Streams or other music21 data; they only
    manipulate raw data formatted for each Graph subclass, hence it is
    unlikely that users will call this class directly.

    The `doneAction` argument determines what happens after the graph
    has been processed. Currently there are three options, 'write' creates
    a file on disk (this is the default), while 'show' opens an
    interactive GUI browser.  The
    third option, None, does the processing but does not write any output.

    figureSize:

        A two-element iterable.

        Scales all graph components but because of matplotlib limitations
        (esp. on 3d graphs) no all labels scale properly.

        defaults to .figureSizeDefault

    >>> a = graph.primitives.Graph(title='a graph of some data to be given soon', tickFontSize=9)
    >>> a.data = [[0, 2], [1, 3]]
    >>> a.graphType
    'genericGraph'
    '''
    graphType = 'genericGraph'
    axisKeys = ('x', 'y')
    figureSizeDefault = (6, 6)

    keywordConfigurables = (
        'alpha', 'dpi', 'colorBackgroundData', 'colorBackgroundFigure',
        'colorGrid', 'title', 'figureSize', 'marker', 'markersize',
        'colors', 'tickFontSize', 'tickColors', 'titleFontSize', 'labelFontSize',
        'fontFamily', 'hideXGrid', 'hideYGrid',
        'xTickLabelRotation',
        'xTickLabelHorizontalAlignment', 'xTickLabelVerticalAlignment',
        'doneAction',
    )

    def __init__(self, *args, **keywords):
        getExtendedModules()
        self.data = None
        self.figure = None  # a matplotlib.Figure object
        self.subplot = None  # an Axes, AxesSubplot or potentially list of these object

        # define a component dictionary for each axis
        self.axis = {}
        for ax in self.axisKeys:
            self.axis[ax] = {}
            self.axis[ax]['range'] = None

        self.grid = True
        self.axisRangeHasBeenSet = {}

        for axisKey in self.axisKeys:
            self.axisRangeHasBeenSet[axisKey] = False

        self.alpha = 0.2
        self.dpi = None  # determine on its own
        self.colorBackgroundData = '#ffffff'  # color of the data region
        self.colorBackgroundFigure = '#ffffff'  # looking good are #c7d2d4, #babecf
        self.colorGrid = '#dddddd'  # grid color
        self.title = 'Music21 Graph'
        self.figureSize = self.figureSizeDefault
        self.marker = 'o'
        self.markersize = 6  # lowercase as in matplotlib
        self.colors = ['#605c7f', '#5c7f60', '#715c7f']

        self.tickFontSize = 7
        self.tickColors = {'x': '#000000', 'y': '#000000'}

        self.titleFontSize = 12
        self.labelFontSize = 10
        self.fontFamily = 'serif'
        self.hideXGrid = False
        self.hideYGrid = False
        self.xTickLabelRotation = 0
        self.xTickLabelHorizontalAlignment = 'center'
        self.xTickLabelVerticalAlignment = 'center'

        self.hideLeftBottomSpines = False

        self._doneAction = 'write'
        self._dataColorIndex = 0

        for kw in self.keywordConfigurables:
            if kw in keywords:
                setattr(self, kw, keywords[kw])

    def __del__(self):
        '''
        Matplotlib Figure objects need to be explicitly closed when no longer used...
        '''
        if hasattr(self, 'figure') and self.figure is not None and self.doneAction is None:
            etm = getExtendedModules()
            etm.plt.close(self.figure)

    @property
    def doneAction(self):
        '''
        returns or sets what should happen when the graph is created (see docs above)
        default is 'write'.
        '''
        return self._doneAction

    @doneAction.setter
    def doneAction(self, action):
        if action in ('show', 'write', None):
            self._doneAction = action
        else:  # pragma: no cover
            raise GraphException(f'not such done action: {action}')

    def nextColor(self):
        '''
        Utility function that cycles through the colors of self.colors...

        >>> g = graph.primitives.Graph()
        >>> g.colors
        ['#605c7f', '#5c7f60', '#715c7f']

        >>> g.nextColor()
        '#605c7f'

        >>> g.nextColor()
        '#5c7f60'

        >>> g.nextColor()
        '#715c7f'

        >>> g.nextColor()
        '#605c7f'
        '''
        c = getColor(self.colors[self._dataColorIndex % len(self.colors)])
        self._dataColorIndex += 1
        return c

    def setTicks(self, axisKey, pairs):
        '''
        Set the tick-labels for a given graph or plot's axisKey
        (generally 'x', and 'y') with a set of pairs

        Pairs are iterables of positions and labels.

        N.B. -- both 'x' and 'y' ticks have to be set in
        order to get matplotlib to display either... (and presumably 'z' for 3D graphs)

        >>> g = graph.primitives.GraphHorizontalBar()
        >>> g.axis['x']['ticks']
        Traceback (most recent call last):
        KeyError: 'ticks'
        >>> g.axis['x']
        {'range': None}

        >>> g.setTicks('x', [(0, 'a'), (1, 'b')])
        >>> g.axis['x']['ticks']
        ([0, 1], ['a', 'b'])

        >>> g.setTicks('m', [('a', 'b')])
        Traceback (most recent call last):
        music21.graph.utilities.GraphException: Cannot find key 'm' in self.axis

        >>> g.setTicks('x', [])
        >>> g.axis['x']['ticks']
        ([], [])
        '''
        if pairs is None:  # is okay to send an empty list to clear everything...
            return

        if axisKey not in self.axis:
            raise GraphException(f"Cannot find key '{axisKey}' in self.axis")

        positions = []
        labels = []
        # ticks are value, label pairs
        for value, label in pairs:
            positions.append(value)
            labels.append(label)
        # environLocal.printDebug(['got labels', labels])
        self.axis[axisKey]['ticks'] = positions, labels

    def setIntegerTicksFromData(self, unsortedData, axisKey='y', dataSteps=8):
        '''
        Set the ticks for an axis (usually 'y') given unsorted data.

        Data steps shows how many ticks to make from the data.

        >>> g = graph.primitives.GraphHorizontalBar()
        >>> g.setIntegerTicksFromData([10, 5, 3, 8, 20, 11], dataSteps=4)
        >>> g.axis['y']['ticks']
        ([0, 5, 10, 15, 20], ['0', '5', '10', '15', '20'])

        TODO: should this not also use min? instead of always starting from zero?
        '''
        maxData = max(unsortedData)
        tickStep = round(maxData / dataSteps)

        tickList = []
        if tickStep <= 1:
            tickStep = 2
        for y in range(0, maxData + 1, tickStep):
            tickList.append([y, f'{y}'])
        tickList.sort()
        return self.setTicks(axisKey, tickList)

    def setAxisRange(self, axisKey, valueRange, paddingFraction=0.1):
        '''
        Set the range for the axis for a given axis key
        (generally, 'x', or 'y')

        ValueRange is a two-element tuple of the lowest
        number and the highest.

        By default there is a padding of 10% of the range
        in either direction.  Set paddingFraction = 0 to
        eliminate this shift
        '''
        if axisKey not in self.axisKeys:  # pragma: no cover
            raise GraphException(f'No such axis exists: {axisKey}')
        # find a shift
        if paddingFraction != 0:
            totalRange = valueRange[1] - valueRange[0]
            shift = totalRange * paddingFraction  # add 10 percent of range
        else:
            shift = 0
        # set range with shift
        self.axis[axisKey]['range'] = (valueRange[0] - shift,
                                       valueRange[1] + shift)

        self.axisRangeHasBeenSet[axisKey] = True

    def setAxisLabel(self, axisKey, label, conditional=False):
        if axisKey not in self.axisKeys:  # pragma: no cover
            raise GraphException(f'No such axis exists: {axisKey}')
        if conditional and 'label' in self.axis[axisKey] and self.axis[axisKey]['label']:
            return

        self.axis[axisKey]['label'] = label

    @staticmethod
    def hideAxisSpines(subplot, leftBottom=False):
        '''
        Remove the right and top spines from the diagram.

        If leftBottom is True, remove the left and bottom spines as well.

        Spines are removed by setting their colors to 'none' and every other
        tick line set_visible to False.
        '''
        for loc, spine in subplot.spines.items():
            if loc in ('left', 'bottom'):
                if leftBottom:
                    spine.set_color('none')  # don't draw spine
                # # this pushes them outward in an interesting way
                # spine.set_position(('outward', 10))  # outward by 10 points
            elif loc in ('right', 'top'):
                spine.set_color('none')  # don't draw spine
            else:  # pragma: no cover
                raise ValueError(f'unknown spine location: {loc}')

        # remove top and right ticks
        for i, line in enumerate(subplot.get_xticklines() + subplot.get_yticklines()):
            if leftBottom:
                line.set_visible(False)
            elif i % 2 == 1:   # top and right are the odd indices
                line.set_visible(False)

    def applyFormatting(self, subplot):
        '''
        Apply formatting to the Subplot (Axes) container and Figure instance.

        ax should be an AxesSubplot object or
        an Axes3D object or something similar.
        '''
        environLocal.printDebug('calling applyFormatting on ' + repr(subplot))

        rect = subplot.patch
        # this sets the color of the main data presentation window
        rect.set_facecolor(getColor(self.colorBackgroundData))
        # this does not do anything yet
        # rect.set_edgecolor(getColor(self.colorBackgroundFigure))

        for axis in self.axisKeys:
            self.applyFormattingToOneAxis(subplot, axis)

        if self.title:
            subplot.set_title(self.title, fontsize=self.titleFontSize, family=self.fontFamily)

        # right and top must be larger
        # this does not work right yet
        # self.figure.subplots_adjust(left=1, bottom=1, right=2, top=2)

        for thisAxisName in self.axisKeys:
            if thisAxisName not in self.tickColors:
                continue
            subplot.tick_params(axis=thisAxisName, colors=self.tickColors[thisAxisName])

        self.applyGrid(self.subplot)

        # this figure instance is created in the subclassed process() method
        # set total size of figure
        self.figure.set_figwidth(self.figureSize[0])
        self.figure.set_figheight(self.figureSize[1])

        # subplot.set_xscale('linear')
        # subplot.set_yscale('linear')
        # subplot.set_aspect('normal')

    def applyGrid(self, subplot):
        '''
        Apply the Grid to the subplot such that it goes below the data.
        '''

        if self.grid and self.colorGrid is not None:  # None is another way to hide grid
            subplot.set_axisbelow(True)
            subplot.grid(True, which='major', color=getColor(self.colorGrid))
        # provide control for each grid line
        if self.hideYGrid:
            subplot.yaxis.grid(False)

        if self.hideXGrid:
            subplot.xaxis.grid(False)

    # noinspection SpellCheckingInspection
    def applyFormattingToOneAxis(self, subplot, axis):
        '''
        Given a matplotlib.Axes object (a subplot) and a string of
        'x', 'y', or 'z', set the Axes object's xlim (or ylim or zlim or xlim3d, etc.) from
        self.axis[axis]['range'], Set the label from self.axis[axis]['label'],
        the scale, the ticks, and the ticklabels.

        Returns the matplotlib Axis object that has been modified
        '''
        thisAxis = self.axis[axis]
        if axis not in ('x', 'y', 'z'):
            return

        if 'range' in thisAxis and thisAxis['range'] is not None:
            rangeFuncName = 'set_' + axis + 'lim'
            if len(self.axisKeys) == 3:
                rangeFuncName += '3d'
            thisRangeFunc = getattr(subplot, rangeFuncName)
            thisRangeFunc(*thisAxis['range'])

        if 'label' in thisAxis and thisAxis['label'] is not None:
            # ax.set_xlabel, set_ylabel, set_zlabel <-- for searching do not delete.
            setLabelFunction = getattr(subplot, 'set_' + axis + 'label')
            setLabelFunction(thisAxis['label'],
                             fontsize=self.labelFontSize, family=self.fontFamily)

        if 'scale' in thisAxis and thisAxis['scale'] is not None:
            # ax.set_xscale, set_yscale, set_zscale <-- for searching do not delete.
            setLabelFunction = getattr(subplot, 'set_' + axis + 'scale')
            setLabelFunction(thisAxis['scale'])

        try:
            getTickFunction = getattr(subplot, 'get_' + axis + 'ticks')
            setTickFunction = getattr(subplot, 'set_' + axis + 'ticks')
            setTickLabelFunction = getattr(subplot, 'set_' + axis + 'ticklabels')
        except AttributeError:
            # for z ?? or maybe it will work now?
            getTickFunction = None
            setTickFunction = None
            setTickLabelFunction = None

        if 'ticks' not in thisAxis and setTickLabelFunction is not None:
            # apply some default formatting to default ticks
            ticks = getTickFunction()
            setTickFunction(ticks)
            setTickLabelFunction(ticks,
                                 fontsize=self.tickFontSize,
                                 family=self.fontFamily)
        else:
            values, labels = thisAxis['ticks']
            if setTickFunction is not None:
                setTickFunction(values)
            if axis == 'x':
                subplot.set_xticklabels(labels,
                                        fontsize=self.tickFontSize,
                                        family=self.fontFamily,
                                        horizontalalignment=self.xTickLabelHorizontalAlignment,
                                        verticalalignment=self.xTickLabelVerticalAlignment,
                                        rotation=self.xTickLabelRotation,
                                        y=-0.01)

            elif axis == 'y':
                subplot.set_yticklabels(labels,
                                        fontsize=self.tickFontSize,
                                        family=self.fontFamily,
                                        horizontalalignment='right',
                                        verticalalignment='center')
            elif callable(setTickLabelFunction):
                # noinspection PyCallingNonCallable
                setTickLabelFunction(labels,
                                     fontsize=self.tickFontSize,
                                     family=self.fontFamily)

        return thisAxis

    def process(self):
        '''
        Creates the figure and subplot, calls renderSubplot to get the
        subclass specific information on the data, runs hideAxisSpines,
        applyFormatting, and then calls the done action.  Returns None,
        but the subplot is available at self.subplot
        '''
        extm = getExtendedModules()
        plt = extm.plt

        # figure size can be set w/ figsize=(5, 10)
        # if self.doneAction is None:
        #     extm.matplotlib.interactive(False)
        self.figure = plt.figure(facecolor=self.colorBackgroundFigure)
        self.subplot = self.figure.add_subplot(1, 1, 1)

        self._dataColorIndex = 0  # just for consistent rendering if run twice
        # call class specific info
        self.renderSubplot(self.subplot)

        # standard procedures
        self.hideAxisSpines(self.subplot, leftBottom=self.hideLeftBottomSpines)
        self.applyFormatting(self.subplot)
        self.callDoneAction()
#         if self.doneAction is None:
#             extm.matplotlib.interactive(False)

    def renderSubplot(self, subplot):
        '''
        Calls the subclass specific information to get the data
        '''
        pass

    # --------------------------------------------------------------------------
    def callDoneAction(self, fp=None):
        '''
        Implement the desired doneAction, after data processing
        '''
        if self.doneAction == 'show':  # pragma: no cover
            self.show()
        elif self.doneAction == 'write':  # pragma: no cover
            self.write(fp)
        elif self.doneAction is None:
            pass

    def show(self):  # pragma: no cover
        '''
        Calls the show() method of the matplotlib plot.
        For most matplotlib back ends, this will open
        a GUI window with the desired graph.
        '''
        self.figure.show()

    def write(self, fp=None):  # pragma: no cover
        '''
        Writes the graph to a file. If no file path is given, a temporary file is used.
        '''
        if fp is None:
            fp = environLocal.getTempFile('.png')

        dpi = self.dpi
        if dpi is None:
            dpi = 300

        self.figure.savefig(fp,
                            # facecolor=getColor(self.colorBackgroundData),
                            # edgecolor=getColor(self.colorBackgroundFigure),
                            dpi=dpi)

        if common.runningUnderIPython() is not True:
            SubConverter().launch(fp, fmt='png')
        else:
            return self.figure


class GraphNetworkxGraph(Graph):
    '''
    Grid a networkx graph -- which is a graph of nodes and edges.
    Requires the optional networkx module.
    '''
    #
    # >>> #_DOCS_SHOW g = graph.primitives.GraphNetworkxGraph()
    #
    # .. image:: images/GraphNetworkxGraph.*
    #     :width: 600
    _DOC_ATTR = {
        'networkxGraph': '''An instance of a networkx graph object.''',
        'hideLeftBottomSpines': 'bool to hide the left and bottom axis spines; default True',
    }

    graphType = 'networkx'
    keywordConfigurables = Graph.keywordConfigurables + (
        'networkxGraph', 'hideLeftBottomSpines',
    )

    def __init__(self, *args, **keywords):
        self.networkxGraph = None
        self.hideLeftBottomSpines = True

        super().__init__(*args, **keywords)

        extm = getExtendedModules()

        if 'title' not in keywords:
            self.title = 'Network Plot'

        elif extm.networkx is not None:  # if we have this module
            # testing default; temporary
            try:  # pragma: no cover
                g = extm.networkx.Graph()
                # g.add_edge('a', 'b',weight=1.0)
                # g.add_edge('b', 'c',weight=0.6)
                # g.add_edge('c', 'd',weight=0.2)
                # g.add_edge('d', 'e',weight=0.6)
                self.networkxGraph = g
            except NameError:
                pass  # keep as None

    def renderSubplot(self, subplot):  # pragma: no cover
        # figure size can be set w/ figsize=(5,10)
        extm = getExtendedModules()
        networkx = extm.networkx

        # positions for all nodes
        # positions are stored in the networkx graph as a pos attribute
        posNodes = {}
        posNodeLabels = {}
        # returns a data dictionary
        for nId, nData in self.networkxGraph.nodes(data=True):
            posNodes[nId] = nData['pos']
            # shift labels off center of nodes
            posNodeLabels[nId] = (nData['pos'][0] + 0.125, nData['pos'][1])

        # environLocal.printDebug(['get position', posNodes])
        # posNodes = networkx.spring_layout(self.networkxGraph, weighted=True)
        # draw nodes
        networkx.draw_networkx_nodes(self.networkxGraph, posNodes,
                                     node_size=300, ax=subplot, node_color='#605C7F', alpha=0.5)

        for (u, v, d) in self.networkxGraph.edges(data=True):
            environLocal.printDebug(['GraphNetworkxGraph', (u, v, d)])
            # print(u,v,d)
            # adding one at a time to permit individual alpha settings
            edgelist = [(u, v)]
            networkx.draw_networkx_edges(self.networkxGraph, posNodes, edgelist=edgelist,
                                         width=2, style=d['style'],
                                         edge_color='#666666', alpha=d['weight'], ax=subplot)

        # labels
        networkx.draw_networkx_labels(self.networkxGraph, posNodeLabels,
                                      font_size=self.labelFontSize,
                                      font_family=self.fontFamily, font_color='#000000',
                                      ax=subplot)

        # remove all labels
        self.setAxisLabel('y', '')
        self.setAxisLabel('x', '')
        self.setTicks('y', [])
        self.setTicks('x', [])
        # turn off grid
        self.grid = False


class GraphColorGrid(Graph):
    '''
    Grid of discrete colored "blocks" to visualize results of a windowed analysis routine.

    Data is provided as a list of lists of colors, where colors are specified as a hex triplet,
    or the common HTML color codes, and based on analysis-specific mapping of colors to results.


    >>> #_DOCS_SHOW g = graph.primitives.GraphColorGrid()
    >>> g = graph.primitives.GraphColorGrid(doneAction=None) #_DOCS_HIDE
    >>> data = [['#55FF00', '#9b0000', '#009b00'],
    ...         ['#FFD600', '#FF5600'],
    ...         ['#201a2b', '#8f73bf', '#a080d5', '#403355', '#999999']]
    >>> g.data = data
    >>> g.process()

    .. image:: images/GraphColorGrid.*
        :width: 600
    '''
    _DOC_ATTR = {
        'hideLeftBottomSpines': 'bool to hide the left and bottom axis spines; default True',
    }

    graphType = 'colorGrid'
    figureSizeDefault = (9, 6)
    keywordConfigurables = Graph.keywordConfigurables + ('hideLeftBottomSpines',)

    def __init__(self, *args, **kwargs):
        self.hideLeftBottomSpines = True
        super().__init__(*args, **kwargs)

    def renderSubplot(self, subplot):        # do not need grid for outer container

        # these approaches do not work:
        # adjust face color of axTop independently
        # this sets the color of the main data presentation window
        # axTop.patch.set_facecolor('#000000')

        # axTop.bar([0.5], [1], 1, color=['#000000'], linewidth=0.5, edgecolor='#111111')

        self.figure.subplots_adjust(left=0.15)

        rowCount = len(self.data)

        for i in range(rowCount):
            thisRowData = self.data[i]

            positions = []
            heights = []
            subColors = []

            for j, thisColor in enumerate(thisRowData):
                positions.append(j + 1 / 2)
                # collect colors in a list to set all at once
                subColors.append(thisColor)
                # correlations.append(float(self.data[i][j][2]))
                heights.append(1)

            # add a new subplot for each row
            ax = self.figure.add_subplot(rowCount, 1, rowCount - i)

            # linewidth: 0.1 is the thinnest possible
            # antialiased = false, for small diagrams, provides tighter images
            ax.bar(positions,
                   heights,
                   1,
                   color=subColors,
                   linewidth=0.3,
                   edgecolor='#000000',
                   antialiased=False)

            # remove spines from each bar plot; cause excessive thickness
            for unused_loc, spine in ax.spines.items():
                # spine.set_color('none')  # don't draw spine
                spine.set_linewidth(0.3)
                spine.set_color('#000000')
                spine.set_alpha(1)

            # remove all ticks for subplots
            for j, line in enumerate(ax.get_xticklines() + ax.get_yticklines()):
                line.set_visible(False)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_yticklabels([''] * len(ax.get_yticklabels()))
            ax.set_xticklabels([''] * len(ax.get_xticklabels()))
            # this is the shifting the visible bars; may not be necessary
            ax.set_xlim([0, len(self.data[i])])

            # these do not seem to do anything
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)

        # adjust space between the bars
        # 0.1 is about the smallest that gives some space
        if rowCount > 12:
            self.figure.subplots_adjust(hspace=0)
        else:
            self.figure.subplots_adjust(hspace=0.1)

        axisRangeNumbers = (0, 1)
        self.setAxisRange('x', axisRangeNumbers, 0)

        # turn off grid
        self.grid = False


class GraphColorGridLegend(Graph):
    '''
    Grid of discrete colored "blocks" where each block can be labeled

    Data is provided as a list of lists of colors, where colors are specified as a hex triplet,
    or the common HTML color codes, and based on analysis-specific mapping of colors to results.


    >>> #_DOCS_SHOW g = graph.primitives.GraphColorGridLegend()
    >>> g = graph.primitives.GraphColorGridLegend(doneAction=None) #_DOCS_HIDE
    >>> data = []
    >>> data.append(('Major', [('C#', '#00AA55'), ('D-', '#5600FF'), ('G#', '#2B00FF')]))
    >>> data.append(('Minor', [('C#', '#004600'), ('D-', '#00009b'), ('G#', '#00009B')]))
    >>> g.data = data
    >>> g.process()

    .. image:: images/GraphColorGridLegend.*
        :width: 600

    '''
    _DOC_ATTR = {
        'hideLeftBottomSpines': 'bool to hide the left and bottom axis spines; default True',
    }

    graphType = 'colorGridLegend'
    figureSizeDefault = (5, 1.5)
    keywordConfigurables = Graph.keywordConfigurables + ('hideLeftBottomSpines',)

    def __init__(self, *args, **keywords):
        self.hideLeftBottomSpines = True

        super().__init__(*args, **keywords)

        if 'title' not in keywords:
            self.title = 'Legend'

    def renderSubplot(self, subplot):
        for i, rowLabelAndData in enumerate(self.data):
            rowLabel = rowLabelAndData[0]
            rowData = rowLabelAndData[1]
            self.makeOneRowOfGraph(self.figure, i, rowLabel, rowData)

        self.setAxisRange('x', (0, 1), 0)

        allTickLines = subplot.get_xticklines() + subplot.get_yticklines()
        for j, line in enumerate(allTickLines):
            line.set_visible(False)

        # sets the space between subplots
        # top and bottom here push diagram more toward center of frame
        # may be useful in other graphs
        # ,
        self.figure.subplots_adjust(hspace=1.5, top=0.75, bottom=0.2)

        self.setAxisLabel('y', '')
        self.setAxisLabel('x', '')
        self.setTicks('y', [])
        self.setTicks('x', [])

    def makeOneRowOfGraph(self, figure, rowIndex, rowLabel, rowData):
        # noinspection PyShadowingNames
        '''
        Makes a subplot for one row of data (such as for the Major label)
        and returns a matplotlib.axes.AxesSubplot instance representing the subplot.

        Here we create an axis with a part of Scriabin's mapping of colors
        to keys in Prometheus: The Poem of Fire.

        >>> import matplotlib.pyplot

        >>> colorLegend = graph.primitives.GraphColorGridLegend()
        >>> rowData = [('C', '#ff0000'), ('G', '#ff8800'), ('D', '#ffff00'),
        ...            ('A', '#00ff00'), ('E', '#4444ff')]
        >>> colorLegend.data = [['Scriabin Mapping', rowData]]

        >>> fig = matplotlib.pyplot.figure()
        >>> subplot = colorLegend.makeOneRowOfGraph(fig, 0, 'Scriabin Mapping', rowData)
        >>> subplot
        <AxesSubplot:>
        '''
        # environLocal.printDebug(['rowLabel', rowLabel, i])

        positions = []
        heights = []
        subColors = []

        for j, oneColorMapping in enumerate(rowData):
            positions.append(1.0 + j)
            subColors.append(oneColorMapping[1])  # second value is colors
            heights.append(1)

        # add a new subplot for each row
        posTriple = (len(self.data), 1, rowIndex + 1)
        # environLocal.printDebug(['posTriple', posTriple])
        ax = figure.add_subplot(*posTriple)

        # ax is an Axes object
        # 1 here is width
        width = 1
        ax.bar(positions, heights, width, color=subColors, linewidth=0.3, edgecolor='#000000')

        # lower thickness of spines
        for spineArtist in ax.spines.values():
            # spineArtist.set_color('none')  # don't draw spine
            spineArtist.set_linewidth(0.3)
            spineArtist.set_color('#000000')

        # remove all ticks for subplots
        allTickLines = ax.get_xticklines() + ax.get_yticklines()
        for j, line in enumerate(allTickLines):
            line.set_visible(False)

        # need one label for each left side; 0.5 is in the middle
        ax.set_yticks([0.5])
        ax.set_yticklabels([rowLabel],
                           fontsize=self.tickFontSize,
                           family=self.fontFamily,
                           horizontalalignment='right',
                           verticalalignment='center')  # one label for one tick

        # need a label for each bars
        ax.set_xticks([x + 1 for x in range(len(rowData))])
        # get labels from row data; first of pair
        # need to push y down as need bottom alignment for lower case
        substitutedAccidentalLabels = [accidentalLabelToUnicode(x)
                                            for x, unused_y in rowData]
        ax.set_xticklabels(
            substitutedAccidentalLabels,
            fontsize=self.tickFontSize,
            family=self.fontFamily,
            horizontalalignment='center',
            verticalalignment='center',
            y=-0.4)
        # this is the scaling to see all bars; not necessary
        ax.set_xlim([0.5, len(rowData) + 0.5])

        return ax


class GraphHorizontalBar(Graph):
    '''
    Numerous horizontal bars in discrete channels, where bars
    can be incomplete and/or overlap.

    Data provided is a list of pairs, where the first value becomes the key,
    the second value is a list of x-start, x-length values.


    >>> a = graph.primitives.GraphHorizontalBar()
    >>> a.doneAction = None #_DOCS_HIDE
    >>> data = [('Chopin', [(1810, 1849-1810)]),
    ...         ('Schumanns', [(1810, 1856-1810), (1819, 1896-1819)]),
    ...         ('Brahms', [(1833, 1897-1833)])]
    >>> a.data = data
    >>> a.process()

    .. image:: images/GraphHorizontalBar.*
        :width: 600

    '''
    _DOC_ATTR = {
        'barSpace': 'Amount of vertical space each bar takes; default 8',
        'margin': 'Space around the bars, default 2',
    }

    graphType = 'horizontalBar'
    figureSizeDefault = (10, 4)
    keywordConfigurables = Graph.keywordConfigurables + (
        'barSpace', 'margin')

    def __init__(self, *args, **keywords):
        self.barSpace = 8
        self.margin = 2

        super().__init__(*args, **keywords)

        if 'alpha' not in keywords:
            self.alpha = 0.6

    @property
    def barHeight(self):
        return self.barSpace - (self.margin * 2)

    def renderSubplot(self, subplot):
        self.figure.subplots_adjust(left=0.15)

        yPos = 0
        xPoints = []  # store all to find min/max
        yTicks = []  # a list of label, value pairs
        xTicks = []

        keys = []
        i = 0
        # TODO: check data orientation; flips in some cases
        for info in self.data:
            if len(info) == 2:
                key, points = info
                unused_formatDict = {}
            else:
                key, points, unused_formatDict = info
            keys.append(key)
            # provide a list of start, end points;
            # then start y position, bar height
            faceColor = self.nextColor()

            if points:
                yRange = (yPos + self.margin,
                          self.barHeight)
                subplot.broken_barh(points,
                                    yRange,
                                    facecolors=faceColor,
                                    alpha=self.alpha)
                for xStart, xLen in points:
                    xEnd = xStart + xLen
                    for x in [xStart, xEnd]:
                        if x not in xPoints:
                            xPoints.append(x)
            # ticks are value, label
            yTicks.append([yPos + self.barSpace * 0.5, key])
            # yTicks.append([key, yPos + self.barSpace * 0.5])
            yPos += self.barSpace
            i += 1

        xMin = min(xPoints)
        xMax = max(xPoints)
        xRange = xMax - xMin
        # environLocal.printDebug(['got xMin, xMax for points', xMin, xMax, ])

        self.setAxisRange('y', (0, len(keys) * self.barSpace))
        self.setAxisRange('x', (xMin, xMax))
        self.setTicks('y', yTicks)

        # first, see if ticks have been set externally
        if 'ticks' in self.axis['x'] and not self.axis['x']['ticks']:
            rangeStep = int(xMin + round(xRange / 10))
            if rangeStep == 0:
                rangeStep = 1
            for x in range(int(math.floor(xMin)),
                           round(math.ceil(xMax)),
                           rangeStep):
                xTicks.append([x, f'{x}'])
            self.setTicks('x', xTicks)


class GraphHorizontalBarWeighted(Graph):
    '''
    Numerous horizontal bars in discrete channels,
    where bars can be incomplete and/or overlap, and
    can have different heights and colors within their
    respective channel.
    '''
    _DOC_ATTR = {
        'barSpace': 'Amount of vertical space each bar takes; default 8',
        'margin': 'Space around the bars, default 2',
    }

    graphType = 'horizontalBarWeighted'
    figureSizeDefault = (10, 4)

    keywordConfigurables = Graph.keywordConfigurables + (
        'barSpace', 'margin')

    def __init__(self, *args, **keywords):
        self.barSpace = 8
        self.margin = 0.25  # was 8; determines space between channels

        super().__init__(*args, **keywords)

        # this default alpha is used if not specified per bar
        if 'alpha' not in keywords:
            self.alpha = 1

# example data
#         data =  [
#         ('Violins',  [(3, 5, 1, '#fff000'), (1, 12, 0.2, '#3ff203')]  ),
#         ('Celli',    [(2, 7, 0.2, '#0ff302'), (10, 3, 0.6, '#ff0000', 1)]  ),
#         ('Clarinet', [(5, 1, 0.5, '#3ff203')]  ),
#         ('Flute',    [(5, 1, 0.1, '#00ff00'), (7, 20, 0.3, '#00ff88')]  ),
#                 ]
    @property
    def barHeight(self):
        return self.barSpace - (self.margin * 2)

    def renderSubplot(self, subplot):
        # might need more space here for larger y-axis labels
        self.figure.subplots_adjust(left=0.15)

        yPos = 0
        xPoints = []  # store all to find min/max
        yTicks = []  # a list of label, value pairs
        # xTicks = []

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
                x = 0
                span = None
                heightScalar = 1
                color = self.nextColor()
                alpha = self.alpha
                yShift = 0  # between -1 and 1

                if len(data) == 3:
                    x, span, heightScalar = data
                elif len(data) == 4:
                    x, span, heightScalar, color = data
                elif len(data) == 5:
                    x, span, heightScalar, color, alpha = data
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
                if (x + span) not in xPoints:
                    xPoints.append(x + span)

                # TODO: add high/low shift to position w/n range
                # provide a list of start, end points;
                # then start y position, bar height
                h = self.barHeight * heightScalar
                yAdjust = (self.barHeight - h) * 0.5
                yShiftUnit = self.barHeight * (1 - heightScalar) * 0.5
                adjustedY = yPos + self.margin + yAdjust + (yShiftUnit * yShift)
                yRanges.append((adjustedY, h))

            for i, xRange in enumerate(xRanges):
                # note: can get ride of bounding lines by providing
                # linewidth=0, however, this may leave gaps in adjacent regions
                subplot.broken_barh([xRange],
                                    yRanges[i],
                                    facecolors=colors[i],
                                    alpha=alphas[i],
                                    edgecolor=colors[i])

            # ticks are value, label
            yTicks.append([yPos + self.barSpace * 0.5, key])
            # yTicks.append([key, yPos + self.barSpace * 0.5])
            yPos += self.barSpace
            i += 1

        xMin = min(xPoints)
        xMax = max(xPoints)
        xRange = xMax - xMin
        # environLocal.printDebug(['got xMin, xMax for points', xMin, xMax, ])

        # NOTE: these pad values determine extra space inside the graph that
        # is not filled with data, a sort of inner margin
        self.setAxisRange('y', (0, len(keys) * self.barSpace), paddingFraction=0.05)
        self.setAxisRange('x', (xMin, xMax), paddingFraction=0.01)
        self.setTicks('y', yTicks)

        # first, see if ticks have been set externally
#         if 'ticks' in self.axis['x'] and len(self.axis['x']['ticks']) == 0:
#             rangeStep = int(xMin round(xRange/10))
#             if rangeStep == 0:
#                 rangeStep = 1
#             for x in range(int(math.floor(xMin)),
#                            round(math.ceil(xMax)),
#                            rangeStep):
#                 xTicks.append([x, '%s' % x])
#                 self.setTicks('x', xTicks)
#         environLocal.printDebug(['xTicks', xTicks])


class GraphScatterWeighted(Graph):
    '''
    A scatter plot where points are scaled in size to
    represent the number of values stored within.

    >>> g = graph.primitives.GraphScatterWeighted()
    >>> g.doneAction = None #_DOCS_HIDE
    >>> data = [(23, 15, 234), (10, 23, 12), (4, 23, 5), (15, 18, 120)]
    >>> g.data = data
    >>> g.process()

    .. image:: images/GraphScatterWeighted.*
        :width: 600

    '''
    _DOC_ATTR = {
        'maxDiameter': 'the maximum diameter of any ellipse, default 1.25',
        'minDiameter': 'the minimum diameter of any ellipse, default 0.25',
    }

    graphType = 'scatterWeighted'
    figureSizeDefault = (5, 5)

    keywordConfigurables = Graph.keywordConfigurables + ('maxDiameter', 'minDiameter')

    def __init__(self, *args, **keywords):
        self.maxDiameter = 1.25
        self.minDiameter = 0.25

        super().__init__(*args, **keywords)

        if 'alpha' not in keywords:
            self.alpha = 0.6

    @property
    def rangeDiameter(self):
        return self.maxDiameter - self.minDiameter

    def renderSubplot(self, subplot):
        extm = getExtendedModules()
        patches = extm.patches

        # these need to be equal to maintain circle scatter points
        self.figure.subplots_adjust(left=0.15, bottom=0.15)

        # need to filter data to weight z values
        xList = [d[0] for d in self.data]
        yList = [d[1] for d in self.data]
        zList = [d[2] for d in self.data]
        formatDictList = []
        for d in self.data:
            if len(d) > 3:
                formatDict = d[3]
            else:
                formatDict = {}
            formatDictList.append(formatDict)

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
        # we need to get a ratio to scale the width of the ellipse
        xDistort = 1
        yDistort = 1
        if xRange > yRange:
            yDistort = yRange / xRange
        elif yRange > xRange:
            xDistort = xRange / yRange
        # environLocal.printDebug(['xDistort, yDistort', xDistort, yDistort])

        zNorm = []
        for z in zList:
            if z == 0:
                zNorm.append([0, 0])
            else:
                # this will make the minimum scalar 0 when z is zero
                if zRange != 0:
                    scalar = (z - zMin) / zRange  # shifted part / range
                else:
                    scalar = 0.5  # if all the same size, use 0.5
                scaled = self.minDiameter + (self.rangeDiameter * scalar)
                zNorm.append([scaled, scalar])

        # draw ellipses
        for i in range(len(self.data)):
            x = xList[i]
            y = yList[i]
            z, unused_zScalar = zNorm[i]  # normalized values
            formatDict = formatDictList[i]

            width = z * xDistort
            height = z * yDistort
            e = patches.Ellipse(xy=(x, y), width=width, height=height, **formatDict)
            # e = patches.Circle(xy=(x, y), radius=z)
            subplot.add_artist(e)

            e.set_clip_box(subplot.bbox)
            # e.set_alpha(self.alpha * zScalar)
            e.set_alpha(self.alpha)
            e.set_facecolor(self.nextColor())
            # # can do this here
            # environLocal.printDebug([e])

            # only show label if min if greater than zNorm min
            if zList[i] > 1:
                # xdistort does not seem to
                # width shift can be between 0.1 and 0.25
                # width is already shifted by distort
                # use half of width == radius
                adjustedX = x + ((width * 0.5) + (0.05 * xDistort))
                adjustedY = y + 0.10  # why?

                subplot.text(adjustedX,
                             adjustedY,
                             str(zList[i]),
                             size=6,
                             va='baseline',
                             ha='left',
                             multialignment='left')

        self.setAxisRange('y', (yMin, yMax))
        self.setAxisRange('x', (xMin, xMax))


class GraphScatter(Graph):
    '''
    Graph two parameters in a scatter plot. Data representation is a list of points of values.

    >>> g = graph.primitives.GraphScatter()
    >>> g.doneAction = None #_DOCS_HIDE
    >>> data = [(x, x * x) for x in range(50)]
    >>> g.data = data
    >>> g.process()

    .. image:: images/GraphScatter.*
        :width: 600
    '''
    graphType = 'scatter'

    def renderSubplot(self, subplot):
        self.figure.subplots_adjust(left=0.15)
        xValues = []
        yValues = []
        i = 0

        for row in self.data:
            if len(row) < 2:  # pragma: no cover
                raise GraphException('Need at least two points for a graph data object!')
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
            color = self.nextColor()
            alpha = self.alpha
            markersize = self.markersize
            if len(row) >= 3:
                displayData = row[2]
                if 'color' in displayData:
                    color = displayData['color']
                if 'marker' in displayData:
                    marker = displayData['marker']
                if 'alpha' in displayData:
                    alpha = displayData['alpha']
                if 'markersize' in displayData:
                    markersize = displayData['markersize']

            subplot.plot(x, y, marker=marker, color=color, alpha=alpha, markersize=markersize)
            i += 1
        # values are sorted, so no need to use max/min
        if not self.axisRangeHasBeenSet['y']:
            self.setAxisRange('y', (yValues[0], yValues[-1]))

        if not self.axisRangeHasBeenSet['x']:
            self.setAxisRange('x', (xValues[0], xValues[-1]))


class GraphHistogram(Graph):
    '''
    Graph the count of a single element.

    Data set is simply a list of x and y pairs, where there
    is only one of each x value, and y value is the count or magnitude
    of that value


    >>> import random
    >>> g = graph.primitives.GraphHistogram()
    >>> g.doneAction = None #_DOCS_HIDE
    >>> g.graphType
    'histogram'

    >>> data = [(x, random.choice(range(30))) for x in range(50)]
    >>> g.data = data
    >>> g.process()

    .. image:: images/GraphHistogram.*
        :width: 600
    '''
    _DOC_ATTR = {
        'binWidth': '''
            Size of each bin; if the bins are equally spaced at intervals of 1,
            then 0.8 is a good default to allow a little space. 1.0 will give no
            space.
            ''',
    }

    graphType = 'histogram'
    keywordConfigurables = Graph.keywordConfigurables + ('binWidth',)

    def __init__(self, *args, **keywords):
        self.binWidth = 0.8
        super().__init__(*args, **keywords)

        if 'alpha' not in keywords:
            self.alpha = 0.8

    def renderSubplot(self, subplot):
        self.figure.subplots_adjust(left=0.15)

        x = []
        y = []
        binWidth = self.binWidth
        color = getColor(self.colors[0])
        alpha = self.alpha
        # TODO: use the formatDict!
        for point in self.data:
            if len(point) > 2:
                a, b, unused_formatDict = point
            else:
                a, b = point
            x.append(a)
            y.append(b)

        subplot.bar(x, y, width=binWidth, alpha=alpha, color=color)


class GraphGroupedVerticalBar(Graph):
    '''
    Graph the count of on or more elements in vertical bars

    Data set is simply a list of x and y pairs, where there
    is only one of each x value, and y value is a list of values

    >>> from collections import OrderedDict
    >>> g = graph.primitives.GraphGroupedVerticalBar()
    >>> g.doneAction = None #_DOCS_HIDE
    >>> lengths = OrderedDict( [('a', 3), ('b', 2), ('c', 1)] )
    >>> data = [('bar' + str(x), lengths) for x in range(3)]
    >>> data
    [('bar0', OrderedDict([('a', 3), ('b', 2), ('c', 1)])),
     ('bar1', OrderedDict([('a', 3), ('b', 2), ('c', 1)])),
     ('bar2', OrderedDict([('a', 3), ('b', 2), ('c', 1)]))]
    >>> g.data = data
    >>> g.process()
    '''
    graphType = 'groupedVerticalBar'
    keywordConfigurables = Graph.keywordConfigurables + (
        'binWidth', 'roundDigits', 'groupLabelHeight',)

    def __init__(self, *args, **keywords):
        self.binWidth = 1
        self.roundDigits = 1
        self.groupLabelHeight = 0.0

        super().__init__(*args, **keywords)

    def labelBars(self, subplot, rects):
        # attach some text labels
        for rect in rects:
            adjustedX = rect.get_x() + (rect.get_width() / 2)
            height = rect.get_height()
            subplot.text(adjustedX,
                         height,
                         str(round(height, self.roundDigits)),
                         ha='center',
                         va='bottom',
                         fontsize=self.tickFontSize,
                         family=self.fontFamily)

    def renderSubplot(self, subplot):
        extm = getExtendedModules()
        matplotlib = extm.matplotlib

        barsPerGroup = 1
        subLabels = []

        # b value is a list of values for each bar
        for unused_a, b in self.data:
            barsPerGroup = len(b)
            # get for legend
            subLabels = sorted(b.keys())
            break

        binWidth = self.binWidth
        widthShift = binWidth / barsPerGroup

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
            # xLabels = []
            for x in xVals:
                xValsShifted.append(x + (widthShift * i))

            rect = subplot.bar(xValsShifted,
                               yVals,
                               width=widthShift,
                               alpha=0.8,
                               color=self.nextColor())
            rects.append(rect)

        colors = []
        for rect in rects:
            self.labelBars(subplot, rect)
            colors.append(rect[0])

        fontProps = matplotlib.font_manager.FontProperties(size=self.tickFontSize,
                                                           family=self.fontFamily)
        subplot.legend(colors, subLabels, prop=fontProps)


class Graph3DBars(Graph):
    '''
    Graph multiple parallel bar graphs in 3D.

    Data definition:
    A list of lists where the inner list of
    (x, y, z) coordinates.

    For instance, a graph where the x values increase
    (left to right), the y values increase in a step
    pattern (front to back), and the z values decrease
    (top to bottom):

    >>> g = graph.primitives.Graph3DBars()
    >>> g.doneAction = None #_DOCS_HIDE
    >>> data = []
    >>> for i in range(1, 10 + 1):
    ...    q = [i, i//2, 10 - i]
    ...    data.append(q)
    >>> g.data = data
    >>> g.process()

    '''
    graphType = '3DBars'
    axisKeys = ('x', 'y', 'z')

    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        if 'alpha' not in keywords:
            self.alpha = 0.8
        if 'colors' not in keywords:
            self.colors = ['#ff0000', '#00ff00', '#6666ff']

    def process(self):
        extm = getExtendedModules()
        plt = extm.plt

        self.figure = plt.figure()
        self.subplot = self.figure.add_subplot(1, 1, 1, projection='3d')

        self.renderSubplot(self.subplot)

        self.applyFormatting(self.subplot)
        self.callDoneAction()

    def renderSubplot(self, subplot):
        yDict = {}
        # TODO: use the formatDict!
        for point in self.data:
            if len(point) > 3:
                x, y, z, unused_formatDict = point
            else:
                x, y, z = point
            if y not in yDict:
                yDict[y] = []
            yDict[y].append((x, z))

        yVals = list(yDict.keys())
        yVals.sort()

        zVals = []
        xVals = []
        for key in yVals:
            for i in range(len(yDict[key])):
                x, z = yDict[key][i]
                zVals.append(z)
                xVals.append(x)
        # environLocal.printDebug(['yVals', yVals])
        # environLocal.printDebug(['xVals', xVals])

        if self.axis['x']['range'] is None:
            self.axis['x']['range'] = min(xVals), max(xVals)
        # swap y for z
        if self.axis['z']['range'] is None:
            self.axis['z']['range'] = min(zVals), max(zVals)
        if self.axis['y']['range'] is None:
            self.axis['y']['range'] = min(yVals), max(yVals)

        barWidth = (max(xVals) - min(xVals)) / 20
        barDepth = (max(yVals) - min(yVals)) / 20

        for dataPoint in self.data:
            if len(dataPoint) == 3:
                x, y, z = dataPoint
                formatDict = {}
            elif len(dataPoint) > 3:
                x, y, z, formatDict = dataPoint
            else:
                raise GraphException('Cannot plot a point with fewer than 3 values')

            if 'color' in formatDict:
                color = formatDict['color']
            else:
                color = self.nextColor()

            subplot.bar3d(x - (barWidth / 2), y - (barDepth / 2), 0,
                          barWidth, barDepth, z,
                          color=color,
                          alpha=self.alpha)

        self.setAxisLabel('x', 'x', conditional=True)
        self.setAxisLabel('y', 'y', conditional=True)
        self.setAxisLabel('z', 'z', conditional=True)


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import copy
        import sys
        import types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            # noinspection PyTypeChecker
            if callable(name) and not isinstance(name, types.FunctionType):
                try:  # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                unused_a = copy.copy(obj)
                unused_b = copy.deepcopy(obj)


# ------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):  # pragma: no cover

    def testBasic(self):
        a = GraphScatter(doneAction=None, title='x to x*x', alpha=1)
        data = [(x, x * x) for x in range(50)]
        a.data = data
        a.process()

        del a

        a = GraphHistogram(doneAction=None, title='50 x with random(30) y counts')
        data = [(x, random.choice(range(30))) for x in range(50)]
        a.data = data
        a.process()

        del a

        a = Graph3DBars(doneAction=None,
                               title='50 x with random values increase by 10 per x',
                               alpha=0.8,
                               colors=['b', 'g'])
        data = []
        for i in range(1, 4):
            q = [(x, random.choice(range(10 * i, 10 * (i + 1))), i) for x in range(50)]
            data.extend(q)
        a.data = data
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
        a.data = data
        a.process()

    def testScatterWeighted(self):
        data = []
        for i in range(50):
            x = random.choice(range(20))
            y = random.choice(range(20))
            z = random.choice(range(1, 20))
            data.append([x, y, z])

        a = GraphScatterWeighted()
        a.data = data
        a.process()

    def writeAllGraphs(self):
        '''
        Write a graphic file for all graphs,
        naming them after the appropriate class.
        This is used to generate documentation samples.
        '''

        # get some data
        data3DPolygonBars = []
        for i in range(1, 4):
            q = [(x, random.choice(range(10 * (i + 1))), i) for x in range(20)]
            data3DPolygonBars.extend(q)

        # pair data with class name
        # noinspection SpellCheckingInspection
        graphClasses = [
            (GraphHorizontalBar,
             [('Chopin', [(1810, 1849 - 1810)]),
              ('Schumanns', [(1810, 1856 - 1810), (1819, 1896 - 1819)]),
              ('Brahms', [(1833, 1897 - 1833)])]
             ),
            (GraphScatterWeighted,
             [(23, 15, 234), (10, 23, 12), (4, 23, 5), (15, 18, 120)]),
            (GraphScatter,
             [(x, x * x) for x in range(50)]),
            (GraphHistogram,
             [(x, random.choice(range(30))) for x in range(50)]),
            (Graph3DBars, data3DPolygonBars),
            (GraphColorGridLegend,
             [('Major', [('C', '#00AA55'), ('D', '#5600FF'), ('G', '#2B00FF')]),
              ('Minor', [('C', '#004600'), ('D', '#00009b'), ('G', '#00009B')]), ]
             ),
            (GraphColorGrid, [['#8968CD', '#96CDCD', '#CD4F39'],
                              ['#FFD600', '#FF5600'],
                              ['#201a2b', '#8f73bf', '#a080d5', '#6495ED', '#FF83FA'],
                              ]
             ),

        ]

        for graphClassName, data in graphClasses:
            obj = graphClassName(doneAction=None)
            obj.data = data  # add data here
            obj.process()
            fn = obj.__class__.__name__ + '.png'
            fp = str(environLocal.getRootTempDir() / fn)
            environLocal.printDebug(['writing fp:', fp])
            obj.write(fp)

    def writeGraphColorGrid(self):
        # this is temporary
        a = GraphColorGrid(doneAction=None)
        data = [['#525252', '#5f5f5f', '#797979', '#858585', '#727272', '#6c6c6c',
                 '#8c8c8c', '#8c8c8c', '#6c6c6c', '#999999', '#999999', '#797979',
                 '#6c6c6c', '#5f5f5f', '#525252', '#464646', '#3f3f3f', '#3f3f3f',
                 '#4c4c4c', '#4c4c4c', '#797979', '#797979', '#4c4c4c', '#4c4c4c',
                 '#525252', '#5f5f5f', '#797979', '#858585', '#727272', '#6c6c6c'],
                ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999',
                 '#999999', '#999999', '#999999', '#999999', '#999999', '#797979',
                 '#6c6c6c', '#5f5f5f', '#5f5f5f', '#858585', '#797979', '#797979',
                 '#797979', '#797979', '#797979', '#797979', '#858585', '#929292', '#999999'],
                ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999',
                 '#999999', '#999999', '#999999', '#999999', '#999999', '#999999',
                 '#8c8c8c', '#8c8c8c', '#8c8c8c', '#858585', '#797979', '#858585',
                 '#929292', '#999999'],
                ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999',
                 '#999999', '#999999', '#999999', '#999999', '#999999', '#999999',
                 '#8c8c8c', '#929292', '#999999'],
                ['#999999', '#999999', '#999999', '#999999', '#999999', '#999999',
                 '#999999', '#999999', '#999999', '#999999'],
                ['#999999', '#999999', '#999999', '#999999', '#999999']]
        a.data = data
        a.process()
        fn = a.__class__.__name__ + '.png'
        fp = str(environLocal.getRootTempDir() / fn)

        a.write(fp)

    def writeGraphingDocs(self):
        '''
        Write graphing examples for the docs
        '''
        post = []

        a = GraphScatter(doneAction=None)
        data = [(x, x * x) for x in range(50)]
        a.data = data
        post.append([a, 'graphing-01'])

        a = GraphScatter(title='Exponential Graph', alpha=1, doneAction=None)
        data = [(x, x * x) for x in range(50)]
        a.data = data
        post.append([a, 'graphing-02'])

        a = GraphHistogram(doneAction=None)
        data = [(x, random.choice(range(30))) for x in range(50)]
        a.data = data
        post.append([a, 'graphing-03'])

        a = Graph3DBars(doneAction=None)
        data = []
        for i in range(1, 4):
            q = [(x, random.choice(range(10 * (i + 1))), i) for x in range(20)]
            data.extend(q)
        a.data = data
        post.append([a, 'graphing-04'])

        b = Graph3DBars(title='Random Data',
                        alpha=0.8,
                        barWidth=0.2,
                        doneAction=None,
                        colors=['b', 'r', 'g'])
        b.data = data
        post.append([b, 'graphing-05'])

        for obj, name in post:
            obj.process()
            fn = name + '.png'
            fp = str(environLocal.getRootTempDir() / fn)
            environLocal.printDebug(['writing fp:', fp])
            obj.write(fp)

    def testColorGridLegend(self, doneAction=None):
        from music21.analysis import discrete

        ks = discrete.KrumhanslSchmuckler()
        data = ks.solutionLegend()
        # print(data)
        a = GraphColorGridLegend(doneAction=doneAction, dpi=300)
        a.data = data
        a.process()

    def testGraphVerticalBar(self):
        g = GraphGroupedVerticalBar(doneAction=None)
        data = [(f'bar{x}', {'a': 3, 'b': 2, 'c': 1}) for x in range(10)]
        g.data = data
        g.process()

    def testGraphNetworkxGraph(self):
        extm = getExtendedModules()  # @UnusedVariable

        if extm.networkx is not None:  # pragma: no cover
            b = GraphNetworkxGraph(doneAction=None)
            # b = GraphNetworkxGraph()
            b.process()


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testPlot3DPitchSpaceQuarterLengthCount')

