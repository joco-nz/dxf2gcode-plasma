#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02.py
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
#Compiled with --onefile --noconsole --upx --tk dxf2gcode_b02.py

#Loeschen aller Module aus dem Speicher
import sys, os, string
import time

if globals().has_key('init_modules'):
    for m in [x for x in sys.modules.keys() if x not in init_modules]:
        del(sys.modules[m]) 
else:
    init_modules = sys.modules.keys()

from dxf2gcode_b02_config import ConfigClass, PostprocessorClass
from dxf2gcode_b02_point import PointClass
from dxf2gcode_b02_shape import ShapeClass, EntitieContentClass
import dxf2gcode_b02_dxf_import as dxf_import 
import dxf2gcode_b02_tsp_opt as tsp
import locale

from math import radians, degrees

import webbrowser,gettext, tempfile, subprocess
from Tkconstants import END, ALL, N, S, E, W, RIDGE, GROOVE, FLAT, DISABLED, NORMAL, ACTIVE, LEFT
from tkMessageBox import showwarning, showerror, showinfo
from Tkinter import Tk, IntVar, DoubleVar, Canvas, Menu, Frame, Radiobutton, Label, Entry, Text, Scrollbar, Toplevel,Button
from tkFileDialog import askopenfile, asksaveasfilename
from tkSimpleDialog import askfloat
from Canvas import Rectangle, Line, Oval, Arc
from copy import copy

# Globale "Konstanten"
APPNAME = "dxf2gcode_b02"
VERSION= "TKINTER Beta 02"
DATE=   "2010-05-04"

# Config Verzeichniss

#===============================================================================
# if os.name == 'posix': 
#    FOLDER = os.path.join(os.environ.get('HOME'), "." + APPNAME.lower()) 
# elif os.name == 'nt': 
#    FOLDER = os.path.join(os.environ.get('APPDATA'), APPNAME.capitalize()).replace("\\", "/")
#===============================================================================
FOLDER=os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")


if os.path.islink(sys.argv[0]):
    FOLDER=os.path.dirname(os.readlink(sys.argv[0]))
    

# Liste der unterstützuden Sprachen anlegen.
langs = []

#Default Sprache des Systems herausfinden
lc, encoding = locale.getdefaultlocale()

if (lc):
    #Wenn wir eine haben diese als Default setzen
    langs = [lc]

# Herausfinden welche sprachen wir haben
language = os.environ.get('LANGUAGE', None)
if (language):
    """langage comes back something like en_CA:en_US:en_GB:en
    on linuxy systems, on Win32 it's nothing, so we need to
    split it up into a list"""
    langs += language.split(":")

"""Now add on to the back of the list the translations that we
know that we have, our defaults"""
langs += []

"""Now langs is a list of all of the languages that we are going
to try to use.  First we check the default, then what the system
told us, and finally the 'known' list"""

gettext.bindtextdomain(APPNAME, FOLDER)
gettext.textdomain(APPNAME)
# Get the language to use
trans = gettext.translation(APPNAME, localedir='languages', languages=langs, fallback = True)
trans.install()

