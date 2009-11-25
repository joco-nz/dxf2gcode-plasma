#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_notebook.py
#Programmers:   Christian Kohloeffel
#               Vinzenz Schulz
#
#Distributed under the terms of the GPL (GNU Public License)
#
#dxf2gcode is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#About Dialog
#First Version of dxf2gcode Hopefully all works as it should


import sys, os, string
import ConfigParser

PROGRAMDIRECTORY = os.path.dirname(os.path.abspath(sys.argv[0]))
BITMAPDIRECTORY = PROGRAMDIRECTORY + "/bitmaps"

from Tkconstants import END, ALL, N, S, E, W, RIDGE, GROOVE, FLAT, DISABLED, NORMAL, ACTIVE, LEFT
from tkMessageBox import showwarning, showerror
from Tkinter import Tk, IntVar, DoubleVar, Canvas, Menu, Frame, Radiobutton, Label, Entry, Text, Scrollbar, Toplevel,Button
from Tkinter import DoubleVar, IntVar

class ExportParasClass:
    def __init__(self,master=None,config=None,postpro=None):
        self.master=master
  
        self.nb = NotebookClass(self.master,width=240)

        # uses the notebook's frame
        self.nb_f1 = Frame(self.nb())
        #self.nb_f2 = Frame(self.nb())

        # keeps the reference to the radiobutton (optional)
        self.nb.add_screen(self.nb_f1, _("Layers"))
        #self.nb.add_screen(self.nb_f2, _("File Beg. & End"))

        self.nb_f1.columnconfigure(0,weight=1)
        #self.nb_f2.columnconfigure(0,weight=1)        
    
        self.erstelle_eingabefelder(config)

        #self.gcode_be.insert(END,postpro.gcode_be)
        #self.gcode_en.insert(END,postpro.gcode_en)


    def erstelle_eingabefelder(self,config):
       
        f1=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f1.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        f2=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f2.grid(row=1,column=0,padx=2,pady=2,sticky=N+W+E)
        f3=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f3.grid(row=2,column=0,padx=2,pady=2,sticky=N+W+E)
    
        f1.columnconfigure(0,weight=1)
        f2.columnconfigure(0,weight=1)
        f3.columnconfigure(0,weight=1)        
   
        Label(f1, text=_("Tool diameter [mm]:"))\
                .grid(row=0,column=0,sticky=N+W,padx=4)
        Entry(f1,width=7,textvariable=self.tool_dia)\
                .grid(row=0,column=1,sticky=N+E)

        Label(f1, text=_("Start radius (for tool comp.) [mm]:"))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        Entry(f1,width=7,textvariable=self.start_rad)\
                .grid(row=1,column=1,sticky=N+E)        

        Label(f2, text=(_("%s safety margin [mm]:") %config.ax3_letter))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=self.axis3_safe_margin)\
                .grid(row=1,column=1,sticky=N+E)

        Label(f2, text=(_("%s infeed depth [mm]:") %config.ax3_letter))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=self.axis3_slice_depth)\
                .grid(row=2,column=1,sticky=N+E)

        Label(f2, text=(_("%s mill depth [mm]:") %config.ax3_letter))\
                .grid(row=3,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=self.axis3_mill_depth)\
                .grid(row=3,column=1,sticky=N+E)

        Label(f3, text=(_("G1 feed %s-direction [mm/min]:") %config.ax3_letter))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        Entry(f3,width=7,textvariable=self.F_G1_Depth)\
                .grid(row=1,column=1,sticky=N+E)

        Label(f3, text=(_("G1 feed %s%s-direction [mm/min]:") %(config.ax1_letter,config.ax2_letter)))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        Entry(f3,width=7,textvariable=self.F_G1_Plane)\
                .grid(row=2,column=1,sticky=N+E)


class NotebookClass:    
    # initialization. receives the master widget
    # reference and the notebook orientation
    def __init__(self, master,width=0,height=0):

        self.active_fr = None
        self.count = 0
        self.choice = IntVar(0)

        self.dummy_x_fr = Frame(master, width=width, borderwidth=0)
        self.dummy_y_fr = Frame(master, height=height, borderwidth=0)
        self.dummy_x_fr.grid(row=0,column=1)
        self.dummy_x_fr.grid_propagate(0)
        self.dummy_y_fr.grid(row=1,rowspan=2,column=0)
        self.dummy_y_fr.grid_propagate(0)

        # creates notebook's frames structure
        self.rb_fr = Frame(master, borderwidth=0)
        self.rb_fr.grid(row=1,column=1, sticky=N+W)
        
        self.screen_fr = Frame(master, borderwidth=2, relief=RIDGE)
        self.screen_fr.grid(row=2,column=1,sticky=N+W+E)
        
        master.rowconfigure(2,weight=1)
        master.columnconfigure(1,weight=1)

    # return a master frame reference for the external frames (screens)
    def __call__(self):
        return self.screen_fr

    # add a new frame (screen) to the (bottom/left of the) notebook
    def add_screen(self, fr, title):

        b = Radiobutton(self.rb_fr,bd=1, text=title, indicatoron=0, \
                        variable=self.choice, value=self.count, \
                        command=lambda: self.display(fr))
        
        b.grid(column=self.count,row=0,sticky=N+E+W)
        self.rb_fr.columnconfigure(self.count,weight=1)

        fr.grid(sticky=N+W+E)
        self.screen_fr.columnconfigure(0,weight=1)
        fr.grid_remove()

        # ensures the first frame will be
        # the first selected/enabled
        if not self.active_fr:
            fr.grid()
            self.active_fr = fr

        self.count += 1

        # returns a reference to the newly created
        # radiobutton (allowing its configuration/destruction)
        return b


        # hides the former active frame and shows 
        # another one, keeping its reference
    def display(self, fr):
        self.active_fr.grid_remove()
        fr.grid()
        self.active_fr = fr
                  
               
