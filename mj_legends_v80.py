'''
Created on 14 feb 2012

@author: thomasg

'''

import geoimagine.gis.gis as mj_gis
import os
import array as arr
import io
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import portrait
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate
import svgwrite
from svgwrite import cm, mm 
#from PyPDF2 import PdfFileWriter
'''
import io.StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import portrait
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
'''
from sys import exit
#import string
from math import log10

def PrecisionScale(x):
    max_digits = 7
    int_part = int(abs(x))
    magnitude = 1 if int_part == 0 else int(log10(int_part)) + 1
    if magnitude >= max_digits:
        return (magnitude, 0)
    frac_part = abs(x) - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    scale = int(log10(frac_digits))
    return (magnitude, magnitude + scale, scale)

class Legend:
    """layer class for legends.""" 
    def __init__(self, process, session): 
        """The constructor expects an instance of the composition class and the wrs (1 or 2)."""
        self.process = process
        self.session = session
        if self.process.proc.processid == 'createcolorlegend':
            self.CreateColorlegend()
        elif self.process.proc.processid == 'exportlegend':
            self.ExportRasterLegend()
        else:
            NOTYET
         
    def WritePng(self, INDEX,imageFPN,cols,lins,paletteL):
        #from geoimagine.ktgraphics import img_png
        import png as img_png
        #import img_png
        RGB = arr.array('B',(int(i) for i in INDEX))
        f = open(imageFPN, 'wb')      # binary mode   
        w = img_png.Writer(width=cols, height=lins, greyscale=False, bitdepth=8, palette=paletteL, chunk_limit = cols)
        w.write_array(f, RGB)
        f.close()
           
    def CreateSepFrame(self,i):
        INDEX = [] 
        sepLins = self.legend.separatebuffer + len(self.sideFrame)*2
        self.legend.totHeight += sepLins + self.legend.buffer 
        INDEX.extend(self.topBotFrame)
        for k in range(self.legend.separatebuffer):  
            INDEX.extend(self.sideFrame)
            for l in range(self.legend.cols-self.legend.frame*2):
                INDEX.append(i) 
            INDEX.extend(self.sideFrame)
        INDEX.extend(self.topBotFrame)
        imgFN = '%s_%s-%s.png' %(self.compid,self.paletteName,i)
        imgFPN = os.path.join(self.pngFP,imgFN)
        self.imgD[i] = {'fpn':imgFPN,'lins':sepLins,'arr':INDEX}
    
    def SeparatePngFrames(self): 
        ''' CREATE THE SEPARATE FRAMES'''    
        for j in range(1,6):
            item = 'two5%s' %(j)
            nr = '25%s' %(j)
            i = int(nr)
            if getattr(self.legend, item):
                #print self.legend.item
                #if self.legendD[item]:
                self.CreateSepFrame(i)                   
       
    def SelectCompFormat(self):
        #Get the data measure from the compid
        '''
        print (self.process.proj.system)
        FISK
        query = {'system':self.process.proj.system,'compid':self.compid}
        rec = self.session._GetCompFormat(query)
        self.measure = rec[3]
        '''
        self.measure = 'R'
        
    def SelectScaling(self,comp):
        '''
        '''
        scalingD = self.session.IniSelectScaling(self.process.proc.comp.paramsD[comp])
        self.scaling = lambda: None 
        for key, value in scalingD.items():
            setattr(self.scaling, key, value)
    
    def SelectLegend(self,comp):
        '''
        '''
        legendD = self.session.IniSelectLegend(self.process.proc.comp.paramsD[comp])
        self.legend = lambda: None
        for key, value in legendD.items():
            setattr(self.legend, key, value)

            
    def _SelectPaletteColors(self):

        if self.process.params.palette == 'default':
            #Look for a default palette for this composition
            query = {'compid':self.compid}
            self.palettename = self.session._SelectCompDefaultPalette(query)
            if self.palettename == None:
                exitstr = 'No default palette for compid %(c)s' %{'c':self.compid}
                exit(exitstr)
        else:
            self.palettename = self.process.params.palette
        #Create the palette valriable
        self.palette = lambda: None
        self.svgPalette = {}
        self.svgColor = {}
        
        #Get the palette
        query = {'palette':self.palettename}
        paramL = ['value','red','green','blue','alpha','label','hint']
        recs = self.session._SelectPaletteColors(query,paramL)
        
        recs.sort()  
        for rec in recs:
            if 0 <= rec[0] <= 250:
                #self.svgPalette[rec[0]] = [rec[1],rec[2],rec[3]]
                self.svgPalette[rec[0]] = 'rgb(%(r)d,%(g)d,%(b)d)' %{ 'r':rec[1], 'g':rec[2], 'b':rec[3] }
            else:
                self.svgColor[rec[0]] = 'rgb(%(r)d,%(g)d,%(b)d)' %{ 'r':rec[1], 'g':rec[2], 'b':rec[3] }

        self.palette.items = recs
        self.palette.paletteL = []
        palette = mj_gis.RasterPalette()
        palette.SetTuplePalette(recs)
        for i in range(256):             
            self.palette.paletteL.append(palette.colortable.GetColorEntry(i))
            
        self.palette.legIdL = []
        self.palette.stickIdL =[]
        self.palette.coreIdL = [] 
        for rec in recs:
            self.palette.legIdL.append(rec[0])
            if rec[0] <= 250:
                self.palette.coreIdL.append(rec[0])
                if rec[6] != 'NA':
                    self.palette.stickIdL.append(rec[0])              
        self.palette.minLeg = max(recs[0][0],self.legend.palmin)
        self.palette.maxLeg = min(recs[len(recs)-1][0],self.legend.palmax) 
        #self.palette.maxLeg = min(max(self.palette.coreIdL),self.legend.palmax,250)
            
    def SetLegendDim(self):
        self.legend.cols = self.legend.width
        self.legend.lins = self.legend.height   
        self.sideFrame = arr.array('B',(254 for i in range(self.legend.frame) ) )
        self.topBotFrame = arr.array('B',(254 for i in range(self.legend.cols*self.legend.frame) ) )
        self.frameStick =  arr.array('B',(254 for i in range(self.legend.sticklen) ) )
            
    def CreateFramesN(self):
        #Create sepframes
        self.legend.totHeight = 0
        self.SeparatePngFrames() 
        for i in range(self.palette.minLeg,self.palette.maxLeg+1):
            if i in self.palette.legIdL:
                #self.CreateSepFrame(self.legend.totHeight,cols,pngFP,i)
                self.CreateSepFrame(i)
                
    def CreateFramesOIR(self):
        INDEX = []
        linsperitem = int(self.legend.lins/(self.palette.maxLeg-self.palette.minLeg))
        printStretch = linsperitem*(self.palette.maxLeg-self.palette.minLeg+1)
        totLins = linsperitem*(self.palette.maxLeg-self.palette.minLeg+1)+(self.legend.frame*2)
        self.legend.totHeight = linsperitem*(self.palette.maxLeg-self.palette.minLeg+1)+(self.legend.frame*2)   
        #self.SeparatePngFrames(self.imgD,self.legend.totHeight,self.legend.cols,pngFP)   
        self.SeparatePngFrames()
        if float(self.legend.height-self.legend.totHeight) / (self.palette.maxLeg-self.palette.minLeg) > 0.5:
            linsperitem += 1
            totLins += (self.palette.maxLeg-self.palette.minLeg+1)
            printStretch += (self.palette.maxLeg-self.palette.minLeg+1)
        for i in range(self.palette.minLeg,self.palette.maxLeg+1):
            for k in range(linsperitem):
                INDEX.extend(self.sideFrame)
                if i in self.palette.stickIdL:
                    INDEX.extend(self.frameStick)        
                    for l in range(self.legend.cols-len(self.sideFrame)*2-len(self.frameStick)):
                        INDEX.append(i)   
                else:
                    for l in range(self.legend.cols-self.legend.frame*2):
                        INDEX.append(i) 
                INDEX.extend(self.sideFrame)          
        # Put the top frame
        INDEX.extend(self.topBotFrame)
        INDEX.reverse()  
        # Put the bottom frame
        INDEX.extend(self.topBotFrame)
        imgFN = '%s_%s.png' %(self.compid,self.palettename)
        imgFPN = os.path.join(self.pngFP,imgFN)
        self.imgD[0] = {'fpn':imgFPN,'lins':totLins,'arr':INDEX}
           
    def _WriteLegendImgs(self):
        #Write png images to file
        for item in self.imgD:    
            if not len(self.imgD[item]['arr']) == self.legend.cols * self.imgD[item]['lins']:
                print ( len(self.imgD[item]['arr']) ) 
                print ( self.legend.cols * self.imgD[item]['lins'] )
                BALLE
            print (len(self.imgD[item]['arr']),self.legend.cols* self.imgD[item]['lins'])
            self.WritePng(self.imgD[item]['arr'],self.imgD[item]['fpn'],self.legend.cols,self.imgD[item]['lins'],self.palette.paletteL)
    
    def _WriteLegendSVG(self):
        #Write svg
        
        for item in self.imgD:
            name = self.imgD[item]['fpn'].replace('.png','.svg') 
            print ( self.legend.cols, self.imgD[item]['lins'] )

            dwg = svgwrite.Drawing(name, size=('5cm', '15cm'), profile='full', debug=True)
            # set user coordinate space
            dwg.viewbox(width=50, height=150)
        
            # create a new linearGradient element
            vertical_gradient = dwg.linearGradient((0, 0), (0, 1))
        
            # add gradient to the defs section of the drawing
            dwg.defs.add(vertical_gradient)

            # define the gradient 
            for key in self.svgPalette:
                i = float(key)/250.0
                vertical_gradient.add_stop_color(i, self.svgPalette[key])

            dwg.add(dwg.rect( (10,10), (30,80), fill=vertical_gradient.get_paint_server(default='currentColor'),stroke=self.svgColor[254], stroke_width=3))
            
            self.svgColor
            dwg.save()

        BALLE
        for item in self.imgD:    
            if not len(self.imgD[item]['arr']) == self.legend.cols * self.imgD[item]['lins']:
                print ( len(self.imgD[item]['arr']) ) 
                print ( self.legend.cols * self.imgD[item]['lins'] )
                BALLE
            print (len(self.imgD[item]['arr']),self.legend.cols* self.imgD[item]['lins'])
            self.WritePng(self.imgD[item]['arr'],self.imgD[item]['fpn'],self.legend.cols,self.imgD[item]['lins'],self.palette.paletteL)

    def ExportRasterLegend(self):
        self.imgD = {}
        #Export each composition (if several)
        for comp in self.process.proc.comp.paramsD:
            print ('exporting legend for', self.process.proc.comp.paramsD[comp]['band'])
            self.compid = '%s_%s' %(self.process.proc.comp.paramsD[comp]['folder'].lower(),self.process.proc.comp.paramsD[comp]['band'].lower() )
            #Create the target paths
            self.pngFP = os.path.join('/Volumes',self.process.dstpath.volume,'legends','png')
            self.pdfFP = os.path.join('/Volumes',self.process.dstpath.volume,'legends','pdf')
            self.svgFP = os.path.join('/Volumes',self.process.dstpath.volume,'legends','svg')
            if not os.path.exists(self.pngFP):
                os.makedirs(self.pngFP)
            if not os.path.exists(self.pdfFP):
                os.makedirs(self.pdfFP)
            if not os.path.exists(self.svgFP):
                os.makedirs(self.svgFP)
            #Get the measure (i.e. O,R,I)
            self.SelectCompFormat()
            #Get the scaling
            self.SelectScaling(comp)
            #Get the legend
            self.SelectLegend(comp)
            #Get the palette
            self._SelectPaletteColors()
            #Set the dimensions
            self.SetLegendDim()

            if self.measure == 'N': 
                self.CreateFramesN()         
            else:
                self.CreateFramesOIR()
            self._WriteLegendImgs()
            self._WriteLegendSVG()
            SNULLE
            #Construct the text items
            
            #set the origin for the printing
            self.xPos,self.yPos = 10,self.legend.fontsize
            #Position the extra legend entries
            self._SetTwoFivePrintPos()
                             
            #self._ConstructPDF()
            
            self._ConstructSVG()
    
    def _SetTwoFivePrintPos(self):   
        #get the print positions for items 255 downto 250:
        for i in range(255,250,-1):
            if i in self.imgD:
                self.imgD[i]['ymin'] = self.yPos
                self.yPos += self.imgD[i]['lins']
                self.imgD[i]['ymax'] = self.yPos
                self.yPos += self.legend.buffer
                self.imgD[i]['ycenter'] = (self.imgD[i]['ymax']+self.imgD[i]['ymin'])/2
                self.imgD[i]['xmin'] = self.xPos
                self.imgD[i]['xmax'] = self.legend.cols+self.imgD[i]['xmin'] 
                
    def _SetValuePrintPosNM(self):
        #Start from the top
        for i in range(0,251):
            if i in self.imgD: 
                topy = self.yPos+(len(self.palette.coreIdL)/self.legend.columns)*(self.imgD[i]['lins']+self.legend.buffer)
                posL = [j for j in range(len(self.palette.coreIdL))]
                item = self.palette.coreIdL.index(i)
                for c in range(self.legend.columns):
                    testL = [j for j in posL if int(j-c) % self.legend.columns == 0]
                    if item in testL:
                        break
                itemx = c
                itemy = testL.index(item)
                #get bottom y
                self.imgD[i]['ymax'] = topy-itemy*(self.imgD[i]['lins']+self.legend.buffer)
                self.imgD[i]['ymin'] = self.imgD[i]['ymax']-self.imgD[i]['lins']
                #150 is a fixed offset to make place for text
                self.imgD[i]['xmin'] = self.xPos+150+itemx*(self.legend.cols+self.legend.buffer)
                self.imgD[i]['xmax'] = self.legend.cols+self.imgD[i]['xmin']          
                self.imgD[i]['ycenter'] = (self.imgD[i]['ymax']+self.imgD[i]['ymin'])/2
                self.imgD[i]['xcenter'] = (self.imgD[i]['xmax']+self.imgD[i]['xmin'])/2 
                
    def _SetValuePrintPos(self):
        for i in range(0,251):
            if i in self.imgD:
                #get left x
                self.imgD[i]['xmin'] = self.xPos
                #get bottom y
                self.imgD[i]['ymin'] = self.yPos    
                self.yPos += self.imgD[i]['lins']
                self.imgD[i]['ymax'] = self.yPos
                self.yPos += self.legend.buffer
                self.imgD[i]['ycenter'] = (self.imgD[i]['ymax']+self.imgD[i]['ymin'])/2       
            
    def _SetValueProntPosR(self):                 
        ymaxtext = self.imgD[0]['ymax'] - self.legend.frame
        ymintext = self.imgD[0]['ymin'] + self.legend.frame
        ytextrange = (ymaxtext-ymintext)/(self.palette.maxLeg-self.palette.minLeg)
        printCenter = self.imgD[0]['ycenter']
        rangeCenter = (self.palette.maxLeg-self.palette.minLeg)/2
        if self.legend.compresslabels:
            printStep = ytextrange*(printCenter+self.legend.fontsize/2)/(printCenter+self.legend.fontsize)
        else:
            printStep = ytextrange*(printCenter+self.legend.fontsize/1)/(printCenter+self.legend.fontsize)

    def _CanvasDrawImages(self):
        '''
        '''
        BALLE
        for item in self.imgD: 
            self.cv.drawImage(self.imgD[item]['fpn'], self.imgD[item]['xmin'], self.imgD[item]['ymin'])
     
    def _CanvasDrawText(self):
            #Set the legend text   
            for rec in self.palette.items:           
                if rec[0] <= self.legend.palmax and rec[6] != 'NA':
                    if self.measure == 'R':
                        if rec[5].isdigit():    
                            if self.scaling.power:                           
                                if self.scaling.mirror0:
                                    iniVal = rec[0]-125
                                    iniVal /= float(self.scaling.scalefac)
                                    if iniVal == 0:
                                        legVal = 0
                                    if iniVal < 0:
                                        legVal = pow(-iniVal,1/self.scaling.power)
                                    else:
                                        legVal = pow(iniVal,1/self.scaling.power)
                                else:
                                    legVal = int(rec[0])-self.scaling.offsetadd
                                    legVal /= float(self.scaling.scalefac)    
                                    legVal = pow(legVal,1/self.scaling.power)
                            else:
                                legVal = int(rec[0])-self.scaling.offsetadd
                                legVal /= float(self.scaling.scalefac) 
                            if self.legend.precision == 0:
                                legStr = '%s' % int(round(float('%.2g' % legVal)))
                            else:
    
                                precision =  '%(p)dg' %{'p':self.legend.precision}
                                precision = '%.'+precision
                                legStr = '%s' % float(precision % legVal)
                            #SEE https://stackoverflow.com/questions/3410976/how-to-round-a-number-to-significant-figures-in-python
                        else: 
                            legStr = rec[5]
               
                        ypos = self.imgD[0]['ycenter'] + (rec[0]-self.palette.minLeg-self.rangeCenter)*self.printStep
                        self.cv.drawString(self.xPos+self.legend.cols+10, ypos-self.legend.fontsize/3, legStr) 
                    else:
                        legStr = rec[5]
                        ypos = self.imgD[rec[0]]['ycenter']-self.legend.fontsize/3
                        self.cv.drawString(self.xPos+self.legend.cols+10, ypos, legStr)
    
          
                elif rec[0] > 250 and rec[6] != 'NA':
                    if rec[0] in self.imgD:
                        ypos = self.imgD[rec[0]]['ycenter']   
                        self.cv.drawString(self.xPos+self.legend.cols+10, ypos-self.legend.fontsize/3, rec[5])
    
            if self.measure == 'N' and self.legend.matrix:
                coltext = self.legend.columntext.split(':')
                rowtext = self.legend.rowtext.split(':')
    
                for c in range(self.legend.columns):
                    xpos = self.imgD[self.palette.coreIdL[c]]['xmin']
                    ypos = self.imgD[self.palette.coreIdL[c]]['ymax']+10
                    self.cv.drawString(xpos, ypos, coltext[c])
                    if c == 1:
                        ypos+= self.legend.fontsize+10
                        self.cv.drawString(xpos, ypos, self.legend.columnhead)
                        #10 is the default x for the row header
                        self.cv.drawString(10, ypos, self.legend.rowhead)
       
                for c in range(len(rowtext)):
                    xpos = 50 #default x position from matrix text
                    ypos = self.imgD[self.palette.coreIdL[c]*len(rowtext)]['ycenter']
                    self.cv.drawString(xpos, ypos, rowtext[c])
                    '''
                    if c == int(len(rowtext)/2):
                        xpos = 10
                        cv.drawString(xpos, ypos, self.legend.rowhead)
                    '''   
            elif len(self.legend.columnhead) > 0:
                print (self.legend.columnhead)
                headcols = self.legend.columnhead.split(':')
                headcols.reverse()
                self.xPos += self.legend.fontsize/2
                for i,col in enumerate(headcols):
                    if i > 0:
                        self.yPos += self.legend.fontsize
                    self.cv.drawString(self.xPos, self.yPos, col)
            
    def _ConstructPDF(self):
        #set the origin for the printing
        self.xPos,self.yPos = 10,self.legend.fontsize
        self._SetTwoFivePrintPos()
        
        #set the pdf
        pdfFN = '%s-%s.pdf' %(self.compid, self.palettename)
        pdfFPN = os.path.join(self.pdfFP,pdfFN)
        #packet = io.StringIO()
        packet = BytesIO
        #packet=StringIO.StringIO()
        #create the canvas
        self.cv=canvas.Canvas(packet)
        #set the font
        #font = self.legend.font
        #fontsize = self.legend.fontsize
        fontttf = '%s.ttf' %(self.legend.font)
        pdfmetrics.registerFont(TTFont(self.legend.font, fontttf ))
        self.cv.setFont(self.legend.font, self.legend.fontsize)
         
        self._SetValuePrintPos()
        
        if self.measure == 'N' and self.legend.matrix:
            self._SetValuePrintPosNM()
        else:
            self._SetValuePrintPos()
            if self.measure != 'N': 
                self._SetValueProntPosR()   
    
        self._CanvasDrawImages()
        
        #self._CanvasDrawText()
        
        #save 
        self.cv.save()    
        #get back to 0
        packet.seek(0)
        #write to a file
        with open(pdfFPN,'wb') as fp:
            fp.write(packet.getvalue())
            
    def _ConstructSVG(self):
        #set the origin for the printing
        self.xPos,self.yPos = 10,self.legend.fontsize
        self._SetTwoFivePrintPos()
        
        #set the pdf
        pdfFN = '%s-%s.pdf' %(self.compid, self.palettename)
        pdfFPN = os.path.join(self.pdfFP,pdfFN)
        #packet = io.StringIO()
        packet = BytesIO
        #packet=StringIO.StringIO()
        #create the canvas
        self.cv=canvas.Canvas(packet)
        #set the font
        #font = self.legend.font
        #fontsize = self.legend.fontsize
        fontttf = '%s.ttf' %(self.legend.font)
        pdfmetrics.registerFont(TTFont(self.legend.font, fontttf ))
        self.cv.setFont(self.legend.font, self.legend.fontsize)
         
        self._SetValuePrintPos()
        
        if self.measure == 'N' and self.legend.matrix:
            self._SetValuePrintPosNM()
        else:
            self._SetValuePrintPos()
            if self.measure != 'N': 
                self._SetValueProntPosR()   
    
        self._CanvasDrawImages()
        
        #self._CanvasDrawText()
        
        #save 
        self.cv.save()    
        #get back to 0
        packet.seek(0)
        #write to a file
        with open(pdfFPN,'wb') as fp:
            fp.write(packet.getvalue())
            
