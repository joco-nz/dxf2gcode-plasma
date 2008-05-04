#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b01.py
#Programmer: Christian Kohloeffel
#E-mail:     n/A
#
#Copyright 2007-2008 Christian Kohlöffel
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
#Compiled with --onefile --noconsole --upx --tk dxf2gcode_b01.py

#Löschen aller Module aus dem Speicher
import sys
if globals().has_key('init_modules'):
	for m in [x for x in sys.modules.keys() if x not in init_modules]:
		del(sys.modules[m]) 
else:
	init_modules = sys.modules.keys()


import sys, os, string, ConfigParser 
from   dxf2gcode_b01_point import PointClass
import dxf2gcode_b01_dxf_import as dxf_import 
import dxf2gcode_b01_tsp_opt as tsp

import webbrowser
from Tkconstants import END, INSERT, ALL, N, S, E, W, RAISED, RIDGE, GROOVE, FLAT, DISABLED, NORMAL, ACTIVE, LEFT
from tkMessageBox import showwarning, showerror
from Tkinter import Tk, Canvas, Menu, Frame, Grid, DoubleVar, IntVar, Radiobutton, Label, Entry, Text, Scrollbar, Toplevel,Button
from tkFileDialog import askopenfile, asksaveasfilename
from tkSimpleDialog import askfloat
from Canvas import Rectangle, Line, Oval, Arc

from math import radians, cos, sin

#reload(dxf_import)
#reload(tsp)

# Globale "Konstanten"
DEBUG = 0
APPNAME = "dxf2gcode_b01"