class LayerContentClass:
    def __init__(self,type='Layer',LayerNr=None,LayerName='',Shapes=[], MyMessages=[]):
        self.type=type
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.Shapes=Shapes
         
        self.folder=os.path.join(PROGRAMDIRECTORY,'layerconfig')
        
        # eine ConfigParser Instanz oeffnen
        self.parser = ConfigParser.ConfigParser()
        self.layer_content_file_name='LayerContent_%s.cfg' %self.LayerName
        
        # Lesen der Config Datei falls vorhanden
        self.parser.read(os.path.join(self.folder,self.layer_content_file_name))
        
        # Überprüfung ob vorhanden sonst neu erstellen
        if len(self.parser.sections())==0:
            self.MakeNewLayerContentFile()
            self.parser.read(os.path.join(self.folder,self.layer_content_file_name))
            MyMessages.prt((_('\nNo LayerContent file found generated new on at: %s') \
                             %os.path.join(self.folder,self.layer_content_file_name)))
        else:
            MyMessages.prt((_('\nLoading LayerContent file:%s') \
                             %os.path.join(self.folder,self.layer_content_file_name)))

        #Tkinter Variablen erstellen zur späteren Verwendung in den Eingabefeldern        
        self.GetAllVars()


    def MakeNewLayerContentFile(self):
        self.tool_dia=2.0
        self.start_rad=0.2
        self.axis3_safe_margin=15
        self.axis3_slice_depth=-1.5
        self.axis3_mill_depth=-3
        self.F_G1_Depth=150
        self.F_G1_Plane=400
        
        self.parser.add_section('Tool Parameters') 
        self.parser.add_section('Depth Coordinates') 
        self.parser.add_section('Feed Rates')
        
        self.MakeSettingFolder()
        self.SaveLayerContentFile()
        
    def MakeSettingFolder(self): 
        # create settings folder if necessary 
        try: 
            os.mkdir(self.folder) 
        except OSError: 
            pass     
    
    def SaveLayerContentFile(self):
        self.parser.set('Tool Parameters', 'diameter', self.tool_dia)
        self.parser.set('Tool Parameters', 'start_radius', self.start_rad)

        self.parser.set('Depth Coordinates', 'axis3_safe_margin', self.axis3_safe_margin)
        self.parser.set('Depth Coordinates', 'axis3_mill_depth', self.axis3_mill_depth)
        self.parser.set('Depth Coordinates', 'axis3_slice_depth', self.axis3_slice_depth)

        self.parser.set('Feed Rates', 'f_g1_depth', self.F_G1_Depth)
        self.parser.set('Feed Rates', 'f_g1_plane', self.F_G1_Plane)
                                          
        open_file = open(os.path.join(self.folder,self.layer_content_file_name), "w") 
        self.parser.write(open_file) 
        open_file.close()
            
    def GetAllVars(self):
        try: 
            self.tool_dia=(float(self.parser.get('Tool Parameters','diameter')))
            self.start_rad=(float(self.parser.get('Tool Parameters','start_radius')))      
               
            self.axis3_safe_margin=(float(self.parser.get('Depth Coordinates','axis3_safe_margin')))
            self.axis3_slice_depth=(float(self.parser.get('Depth Coordinates','axis3_slice_depth')))        
            self.axis3_mill_depth=(float(self.parser.get('Depth Coordinates','axis3_mill_depth')))        
             
            self.F_G1_Depth=(float(self.parser.get('Feed Rates','f_g1_depth')))
            self.F_G1_Plane=(float(self.parser.get('Feed Rates','f_g1_plane')))

        except:
#            dial=wx.MessageDialog(None, _("Please delete or correct\n %s")\
#                      %(os.path.join(self.folder,self.cfg_file_name)),_("Error during reading config file"), wx.OK | 
#            wx.ICON_ERROR)
#            dial.ShowModal()

            raise Exception, _("Problem during import from INI File") 
            
        
    def __cmp__(self, other):
         return cmp(self.LayerNr, other.LayerNr)

    def __str__(self):
        return ('\ntype:        %s' %self.type) +\
               ('\nLayerNr :      %i' %self.LayerNr) +\
               ('\nLayerName:     %s' %self.LayerName)+\
               ('\ntool_dia:     %s' %self.tool_dia)+\
               ('\nstart_rad:     %s' %self.start_rad)+\
               ('\naxis3_safe_margin:     %s' %self.axis3_safe_margin)+\
               ('\naxis3_slice_depth:     %s' %self.axis3_slice_depth)+\
               ('\naxis3_mill_depth:     %s' %self.axis3_mill_depth)+\
               ('\nF_G1_Depth:     %s' %self.F_G1_Depth)+\
               ('\nF_G1_Plane:     %s' %self.F_G1_Plane)+\
               ('\nShapes:    %s' %self.Shapes)