def basic_shapes(name):
    dwg = svgwrite.Drawing(filename=name, debug=True)
    hlines = dwg.add(dwg.g(id='hlines', stroke='green'))
    for y in range(20):
        hlines.add(dwg.line(start=(2*cm, (2+y)*cm), end=(18*cm, (2+y)*cm)))
    vlines = dwg.add(dwg.g(id='vline', stroke='blue'))
    for x in range(17):
        vlines.add(dwg.line(start=((2+x)*cm, 2*cm), end=((2+x)*cm, 21*cm)))
    shapes = dwg.add(dwg.g(id='shapes', fill='red'))

    # set presentation attributes at object creation as SVG-Attributes
    circle = dwg.circle(center=(15*cm, 8*cm), r='2.5cm', stroke='blue', stroke_width=3)
    circle['class'] = 'class1 class2'
    shapes.add(circle)

    # override the 'fill' attribute of the parent group 'shapes'
    shapes.add(dwg.rect(insert=(5*cm, 5*cm), size=(45*mm, 45*mm),
                        fill='blue', stroke='red', stroke_width=3))

    # or set presentation attributes by helper functions of the Presentation-Mixin
    ellipse = shapes.add(dwg.ellipse(center=(10*cm, 15*cm), r=('5cm', '10mm')))
    ellipse.fill('green', opacity=0.5).stroke('black', width=5).dasharray([20, 20])
    dwg.save()
    