class Erstelle_Fenster:
    def __init__(self, master = None, load_filename=None ):

        #Uebergabe des load_filenames falls von EMC gestartet
        self.load_filename=load_filename
        
        self.master=master

        #Linker Rahmen erstellen, in welchen später die Eingabefelder kommen       
        self.frame_l=Frame(master) 
        self.frame_l.grid(row=0,column=0,rowspan=2,padx=4,pady=4,sticky=N+E+W)
        
        #Erstellen des Canvas Rahmens
        self.frame_c=Frame(master,relief = RIDGE,bd = 2)
        self.frame_c.grid(row=0,column=1,padx=4,pady=4,sticky=N+E+S+W)
        
        #Unterer Rahmen erstellen mit der Lisbox + Scrollbar zur Darstellung der Ereignisse.
        self.frame_u=Frame(master) 
        self.frame_u.grid(row=1,column=1,padx=4,sticky=N+E+W+S)
        
        self.master.columnconfigure(0,weight=0)
        self.master.columnconfigure(1,weight=1)
        self.master.rowconfigure(0,weight=1)
        self.master.rowconfigure(1,weight=0)
            
        self.text = Text(self.frame_u,height=7)
        self.textscr = Scrollbar(self.frame_u)
        self.text.grid(row=0,column=0,pady=4,sticky=E+W)
        self.textscr.grid(row=0,column=1,pady=4,sticky=N+S)
        self.frame_u.columnconfigure(0,weight=1)
        self.frame_u.columnconfigure(1,weight=0)

        #Binding für Contextmenu
        self.text.bind("<Button-3>", self.text_contextmenu)

        self.textscr.config(command=self.text.yview)
        self.text.config(yscrollcommand=self.textscr.set)
        self.text.insert(END,'Program started\nVersion 0.1\nCoded by C. Kohlöffel')
        

        #Einstellungen für das Programm
        self.config=ConfigClass(self.text)

        if DEBUG>0:
            self.text.config(height=15)
        self.points_tol=float(self.config.parser.get('Import Parameters','point_tolerance'))    

        #Erstellen de Eingabefelder und des Canvas. 
        self.ExportParas =ExportParasClass(self.frame_l,self.config)
        self.Canvas =CanvasClass(self.frame_c,self)

        #Erstellen der Canvas Content Klasse & Bezug in Canvas Klasse
        self.CanvasContent=CanvasContentClass(self.Canvas,self.text)
        self.Canvas.Content=self.CanvasContent

        #Erstellen des Fenster Menus
        self.erstelle_menu()        
        
        #Falls ein load_filename_uebergeben wurde
        if not(self.load_filename==None):
            #Zuerst alle ausstehenden Events und Callbacks ausführen (sonst klappts beim Laden nicht)
            self.Canvas.canvas.update()
            self.Load_File(self.load_filename)

    def erstelle_menu(self): 
        self.menu = Menu(self.master)
        self.master.config(menu=self.menu)

        self.filemenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="Read DXF", command=self.Get_Load_File)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.ende)

        self.exportmenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="Export", menu=self.exportmenu)
        self.exportmenu.add_command(label="Write G-Code", command=self.Write_GCode)
        #Disabled bis was gelesen wurde
        self.exportmenu.entryconfig(0,state=DISABLED)

        self.viewmenu=Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="View",menu=self.viewmenu)
        self.viewmenu.add_checkbutton(label="Show workpiece zero",\
                                      variable=self.CanvasContent.toggle_wp_zero,\
                                      command=self.CanvasContent.plot_wp_zero)
        self.viewmenu.add_checkbutton(label="Show all path directions",\
                                      variable=self.CanvasContent.toggle_start_stop,\
                                      command=self.CanvasContent.plot_start_end)
        self.viewmenu.add_checkbutton(label="Show disabled shapes",\
                                      variable=self.CanvasContent.toggle_show_disabled,\
                                      command=self.CanvasContent.show_disabled)
            
        self.viewmenu.add_separator()
        self.viewmenu.add_command(label='Autoscale',command=self.Canvas.autoscale)

        #Menupunkt einfügen zum löschen der Route
        self.viewmenu.add_separator()
        self.viewmenu.add_command(label='Delete Route',command=self.del_route_and_menuentry)         

        #Disabled bis was gelesen wurde
        self.viewmenu.entryconfig(0,state=DISABLED)
        self.viewmenu.entryconfig(1,state=DISABLED)
        self.viewmenu.entryconfig(2,state=DISABLED)
        self.viewmenu.entryconfig(4,state=DISABLED)
        self.viewmenu.entryconfig(6,state=DISABLED)

        self.optionmenu=Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="Options",menu=self.optionmenu)
        self.optionmenu.add_command(label="Set contour tolerance", command=self.Get_Cont_Tol)
        self.optionmenu.add_separator()
        self.optionmenu.add_command(label="Scale contours", command=self.Get_Cont_Scale)
        self.optionmenu.add_command(label="Move workpiece zero", command=self.Move_WP_zero)
        self.optionmenu.entryconfig(2,state=DISABLED)
        self.optionmenu.entryconfig(3,state=DISABLED)
        
        
        self.helpmenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label="Help", menu=self.helpmenu)
        self.helpmenu.add_command(label="About...", command=self.Show_About)

    # Callback des Menu Punkts File Laden
    def Get_Load_File(self):
        #Auswahl des zu ladenden Files
        myFormats = [('AutoCAD / QCAD Drawing','*.dxf'),\
        ('All File','*.*') ]
        inidir=self.config.parser.get('Paths','load_path')
        filename = askopenfile(initialdir=inidir,\
                               filetypes=myFormats)
        if not filename:
            return
        else:
            self.load_filename=filename.name
            
        self.Load_File(self.load_filename)

    def Load_File(self,filename):
   
        self.text.delete(4.0,END)
        self.text.insert(END,'\nLoading file: '+filename)
        self.text.yview(END)
        
        self.values=dxf_import.Load_DXF(filename,self.points_tol,DEBUG,self.text)
        #self.values=Load_DXF(filename,self.points_tol,DEBUG,self.text)
        
        #Ausgabe der Informationen im Text Fenster
        self.text.insert(END,'\nLoaded layers: ' +str(len(self.values.layers)))
        self.text.insert(END,'\nLoaded blocks: ' +str(len(self.values.blocks.Entities)))
        for i in range(len(self.values.blocks.Entities)):
            layers=self.values.blocks.Entities[i].get_used_layers()
            self.text.insert(END,'\nBlock ' +str(i) +' includes '+str(len(self.values.blocks.Entities[i].geo))\
                             +' Geometries, reduced to ' +str(len(self.values.blocks.Entities[i].cont)) \
                             +' Contours, used layers: ' +str(layers))
        layers=self.values.entities.get_used_layers()
        insert_nr=self.values.entities.get_insert_nr()
        self.text.insert(END,'\nLoaded ' +str(len(self.values.entities.geo))\
                             +' Entities geometries, reduced to ' +str(len(self.values.entities.cont))\
                             +' Contours, used layers: ' +str(layers)\
                             +' ,Number of inserts: ' +str(insert_nr))
        self.text.yview(END)

        #Skalierung der Kontur
        self.cont_scale=1.0
        
        #Verschiebung der Kontur
        self.cont_dx=0.0
        self.cont_dy=0.0

        #Disabled bis was gelesen wurde
        self.viewmenu.entryconfig(0,state=NORMAL)
        self.viewmenu.entryconfig(1,state=NORMAL)
        self.viewmenu.entryconfig(2,state=NORMAL)
        self.viewmenu.entryconfig(4,state=NORMAL)

        #Disabled bis was gelesen wurde
        self.exportmenu.entryconfig(0,state=NORMAL)

        #Disabled bis was gelesen wurde
        self.optionmenu.entryconfig(2,state=NORMAL)
        self.optionmenu.entryconfig(3,state=NORMAL)        

        #Ausdrucken der Werte        
        self.CanvasContent.makeplot(self.values)

        #Löschen alter Route Menues
        self.del_route_and_menuentry()
            
    def Get_Cont_Tol(self):
        value=askfloat('Contour Tolerance','Set the tolerance for common points',\
                                initialvalue=self.points_tol)
        #Abfrage ob Cancel gedrückt wurde
        if value==None:
            return
        
        self.points_tol=value

        #Falls noch kein File geladen wurde nichts machen
        if self.load_filename==None:
            return
        self.Load_File(self.load_filename)
        
        self.text.insert(END,("\nSet new contour tolerance %0.3f, reloaded file" %value))
        self.text.yview(END)
    def Get_Cont_Scale(self):
        #Abspeichern der alten Werte
        old_scale=self.cont_scale
                
        value=askfloat('Scale Contours','Set the scale factor',\
                                initialvalue=self.cont_scale)
        #Abfrage ob Cancel gedrückt wurde
        if value==None:
            return
        
        self.cont_scale=value

        #Falls noch kein File geladen wurde nichts machen
        self.text.insert(END,("\nScaled Contours by factor %0.3f" %self.cont_scale))
        self.text.yview(END)

        self.Canvas.scale_contours(self.cont_scale/old_scale)        
        
    def Move_WP_zero(self):
        #Achsenbelegung für den Export
        axis1,axis2,axis3=self.config.get_axis_names()

        #Abspeichern der alten Werte        
        old_dx=self.cont_dx
        old_dy=self.cont_dy
        
        dialog=Get_WP_Offset_Dialog(self.master,axis1,axis2,self.cont_dx,self.cont_dy)
        
        if dialog.dx==None:
            return

        self.cont_dx=dialog.dx
        self.cont_dy=dialog.dy

        #Falls noch kein File geladen wurde nichts machen
        self.text.insert(END,("\nWorpiece zero offset: %s %0.2f; %s %0.2f" \
                              %(axis1,self.cont_dx,axis2,self.cont_dy)))
        self.text.yview(END)

        #Verschieben des Canvas WP zero
        self.Canvas.move_wp_zero(self.cont_dx-old_dx,self.cont_dy-old_dy)

    def Get_Save_File(self):

        #Abbruch falls noch kein File geladen wurde.
        if self.load_filename==None:
            showwarning("Export G-Code", "Nothing to export!")
            return
        
        #Auswahl des zu ladenden Files
        myFormats = [('G-Code for EMC2','*.ngc'),\
        ('All File','*.*') ]

        (beg, ende)=os.path.split(self.load_filename)
        (fileBaseName, fileExtension)=os.path.splitext(ende)

        inidir=self.config.parser.get('Paths','save_path')
        self.save_filename = asksaveasfilename(initialdir=inidir,\
                               initialfile=fileBaseName +'.ngc',filetypes=myFormats)

    # Callback des Menu Punkts Exportieren
    def Write_GCode(self):

        #Funktion zum optimieren des Wegs aufrufen
        self.opt_export_route()

        #Initial Status für den Export
        status=1

        #Achsenbelegung für den Export
        axis1,axis2,axis3=self.config.get_axis_names()
      
        #Daten aus den beiden Textfeldern in strings speichern        
        s_begin=self.ExportParas.gcode_be.get(1.0,END)
        s_end=self.ExportParas.gcode_en.get(1.0,END)
        paras=self.ExportParas

        #Schreiben in einen String
        str="(Generated with dxf2code)\n(Created from file: "+self.load_filename+")\n"
        string=(str.encode("utf-8"))
        string+=self.config.parser.get('Plane Selection', 'gcode')
        string+=" (Plane Selection from Ini File)\n"
        string+=(s_begin.strip()+"\n")

        #Maschine auf die Anfangshöhe bringen
        string+=("G0 %s%0.3f\n" %(axis3,paras.Axis3_retract.get()))

        #Bei 1 starten da 0 der Startpunkt ist
        #print self.TSP.opt_route[0]
        for nr in range(1,len(self.TSP.opt_route)):
            shape=self.shapes_to_write[self.TSP.opt_route[nr]]
            if DEBUG:
                self.text.insert(END,("\nWriting Shape: %s" %shape))
                self.text.yview(END)

            #Drucken falls die Shape nicht disabled ist
            if not(shape.nr in self.CanvasContent.Disabled):
                #Falls sich die Fräserkorrektur verändert hat diese in File schreiben
                stat, string =shape.Write_GCode(string,paras,axis1,axis2,axis3)
                status=status*stat

        #Maschine auf den Endwert positinieren
        string+=("G0 %s%0.3f \n" %(axis3,paras.Axis3_retract.get()))
        string+=("G0 %s%0.3f %s%0.3f\n" \
                %(axis1,paras.Axis1_st_en.get(),axis2,paras.Axis2_st_en.get()))

        string+=(s_end.strip()+"\n")

        if status==1:
            self.text.insert(END,("\nSuccessfully generated G-Code"))
        else:
            self.text.insert(END,("\nError during G-Code Generation"))
            
        self.text.yview(END)        
        
        #Drucken in den Stdout, speziell für EMC2 
        if int(self.config.parser.get('Export Parameters','write_to_stdout')):
            print(string)
            self.ende()     
        else:
            #Exportieren der Daten
                try:
                    #Abfrage des Namens um das File zu speichern
                    self.Get_Save_File()
                    
                    #Wenn Cancel gedrückt wurde
                    if not self.save_filename:
                        return
                    
                    #Das File öffnen und schreiben    
                    f = open(self.save_filename, "w")
                    f.write(string)
                    f.close()    
                      
                except IOError:
                    showwarning("Save As", "Cannot save the file.")
            

    def opt_export_route(self):
                
        #Anfangswerte für das Sortieren der Shapes
        self.shapes_to_write=[]
        shapes_st_en_points=[]
        
        #Alle Shapes die geschrieben werden zusammenfassen
        for shape_nr in range(len(self.CanvasContent.Shapes)):
            shape=self.CanvasContent.Shapes[shape_nr]
            if not(shape.nr in self.CanvasContent.Disabled):
                self.shapes_to_write.append(shape)
                shapes_st_en_points.append(shape.get_st_en_points())

        #Hinzufügen des Start- Endpunkte ausserhalb der Geometrie
        x_st=self.ExportParas.Axis1_st_en.get()
        y_st=self.ExportParas.Axis2_st_en.get()
        start=PointClass(x=x_st,y=y_st)
        ende=PointClass(x=x_st,y=y_st)
        shapes_st_en_points.append([start,ende])

        #Optimieren der Reihenfolge            
        self.TSP=tsp.TSPoptimize(shapes_st_en_points,self.text,DEBUG)

        for it_nr in range(20):
            self.TSP.start_optimisation()
            for hdl in self.CanvasContent.path_hdls:
                self.Canvas.canvas.delete(hdl)
            self.CanvasContent.path_hdls=[]
            self.CanvasContent.plot_opt_route(shapes_st_en_points,self.TSP.opt_route)
            
        self.text.insert(END,("\n%s" %self.TSP))
        self.text.yview(END)

        self.viewmenu.entryconfig(6,state=NORMAL)        

    def del_route_and_menuentry(self):
        try:
            self.viewmenu.entryconfig(6,state=DISABLED)
            self.CanvasContent.delete_opt_path()
        except:
            pass
        
    def Show_About(self):
        Show_About_Info(self.master)
  

    #Contextmenu Text mit Bindings beim Rechtsklick
    def text_contextmenu(self,event):

        #Contextmenu erstellen zu der Geometrie        
        popup = Menu(self.text,tearoff=0)        
        popup.add_command(label='Delete text entries',command=self.text_delete_entries)
        popup.post(event.x_root, event.y_root)
        
    def text_delete_entries(self):
        self.text.delete(4.0,END)
        self.text.yview(END)   
  
    def ende(self):
        self.master.destroy()
        self.master.quit()