class Erstelle_Fenster:
    def __init__(self, master = None, load_filename=None ):
        
        self.master=master
        self.menu=None
        self.filemenu=None
        self.exportmenu=None
        self.optionmenu=None
        self.helpmenu=None
        self.viewemnu=None
            

         #Skalierung der Kontur
        self.cont_scale=1.0
        
        #Verschiebung der Kontur
        self.cont_dx=0.0
        self.cont_dy=0.0
        
        #Rotieren um den WP zero
        self.rotate=0.0
        
        #Uebergabe des load_filenames falls von EMC gestartet
        self.load_filename=load_filename

        #Linker Rahmen erstellen, in welchen später die Eingabefelder kommen       
        self.frame_l=Frame(master) 
        self.frame_l.grid(row=0,column=0,rowspan=2,padx=4,pady=4,sticky=N+E+W)
        
        #Erstellen des Canvas Rahmens
        self.frame_c=Frame(master,relief = RIDGE,bd = 2)
        self.frame_c.grid(row=0,column=1,padx=4,pady=4,sticky=N+E+S+W)
        
        #Unterer Rahmen erstellen mit der Lisbox + Scrollbar zur Darstellung der Ereignisse.
        self.frame_u=Frame(master) 
        self.frame_u.grid(row=1,column=1,padx=4,sticky=N+E+W+S)
        #Erstellen des Statusfenster
        self.textbox=TextboxClass(frame=self.frame_u,master=self.master)

        #Voreininstellungen fuer das Programm laden
        self.config=ConfigClass(self.textbox,FOLDER,APPNAME)

        #PostprocessorClass initialisieren (Voreinstellungen aus Config)
        self.postpro=PostprocessorClass(self.config,self.textbox,FOLDER,APPNAME,VERSION,DATE)

        self.master.columnconfigure(0,weight=0)
        self.master.columnconfigure(1,weight=1)
        self.master.rowconfigure(0,weight=1)
        self.master.rowconfigure(1,weight=0)
            

        #Erstellen de Eingabefelder und des Canvas
        self.ExportParas =ExportParasClass(self.frame_l,self.config,self.postpro)
        self.Canvas =CanvasClass(self.frame_c,self)

        #Erstellen der Canvas Content Klasse & Bezug in Canvas Klasse
        self.CanvasContent=CanvasContentClass(self.Canvas,self.textbox,self.config)
        self.Canvas.Content=self.CanvasContent

        #Erstellen des Fenster Menus
        self.erstelle_menu()        
        
        #Falls ein load_filename_uebergeben wurde
        if not(self.load_filename is None):
            #Zuerst alle ausstehenden Events und Callbacks ausfuehren (sonst klappts beim Laden nicht)
            self.Canvas.canvas.update()
            self.Load_File()

    def erstelle_menu(self): 
        self.menu = Menu(self.master)
        self.master.config(menu=self.menu)

        self.filemenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label=_("File"), menu=self.filemenu)
        self.filemenu.add_command(label=_("Read DXF"), command=self.Get_Load_File)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=_("Exit"), command=self.ende)

        self.exportmenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label=_("Export"), menu=self.exportmenu)
        self.exportmenu.add_command(label=_("Write G-Code"), command=self.Write_GCode)
        #Disabled bis was gelesen wurde
        self.exportmenu.entryconfig(0,state=DISABLED)

        self.viewmenu=Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label=_("View"),menu=self.viewmenu)
        self.viewmenu.add_checkbutton(label=_("Show workpiece zero"),\
                                      variable=self.CanvasContent.toggle_wp_zero,\
                                      command=self.CanvasContent.plot_wp_zero)
        self.viewmenu.add_checkbutton(label=_("Show all path directions"),\
                                      variable=self.CanvasContent.toggle_start_stop,\
                                      command=self.CanvasContent.plot_cut_info)
        self.viewmenu.add_checkbutton(label=_("Show disabled shapes"),\
                                      variable=self.CanvasContent.toggle_show_disabled,\
                                      command=self.CanvasContent.show_disabled)
            
        self.viewmenu.add_separator()
        self.viewmenu.add_command(label=_('Autoscale'),command=self.Canvas.autoscale)

        #Menupunkt einfuegen zum loeschen der Route
        self.viewmenu.add_separator()
        self.viewmenu.add_command(label=_('Delete Route'),command=self.del_route_and_menuentry)         

        #Disabled bis was gelesen wurde
        self.viewmenu.entryconfig(0,state=DISABLED)
        self.viewmenu.entryconfig(1,state=DISABLED)
        self.viewmenu.entryconfig(2,state=DISABLED)
        self.viewmenu.entryconfig(4,state=DISABLED)
        self.viewmenu.entryconfig(6,state=DISABLED)

        self.optionmenu=Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label=_("Options"),menu=self.optionmenu)
        self.optionmenu.add_command(label=_("Set tolerances"), command=self.Get_Cont_Tol)
        self.optionmenu.add_separator()
        self.optionmenu.add_command(label=_("Scale contours"), command=self.Get_Cont_Scale)
        self.optionmenu.add_command(label=_("Move workpiece zero"), command=self.Move_WP_zero)
        self.optionmenu.add_command(label=_("Rotate contours"), command=self.Rotate_Cont)
        self.optionmenu.entryconfig(2,state=DISABLED)
        self.optionmenu.entryconfig(3,state=DISABLED)
        self.optionmenu.entryconfig(4,state=DISABLED)
        
        
        self.helpmenu = Menu(self.menu,tearoff=0)
        self.menu.add_cascade(label=_("Help"), menu=self.helpmenu)
        self.helpmenu.add_command(label=_("About..."), command=self.Show_About)

    # Callback des Menu Punkts File Laden
    def Get_Load_File(self):
        #Auswahl des zu ladenden Files
        myFormats = [(_('Supported files'),'*.dxf *.ps *.pdf'),\
                     (_('AutoCAD / QCAD Drawing'),'*.dxf'),\
                     (_('Postscript File'),'.ps'),\
                     (_('PDF File'),'.pdf'),\
                     (_('All File'),'*.*') ]
        inidir=self.config.load_path
        filename = askopenfile(initialdir=inidir,\
                               filetypes=myFormats)
        #Falls abgebrochen wurde
        if not filename:
            return
        else:
            self.load_filename=filename.name

        self.Load_File()

    def Load_File(self):

        #Dateiendung pruefen
        (name,ext)=os.path.splitext(self.load_filename)

        if ext.lower()==".dxf":
            filename=self.load_filename
            
        elif (ext.lower()==".ps")or(ext.lower()==".pdf"):
            self.textbox.prt(_("\nSending Postscript/PDF to pstoedit"))
            
            # temporäre Datei erzeugen
            filename=os.path.join(tempfile.gettempdir(),'dxf2gcode_temp.dxf').encode("cp1252")
            
            pstoedit_cmd=self.config.pstoedit_cmd.encode("cp1252") #"C:\Program Files (x86)\pstoedit\pstoedit.exe"
            pstoedit_opt=eval(self.config.pstoedit_opt) #['-f','dxf','-mm']
            
            #print pstoedit_opt
            
            ps_filename=os.path.normcase(self.load_filename.encode("cp1252"))

            cmd=[(('%s')%pstoedit_cmd)]+pstoedit_opt+[(('%s')%ps_filename),(('%s')%filename)]

            #print cmd
    
            retcode=subprocess.call(cmd)
            #print retcode

        self.textbox.text.delete(7.0,END)
        self.textbox.prt(_('\nLoading file: %s') %self.load_filename)
        
        self.values=dxf_import.Load_DXF(filename,self.config,self.textbox)
        
        #Ausgabe der Informationen im Text Fenster
        self.textbox.prt(_('\nLoaded layers: %s') %len(self.values.layers))
        self.textbox.prt(_('\nLoaded blocks: %s') %len(self.values.blocks.Entities))
        for i in range(len(self.values.blocks.Entities)):
            layers=self.values.blocks.Entities[i].get_used_layers()
            self.textbox.prt(_('\nBlock %i includes %i Geometries, reduced to %i Contours, used layers: %s ')\
                               %(i,len(self.values.blocks.Entities[i].geo),len(self.values.blocks.Entities[i].cont),layers))
        layers=self.values.entities.get_used_layers()
        insert_nr=self.values.entities.get_insert_nr()
        self.textbox.prt(_('\nLoaded %i Entities geometries, reduced to %i Contours, used layers: %s ,Number of inserts: %i') \
                             %(len(self.values.entities.geo),len(self.values.entities.cont),layers,insert_nr))

        #Skalierung der Kontur
        self.cont_scale=1.0
        
        #Verschiebung der Kontur
        self.cont_dx=0.0
        self.cont_dy=0.0
        
        #Rotieren um den WP zero
        self.rotate=0.0

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
        self.optionmenu.entryconfig(4,state=NORMAL) 

        #Ausdrucken der Werte        
        self.CanvasContent.makeplot(self.values,
                                    p0=PointClass(x=self.cont_dx,y=self.cont_dy),
                                    pb=PointClass(x=0,y=0),
                                    sca=[self.cont_scale,self.cont_scale,self.cont_scale],
                                    rot=self.rotate)

        #Loeschen alter Route Menues
        self.del_route_and_menuentry()
            
    def Get_Cont_Tol(self):

        #Dialog fuer die Toleranzvoreinstellungen oeffnen      
        title=_('Contour tolerances')
        label=(_("Tolerance for common points [mm]:"),\
               _("Tolerance for curve fitting [mm]:"))
        value=(self.config.points_tolerance.get(),self.config.fitting_tolerance.get())
        dialog=Tkinter_Variable_Dialog(self.master,title,label,value)
        self.config.points_tolerance.set(dialog.result[0])
        self.config.fitting_tolerance.set(dialog.result[1])
        
        #Falls noch kein File geladen wurde nichts machen
        if self.load_filename is None:
            return
        self.Load_File()
        self.textbox.prt(_("\nSet new Contour tolerances (Pts: %0.3f, Fit: %0.3f) reloaded file")\
                              %(dialog.result[0],dialog.result[1]))
        
    def Get_Cont_Scale(self):
        #Abspeichern der alten Werte
        old_scale=self.cont_scale
                
        value=askfloat(_('Scale Contours'),_('Set the scale factor'),\
                                initialvalue=self.cont_scale)
        #Abfrage ob Cancel gedrueckt wurde
        if value is None:
            return
        
        self.cont_scale=value
        
        #Falls noch kein File geladen wurde nichts machen
        self.textbox.prt(_("\nScaled Contours by factor %0.3f") %self.cont_scale)

        #Neu ausdrucken
        self.CanvasContent.makeplot(self.values,
                                    p0=PointClass(x=self.cont_dx,y=self.cont_dy),
                                    pb=PointClass(x=0,y=0),
                                    sca=[self.cont_scale,self.cont_scale,self.cont_scale],
                                    rot=self.rotate)       
    def Rotate_Cont(self):
                
        value=askfloat(_('Rotate Contours'),_('Set the Angle [deg]'),\
                                initialvalue=degrees(self.rotate))
        #Abfrage ob Cancel gedrueckt wurde
        if value is None:
            return
        
        self.rotate=radians(value)
        
        #Falls noch kein File geladen wurde nichts machen
        self.textbox.prt(_("\nRotated Contours by %0.3f deg") %degrees(self.rotate))

        #Neu ausdrucken
        self.CanvasContent.makeplot(self.values,
                                    p0=PointClass(x=self.cont_dx,y=self.cont_dy),
                                    pb=PointClass(x=0,y=0),
                                    sca=[self.cont_scale,self.cont_scale,self.cont_scale],
                                    rot=self.rotate)       
        
        
    def Move_WP_zero(self):

        #Dialog mit den definierten Parametern oeffnen       
        title=_('Workpiece zero offset')
        label=((_("Offset %s axis by mm:") %self.config.ax1_letter),\
               (_("Offset %s axis by mm:") %self.config.ax2_letter))
        value=(self.cont_dx,self.cont_dy)
        dialog=Tkinter_Variable_Dialog(self.master,title,label,value)

        #Abbruch wenn nicht uebergeben wurde
        if dialog.result==False:
            return
        
        self.cont_dx=dialog.result[0]
        self.cont_dy=dialog.result[1]

        #Falls noch kein File geladen wurde nichts machen
        self.textbox.prt(_("\nWorpiece zero offset: %s %0.2f; %s %0.2f") \
                              %(self.config.ax1_letter,self.cont_dx,
                                self.config.ax2_letter,self.cont_dy))

        #Neu ausdrucken
        self.CanvasContent.makeplot(self.values,
                                    p0=PointClass(x=self.cont_dx,y=self.cont_dy),
                                    pb=PointClass(x=0,y=0),
                                    sca=[self.cont_scale,self.cont_scale,self.cont_scale],
                                    rot=self.rotate)

    def Get_Save_File(self):
        MyFormats=[]
        for i in range(len(self.postpro.output_format)):
            name="%s" %(self.postpro.output_text[i])
            format="*%s" %(self.postpro.output_format[i])
            MyFormats.append((name,format ))
            

        #Abbruch falls noch kein File geladen wurde.
        if self.load_filename==None:
            showwarning(_("Export G-Code"), _("Nothing to export!"))
            return
        

        (beg, ende)=os.path.split(self.load_filename)
        (fileBaseName, fileExtension)=os.path.splitext(ende)

        inidir=self.config.save_path
        
        save_filename = asksaveasfilename(initialdir=inidir,\
                               initialfile=fileBaseName,filetypes=MyFormats,defaultextension=self.postpro.output_format[0])
               
        return save_filename

    # Callback des Menu Punkts Exportieren
    def Write_GCode(self):
        
       #Config & postpro in einen kurzen Namen speichern
        config=self.config
        postpro=self.postpro

        if not(config.write_to_stdout):
           
                #Abfrage des Namens um das File zu speichern
                self.save_filename=self.Get_Save_File()
                
                
                 #Wenn Cancel gedrueckt wurde
                if not self.save_filename:
                    return
                
                (beg, ende)=os.path.split(self.save_filename)
                (fileBaseName, fileExtension)=os.path.splitext(ende) 
        
                pp_file_nr=postpro.output_format.index(fileExtension)
                
                postpro.get_all_vars(pp_file_nr)
        else:
                postpro.get_all_vars(0)
        
               
        #Funktion zum optimieren des Wegs aufrufen
        self.opt_export_route()

        #Initial Status fuer den Export
        status=1

        #Schreiben der Standardwert am Anfang        
        postpro.write_gcode_be(postpro,self.load_filename)

        #Maschine auf die Anfangshoehe bringen
        postpro.rap_pos_z(config.axis3_retract.get())

        #Bei 1 starten da 0 der Startpunkt ist
        for nr in range(1,len(self.TSP.opt_route)):
            shape=self.shapes_to_write[self.TSP.opt_route[nr]]
            self.textbox.prt((_("\nWriting Shape: %s") %shape),1)
                


            #Drucken falls die Shape nicht disabled ist
            if not(shape.nr in self.CanvasContent.Disabled):
                #Falls sich die Fräserkorrektur verändert hat diese in File schreiben
                stat =shape.Write_GCode(config,postpro)
                status=status*stat

        #Maschine auf den Endwert positinieren
        postpro.rap_pos_xy(PointClass(x=config.axis1_st_en.get(),\
                                              y=config.axis2_st_en.get()))

        #Schreiben der Standardwert am Ende        
        string=postpro.write_gcode_en(postpro)

        if status==1:
            self.textbox.prt(_("\nSuccessfully generated G-Code"))
            self.master.update_idletasks()

        else:
            self.textbox.prt(_("\nError during G-Code Generation"))
            self.master.update_idletasks()

                    
        #Drucken in den Stdout, speziell fuer EMC2 
        if config.write_to_stdout:
            print(string)
            self.ende()     
        else:
            #Exportieren der Daten
                try:
                    #Das File oeffnen und schreiben    
                    f = open(self.save_filename, "w")
                    f.write(string)
                    f.close()       
                except IOError:
                    showwarning(_("Save As"), _("Cannot save the file."))
            

    def opt_export_route(self):
        
        #Errechnen der Iterationen
        iter =min(self.config.max_iterations,len(self.CanvasContent.Shapes)*20)
        
        #Anfangswerte fuer das Sortieren der Shapes
        self.shapes_to_write=[]
        shapes_st_en_points=[]
        
        #Alle Shapes die geschrieben werden zusammenfassen
        for shape_nr in range(len(self.CanvasContent.Shapes)):
            shape=self.CanvasContent.Shapes[shape_nr]
            if not(shape.nr in self.CanvasContent.Disabled):
                self.shapes_to_write.append(shape)
                shapes_st_en_points.append(shape.get_st_en_points())
                

        #Hinzufuegen des Start- Endpunkte ausserhalb der Geometrie
        x_st=self.config.axis1_st_en.get()
        y_st=self.config.axis2_st_en.get()
        start=PointClass(x=x_st,y=y_st)
        ende=PointClass(x=x_st,y=y_st)
        shapes_st_en_points.append([start,ende])

        #Optimieren der Reihenfolge
        self.textbox.prt(_("\nTSP Starting"),1)
                
        self.TSP=tsp.TSPoptimize(shapes_st_en_points,self.textbox,self.master,self.config)
        self.textbox.prt(_("\nTSP start values initialised"),1)
        #self.CanvasContent.path_hdls=[]
        #self.CanvasContent.plot_opt_route(shapes_st_en_points,self.TSP.opt_route)

        for it_nr in range(iter):
            #Jeden 10ten Schrit rausdrucken
            if (it_nr%10)==0:
                self.textbox.prt((_("\nTSP Iteration nr: %i") %it_nr),1)
                for hdl in self.CanvasContent.path_hdls:
                    self.Canvas.canvas.delete(hdl)
                self.CanvasContent.path_hdls=[]
                self.CanvasContent.plot_opt_route(shapes_st_en_points,self.TSP.opt_route)
                self.master.update_idletasks()
                
            self.TSP.calc_next_iteration()
            
        self.textbox.prt(_("\nTSP done with result:"),1)
        self.textbox.prt(("\n%s" %self.TSP),1)

        self.viewmenu.entryconfig(6,state=NORMAL)        

    def del_route_and_menuentry(self):
        try:
            self.viewmenu.entryconfig(6,state=DISABLED)
            self.CanvasContent.delete_opt_path()
        except:
            pass
        
    def Show_About(self):
        Show_About_Info(self.master)
  
    def ende(self):
        self.master.destroy()
        self.master.quit()

