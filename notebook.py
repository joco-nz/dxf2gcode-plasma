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

from Tkconstants import END, ALL, N, S, E, W, RIDGE, GROOVE, FLAT, DISABLED, NORMAL, ACTIVE, LEFT, RIGHT, VERTICAL, Y, BOTH, EXTENDED
from tkMessageBox import showwarning, showerror
from Tkinter import Tk, IntVar, DoubleVar, Canvas, Menu, Frame, Radiobutton, Label, Entry, Text, Scrollbar, Toplevel,Button
from Tkinter import DoubleVar, IntVar, Listbox
from widgets import Notebook

class MyNotebookClass(Notebook):
    def __init__(self,master=None,config=None,postpro=None,LayerContents=None):
        Notebook.__init__(self,master,width=240)
    
        self.nb_f1 = Frame(self())
        
        self.LayerContents=LayerContents
        
        self.ExportParas=ExportParasClass(self.nb_f1,config)
        
        self.LayerListbox=LayerListboxClass(self.nb_f1,self)
        self.LayerListbox.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        self.LayerListbox.scrollbar.grid(row=0,column=1,padx=2,pady=2,sticky=N+W+E+S)
        #self.nb_f2 = Frame(self.nb())

        self.add_screen(self.nb_f1, _("Layers"))
        #self.nb.add_screen(self.nb_f2, _("File Beg. & End"))

        #self.nb_f1.columnconfigure(0,weight=1)
        #self.nb_f2.columnconfigure(0,weight=1)        


    def CreateLayerContent(self,LayerContents):
        self.LayerListbox.CreateLayerContent(LayerContents)
        self.ExportParas.LayerContents=LayerContents
        
    def change_selection(self,sel_shapes):
        self.CanvasContent.deselect()
        self.CanvasContent.change_selection(sel_shapes)
        
class ExportParasClass:
    def __init__(self,frame=None,config=None,postpro=None):
        self.frame=frame

        self.initialise_textvariables()
        self.generate_entryfields(config)
        
        #self.change_entry_state(NORMAL)

    def initialise_textvariables(self):
        self.tool_dia=DoubleVar()
        self.tool_dia.set(0.0)
        
        self.start_rad=DoubleVar()
        self.start_rad.set(0.0)        
       
        self.axis3_retract=DoubleVar()
        self.axis3_retract.set(0.0)
        
        self.axis3_safe_margin=DoubleVar()
        self.axis3_safe_margin.set(0.0)

        self.axis3_slice_depth=DoubleVar()
        self.axis3_slice_depth.set(0.0)        

        self.axis3_mill_depth=DoubleVar()
        self.axis3_mill_depth.set(0.0)        
        
        self.F_G1_Depth=DoubleVar()
        self.F_G1_Depth.set(0.0)

        self.F_G1_Plane=DoubleVar()
        self.F_G1_Plane.set(0.0)

    def generate_entryfields(self,config):
        self.entries=[]
       
        f1=Frame(self.frame,relief = GROOVE,bd = 2)
        f1.grid(row=1,column=0,padx=2,pady=2,sticky=N+W+E)
        f2=Frame(self.frame,relief = GROOVE,bd = 2)
        f2.grid(row=2,column=0,padx=2,pady=2,sticky=N+W+E)
        f3=Frame(self.frame,relief = GROOVE,bd = 2)
        f3.grid(row=3,column=0,padx=2,pady=2,sticky=N+W+E)
    
        f1.columnconfigure(0,weight=1)
        f2.columnconfigure(0,weight=1)
        f3.columnconfigure(0,weight=1)        
   
        Label(f1, text=_("Tool diameter [mm]:"))\
                .grid(row=0,column=0,sticky=N+W,padx=4)
        self.entries.append(Entry(f1,width=7,textvariable=self.tool_dia,state=DISABLED))
        self.entries[-1].grid(row=0,column=1,sticky=N+E)


        Label(f1, text=_("Start radius (for tool comp.) [mm]:"))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        self.entries.append(Entry(f1,width=7,textvariable=self.start_rad,state=DISABLED))
        self.entries[-1].grid(row=1,column=1,sticky=N+E) 

        Label(f2, text=(_("%s safety margin [mm]:") %config.ax3_letter))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        self.entries.append(Entry(f2,width=7,textvariable=self.axis3_safe_margin,state=DISABLED))
        self.entries[-1].grid(row=1,column=1,sticky=N+E)

        Label(f2, text=(_("%s infeed depth [mm]:") %config.ax3_letter))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        self.entries.append(Entry(f2,width=7,textvariable=self.axis3_slice_depth,state=DISABLED))
        self.entries[-1].grid(row=2,column=1,sticky=N+E)

        Label(f2, text=(_("%s mill depth [mm]:") %config.ax3_letter))\
                .grid(row=3,column=0,sticky=N+W,padx=4)
        self.entries.append(Entry(f2,width=7,textvariable=self.axis3_mill_depth,state=DISABLED))
        self.entries[-1].grid(row=3,column=1,sticky=N+E)

        Label(f3, text=(_("G1 feed %s-direction [mm/min]:") %config.ax3_letter))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        self.entries.append(Entry(f3,width=7,textvariable=self.F_G1_Depth,state=DISABLED))
        self.entries[-1].grid(row=1,column=1,sticky=N+E)

        Label(f3, text=(_("G1 feed %s%s-direction [mm/min]:") %(config.ax1_letter,config.ax2_letter)))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        self.entries.append(Entry(f3,width=7,textvariable=self.F_G1_Plane,state=DISABLED))
        self.entries[-1].grid(row=2,column=1,sticky=N+E)

    def change_entry_state(self,new_state):
        for entry in self.entries:
            entry.config(state=new_state)
            
    def ShowParas(self,LayerContent):
        print 'Kommt noch'
             