class ExportParasClass:
    def __init__(self,master=None,config=None):
        self.master=master
        try:
            self.tool_dia=DoubleVar()
            self.tool_dia.set(float(config.parser.get('Tool Parameters','diameter')))

            self.start_rad=DoubleVar()
            self.start_rad.set(float(config.parser.get('Tool Parameters','start_radius')))        
           
            self.Axis1_st_en=DoubleVar()
            self.Axis1_st_en.set(float(config.parser.get('Plane Coordinates','axis1_start_end')))

            self.Axis2_st_en=DoubleVar()
            self.Axis2_st_en.set(float(config.parser.get('Plane Coordinates','axis2_start_end')))        
            
            self.Axis3_retract=DoubleVar()
            self.Axis3_retract.set(float(config.parser.get('Depth Coordinates','axis3_retract')))
            
            self.Axis3_safe_margin=DoubleVar()
            self.Axis3_safe_margin.set(float(config.parser.get('Depth Coordinates','axis3_safe_margin')))

            self.Axis3_slice_depth=DoubleVar()
            self.Axis3_slice_depth.set(float(config.parser.get('Depth Coordinates','axis3_slice_depth')))        

            self.Axis3_mill_depth=DoubleVar()
            self.Axis3_mill_depth.set(float(config.parser.get('Depth Coordinates','axis3_mill_depth')))        
            
            self.F_G1_Depth=DoubleVar()
            self.F_G1_Depth.set(float(config.parser.get('Feed Rates','f_g1_depth')))

            self.F_G1_Plane=DoubleVar()
            self.F_G1_Plane.set(float(config.parser.get('Feed Rates','f_g1_plane')))

            self.nb = NotebookClass(self.master,width=240)

            # uses the notebook's frame
            self.nb_f1 = Frame(self.nb())
            self.nb_f2 = Frame(self.nb())

            # keeps the reference to the radiobutton (optional)
            self.nb.add_screen(self.nb_f1, "Coordinates")
            self.nb.add_screen(self.nb_f2, "File Beg. & End")

            self.nb_f1.columnconfigure(0,weight=1)
            self.nb_f2.columnconfigure(0,weight=1)        
        
            self.erstelle_eingabefelder(config)
            self.erstelle_textfelder()

            self.gcode_be.insert(END,config.parser.get('Standard Code','begin'))
            self.gcode_en.insert(END,config.parser.get('Standard Code','end'))
        except:
            showerror("Error during reading INI File", "Please delete or correct\n %s"\
                      %(os.path.join(config.folder,config.cfg_file_name)))
            raise Exception, "Problem during import from INI File" 

    def erstelle_eingabefelder(self,config):
        #Funktion zum erhalten der Achsen Namen aus der Config Klasse
        axis1,axis2,axis3=config.get_axis_names()
       
        f1=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f1.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        f2=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f2.grid(row=1,column=0,padx=2,pady=2,sticky=N+W+E)
        f3=Frame(self.nb_f1,relief = GROOVE,bd = 2)
        f3.grid(row=2,column=0,padx=2,pady=2,sticky=N+W+E)
    
        f1.columnconfigure(0,weight=1)
        f2.columnconfigure(0,weight=1)
        f3.columnconfigure(0,weight=1)        
   
        Label(f1, text="Tool diameter [mm]:")\
                .grid(row=0,column=0,sticky=N+W,padx=4)
        Entry(f1,width=7,textvariable=self.tool_dia)\
                .grid(row=0,column=1,sticky=N+E)

        Label(f1, text="Start radius (for tool comp.) [mm]:")\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        Entry(f1,width=7,textvariable=self.start_rad)\
                .grid(row=1,column=1,sticky=N+E)        

        Label(f2, text=("Start at %s [mm]:" %axis1))\
                .grid(row=0,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=self.Axis1_st_en)\
                .grid(row=0,column=1,sticky=N+E)

        Label(f2, text=("Start at %s [mm]:" %axis2))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=self.Axis2_st_en)\
                .grid(row=1,column=1,sticky=N+E)

        Label(f2, text=("%s retraction area [mm]:" %axis3))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=self.Axis3_retract)\
                .grid(row=2,column=1,sticky=N+E)

        Label(f2, text=("%s safety margin [mm]:" %axis3))\
                .grid(row=3,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=self.Axis3_safe_margin)\
                .grid(row=3,column=1,sticky=N+E)

        Label(f2, text=("%s infeed depth [mm]:" %axis3))\
                .grid(row=4,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=self.Axis3_slice_depth)\
                .grid(row=4,column=1,sticky=N+E)

        Label(f2, text=("%s mill depth [mm]:" %axis3))\
                .grid(row=5,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=self.Axis3_mill_depth)\
                .grid(row=5,column=1,sticky=N+E)

        Label(f3, text=("G1 feed %s-direction [mm/min]:" %axis3))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        Entry(f3,width=7,textvariable=self.F_G1_Depth)\
                .grid(row=1,column=1,sticky=N+E)

        Label(f3, text=("G1 feed %s%s-direction [mm/min]:" %(axis1,axis2)))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        Entry(f3,width=7,textvariable=self.F_G1_Plane)\
                .grid(row=2,column=1,sticky=N+E)

    def erstelle_textfelder(self):
        f22=Frame(self.nb_f2,relief = FLAT,bd = 1)
        f22.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        f22.columnconfigure(0,weight=1)        

        Label(f22 , text="G-Code at the begin of file")\
                .grid(row=0,column=0,columnspan=2,sticky=N+W,padx=2)
        self.gcode_be = Text(f22,width=10,height=8)
        self.gcode_be_sc = Scrollbar(f22)
        self.gcode_be.grid(row=1,column=0,pady=2,sticky=E+W)
        self.gcode_be_sc.grid(row=1,column=1,padx=2,pady=2,sticky=N+S)
        self.gcode_be_sc.config(command=self.gcode_be.yview)
        self.gcode_be.config(yscrollcommand=self.gcode_be_sc.set)

        Label(f22, text="G-Code at the end of file")\
                .grid(row=2,column=0,columnspan=2,sticky=N+W,padx=2)
        self.gcode_en = Text(f22,width=10,height=5)
        self.gcode_en_sc = Scrollbar(f22)
        self.gcode_en.grid(row=3,column=0,pady=2,sticky=E+W)
        self.gcode_en_sc.grid(row=3,column=1,padx=2,pady=2,sticky=N+S)
        self.gcode_en_sc.config(command=self.gcode_en.yview)
        self.gcode_en.config(yscrollcommand=self.gcode_en_sc.set)

        f22.columnconfigure(0,weight=1)
        f22.rowconfigure(1,weight=0)
        f22.rowconfigure(3,weight=0)
         
