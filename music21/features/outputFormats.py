# -*- coding: utf-8 -*-
from music21 import exceptions21
from music21 import environment

environLocal = environment.Environment('features.outputFormats')


class OutputFormatException(exceptions21.Music21Exception):
    pass


class OutputFormat:
    '''
    Provide output for a DataSet, which is passed in as an initial argument.
    '''

    def __init__(self, dataSet=None):
        # assume a two dimensional array
        self.ext = None  # store a file extension if necessary
        # pass a data set object
        self._dataSet = dataSet

    def getHeaderLines(self):
        '''Get the header as a list of lines.
        '''
        pass  # define in subclass

    def write(self, fp=None, includeClassLabel=True, includeId=True):
        '''
        Write the file. If not file path is given, a temporary file will be written.
        '''
        if fp is None:
            fp = environLocal.getTempFile(suffix=self.ext)
        if not str(fp).endswith(self.ext):
            raise OutputFormatException('Could not get a temp file with the right extension')
        with open(fp, 'w') as f:
            f.write(self.getString(includeClassLabel=includeClassLabel,
                                   includeId=includeId))
        return fp


class OutputTabOrange(OutputFormat):
    '''
    Tab delimited file format used with Orange.

    For more information, see:

    http://docs.orange.biolab.si/3/data-mining-library/tutorial/data.html#saving-the-data
    '''

    def __init__(self, dataSet=None):
        super().__init__(dataSet=dataSet)
        self.ext = '.tab'

    def getHeaderLines(self, includeClassLabel=True, includeId=True):
        '''Get the header as a list of lines.


        >>> f = [features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet()
        >>> ds.addFeatureExtractors(f)
        >>> of = features.outputFormats.OutputTabOrange(ds)
        >>> for x in of.getHeaderLines(): print(x)
        ['Identifier', 'Changes_of_Meter']
        ['string', 'discrete']
        ['meta', '']

        >>> ds = features.DataSet(classLabel='Composer')
        >>> ds.addFeatureExtractors(f)
        >>> of = features.outputFormats.OutputTabOrange(ds)
        >>> for x in of.getHeaderLines(): print(x)
        ['Identifier', 'Changes_of_Meter', 'Composer']
        ['string', 'discrete', 'discrete']
        ['meta', '', 'class']

        '''
        post = []
        post.append(self._dataSet.getAttributeLabels(
            includeClassLabel=includeClassLabel, includeId=includeId))

        # second row meta data
        row = []
        for x in self._dataSet.getDiscreteLabels(
                includeClassLabel=includeClassLabel, includeId=includeId):
            if x is None:  # this is a string entry
                row.append('string')
            elif x is True:  # if True, it is discrete
                row.append('discrete')
            else:
                row.append('continuous')
        post.append(row)

        # third row metadata
        row = []
        for x in self._dataSet.getClassPositionLabels(includeId=includeId):
            if x is None:  # the id value
                row.append('meta')
            elif x is True:  # if True, it is the class column
                row.append('class')
            else:
                row.append('')
        post.append(row)
        return post

    def getString(self, includeClassLabel=True, includeId=True, lineBreak=None):
        '''Get the complete DataSet as a string with the appropriate headers.
        '''
        if lineBreak is None:
            lineBreak = '\n'
        msg = []
        header = self.getHeaderLines(includeClassLabel=includeClassLabel,
                                     includeId=includeId)
        data = header + self._dataSet.getFeaturesAsList(
            includeClassLabel=includeClassLabel)
        for row in data:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append('\t'.join(sub))
        return lineBreak.join(msg)


class OutputCSV(OutputFormat):
    '''
    Comma-separated value list.
    '''

    def __init__(self, dataSet=None):
        super().__init__(dataSet=dataSet)
        self.ext = '.csv'

    def getHeaderLines(self, includeClassLabel=True, includeId=True):
        '''Get the header as a list of lines.


        >>> f = [features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet(classLabel='Composer')
        >>> ds.addFeatureExtractors(f)
        >>> of = features.outputFormats.OutputCSV(ds)
        >>> of.getHeaderLines()[0]
        ['Identifier', 'Changes_of_Meter', 'Composer']
        '''
        post = []
        post.append(self._dataSet.getAttributeLabels(
            includeClassLabel=includeClassLabel, includeId=includeId))
        return post

    def getString(self, includeClassLabel=True, includeId=True, lineBreak=None):
        if lineBreak is None:
            lineBreak = '\n'
        msg = []
        header = self.getHeaderLines(includeClassLabel=includeClassLabel,
                                     includeId=includeId)
        data = header + self._dataSet.getFeaturesAsList(
            includeClassLabel=includeClassLabel, includeId=includeId)
        for row in data:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append(','.join(sub))
        return lineBreak.join(msg)


class OutputARFF(OutputFormat):
    '''An ARFF (Attribute-Relation File Format) file.

    See http://weka.wikispaces.com/ARFF+%28stable+version%29 for more details


    >>> oa = features.outputFormats.OutputARFF()
    >>> oa.ext
    '.arff'
    '''

    def __init__(self, dataSet=None):
        super().__init__(dataSet=dataSet)
        self.ext = '.arff'

    def getHeaderLines(self, includeClassLabel=True, includeId=True):
        '''Get the header as a list of lines.


        >>> f = [features.jSymbolic.ChangesOfMeterFeature]
        >>> ds = features.DataSet(classLabel='Composer')
        >>> ds.addFeatureExtractors(f)
        >>> of = features.outputFormats.OutputARFF(ds)
        >>> for x in of.getHeaderLines(): print(x)
        @RELATION Composer
        @ATTRIBUTE Identifier STRING
        @ATTRIBUTE Changes_of_Meter NUMERIC
        @ATTRIBUTE class {}
        @DATA

        '''
        post = []

        # get three parallel lists
        attrs = self._dataSet.getAttributeLabels(
            includeClassLabel=includeClassLabel, includeId=includeId)
        discreteLabels = self._dataSet.getDiscreteLabels(
            includeClassLabel=includeClassLabel, includeId=includeId)
        classLabels = self._dataSet.getClassPositionLabels(includeId=includeId)

        post.append(f'@RELATION {self._dataSet.getClassLabel()}')

        for i, attrLabel in enumerate(attrs):
            discrete = discreteLabels[i]
            classLabel = classLabels[i]
            if not classLabel:  # a normal attribute
                if discrete is None:  # this is an identifier
                    post.append(f'@ATTRIBUTE {attrLabel} STRING')
                elif discrete is True:
                    post.append(f'@ATTRIBUTE {attrLabel} NUMERIC')
                else:  # this needs to be a NOMINAL type
                    post.append(f'@ATTRIBUTE {attrLabel} NUMERIC')
            else:
                values = self._dataSet.getUniqueClassValues()
                joined = ','.join(values)
                post.append('@ATTRIBUTE class {' + joined + '}')
        # include start of data declaration
        post.append('@DATA')
        return post

    def getString(self, includeClassLabel=True, includeId=True, lineBreak=None):
        if lineBreak is None:
            lineBreak = '\n'

        msg = []

        header = self.getHeaderLines(includeClassLabel=includeClassLabel,
                                     includeId=includeId)
        for row in header:
            msg.append(row)

        data = self._dataSet.getFeaturesAsList(
            includeClassLabel=includeClassLabel)
        # data is separated by commas
        for row in data:
            sub = []
            for e in row:
                sub.append(str(e))
            msg.append(','.join(sub))
        return lineBreak.join(msg)


if __name__ == '__main__':
    import music21
    music21.mainTest()