class LayerListboxClass(Listbox):
    def __init__(self,master=None,MyNotebook=None):
        Listbox.__init__(self,master)
        
        self.MyNotebook=MyNotebook
        
        self.current = None
        
        self.scrollbar = Scrollbar(master, orient=VERTICAL)
        self.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.yview)
        #self.scrollbar.pack(side=RIGHT, fill=Y)
        #self.pack(side=LEFT, fill=BOTH, expand=1)
        self.bind("<<ListboxSelect>> ",self.list_clicked)
        self.LayerContents=[]
        
    def CreateLayerContent(self,LayerContents):
        self.LayerContents=LayerContents
        self.delete(0, END)
        
        for LayerContent in LayerContents:
            self.insert(END,('Layer Nr: %i, %s' 
                                    %(LayerContent.LayerNr, LayerContent.LayerName)))
    
    def list_clicked(self, event):
        now = self.curselection()
        if now != self.current:
            self.changed_selection()
            self.current = now

    def changed_selection(self):
        print "selection is", self.curselection()
        
        #Wenn nichts ausgewählt ist die Edit Felder ausschalten.
        if len(self.curselection())==0:
            self.MyNotebook.ExportParas.change_entry_state(state=DISABLED)
        #Sonst Werte anzeigen
        else:
            sel=int(self.curselection()[0])
            self.MyNotebook.ExportParas.ShowParas(self.LayerContents[sel])
            self.MyNotebook.change_selection(self.LayerContents[sel].Shapes)
        
        
class LayerContentClass:
    def __init__(self,type='Layer',LayerNr=None,LayerName='',Shapes=[], MyMessages=[]):
        self.type=type
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.Shapes=Shapes
         
        self.folder=os.path.join(PROGRAMDIRECTORY,'layerconfig')
        
        # open a ConfigParser Instance
        self.parser = ConfigParser.ConfigParser()
        self.layer_content_file_name='LayerContent_%s.cfg' %self.LayerName
        
        # Read the config file 
        self.parser.read(os.path.join(self.folder,self.layer_content_file_name))
        
        # check if it already exists 
        if len(self.parser.sections())==0:
            self.MakeNewLayerContentFile()
            self.parser.read(os.path.join(self.folder,self.layer_content_file_name))
            MyMessages.prt((_('\nNo LayerContent file found generated new on at: %s') \
                             %os.path.join(self.folder,self.layer_content_file_name)))
        else:
            MyMessages.prt((_('\nLoading LayerContent file:%s') \
                             %os.path.join(self.folder,self.layer_content_file_name)))

        #Read the variables from the existing layer config file  
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