#Klasse zum Erstellen des Plots
class CanvasClass:
    def __init__(self, master = None,text=None):
        
        #Übergabe der Funktionswerte
        self.master=master
        self.Content=[]

        #Erstellen der Standardwerte
        self.lastevent=[]
        self.sel_rect_hdl=[]
        self.dir_var = IntVar()
        self.dx=0.0
        self.dy=0.0
        self.scale=1.0

        #Wird momentan nicht benötigt, eventuell für Beschreibung von Aktionen im Textfeld #self.text=text

        #Erstellen des Labels am Unteren Rand für Status Leiste        
        self.label=Label(self.master, text="Curser Coordinates: X=0.0, Y=0.0, Scale: 1.00",bg="white",anchor="w")
        self.label.grid(row=1,column=0,sticky=E+W)

        #Canvas Erstellen und Fenster ausfüllen        
        self.canvas=Canvas(self.master,width=650,height=500, bg = "white")
        self.canvas.grid(row=0,column=0,sticky=N+E+S+W)
        self.master.columnconfigure(0,weight=1)
        self.master.rowconfigure(0,weight=1)


        #Binding für die Bewegung des Mousezeigers
        self.canvas.bind("<Motion>", self.moving)

        #Bindings für Selektieren
        self.canvas.bind("<Button-1>", self.select_cont)
        
        #Eventuell mit Abfrage probieren???????????????????????????????????????????
        self.canvas.bind("<Shift-Button-1>", self.multiselect_cont)
        self.canvas.bind("<B1-Motion>", self.select_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.select_release)

        #Binding für Contextmenu
        self.canvas.bind("<Button-3>", self.make_contextmenu)

        #Bindings für Zoom und Bewegen des Bilds        
        self.canvas.bind("<Control-Button-1>", self.mouse_move)
        self.canvas.bind("<Control-B1-Motion>", self.mouse_move_motion)
        self.canvas.bind("<Control-ButtonRelease-1>", self.mouse_move_release)
        self.canvas.bind("<Control-Button-3>", self.mouse_zoom)
        self.canvas.bind("<Control-B3-Motion>", self.mouse_zoom_motion)
        self.canvas.bind("<Control-ButtonRelease-3>", self.mouse_zoom_release)   

    #Callback für das Bewegen der Mouse mit Darstellung in untere Leiste
    def moving(self,event):
        x=self.dx+(event.x/self.scale)
        y=self.dy+(self.canvas.winfo_height()-event.y)/self.scale

        if self.scale<1:
            self.label['text']=("Curser Coordinates: X= %5.0f Y= %5.0f , Scale: %5.3f" \
                                %(x,y,self.scale))
            
        elif (self.scale>=1)and(self.scale<10):      
            self.label['text']=("Curser Coordinates: X= %5.1f Y= %5.1f , Scale: %5.2f" \
                                %(x,y,self.scale))
        elif self.scale>=10:      
            self.label['text']=("Curser Coordinates: X= %5.2f Y= %5.2f , Scale: %5.1f" \
                                %(x,y,self.scale))
        
    #Callback für das Auswählen von Elementen
    def select_cont(self,event):
        #Abfrage ob ein Contextfenster offen ist, speziell für Linux
        self.schliesse_contextmenu()
        
        self.moving(event)
        self.Content.deselect()
        self.sel_rect_hdl=Rectangle(self.canvas,event.x,event.y,event.x,event.y,outline="grey") 
        self.lastevent=event

    def multiselect_cont(self,event):
        #Abfrage ob ein Contextfenster offen ist, speziell für Linux
        self.schliesse_contextmenu()
        
        self.sel_rect_hdl=Rectangle(self.canvas,event.x,event.y,event.x,event.y,outline="grey") 
        self.lastevent=event

    def select_rectangle(self,event):
        self.moving(event)
        self.canvas.coords(self.sel_rect_hdl,self.lastevent.x,self.lastevent.y,\
                           event.x,event.y)

    def select_release(self,event):
 
        dx=self.lastevent.x-event.x
        dy=self.lastevent.y-event.y
        self.canvas.delete(self.sel_rect_hdl)
        
        #Beim Auswählen sollen die Direction Pfeile gelöscht werden!!!!!!!!!!!!!!!!!!        
        #self.Content.delete_opt_path()   
        
        #Wenn mehr als 6 Pixel gezogen wurde Enclosed        
        if (abs(dx)+abs(dy))>6:
            items=self.canvas.find_overlapping(event.x,event.y,event.x+dx,event.y+dy)
            mode='multi'
        else:
            #items=self.canvas.find_closest(event.x, event.y)
            items=self.canvas.find_overlapping(event.x-3,event.y-3,event.x+3,event.y+3)
            mode='single'
            
        self.Content.addselection(items,mode)

    #Callback für Bewegung des Bildes
    def mouse_move(self,event):
        self.master.config(cursor="fleur")
        self.lastevent=event

    def mouse_move_motion(self,event):
        self.moving(event)
        dx=event.x-self.lastevent.x
        dy=event.y-self.lastevent.y
        self.dx=self.dx-dx/self.scale
        self.dy=self.dy+dy/self.scale
        self.canvas.move(ALL,dx,dy)
        self.lastevent=event

    def mouse_move_release(self,event):
        self.master.config(cursor="")      

    #Callback für das Zoomen des Bildes     
    def mouse_zoom(self,event):
        self.canvas.focus_set()
        self.master.config(cursor="sizing")
        self.firstevent=event
        self.lastevent=event

    def mouse_zoom_motion(self,event):
        self.moving(event)
        dy=self.lastevent.y-event.y
        sca=(1+(dy*3)/float(self.canvas.winfo_height()))
       
        self.dx=(self.firstevent.x+((-self.dx*self.scale)-self.firstevent.x)*sca)/sca/-self.scale
        eventy=self.canvas.winfo_height()-self.firstevent.y
        self.dy=(eventy+((-self.dy*self.scale)-eventy)*sca)/sca/-self.scale
        
        self.scale=self.scale*sca
        self.canvas.scale( ALL, self.firstevent.x,self.firstevent.y,sca,sca)
        self.lastevent=event

        self.Content.plot_start_end() 
        self.Content.plot_wp_zero()

    def mouse_zoom_release(self,event):
        self.master.config(cursor="")
                
    #Contextmenu mit Bindings beim Rechtsklick
    def make_contextmenu(self,event):
        self.lastevent=event

        #Abfrage ob das Contextfenster schon existiert, speziell für Linux
        self.schliesse_contextmenu()
            
        #Contextmenu erstellen zu der Geometrie        
        popup = Menu(self.canvas,tearoff=0)
        self.popup=popup
        popup.add_command(label='Invert Selection',command=self.Content.invert_selection)
        popup.add_command(label='Disable Selection',command=self.Content.disable_selection)
        popup.add_command(label='Enable Selection',command=self.Content.enable_selection)

        popup.add_separator()
        popup.add_command(label='Switch Direction',command=self.Content.switch_shape_dir)
        
        #Untermenu für die Fräserkorrektur
        self.dir_var.set(self.Content.calc_dir_var())
        cut_cor_menu = Menu(popup,tearoff=0)
        cut_cor_menu.add_checkbutton(label="G40 No correction",\
                                     variable=self.dir_var,onvalue=0,\
                                     command=lambda:self.Content.set_cut_cor(40))
        cut_cor_menu.add_checkbutton(label="G41 Cutting left",\
                                     variable=self.dir_var,onvalue=1,\
                                     command=lambda:self.Content.set_cut_cor(41))
        cut_cor_menu.add_checkbutton(label="G42 Cutting right",\
                                     variable=self.dir_var,onvalue=2,\
                                     command=lambda:self.Content.set_cut_cor(42))
        popup.add_cascade(label='Set Cutter Correction',menu=cut_cor_menu)

        #Menus Disablen wenn nicht ausgewählt wurde        
        if len(self.Content.Selected)==0:
            popup.entryconfig(0,state=DISABLED)
            popup.entryconfig(1,state=DISABLED)
            popup.entryconfig(2,state=DISABLED)
            popup.entryconfig(4,state=DISABLED)
            popup.entryconfig(5,state=DISABLED)

        popup.post(event.x_root, event.y_root)
        
    #Speziell für Linux falls das Contextmenu offen ist dann schliessen
    def schliesse_contextmenu(self):
        try:
            self.popup.destroy()
            del(self.popup)
        except:
            pass

    def autoscale(self):

        #Rand der um die Extreme des Elemente dargestellt wird        
        rand=20

        #Alles auf die 0 Koordinaten verschieben, dass später DX und DY Berechnung richtig erfolgt       
        self.canvas.move(ALL,self.dx*self.scale,-self.canvas.winfo_height()-self.dy*self.scale)
        self.dx=0;
        self.dy=-self.canvas.winfo_height()/self.scale

        #Umriss aller Elemente
        d=self.canvas.bbox(ALL)
        cx=(d[0]+d[2])/2
        cy=(d[1]+d[3])/2
        dx=d[2]-d[0]
        dy=d[3]-d[1]

        #Skalierung des Canvas errechnen
        xs=float(dx)/(self.canvas.winfo_width()-rand)
        ys=float(dy)/(self.canvas.winfo_height()-rand)
        scale=1/max(xs,ys)
        
        #Skalieren der Elemente        
        self.canvas.scale( ALL,0,0,scale,scale)
        self.scale=self.scale*scale

        #Verschieben der Elemente zum Mittelpunkt        
        dx=self.canvas.winfo_width()/2-cx*scale
        dy=self.canvas.winfo_height()/2-cy*scale
        self.dy=self.dy/scale
        self.dx=self.dx/scale
        self.canvas.move(ALL,dx,dy)
        
        #Mouse Position errechnen
        self.dx=self.dx-dx/self.scale
        self.dy=self.dy+dy/self.scale

        self.Content.plot_start_end()
        self.Content.plot_wp_zero()
        
    def get_can_coordinates(self,x_st,y_st):
        x_ca=(x_st-self.dx)*self.scale
        y_ca=(y_st-self.dy)*self.scale-self.canvas.winfo_height()
        return x_ca, y_ca

    def scale_contours(self,delta_scale):     
        self.scale=self.scale/delta_scale
        self.dx=self.dx*delta_scale
        self.dy=self.dy*delta_scale

        #Schreiben der neuen WErte simulierne auf Curser Punkt 0, 0
        event=PointClass(x=0,y=0)
        self.moving(event)

        #Skalieren der Shapes
        for shape in self.Content.Shapes:
            shape.sca[0]=shape.sca[0]*delta_scale
            shape.sca[1]=shape.sca[1]*delta_scale
            shape.sca[2]=shape.sca[2]*delta_scale
            
            shape.p0=shape.p0*[delta_scale,delta_scale]

    def move_wp_zero(self,delta_dx,delta_dy):
        self.dx=self.dx-delta_dx
        self.dy=self.dy-delta_dy

        self.Content.plot_start_end() 
        self.Content.plot_wp_zero()

        #Schreiben der neuen WErte simulierne auf Curser Punkt 0, 0
        event=PointClass(x=0,y=0)
        self.moving(event)

        #Verschieben der Shapes
        for shape in self.Content.Shapes:
            shape.po.x=shape.p0.x-delta_dx
            shape.p0.y=shape.p0.y-delta_dy
        