class TextboxClass:
    def __init__(self,frame=None,master=None,DEBUG=0):
            
        self.DEBUG=DEBUG
        self.master=master
        self.text = Text(frame,height=7)
        
        self.textscr = Scrollbar(frame)
        self.text.grid(row=0,column=0,pady=4,sticky=E+W)
        self.textscr.grid(row=0,column=1,pady=4,sticky=N+S)
        frame.columnconfigure(0,weight=1)
        frame.columnconfigure(1,weight=0)

        
        #Binding fuer Contextmenu
        self.text.bind("<Button-3>", self.text_contextmenu)

        #Anfangstext einfuegen
        self.textscr.config(command=self.text.yview)
        self.text.config(yscrollcommand=self.textscr.set)
        self.prt(_('Program started\n %s %s \nCoded by V. Schulz and C. Kohloeffel' %(VERSION, DATE)))

    def set_debuglevel(self,DEBUG=0):
        self.DEBUG=DEBUG
        if DEBUG:
            self.text.config(height=15)

    def prt(self,txt='',DEBUGLEVEL=0):

        if self.DEBUG>=DEBUGLEVEL:
            self.text.insert(END,txt)
            self.text.yview(END)
            self.master.update_idletasks()
            

    #Contextmenu Text mit Bindings beim Rechtsklick
    def text_contextmenu(self,event):

        #Contextmenu erstellen zu der Geometrie        
        popup = Menu(self.text,tearoff=0)        
        popup.add_command(label='Delete text entries',command=self.text_delete_entries)
        popup.post(event.x_root, event.y_root)
        
    def text_delete_entries(self):
        self.text.delete(7.0,END)
        self.text.yview(END)           

