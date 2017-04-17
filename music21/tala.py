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
        
        if taliKhali is not None and not isinstance(taliKhali, int):
            raise TypeError('argument taliKhali should be of type int')
        elif taliKhali is not None and taliKhali != 1 and taliKhali != 0:
            raise ValueError('argument taliKhali takes a binary value: 0 or 1')
        # Set the bol when creating a composition.
        self.bols = bols
        
        # This variable takes either of the one the class variables 'tali' or 'khali'
        self.taliKhali = taliKhali
    

class Vibhaga(base.Music21Object):
    '''
    This class represents a vibhaga in a tala cycle and other information related to it.
    '''
    
    def __init__(self, matras = None):
        '''
        This class is used to define a vibhaga in a tala cycle
        '''

        # Handling exceptions for matra
        if matras is not None and (not isinstance(matras, list) or not all(isinstance(x, Matra)for x in matras)):
            raise TypeError('argument matra should either be None or a list of Matra')  
        
        self.matras = matras
        
        
    @property
    def numMatras(self):
        return len(self.matras)
        
        
class Avartan(base.Music21Object):
    '''
    This class represents one avartan of a tala cycle
    '''
    def __init__(self, vibhagas):
        
        if not isinstance(vibhagas, list) or not all(isinstance(x, Vibhaga)for x in vibhagas):
            raise TypeError('second argument vibhagas should be a list of Vibhaga')
        
        self.vibhagas = vibhagas
        
    @property
    def numVibhagas(self):
        return len(self.vibhagas)
        
        

class TeenTalAvartan(Avartan):
    '''
    This class represents an Avartan of TeenTal
    '''
    def __init__(self):
        matra1 = Matra(1)
        matra2 = Matra()
        matra3 = Matra()
        matra4 = Matra()
        vibhaga1 = Vibhaga([matra1, matra2, matra3, matra4])
    
        matra5 = Matra(1)
        matra6 = Matra()
        matra7 = Matra()
        matra8 = Matra()
        vibhaga2 = Vibhaga([matra5, matra6, matra7, matra8])
        
        matra9 = Matra(0)
        matra10 = Matra()
        matra11 = Matra()
        matra12 = Matra()
        vibhaga3 = Vibhaga([matra9, matra10, matra11, matra12])
        
        matra13 = Matra(1)
        matra14 = Matra()
        matra15 = Matra()
        matra16 = Matra()
        vibhaga4 = Vibhaga([matra13, matra14, matra15, matra16])
        
        super(TeenTalAvartan, self).__init__([vibhaga1, vibhaga2, vibhaga3, vibhaga4])