#Klasse mit den Inhalten des Canvas & Verbindung zu den Konturen
class CanvasContentClass:
    def __init__(self,Canvas,text):
        self.Canvas=Canvas
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitieContents=[]
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]
        #self.show_dis=0
        self.text=text

        #Anfangswert für das Ansicht Toggle Menu
        self.toggle_wp_zero=IntVar()
        self.toggle_wp_zero.set(1)

        self.toggle_start_stop=IntVar()
        self.toggle_start_stop.set(0)

        self.toggle_show_disabled=IntVar()
        self.toggle_show_disabled.set(0)  
        
    def __str__(self):
        s='\nNr. of Shapes ->'+str(len(self.Shapes))
        for lay in self.LayerContents:
            s=s+'\n'+str(lay)
        for ent in self.EntitieContents:
            s=s+'\n'+str(ent)
        s=s+'\nSelected ->'+str(self.Selected)\
           +'\nDisabled ->'+str(self.Disabled)
        return s

    def calc_dir_var(self):
        if len(self.Selected)==0:
            return -1
        dir=self.Shapes[self.Selected[0]].cut_cor
        for shape_nr in self.Selected[1:len(self.Selected)]: 
            if not(dir==self.Shapes[shape_nr].cut_cor):
                return -1   
        return dir-40
            
    #Erstellen des Gesamten Ausdrucks      
    def makeplot(self,values):
        self.values=values

        #Löschen des Inhalts
        self.Canvas.canvas.delete(ALL)
        
        #Standardwerte für scale, dx, dy zuweisen
        self.Canvas.scale=1
        self.Canvas.dx=0
        self.Canvas.dy=-self.Canvas.canvas.winfo_height()

        #Zurücksetzen der Konturen
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitieContents=[]
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]

        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        self.plot_entities()
        self.LayerContents.sort()
        self.EntitieContents.sort()

        #Autoscale des Canvas        
        self.Canvas.autoscale()

    #Drucken des Werkstücknullpunkts
    def plot_wp_zero(self):
        for hdl in self.wp_zero_hdls:
            self.Canvas.canvas.delete(hdl) 
        self.wp_zero_hdls=[]
        if self.toggle_wp_zero.get(): 
            x_zero,y_zero=self.Canvas.get_can_coordinates(0,0)
            xy=x_zero-8,-y_zero-8,x_zero+8,-y_zero+8
            hdl=Oval(self.Canvas.canvas,xy,outline="gray")
            self.wp_zero_hdls.append(hdl)

            xy=x_zero-6,-y_zero-6,x_zero+6,-y_zero+6
            hdl=Arc(self.Canvas.canvas,xy,start=0,extent=180,style="pieslice",outline="gray")
            self.wp_zero_hdls.append(hdl)
            hdl=Arc(self.Canvas.canvas,xy,start=90,extent=180,style="pieslice",outline="gray")
            self.wp_zero_hdls.append(hdl)
            hdl=Arc(self.Canvas.canvas,xy,start=270,extent=90,style="pieslice",outline="gray",fill="gray")
            self.wp_zero_hdls.append(hdl)

    def plot_start_end(self):
        for hdl in self.dir_hdls:
            self.Canvas.canvas.delete(hdl) 
        self.dir_hdls=[]

        if not(self.toggle_start_stop.get()):
            draw_list=self.Selected[:]
        else:
            draw_list=range(len(self.Shapes))
               
        for shape_nr in draw_list:
            if not(shape_nr in self.Disabled):
                self.dir_hdls.append(self.Shapes[shape_nr].plot_start(self.Canvas))
                self.dir_hdls.append(self.Shapes[shape_nr].plot_end(self.Canvas))
                
                if self.Shapes[shape_nr].cut_cor>40:
                    self.dir_hdls.append(self.Shapes[shape_nr].plot_cut_cor(self.Canvas))
                        
    def plot_entities(self,ent_nr=-1,p0=PointClass(x=0,y=0),sca=[1,1,1]):
            
        #Zuweisen der richtigen Entities für das Ploten
        if ent_nr==-1:
            entities=self.values.entities
        else:
            entities=self.values.blocks.Entities[ent_nr]
        
        #Zuweisen der Geometrien in die Variable geos & Konturen in cont
        geos=entities.geo
        cont=entities.cont
        
        #Schleife für die Anzahl der Konturen 
        for c_nr in range(len(cont)):
            #Abfrage falls es sich bei der Kontur um ein Insert eines Blocks handelt
            if geos[cont[c_nr].order[0][0]].Typ=="Insert":
                geo=geos[cont[c_nr].order[0][0]]
                self.plot_entities(geo.Block,geo.Point,geo.Scale)
                
            else:
                #Schleife für die Anzahl der Geometrien
                self.Shapes.append(ShapeClass(len(self.Shapes),ent_nr,c_nr,cont[c_nr].closed,p0,sca[:],40,[],[],[]))

                for geo_nr in range(len(cont[c_nr].order)):
                    geo=geos[cont[c_nr].order[geo_nr][0]]
                    geo_hdl=geo.plot2can(self.Canvas.canvas,p0,sca,self.Shapes[-1].nr)
                    self.Shapes[-1].geos.append(geo)
                    self.Shapes[-1].geos_dir.append(cont[c_nr].order[geo_nr][1])
                    self.Shapes[-1].geos_hdls.append(geo_hdl)
                    
                self.addtoLayerContents(self.Shapes[-1].nr,geo.Layer_Nr)
                self.addtoEntitieContents(self.Shapes[-1].nr,ent_nr,c_nr)

        self.plot_wp_zero()


    def plot_opt_route(self,shapes_st_en_points,route):
        #Ausdrucken der optimierten Route        
        for en_nr in range(len(route)):
            if en_nr==0:
                st_nr=-1
                col='gray'
            elif en_nr==1:
                st_nr=en_nr-1
                col='gray'
            else:
                st_nr=en_nr-1
                col='peru'
                
            st=shapes_st_en_points[route[st_nr]][1]
            en=shapes_st_en_points[route[en_nr]][0]

            x_ca_s,y_ca_s=self.Canvas.get_can_coordinates(st.x,st.y)
            x_ca_e,y_ca_e=self.Canvas.get_can_coordinates(en.x,en.y)

            self.path_hdls.append(Line(self.Canvas.canvas,x_ca_s,-y_ca_s,x_ca_e,-y_ca_e,fill=col,arrow='last'))
        self.Canvas.canvas.update()
    #Hinzufügen der Kontur zum Layer        
    def addtoLayerContents(self,shape_nr,lay_nr):
        #Abfrage of der gesuchte Layer schon existiert
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.Shapes.append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen      
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr,LayerName,[shape_nr]))
        
    #Hinzufügen der Kontur zu den Entities
    def addtoEntitieContents(self,shape_nr,ent_nr,c_nr):
        
        for EntCon in self.EntitieContents:
            if EntCon.EntNr==ent_nr:
                if c_nr==0:
                    EntCon.Shapes.append([])
                
                EntCon.Shapes[-1].append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen
        if ent_nr==-1:
            EntName='Entities'
        else:
            EntName=self.values.blocks.Entities[ent_nr].Name
            
        self.EntitieContents.append(EntitieContentClass(ent_nr,EntName,[[shape_nr]]))

    def delete_opt_path(self):
        for hdl in self.path_hdls:
            self.Canvas.canvas.delete(hdl)
            
        self.path_hdls=[]
        
    def deselect(self): 
        self.set_shapes_color(self.Selected,'deselected')
        
        if not(self.toggle_start_stop.get()):
            for hdl in self.dir_hdls:
                self.Canvas.canvas.delete(hdl) 
            self.dir_hdls=[]
        
    def addselection(self,items,mode):
        for item in items:
            try:
                tag=int(self.Canvas.canvas.gettags(item)[-1])
                if not(tag in self.Selected):
                    self.Selected.append(tag)

                    if DEBUG:
                        self.text.insert(END,'\n\nAdded shape to selection:'\
                                         +str(self.Shapes[tag]))
                        self.text.yview(END)
                    if mode=='single':
                        break
            except:
                pass
            
        self.plot_start_end()
        self.set_shapes_color(self.Selected,'selected')
 
    def invert_selection(self):
        new_sel=[]
        for shape_nr in range(len(self.Shapes)):
            if (not(shape_nr in self.Disabled)) & (not(shape_nr in self.Selected)):
                new_sel.append(shape_nr)

        self.deselect()
        self.Selected=new_sel
        self.set_shapes_color(self.Selected,'selected')
        self.plot_start_end()

        if DEBUG:
            self.text.insert(END,'\nInverting Selection')
            self.text.yview(END)        
        

    def disable_selection(self):
        for shape_nr in self.Selected:
            if not(shape_nr in self.Disabled):
                self.Disabled.append(shape_nr)
        self.set_shapes_color(self.Selected,'disabled')
        self.Selected=[]
        self.plot_start_end()

    def enable_selection(self):
        for shape_nr in self.Selected:
            if shape_nr in self.Disabled:
                nr=self.Disabled.index(shape_nr)
                del(self.Disabled[nr])
        self.set_shapes_color(self.Selected,'deselected')
        self.Selected=[]
        self.plot_start_end()

    def show_disabled(self):
        if (self.toggle_show_disabled.get()==1):
            self.set_hdls_normal(self.Disabled)
            self.show_dis=1
        else:
            self.set_hdls_hidden(self.Disabled)
            self.show_dis=0

    def switch_shape_dir(self):
        for shape_nr in self.Selected:
            self.Shapes[shape_nr].reverse()
            if DEBUG:
                self.text.insert(END,'\n\nSwitched Direction at Shape:'\
                                 +str(self.Shapes[shape_nr]))
                self.text.yview(END)
        self.plot_start_end()
        
    def set_cut_cor(self,correction):
        for shape_nr in self.Selected: 
            self.Shapes[shape_nr].cut_cor=correction
            if DEBUG:
                self.text.insert(END,'\n\nChanged Cutter Correction at Shape:'\
                                 +str(self.Shapes[shape_nr]))
                self.text.yview(END)       
        self.plot_start_end() 
        
    def set_shapes_color(self,shape_nrs,state):
        s_shape_nrs=[]
        d_shape_nrs=[]
        for shape in shape_nrs:
            if not(shape in self.Disabled):
                s_shape_nrs.append(shape)
            else:
                d_shape_nrs.append(shape)
        
        s_hdls=self.get_shape_hdls(s_shape_nrs)
        d_hdls=self.get_shape_hdls(d_shape_nrs)
    
        if state=='deselected':
            s_color='black'
            d_color='gray'
            self.Selected=[]
        elif state=='selected':
            s_color='red'
            d_color='blue'
        elif state=='disabled':
            s_color='gray'
            d_color='gray'
            
        self.set_color(s_hdls,s_color)
        self.set_color(d_hdls,d_color)

        if (self.toggle_show_disabled.get()==0):
            self.set_hdls_hidden(d_shape_nrs)
        
    def set_color(self,hdls,color):
        for hdl in hdls:
            if (self.Canvas.canvas.type(hdl)=="arc") | (self.Canvas.canvas.type(hdl)=="oval") :
                self.Canvas.canvas.itemconfig(hdl, outline=color)
            else:
                self.Canvas.canvas.itemconfig(hdl, fill=color)

    def set_hdls_hidden(self,shape_nrs):
        hdls=self.get_shape_hdls(shape_nrs)
        for hdl in hdls:
            self.Canvas.canvas.itemconfig(hdl,state='hidden')

    def set_hdls_normal(self,shape_nrs):
        hdls=self.get_shape_hdls(shape_nrs)
        for hdl in hdls:
            self.Canvas.canvas.itemconfig(hdl,state='normal')            
        
    def get_shape_hdls(self,shape_nrs):        
        hdls=[]
        for s_nr in shape_nrs:
            if type(self.Shapes[s_nr].geos_hdls[0]) is list:
                for subcont in self.Shapes[s_nr].geos_hdls:
                    hdls=hdls+subcont
            else:
                hdls=hdls+self.Shapes[s_nr].geos_hdls
        return hdls      
                                       
