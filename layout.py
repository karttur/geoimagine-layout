'''
Created on 22 Oct 2018

@author: thomasgumbricht
'''
from geoimagine.layout import mj_legends as mj_legends

class ProcessLayout():
    def __init__(self, process, session, verbose):
        #self.session = session
        self.verbose = verbose
        self.process = process   
        self.session = session         
        #direct to subprocess

        print ('    ProcessLayout:',self.process.proc.processid )
        if self.process.proc.processid == 'addrasterpalette':
            self._AddRasterPalette()
        elif self.process.proc.processid == 'createlegend':
            self._AddRasterLegend()
        elif self.process.proc.processid == 'createscaling':
            self._AddRasterScaling()
        elif self.process.proc.processid == 'exportlegend':
            self._ExportRasterLegend()
        elif self.process.proc.processid == 'addmovieclock':
            self._AddMovieClock()
        elif self.process.proc.processid.lower() == 'movieclock':
            self._MovieClock()
        else:
            NOTYET
            
    def _AddRasterPalette(self):
        for item in self.process.proc.subparamsD:
            if item == 'setcolor':
                self.session._ManageRasterPalette(self.process.proc.userProj.userid, self.process.params,
                            self.process.proc.subparamsD[item],
                            self.process.overwrite,self.process.delete)
                
    def _AddRasterLegend(self):
        for comp in self.process.proc.comp.paramsD:
            self.session._ManageRasterLegend(self.process.proc.paramsD,
                                self.process.proc.comp.paramsD[comp],
                                self.process.overwrite,self.process.delete)
        
    def _AddRasterScaling(self):
        '''
        '''
        #change bool params to Y/N prior to looping otherwise the bool value always becomes True after first loop
        booleans = ['mirror0']
        for b in booleans:
            if self.process.proc.paramsD[b]:
                self.process.proc.paramsD[b] = 'Y'
            else:
                self.process.proc.paramsD[b] = 'N'
        for comp in self.process.proc.comp.paramsD:
            self.session._ManageRasterScaling(self.process.proc.paramsD,
                                self.process.proc.comp.paramsD[comp],
                                self.process.overwrite,self.process.delete)
    
    def _ExportRasterLegend(self):
        mj_legends.Legend(self.process, self.session)
    
    def _AddMovieClock(self):
        '''
        '''
        self.session._ManageMovieClock(self.process.proc.paramsD,
                self.process.overwrite,self.process.delete)
        
    def _MovieClock(self):
        '''
        '''
        BALLE
        