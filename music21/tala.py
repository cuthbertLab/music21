'''
This module is for adding support for talas support in music21 in Indian Art Music.
'''
from music21 import base
from __builtin__ import int

class Matra(base.Music21Object):
    ''' 
    This class represents the matra in a tala cycle 
    '''
    
    khali = 0
    tali = 1
    
    _DOC_ATTR_ = {
    'khali' : 'int variable representing khali for the property taliKhali',
    'tali' : 'int variable representing tali for the property taliKhali'
    }
    
    def __init__(self, taliKhali = None, bols = None):
        
        # Set the bol when creating a composition.
        self.bols = bols
        
        # This variable takes either of the one the class variables 'tali' or 'khali'
        self.taliKhali = taliKhali
        
    def setBol(self, bols):
        self.bols = bols
        
    def setTali(self):
        self.taliKhali = Matra.tali
    
    def setKhali(self):
        self.taliKhali = Matra.khali
    
    

class Vibhaga(base.Music21Object):
    '''
    This class represents a vibhaga in a tala cycle and other information related to it.
    '''
    
    def __init__(self, numMatras, startMatraPos, matras = None):
        '''
        This class is used to define a vibhaga in a tala cycle
        '''
        
        # Handling exceptions for the numMatras
        if not isinstance(numMatras, int):
            raise TypeError('first argument numMatras should be of type int')
        elif numMatras < 1:
            raise ValueError('first argument numMatras should be a positive integer')
        
        # Handling exceptions for the startMatraPos
        if not isinstance(startMatraPos, int):
            raise TypeError('second argument startMatraPos should be of type int')
        elif startMatraPos < 1:
            raise ValueError('second argument startMatraPos should be a positive integer')

        # Handling exceptions for matra
        if matras is not None and (not isinstance(matras, list) or not all(isinstance(x, Matra)for x in matras)):
            raise TypeError('argument matra should either be None or a list of Matra')
        elif matras is not None and len(matras) is not numMatras:
            raise ValueError('number of elements in list matras should be equal to numMatras')    
        
        
        self.numMatras = numMatras
        self.matras = matras
        self.startMatraPos = startMatraPos
        
        
    def setMatras(self, matras):
        if not isinstance(matras, Matra) and not all(isinstance(x, Matra)for x in matras):
            raise TypeError('argument matra should either be None or a list of Matra')
        elif len(matras) != self.numMatras:
            raise ValueError('number of elements in list matras should be equal to numMatras')
        self.matras = matras
            
        
    def setNumMatras(self, numMatras):
        # Handling exceptions for the numMatras
        if not isinstance(numMatras, int):
            raise TypeError('first argument numMatras should be of type int')
        elif numMatras < 1:
            raise ValueError('first argument numMatras should be a positive integer')
        self.numMatras = numMatras
        
        
    def setStartMatraPos(self, startMatraPos):
        # Handling exceptions for the startMatraPos
        if not isinstance(startMatraPos, int):
            raise TypeError('second argument startMatraPos should be of type int')
        elif startMatraPos < 0:
            raise ValueError('second argument startMatraPos should be a positive integer')
        self.startMatraPos = startMatraPos
        
        
class Avartan(base.Music21Object):
    '''
    This class represents one avartan of a tala cycle
    '''
    def __init__(self, vibhagas):
        
        if not isinstance(vibhagas, list) or not all(isinstance(x, Vibhaga)for x in vibhagas):
            raise TypeError('second argument vibhagas should be a list of Vibhaga')
        
        self.numVibhagas = len(vibhagas)
        self.vibhagas = vibhagas
        
    def setVibhagas(self, vibhagas):
        
        if not isinstance(vibhagas, list) or not all(isinstance(x, Vibhaga)for x in vibhagas):
            raise TypeError('second argument vibhagas should be a list of Vibhaga')
        
        self.vibhagas = vibhagas
        self.updateVals()
        
    def updateVals(self):
        self.numVibhagas = len(self.vibhagas)
        

class TeenTalAvartan(Avartan):
    '''
    This class represents an Avartan of TeenTal
    '''
    def __init__(self):
        matra1 = Matra(1)
        matra2 = Matra()
        matra3 = Matra()
        matra4 = Matra()
        vibhaga1 = Vibhaga(4, 1, [matra1, matra2, matra3, matra4])
    
        matra5 = Matra(1)
        matra6 = Matra()
        matra7 = Matra()
        matra8 = Matra()
        vibhaga2 = Vibhaga(4, 5, [matra5, matra6, matra7, matra8])
        
        matra9 = Matra(0)
        matra10 = Matra()
        matra11 = Matra()
        matra12 = Matra()
        vibhaga3 = Vibhaga(4, 9, [matra9, matra10, matra11, matra12])
        
        matra13 = Matra(1)
        matra14 = Matra()
        matra15 = Matra()
        matra16 = Matra()
        vibhaga4 = Vibhaga(4, 13,[matra13, matra14, matra15, matra16])
        
        super(TeenTalAvartan, self).__init__([vibhaga1, vibhaga2, vibhaga3, vibhaga4])