class ShapeClass:
    def __init__(self,nr='None',ent_nr='None',ent_cnr='None',closed=0,\
                 p0=PointClass(x=0,y=0),sca=[],cut_cor=40,geos=[],geos_dir=[],geos_hdls=[]):
        self.nr=nr
        self.ent_nr=ent_nr
        self.ent_cnr=ent_cnr
        self.closed=closed
        self.p0=p0
        self.sca=sca
        self.cut_cor=40
        self.geos=geos
        self.geos_dir=geos_dir
        self.geos_hdls=geos_hdls
        
    def __str__(self):

        s='\nnr ->'+str(self.nr)+'\nent_nr ->'+str(self.ent_nr)\
               +'\nent_cnr ->'+str(self.ent_cnr)+'\nclosed ->'+str(self.closed)\
               +'\np0 ->'+str(self.p0)\
               +'\nsca ->'+str(self.sca)+'\ncut_cor ->'+str(self.cut_cor)\
               +'\ngeos ->'+str(self.geos)\
               +'\ngeos_dir ->'+str(self.geos_dir)+'\ngeo_hdls ->'+str(self.geos_hdls)
        if DEBUG>3:
            for geo_nr in range(len(self.geos)):
                s=s+'\n\nShape geometrie Nr:'+str(geo_nr)+str(self.geos[geo_nr])

        return s
        

    def reverse(self):
        self.geos.reverse()
        self.geos_dir.reverse()
        for geo_nr in range(len(self.geos_dir)):
            if self.geos_dir[geo_nr]==0:
                self.geos_dir[geo_nr]=1
            else:
                self.geos_dir[geo_nr]=0

    def switch_cut_cor(self):
        if self.cut_cor==41:
            self.cut_cor=42
        elif self.cut_cor==42:
            self.cut_cor=41

    def get_st_en_points(self):
        st_point, st_angle=self.geos[0].get_start_end_points(self.geos_dir[0])
        start=(st_point*self.sca)+self.p0
        
        en_point, en_angle=self.geos[-1].get_start_end_points(not(self.geos_dir[-1]))
        ende=en_point*self.sca+self.p0
        return [start,ende]
          
    def plot_start(self,CanvasClass):
        st_point, st_angle=self.geos[0].get_start_end_points(self.geos_dir[0])
        start=(st_point*self.sca)+self.p0
        
        x_ca,y_ca=CanvasClass.get_can_coordinates(start.x,start.y)
        length=20
        dx=cos(radians(st_angle))*length
        dy=sin(radians(st_angle))*length

        hdl=Line(CanvasClass.canvas,x_ca,-y_ca,x_ca+dx,-y_ca-dy,fill='SteelBlue3',arrow='last')
        return hdl

    def plot_cut_cor(self,CanvasClass):
        st_point, st_angle=self.geos[0].get_start_end_points(self.geos_dir[0])
        start=(st_point*self.sca)+self.p0
        x_ca,y_ca=CanvasClass.get_can_coordinates(start.x,start.y)
        length=20
        
        if self.cut_cor==41:
            st_angle=st_angle+90
        else:
            st_angle=st_angle-90
            
        dx=cos(radians(st_angle))*length
        dy=sin(radians(st_angle))*length

        hdl=Line(CanvasClass.canvas,x_ca,-y_ca,x_ca+dx,-y_ca-dy,fill='SteelBlue3',arrow='last')
        return hdl

    def plot_end(self,CanvasClass):
        en_point, en_angle=self.geos[-1].get_start_end_points(not(self.geos_dir[-1]))
        ende=(en_point*self.sca)+self.p0
        
        x_ca,y_ca=CanvasClass.get_can_coordinates(ende.x,ende.y)
        length=20
        dx=cos(radians(en_angle))*length
        dy=sin(radians(en_angle))*length

        hdl=Line(CanvasClass.canvas,x_ca,-y_ca,x_ca+dx,-y_ca-dy,fill='PaleGreen2',arrow='first')
        return hdl
    
    def Write_GCode(self,string,paras,axis1,axis2,axis3):

        #Einlaufradius und Versatz 
        start_rad=paras.start_rad.get()
        start_ver=start_rad

        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=paras.tool_dia.get()/2
        
        depth=paras.Axis3_mill_depth.get()
        max_slice=paras.Axis3_slice_depth.get()

        #Scheibchendicke bei Frästiefe auf Frästiefe begrenzen
        if -abs(max_slice)<=depth:
            mom_depth=depth
        else:
            mom_depth=-abs(max_slice)

        #Errechnen des Startpunkts mit und ohne Werkzeug Kompensation        
        st_point, st_angle=self.geos[0].get_start_end_points(self.geos_dir[0])
        start_cont=(st_point*self.sca)+self.p0
        
        if self.cut_cor==40:              
            #Positionieren des Werkzeugs über dem Anfang und Eintauchen
            string+=("G0 %s%0.3f %s%0.3f\n" %(axis1,start_cont.x,axis2,start_cont.y))
            string+=("G0 %s%0.3f \n" %(axis3,paras.Axis3_safe_margin.get()))
            string+=("F%0.0f\n" %paras.F_G1_Depth.get())
            string+=("G1 %s%0.3f \n" %(axis3,mom_depth))
            string+=("F%0.0f\n" %paras.F_G1_Plane.get())

        #Fräsradiuskorrektur Links        
        elif self.cut_cor==41:

            #Mittelpunkts für Einlaufradius
            Oein=start_cont.get_arc_point(st_angle+90,start_rad+tool_rad)
            #Startpunkts für Einlaufradius
            Pa_ein=Oein.get_arc_point(st_angle+180,start_rad+tool_rad)
            IJ=Oein-Pa_ein
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(st_angle+90,start_ver)
            #Eintauchpunkts
            start_ein=Pg_ein.get_arc_point(st_angle,tool_rad)