def simple_text(name):
    dwg = svgwrite.Drawing(name, (200, 200), debug=True)
    paragraph = dwg.add(dwg.g(font_size=14))
    paragraph.add(dwg.text("This is a Test!", (10, 20)))
    # 'x', 'y', 'dx', 'dy' and 'rotate' has to be a <list> or a <tuple>!!!
    # 'param'[0] .. first letter, 'param'[1] .. second letter, and so on
    # if there are more letters than values, the last list-value is used
    #
    # different 'y' coordinates does not work with Firefox 3.6
    paragraph.add(dwg.text("This is a Test", x=[10], y=[40, 45, 50, 55, 60]))

    # different formats can be used by the TSpan element
    # The atext.tspan(...) method is a shortcut for: atext.add(dwg.tspan(...))
    atext = dwg.text("A", insert=(10, 80), style="text-shadow: 2px 2px;")

    # text color is set by the 'fill' property and 'stroke sets the outline color.
    atext.add(dwg.tspan(' Word', font_size='1.5em', fill='red'))
    atext.add(dwg.tspan(' is a Word!', dy=['1em'], font_size='0.7em', fill='green'))
    paragraph.add(dwg.text("Das ist ein Test mit ÖÄÜäüö!", (10, 120)))
    paragraph.add(atext)
    dwg.save()
    