class ExportParasClass:
    def __init__(self,master=None,config=None,postpro=None):
        self.master=master
  
        self.nb = NotebookClass(self.master,width=240)

        # uses the notebook's frame
        self.nb_f1 = Frame(self.nb())
        #self.nb_f2 = Frame(self.nb())

        # keeps the reference to the radiobutton (optional)
        self.nb.add_screen(self.nb_f1, _("Coordinates"))
        #self.nb.add_screen(self.nb_f2, _("File Beg. & End"))

        self.nb_f1.columnconfigure(0,weight=1)
        #self.nb_f2.columnconfigure(0,weight=1)        
    
        self.erstelle_eingabefelder(config)
        #self.erstelle_textfelder(config)

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
        Entry(f1,width=7,textvariable=config.tool_dia)\
                .grid(row=0,column=1,sticky=N+E)

        Label(f1, text=_("Start radius (for tool comp.) [mm]:"))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        Entry(f1,width=7,textvariable=config.start_rad)\
                .grid(row=1,column=1,sticky=N+E)        

        Label(f2, text=(_("Start at %s [mm]:") %config.ax1_letter))\
                .grid(row=0,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=config.axis1_st_en)\
                .grid(row=0,column=1,sticky=N+E)

        Label(f2, text=(_("Start at %s [mm]:") %config.ax2_letter))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=config.axis2_st_en)\
                .grid(row=1,column=1,sticky=N+E)

        Label(f2, text=(_("%s retraction area [mm]:") %config.ax3_letter))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=config.axis3_retract)\
                .grid(row=2,column=1,sticky=N+E)

        Label(f2, text=(_("%s safety margin [mm]:") %config.ax3_letter))\
                .grid(row=3,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=config.axis3_safe_margin)\
                .grid(row=3,column=1,sticky=N+E)

        Label(f2, text=(_("%s infeed depth [mm]:") %config.ax3_letter))\
                .grid(row=4,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=config.axis3_slice_depth)\
                .grid(row=4,column=1,sticky=N+E)

        Label(f2, text=(_("%s mill depth [mm]:") %config.ax3_letter))\
                .grid(row=5,column=0,sticky=N+W,padx=4)
        Entry(f2,width=7,textvariable=config.axis3_mill_depth)\
                .grid(row=5,column=1,sticky=N+E)

        Label(f3, text=(_("G1 feed %s-direction [mm/min]:") %config.ax3_letter))\
                .grid(row=1,column=0,sticky=N+W,padx=4)
        Entry(f3,width=7,textvariable=config.F_G1_Depth)\
                .grid(row=1,column=1,sticky=N+E)

        Label(f3, text=(_("G1 feed %s%s-direction [mm/min]:") %(config.ax1_letter,config.ax2_letter)))\
                .grid(row=2,column=0,sticky=N+W,padx=4)
        Entry(f3,width=7,textvariable=config.F_G1_Plane)\
                .grid(row=2,column=1,sticky=N+E)

    def erstelle_textfelder(self,config):
        f22=Frame(self.nb_f2,relief = FLAT,bd = 1)
        f22.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
        f22.columnconfigure(0,weight=1)        

        Label(f22 , text=_("G-Code at the begin of file"))\
                .grid(row=0,column=0,columnspan=2,sticky=N+W,padx=2)
        self.gcode_be = Text(f22,width=10,height=8)
        self.gcode_be_sc = Scrollbar(f22)
        self.gcode_be.grid(row=1,column=0,pady=2,sticky=E+W)
        self.gcode_be_sc.grid(row=1,column=1,padx=2,pady=2,sticky=N+S)
        self.gcode_be_sc.config(command=self.gcode_be.yview)
        self.gcode_be.config(yscrollcommand=self.gcode_be_sc.set)

        Label(f22, text=_("G-Code at the end of file"))\
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

        #Wird momentan nicht benoetigt, eventuell fuer Beschreibung von Aktionen im Textfeld #self.text=text

        #Erstellen des Labels am Unteren Rand fuer Status Leiste        
        self.label=Label(self.master, text=_("Curser Coordinates: X=0.0, Y=0.0, Scale: 1.00"),bg="white",anchor="w")
        self.label.grid(row=1,column=0,sticky=E+W)

        #Canvas Erstellen und Fenster ausfuellen        
        self.canvas=Canvas(self.master,width=650,height=500, bg = "white")
        self.canvas.grid(row=0,column=0,sticky=N+E+S+W)
        self.master.columnconfigure(0,weight=1)
        self.master.rowconfigure(0,weight=1)


        #Binding fuer die Bewegung des Mousezeigers
        self.canvas.bind("<Motion>", self.moving)

        #Bindings fuer Selektieren
        self.canvas.bind("<Button-1>", self.select_cont)
        
        #Eventuell mit Abfrage probieren???????????????????????????????????????????
        self.canvas.bind("<Shift-Button-1>", self.multiselect_cont)
        self.canvas.bind("<B1-Motion>", self.select_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.select_release)

        #Binding fuer Contextmenu
        self.canvas.bind("<Button-3>", self.make_contextmenu)

        #Bindings fuer Zoom und Bewegen des Bilds        
        self.canvas.bind("<Control-Button-1>", self.mouse_move)
        self.canvas.bind("<Control-B1-Motion>", self.mouse_move_motion)
        self.canvas.bind("<Control-ButtonRelease-1>", self.mouse_move_release)
        self.canvas.bind("<Control-Button-3>", self.mouse_zoom)
        self.canvas.bind("<Control-B3-Motion>", self.mouse_zoom_motion)
        self.canvas.bind("<Control-ButtonRelease-3>", self.mouse_zoom_release)   

    #Callback fuer das Bewegen der Mouse mit Darstellung in untere Leiste
    def moving(self,event):
        x=self.dx+(event.x/self.scale)
        y=self.dy+(self.canvas.winfo_height()-event.y)/self.scale

        if self.scale<1:
            self.label['text']=(_("Curser Coordinates: X= %5.0f Y= %5.0f , Scale: %5.3f") \
                                %(x,y,self.scale))
            
        elif (self.scale>=1)and(self.scale<10):      
            self.label['text']=(_("Curser Coordinates: X= %5.1f Y= %5.1f , Scale: %5.2f") \
                                %(x,y,self.scale))
        elif self.scale>=10:      
            self.label['text']=(_("Curser Coordinates: X= %5.2f Y= %5.2f , Scale: %5.1f") \
                                %(x,y,self.scale))
        
    #Callback fuer das Auswählen von Elementen
    def select_cont(self,event):
        #Abfrage ob ein Contextfenster offen ist, speziell fuer Linux
        self.schliesse_contextmenu()
        
        self.moving(event)
        self.Content.deselect()
        self.sel_rect_hdl=Rectangle(self.canvas,event.x,event.y,event.x,event.y,outline="grey") 
        self.lastevent=event

    def multiselect_cont(self,event):
        #Abfrage ob ein Contextfenster offen ist, speziell fuer Linux
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
        
        #Beim Auswählen sollen die Direction Pfeile geloescht werden!!!!!!!!!!!!!!!!!!        
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

    #Callback fuer Bewegung des Bildes
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

    #Callback fuer das Zoomen des Bildes     
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

        self.Content.plot_cut_info() 
        self.Content.plot_wp_zero()

    def mouse_zoom_release(self,event):
        self.master.config(cursor="")
                
    #Contextmenu mit Bindings beim Rechtsklick
    def make_contextmenu(self,event):
        self.lastevent=event

        #Abfrage ob das Contextfenster schon existiert, speziell fuer Linux
        self.schliesse_contextmenu()
            
        #Contextmenu erstellen zu der Geometrie        
        popup = Menu(self.canvas,tearoff=0)
        self.popup=popup
        popup.add_command(label=_('Invert Selection'),command=self.Content.invert_selection)
        popup.add_command(label=_('Disable Selection'),command=self.Content.disable_selection)
        popup.add_command(label=_('Enable Selection'),command=self.Content.enable_selection)

        popup.add_separator()
        popup.add_command(label=_('Switch Direction'),command=self.Content.switch_shape_dir)
        
        #Untermenu fuer die Fräserkorrektur
        self.dir_var.set(self.Content.calc_dir_var())
        cut_cor_menu = Menu(popup,tearoff=0)
        cut_cor_menu.add_checkbutton(label=_("G40 No correction"),\
                                     variable=self.dir_var,onvalue=0,\
                                     command=lambda:self.Content.set_cut_cor(40))
        cut_cor_menu.add_checkbutton(label=_("G41 Cutting left"),\
                                     variable=self.dir_var,onvalue=1,\
                                     command=lambda:self.Content.set_cut_cor(41))
        cut_cor_menu.add_checkbutton(label=_("G42 Cutting right"),\
                                     variable=self.dir_var,onvalue=2,\
                                     command=lambda:self.Content.set_cut_cor(42))
        popup.add_cascade(label=_('Set Cutter Correction'),menu=cut_cor_menu)

        #Menus Disablen wenn nicht ausgewählt wurde        
        if len(self.Content.Selected)==0:
            popup.entryconfig(0,state=DISABLED)
            popup.entryconfig(1,state=DISABLED)
            popup.entryconfig(2,state=DISABLED)
            popup.entryconfig(4,state=DISABLED)
            popup.entryconfig(5,state=DISABLED)

        popup.post(event.x_root, event.y_root)
        
    #Speziell fuer Linux falls das Contextmenu offen ist dann schliessen
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

        self.Content.plot_cut_info()
        self.Content.plot_wp_zero()
        
    def get_can_coordinates(self,x_st,y_st):
        x_ca=(x_st-self.dx)*self.scale
        y_ca=(y_st-self.dy)*self.scale-self.canvas.winfo_height()
        return x_ca, y_ca