##            print("start_cont: %s; st_angle: %0.3f" %(start_cont,st_angle))
##            print Oein
##            print Pa_ein
##            print IJ
##            print Pg_ein
##            print start_ein

            #Positionieren des Werkzeugs über dem Anfang und Eintauchen
            string+=("G0 %s%0.3f %s%0.3f\n" %(axis1,start_ein.x,axis2,start_ein.y))
            string+=("G0 %s%0.3f \n" %(axis3,paras.Axis3_safe_margin.get()))
            string+=("F%0.0f\n" %paras.F_G1_Depth.get())
            string+=("G1 %s%0.3f \n" %(axis3,mom_depth))
            string+=("F%0.0f\n" %paras.F_G1_Plane.get())
            string+=("G41 \n")
            string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,Pa_ein.x,axis2,Pa_ein.y))
            string+=("G3 %s%0.3f %s%0.3f I%0.3f J%0.3f \n" %(axis1,start_cont.x,axis2,start_cont.y,IJ.x,IJ.y))
            

         
        #Fräsradiuskorrektur Rechts        
        elif self.cut_cor==42:

            #Mittelpunkts für Einlaufradius
            Oein=start_cont.get_arc_point(st_angle-90,start_rad+tool_rad)
            #Startpunkts für Einlaufradius
            Pa_ein=Oein.get_arc_point(st_angle+180,start_rad+tool_rad)
            IJ=Oein-Pa_ein
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(st_angle-90,start_ver)
            #Eintauchpunkts
            start_ein=Pg_ein.get_arc_point(st_angle,tool_rad)

##            print("start_cont: %s; st_angle: %0.3f" %(start_cont,st_angle))
##            print Oein
##            print Pa_ein
##            print IJ
##            print Pg_ein
##            print start_ein

            #Positionieren des Werkzeugs über dem Anfang und Eintauchen
            string+=("G0 %s%0.3f %s%0.3f\n" %(axis1,start_ein.x,axis2,start_ein.y))
            string+=("G0 %s%0.3f \n" %(axis3,paras.Axis3_safe_margin.get()))
            string+=("F%0.0f\n" %paras.F_G1_Depth.get())
            string+=("G1 %s%0.3f \n" %(axis3,mom_depth))
            string+=("F%0.0f\n" %paras.F_G1_Plane.get())
            string+=("G41 \n")
            string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,Pa_ein.x,axis2,Pa_ein.y))
            string+=("G2 %s%0.3f %s%0.3f I%0.3f J%0.3f \n" %(axis1,start_cont.x,axis2,start_cont.y,IJ.x,IJ.y))
            
            
        #Schreiben der Geometrien für den ersten Schnitt
        for geo_nr in range(len(self.geos)):
            string=self.geos[geo_nr].Write_GCode(string,paras,\
                                                 self.sca,self.p0,\
                                                 self.geos_dir[geo_nr],\
                                                 axis1,axis2)

        #Schleifen für die Anzahl der Schnitte
        #Anfangswert für Direction merken
        anfang=self.geos_dir[0]
        while mom_depth>depth:
            mom_depth=mom_depth-abs(max_slice)
            if mom_depth<depth:
                mom_depth=depth                

            #Erneutes Eintauchen
            string+=("F%0.0f\n" %paras.F_G1_Depth.get())
            string+=("G1 %s%0.3f \n" %(axis3,mom_depth))
            string+=("F%0.0f\n" %paras.F_G1_Plane.get())

            #Falls es keine geschlossene Kontur ist    
            if self.closed==0:
                self.reverse()
                self.switch_cut_cor()
                
                #Falls cut correction eingeschaltet ist diese umdrehen.
                if not(self.cut_cor==40):
                    string+=("G"+str(self.cut_cor)+" \n")
                
            for geo_nr in range(len(self.geos)):
                string=self.geos[geo_nr].Write_GCode(string,paras,\
                                                     self.sca,self.p0,\
                                                     self.geos_dir[geo_nr],\
                                                     axis1,axis2)

        #Anfangswert für Direction wieder herstellen falls nötig
        if not(anfang==self.geos_dir[0]):
            self.reverse()
            self.switch_cut_cor()

        #Fertig und Zurückziehen des Werkzeugs
        string+=("G1 %s%0.3f \n" %(axis3,paras.Axis3_safe_margin.get()))
        string+=("G0 %s%0.3f \n" %(axis3,paras.Axis3_retract.get()))
        string+=("G40\n")

        return 1, string        