def linearGradient(name):
    dwg = svgwrite.Drawing(name, size=('5cm', '15cm'), profile='full', debug=True)

    # set user coordinate space
    dwg.viewbox(width=50, height=150)

    # create a new linearGradient element
    #horizontal_gradient = dwg.linearGradient((0, 0), (1, 0))
    vertical_gradient = dwg.linearGradient((0, 0), (0, 1))
    #diagonal_gradient = dwg.linearGradient((0, 0), (1, 1))
    #tricolor_gradient = dwg.linearGradient((0, 0), (1, 1))

    # add gradient to the defs section of the drawing
    #dwg.defs.add(horizontal_gradient)
    dwg.defs.add(vertical_gradient)
    #dwg.defs.add(diagonal_gradient)
    #dwg.defs.add(tricolor_gradient)

    # define the gradient from white to red
    #horizontal_gradient.add_stop_color(0, 'white')
    #horizontal_gradient.add_stop_color(1, 'red')
    vertical_gradient.add_stop_color(0, 'yellow')
    vertical_gradient.add_stop_color(.33, 'red')
    vertical_gradient.add_stop_color(.66, 'green')
    vertical_gradient.add_stop_color(1, 'blue')

    # define the gradient from white to green
    #vertical_gradient.add_stop_color(0, 'white')
    #vertical_gradient.add_stop_color(1, 'green')

    # define the gradient from white to blue
    #diagonal_gradient.add_stop_color(0, 'white')
    #diagonal_gradient.add_stop_color(1, 'blue')

    # define the gradient from white to red to green to blue
    #tricolor_gradient.add_stop_color(0, 'white')
    #tricolor_gradient.add_stop_color(.33, 'red')
    #tricolor_gradient.add_stop_color(.66, 'green')
    #tricolor_gradient.add_stop_color(1, 'blue')


    # use gradient for filling the rect
    dwg.add(dwg.rect((10,10), (30,60), fill=vertical_gradient.get_paint_server(default='currentColor')))
    #dwg.add(dwg.rect((70,10), (50,50), fill=vertical_gradient.get_paint_server(default='currentColor')))
    #dwg.add(dwg.rect((130,10), (50,50), fill=diagonal_gradient.get_paint_server(default='currentColor')))

    #dwg.add(dwg.rect((10,70), (50,50), fill=tricolor_gradient.get_paint_server(default='currentColor')))

    # rotate gradient about 90 degree
    # first copy gradient
    #tricolor2_gradient = tricolor_gradient.copy()
    # rotate the gradient
    #tricolor2_gradient.rotate(90, (.5, .5))
    # add gradient to the defs section of the drawing
    #dwg.defs.add(tricolor2_gradient)
    # use the gradient
    #dwg.add(dwg.rect((70,70), (50,50), fill=tricolor2_gradient.get_paint_server(default='currentColor')))

    #updown = dwg.linearGradient()
    #dwg.defs.add(updown)
    #updown.add_colors(['red', 'white', 'red', 'white', 'red'], sweep=(.2, .8))
    #dwg.add(dwg.rect((130,70), (50,50), fill=updown.get_paint_server(default='currentColor')))

    dwg.save()

if __name__ == "__main__":
    '''
    global ConnProcess, ConnRegions  
    print (PrecisionScale(12.00) )
    
    #ConnProcess,ConnRegions,ConnAncillary, ConnComp = StartUp()[0:4] #Link all the python scripts and some default databases for format translations, must be run at stratup each time
    #LegendTester()
    #AddUserProject()
    '''

    
    #basic_shapes('/Volumes/africa/legends/basic_shapes.svg')
    
    #simple_text('/Volumes/africa/legends/simple_text.svg')
    
    linearGradient('/Volumes/africa/legends/linearGradient.svg')