#    def scale_contours(self,delta_scale):     
#        self.scale=self.scale/delta_scale
#        self.dx=self.dx*delta_scale
#        self.dy=self.dy*delta_scale
#
#        #Schreiben der neuen WErte simulierne auf Curser Punkt 0, 0
#        event=PointClass(x=0,y=0)
#        self.moving(event)
#
#        #Skalieren der Shapes
#        for shape in self.Content.Shapes:
#            shape.sca[0]=shape.sca[0]*delta_scale
#            shape.sca[1]=shape.sca[1]*delta_scale
#            shape.sca[2]=shape.sca[2]*delta_scale
#            
#            shape.p0=shape.p0*[delta_scale,delta_scale]
#
#    def move_wp_zero(self,delta_dx,delta_dy):
#        self.dx=self.dx-delta_dx
#        self.dy=self.dy-delta_dy
#
#        #Verschieben der Shapes 
#        for shape in self.Content.Shapes:
#            shape.p0-=PointClass(x=delta_dx,y=delta_dy)
#
#        #Update des Nullpunkts auf neue Koordinaten
#        self.Content.plot_wp_zero()
        
#Klasse mit den Inhalten des Canvas & Verbindung zu den Konturen
class CanvasContentClass:
    def __init__(self,Canvas,textbox,config):
        self.Canvas=Canvas
        self.textbox=textbox
        self.config=config
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitiesRoot=EntitieContentClass()
        self.BaseEntities=EntitieContentClass()
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]
        

        #Anfangswert fuer das Ansicht Toggle Menu
        self.toggle_wp_zero=IntVar()
        self.toggle_wp_zero.set(1)

        self.toggle_start_stop=IntVar()
        self.toggle_start_stop.set(0)

        self.toggle_show_disabled=IntVar()
        self.toggle_show_disabled.set(0)  
        
    def __str__(self):
        s='\nNr. of Shapes -> %s' %len(self.Shapes)
        for lay in self.LayerContents:
            s=s+'\n'+str(lay)
        for ent in self.EntitieContents:
            s=s+'\n'+str(ent)
        s=s+'\nSelected -> %s'%(self.Selected)\
           +'\nDisabled -> %s'%(self.Disabled)
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
    def makeplot(self,values,p0,pb,sca,rot):
        self.values=values

        #Loeschen des Inhalts
        self.Canvas.canvas.delete(ALL)
        
        #Standardwerte fuer scale, dx, dy zuweisen
        self.Canvas.scale=1
        self.Canvas.dx=0
        self.Canvas.dy=-self.Canvas.canvas.winfo_height()

        #Zuruecksetzen der Konturen
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitiesRoot=EntitieContentClass(Nr=0,Name='Entities',parent=None,children=[],
                                            p0=p0,pb=pb,sca=sca,rot=rot)
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]

        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        self.makeshapes(parent=self.EntitiesRoot)
        self.plot_shapes()
        self.LayerContents.sort()
        #self.EntitieContents.sort()

        #Autoscale des Canvas        
        self.Canvas.autoscale()

    def makeshapes(self,parent=None,ent_nr=-1):

        if parent.Name=="Entities":      
            entities=self.values.entities
        else:
            ent_nr=self.values.Get_Block_Nr(parent.Name)
            entities=self.values.blocks.Entities[ent_nr]
            
        #Zuweisen der Geometrien in die Variable geos & Konturen in cont
        ent_geos=entities.geo
               
        #Schleife fuer die Anzahl der Konturen 
        for cont in entities.cont:
            #Abfrage falls es sich bei der Kontur um ein Insert eines Blocks handelt
            if ent_geos[cont.order[0][0]].Typ=="Insert":
                ent_geo=ent_geos[cont.order[0][0]]
                
                #Zuweisen des Basispunkts für den Block
                new_ent_nr=self.values.Get_Block_Nr(ent_geo.BlockName)
                new_entities=self.values.blocks.Entities[new_ent_nr]
                pb=new_entities.basep
                
                #Skalierung usw. des Blocks zuweisen
                p0=ent_geos[cont.order[0][0]].Point
                sca=ent_geos[cont.order[0][0]].Scale
                rot=ent_geos[cont.order[0][0]].rot
                
                #Erstellen des neuen Entitie Contents für das Insert
                NewEntitieContent=EntitieContentClass(Nr=0,Name=ent_geo.BlockName,
                                        parent=parent,children=[],
                                        p0=p0,
                                        pb=pb,
                                        sca=sca,
                                        rot=rot)

                parent.addchild(NewEntitieContent)
            
                self.makeshapes(parent=NewEntitieContent,ent_nr=ent_nr)
                
            else:
                #Schleife fuer die Anzahl der Geometrien
                self.Shapes.append(ShapeClass(len(self.Shapes),\
                                                cont.closed,\
                                                40,\
                                                0.0,\
                                                parent,\
                                                [],\
                                                []))
                for ent_geo_nr in range(len(cont.order)):
                    ent_geo=ent_geos[cont.order[ent_geo_nr][0]]
                    if cont.order[ent_geo_nr][1]:
                        ent_geo.geo.reverse()
                        for geo in ent_geo.geo:
                            geo=copy(geo)
                            geo.reverse()
                            self.Shapes[-1].geos.append(geo)

                        ent_geo.geo.reverse()
                    else:
                        for geo in ent_geo.geo:
                            self.Shapes[-1].geos.append(copy(geo))
                        
                self.addtoLayerContents(self.Shapes[-1],ent_geo.Layer_Nr)
                parent.addchild(self.Shapes[-1])

    def plot_shapes(self):
        for shape in self.Shapes:
            shape.plot2can(self.Canvas.canvas)
            
    #Drucken des Werkstuecknullpunkts
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
    def plot_cut_info(self):
        for hdl in self.dir_hdls:
            self.Canvas.canvas.delete(hdl) 
        self.dir_hdls=[]

        if not(self.toggle_start_stop.get()):
            draw_list=self.Selected[:]
        else:
            draw_list=range(len(self.Shapes))
               
        for shape_nr in draw_list:
            if not(shape_nr in self.Disabled):
                self.dir_hdls+=self.Shapes[shape_nr].plot_cut_info(self.Canvas,self.config)


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


    #Hinzufuegen der Kontur zum Layer        
    def addtoLayerContents(self,shape_nr,lay_nr):
        #Abfrage of der gesuchte Layer schon existiert
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.Shapes.append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(LayerContentClass(lay_nr,LayerName,[shape_nr]))
        
    #Hinzufuegen der Kontur zu den Entities
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

                    self.textbox.prt(_('\n\nAdded shape to selection %s:')%(self.Shapes[tag]),3)
                    
                    if mode=='single':
                        break
            except:
                pass
            
        self.plot_cut_info()
        self.set_shapes_color(self.Selected,'selected')
 
    def invert_selection(self):
        new_sel=[]
        for shape_nr in range(len(self.Shapes)):
            if (not(shape_nr in self.Disabled)) & (not(shape_nr in self.Selected)):
                new_sel.append(shape_nr)

        self.deselect()
        self.Selected=new_sel
        self.set_shapes_color(self.Selected,'selected')
        self.plot_cut_info()

        self.textbox.prt(_('\nInverting Selection'),3)
        

    def disable_selection(self):
        for shape_nr in self.Selected:
            if not(shape_nr in self.Disabled):
                self.Disabled.append(shape_nr)
        self.set_shapes_color(self.Selected,'disabled')
        self.Selected=[]
        self.plot_cut_info()

    def enable_selection(self):
        for shape_nr in self.Selected:
            if shape_nr in self.Disabled:
                nr=self.Disabled.index(shape_nr)
                del(self.Disabled[nr])
        self.set_shapes_color(self.Selected,'deselected')
        self.Selected=[]
        self.plot_cut_info()

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
            self.textbox.prt(_('\n\nSwitched Direction at Shape: %s')\
                             %(self.Shapes[shape_nr]),3)
        self.plot_cut_info()
        
    def set_cut_cor(self,correction):
        for shape_nr in self.Selected: 
            self.Shapes[shape_nr].cut_cor=correction
            
            self.textbox.prt(_('\n\nChanged Cutter Correction at Shape: %s')\
                             %(self.Shapes[shape_nr]),3)
        self.plot_cut_info() 
        
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
            if (self.Canvas.canvas.type(hdl)=="oval") :
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
                                       
       
class LayerContentClass:
    def __init__(self,LayerNr=None,LayerName='',Shapes=[]):
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.Shapes=Shapes
        
    def __cmp__(self, other):
         return cmp(self.LayerNr, other.LayerNr)

    def __str__(self):
        return ('\ntype:        %s' %self.type) +\
               ('\nLayerNr :      %i' %self.LayerNr) +\
               ('\nLayerName:     %s' %self.LayerName)+\
               ('\nShapes:    %s' %self.Shapes)