class ConfigClass:
    def __init__(self,text):
        # Das Standard App Verzeichniss für das Betriebssystem abfragen
        self.folder=self.get_settings_folder(str(APPNAME))

        # eine ConfigParser Instanz öffnen und evt. vorhandenes Config File Laden        
        self.parser = ConfigParser.ConfigParser()
        self.cfg_file_name=APPNAME+'.cfg'
        self.parser.read(os.path.join(self.folder,self.cfg_file_name))

        text.insert(END,'\nLoading config file: ' +str(os.path.join(self.folder,self.cfg_file_name)))
        text.yview(END)        

        # Falls kein Config File vorhanden ist oder File leer ist neue File anlegen
        if len(self.parser.sections())==0:

            self.parser.add_section('Paths') 
            self.parser.set('Paths', 'load_path', 'C:\Users\Christian Kohlöffel\Documents\Python\dxfs')
            self.parser.set('Paths', 'save_path', 'C:\Users\Christian Kohlöffel\Documents\Python')

            self.parser.add_section('Import Parameters') 
            self.parser.set('Import Parameters', 'point_tolerance', 0.01)

            self.parser.add_section('Export Parameters')
            self.parser.set('Export Parameters', 'write_to_stdout', 0)               
            
            self.parser.add_section('Tool Parameters') 
            self.parser.set('Tool Parameters', 'diameter', 2.0)
            self.parser.set('Tool Parameters', 'start_radius', 0.2)

            self.parser.add_section('Plane Selection') 
            self.parser.set('Plane Selection', 'gcode', 'G17')

            self.parser.add_section('Plane Coordinates') 
            self.parser.set('Plane Coordinates', 'axis1_start_end', 0)
            self.parser.set('Plane Coordinates', 'axis2_start_end', 0)

            self.parser.add_section('Depth Coordinates') 
            self.parser.set('Depth Coordinates', 'axis3_retract', 15)
            self.parser.set('Depth Coordinates', 'axis3_safe_margin', 3.0)
            self.parser.set('Depth Coordinates', 'axis3_mill_depth', -3.0)
            self.parser.set('Depth Coordinates', 'axis3_slice_depth', -1.5)

            self.parser.add_section('Feed Rates')
            self.parser.set('Feed Rates', 'f_g1_depth', 150)
            self.parser.set('Feed Rates', 'f_g1_plane', 400)

            self.parser.add_section('Standard Code')
            self.parser.set('Standard Code', 'begin',\
                            'G21 (Unit in mm) \nG90 (Absolute distance mode)'\
                            +'\nG61 P0.01 (Exact Path 0.001 tol.)'\
                            +'\nG40 (Cancel diameter comp.) \nG49 (Cancel length comp.)'\
                            +'\nT1M6 (Tool change to T1)\nM8 (Coolant flood on)'\
                            +'\nS5000M03 (Spindle 5000rpm cw)')
            
            self.parser.set('Standard Code', 'end','M9 (Coolant off)\nM5 (Spindle off)\nM2 (Prgram end)')    

            self.parser.add_section('Debug')
            self.parser.set('Debug', 'global_debug_level', 0)         
                    
            open_file = open(os.path.join(self.folder,self.cfg_file_name), "w") 
            self.parser.write(open_file) 
            open_file.close()
            self.parser.read(os.path.join(self.folder,self.cfg_file_name))
            text.insert(END,'\nNo config file found generated new on at: ' +str(os.path.join(self.folder,self.cfg_file_name)))
            text.yview(END)

        try:
            if int(self.parser.get('Debug', 'global_debug_level'))>0:
                global DEBUG
                DEBUG=int(self.parser.get('Debug', 'global_debug_level'))
                text.insert(END,'\nDebug Level: ' +str(DEBUG))
                text.yview(END)

            #Initialisieren der Ebenen Koordinaten
            plane_selection=self.parser.get('Plane Selection', 'gcode')
            if plane_selection=='G17':
                self.axis1='X'
                self.axis2='Y'
                self.axis3='Z'
            elif plane_selection=='G18':
                self.axis1='X'
                self.axis2='Z'
                self.axis3='Y'
            elif plane_selection=='G19':
                self.axis1='Y'
                self.axis2='Z'
                self.axis3='X'
            else:
                text.insert(END,'\nFAILURE UNKNOWN PLANE SELECTED ')
                text.yview(END)

            if DEBUG:
                text.insert(END,'\n' +str(self))
                text.yview(END)
        except:
            showerror("Error during reading INI File", "Please delete or correct\n %s" \
                      %os.path.join(self.folder,self.cfg_file_name))
            raise Exception, "Problem during import from INI File " 
    #Die drei Achsen Namen zurück geben
    def get_axis_names(self):
        return self.axis1, self.axis2, self.axis3

    def get_settings_folder(self,appname): 
        # resolve settings folder 
        if os.name == 'posix': 
            folder = os.path.join(os.environ.get('HOME'), "." + appname.lower()) 
        elif os.name == 'nt': 
            folder = os.path.join(os.environ.get('APPDATA'), appname.capitalize()) 
        else: 
            folder = os.path.join(os.getcwd(), appname) 

        # create settings folder if necessary 
        try: 
            os.mkdir(folder) 
        except OSError: 
            pass 

        return folder 

    def __str__(self):

        str=''
        for section in self.parser.sections(): 
            str= str +"\nSection: "+section 
            for option in self.parser.options(section): 
                str= str+ "\n   -> %s=%s" % (option, self.parser.get(section, option))
        return str

class Get_WP_Offset_Dialog(Toplevel):
    def __init__(self, parent,axis1,axis2,cont_dx,cont_dy):
        self.dx_var=DoubleVar()
        self.dx_var.set(cont_dx)
        self.dy_var=DoubleVar()
        self.dy_var.set(cont_dy)

        Toplevel.__init__(self, parent)
        self.transient(parent)

        self.title("Get workpiece zero offsets")
        self.parent = parent
        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body,axis1,axis2)
        body.pack(padx=5, pady=5)

        self.buttonbox()
        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()
        self.wait_window(self)

    def buttonbox(self):
        
        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def ok(self, event=None):   
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def body(self, master,axis1,axis2):
        self.dx=None
        self.dy=None

        Label(master, text=("Offset %s axis by mm:" %axis1)).grid(row=0,padx=4)
        Label(master, text=("Offset %s axis by mm:" %axis2)).grid(row=1,padx=4)

        self.dx_entry = Entry(master,textvariable=self.dx_var)
        self.dy_entry = Entry(master,textvariable=self.dy_var)

        self.dx_entry.grid(row=0, column=1,padx=4)
        self.dy_entry.grid(row=1, column=1,padx=4)

    def apply(self):
        self.dx = self.dx_var.get()
        self.dy = self.dy_var.get()

class Show_About_Info(Toplevel):
    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.transient(parent)

        self.title("About DXF2GCODE")
        self.parent = parent
        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()
        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()
        self.wait_window(self)

    def buttonbox(self):
        box = Frame(self)
        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(padx=5, pady=5)
        self.bind("<Return>", self.ok)
        box.pack()

    def ok(self, event=None):   
        self.withdraw()
        self.update_idletasks()
        self.close()

    def close(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def show_hand_cursor(self,event):
        event.widget.configure(cursor="hand1")
    def show_arrow_cursor(self,event):
        event.widget.configure(cursor="")
        
    def click(self,event):
        w = event.widget
        x, y = event.x, event.y
        tags = w.tag_names("@%d,%d" % (x, y))
        for t in tags:
            if t.startswith("href:"):
                webbrowser.open(t[5:])
                break


    def body(self, master):
        text = Text(master,width=40,height=8)
        text.pack()
        # configure text tag
        text.tag_config("a", foreground="blue", underline=1)
        text.tag_bind("a", "<Enter>", self.show_hand_cursor)
        text.tag_bind("a", "<Leave>", self.show_arrow_cursor)
        text.tag_bind("a", "<Button-1>", self.click)
        text.config(cursor="arrow")

        #add a link with data
        href = "http://christian-kohloeffel.homepage.t-online.de/index.html"
        text.insert(END, "You are using DXF2GCODE")
        text.insert(END, "\nVersion b01 from the 16th April 2008")
        text.insert(END, "\nFor more information und updates about")
        text.insert(END, "\nplease visit my homepage at:")
        text.insert(END, "\nwww.christian-kohloeffel.homepage.t-online.de", ("a", "href:"+href))




class LayerContentClass:
    def __init__(self,LayerNr=None,LayerName='',Shapes=[]):
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.Shapes=Shapes
        
    def __cmp__(self, other):
         return cmp(self.LayerNr, other.LayerNr)

    def __str__(self):
        return '\nLayerNr ->'+str(self.LayerNr)+'\nLayerName ->'+str(self.LayerName)\
               +'\nShapes ->'+str(self.Shapes)
    
class EntitieContentClass:
    def __init__(self,EntNr=None,EntName='',Shapes=[]):
        self.EntNr=EntNr
        self.EntName=EntName
        self.Shapes=Shapes

    def __cmp__(self, other):
         return cmp(self.EntNr, other.EntNr)        
        
    def __str__(self):
        return '\nEntNr ->'+str(self.EntNr)+'\nEntName ->'+str(self.EntName)\
               +'\nShapes ->'+str(self.Shapes)

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




#Hauptfunktion zum Aufruf des Fensters und Mainloop     
if __name__ == "__main__":
   
    master = Tk()
    master.title("DXF 2 G-Code, Version Beta 0.1")

    #Falls das Programm mit Parametern von EMC gestartet wurde
    if len(sys.argv) > 1:
        Erstelle_Fenster(master,sys.argv[1])
    else:
        Erstelle_Fenster(master)

    master.mainloop()        
    