class Show_About_Info(Toplevel):
    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.transient(parent)

        self.title(_("About DXF2GCODE"))
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
        w = Button(box, text=_("OK"), width=10, command=self.ok, default=ACTIVE)
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
        text.insert(END, _("You are using DXF2GCODE"))
        text.insert(END, ("\nVersion %s (%s)" %(VERSION,DATE)))
        text.insert(END, _("\nFor more information und updates about"))
        text.insert(END, _("\nplease visit my homepage at:"))
        text.insert(END, _("\nwww.christian-kohloeffel.homepage.t-online.de"), ("a", "href:"+href))

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

class Tkinter_Variable_Dialog(Toplevel):
    def __init__(self, parent=None,title='Test Dialog',label=('label1','label2'),value=(0.0,0.0)):
        if not(len(label)==len(value)):
            raise Exception, "Number of labels different to number of values"

        #Eingabewerte in self speichern
        self.label=label
        self.value=value
        self.result=False

        Toplevel.__init__(self, parent)
        self.transient(parent)

        self.title(title)
        self.parent = parent

        body = Frame(self)
        self.initial_focus = self.body(body)
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

        w = Button(box, text=_("OK"), width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text=_("Cancel"), width=10, command=self.cancel)
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

    def body(self, master):
        #Die Werte den Tkintervarialben zuweisen
        self.tkintervars=[]
        for row_nr in range(len(self.label)):
            self.tkintervars.append(DoubleVar())
            self.tkintervars[-1].set(self.value[row_nr])
            Label(master, text=self.label[row_nr]).grid(row=row_nr,padx=4,sticky=N+W)
            Entry(master,textvariable=self.tkintervars[row_nr],width=10).grid(row=row_nr, column=1,padx=4,sticky=N+W)

    def apply(self):
        self.result=[]
        for tkintervar in self.tkintervars:
            self.result.append(tkintervar.get())

#class SysOutListener:
#    def __init__(self):
#        self.first = True
#    def write(self, string):
#        f=open('d:/dxf2gcode_out.txt', 'a')
#        if self.first:
#            self.first = False
#            f.write('\n\n' + time.ctime() + ':\n')
#        f.write(string)
#        f.flush()
#        f.close()
#        sys.__stdout__.write(string)


class SysErrListener:
    def __init__(self):
        self.first = True
    def write(self, string):
        
        f=open(os.path.join(FOLDER,'dxf2gcode_err.txt'), 'a')
        if self.first:
            self.first = False
            f.write('\n\n' + time.ctime() + ':\n')
        f.write(string)
        f.flush()
        f.close()
        sys.__stderr__.write(string)



#Hauptfunktion zum Aufruf des Fensters und Mainloop     
if __name__ == "__main__":
   
    #sys.stdout = SysOutListener()
    #sys.stderr = SysErrListener()

    master = Tk()
    master.title("%s, Version: %s, Date: %s " %(APPNAME,VERSION,DATE))

    #Falls das Programm mit Parametern von EMC gestartet wurde
    if len(sys.argv) > 1:
        Erstelle_Fenster(master,sys.argv[1])
    else:
        Erstelle_Fenster(master)

    master.mainloop()

    
