#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_wx2.8.py
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

# Globale Konstanten
APPNAME = "dxf2gcode"
VERSION = "2.0 beta1"
DEBUG   = 3

#Loeschen aller Module aus dem Speicher---------------------------------------------------------------
import sys, os, string
if globals().has_key('init_modules'):
    for m in [x for x in sys.modules.keys() if x not in init_modules]:
        del(sys.modules[m]) 
else:
    init_modules = sys.modules.keys()
    

#Importieren der Module beginnt hier-----------------------------------------------------------------
#Schauen ob das numpy Modul geladen werden kann
try:
    import numpy as N
    haveNumpy = True
except ImportError:
            # numpy isn't there
            print ("The FloatCanvas requires the numpy module, version 1.* \n\n"
            "You can get info about it at:\n"
            "http://numpy.scipy.org/\n\n")
      
import wx
import wx.aui
from wx.lib.wordwrap import wordwrap

from wx.lib.floatcanvas import NavCanvas, FloatCanvas, Resources
import wx.lib.colourdb

import locale
import gettext, ConfigParser, tempfile, subprocess
from copy import copy

from dxf2gcode_b02_point import PointClass
from dxf2gcode_b02_shape import ShapeClass
import dxf2gcode_b02_dxf_import as dxfimport 
import dxf2gcode_b02_tsp_opt as tsp

import time, random

# Config Verzeichnisse----------------------------------------------------------------------------------
if os.name == 'posix': 
    FOLDER = os.path.join(os.environ.get('HOME'), "." + APPNAME.lower()) 
elif os.name == 'nt': 
    FOLDER = os.path.join(os.environ.get('APPDATA'), APPNAME.capitalize()) 

#Das momentane Verzeichnis herausfinden
local_path = os.path.realpath(os.path.dirname(sys.argv[0]))


#Übersetzungen initialisieren----------------------------------------------------------------------------
# Liste der unterstützuden Sprachen anlegen.
langs = ['DE_de']

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


gettext.bindtextdomain("dxf2gcode", local_path)
gettext.textdomain("dxf2gcode")
trans = gettext.translation("dxf2gcode", localedir='languages', languages=langs, fallback = True)
trans.install()


class MyFrameClass(wx.Frame):
    def __init__(self, parent, load_filename=None,id=-1, title='%s, Version: %s' %(APPNAME.capitalize(),VERSION),
                 pos=wx.DefaultPosition, size=(1024, 768),
                 style=wx.DEFAULT_FRAME_STYLE):

                            
        #Erstellen der verschiedenen Verzeichnisse
        self.GetFoldernames()
        
        #Uebergabe des load_filenames falls von EMC gestartet
        self.load_filename=load_filename
        
        #Erstellen des Fenster
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self._mgr = wx.aui.AuiManager(self)

        #Erstellen der Status Bar am unteren Ende
        self.CreateStatusBar()
        self.SetStatusText("This is the statusbar")       

        #Erstellen des Fenster Menus
        self.CreateMenues()
        self.BindMenuEvents()
        self.DisableAllMenues()
            
        #Erstellen des Baums für die Entities
        self.MyEntTree = MyTreeClass(self, wx.ID_ANY)   

        #Erstellen der Messagebox für die Meldungen
        self.MyMessages = MyMessagesClass(self, -1)
        
        #Erstellen des Rahmens für die verwendeten Layers
        self.MyLayers = MyLayersClass(self, -1)

        #Erstellen des Zeichenbereichs (früher Canvas?!)
        self.MyGraphic = MyGraphicClass(self,-1)
                        
        #Die Verschiedeneen Objecte zum Sizer AUIManager hinzufügen
        self._mgr.AddPane(self.MyEntTree, wx.aui.AuiPaneInfo(). 
                          Caption("Entities").Floatable(False).
                          Left().CloseButton(False))            
        self._mgr.AddPane(self.MyLayers,wx.aui.AuiPaneInfo(). 
                          Caption("Layers").Floatable(False). 
                          Left().CloseButton(False))
        self._mgr.AddPane(self.MyMessages, wx.aui.AuiPaneInfo(). 
                          Caption("Messages").Floatable(False).
                          Bottom().CloseButton(False))
        self._mgr.AddPane(self.MyGraphic, wx.aui.AuiPaneInfo(). 
                          CaptionVisible(False). 
                          Center())

        #Dem Manager sagen er soll alles auf Stand bringen
        self._mgr.Update()

        #Den Event Schliessen hinzufügen
        self.Bind(wx.EVT_CLOSE, self.CloseWindow)
        
        #Voreininstellungen fuer das Programm laden
        self.config=MyConfigClass(self.MyMessages)

        #PostprocessorClass initialisieren (Voreinstellungen aus Config)
        self.postpro=MyPostprocessorClass(self.config,self.MyMessages)
            
#        #Erstellen de Eingabefelder und des Canvas
#        self.ExportParas =ExportParasClass(self.frame_l,self.config,self.postpro)
#        self.Canvas =CanvasClass(self.frame_c,self)
#
#        #Erstellen der Canvas Content Klasse & Bezug in Canvas Klasse
#        self.CanvasContent=CanvasContentClass(self.Canvas,self.textbox,self.config)
#        self.Canvas.Content=self.CanvasContent
# 
#        
        #Falls ein load_filename_uebergeben wurde
        if not(self.load_filename is None):
            #Zuerst alle ausstehenden Events und Callbacks ausfuehren (sonst klappts beim Laden nicht)
            self.Load_File()

    def GetFoldernames(self):
        self.programdirectory = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
        self.bitmapdirectory = self.programdirectory + "/bitmaps"
       
    def CreateMenues(self):
        #Filemenu erstellen
        menuBar = wx.MenuBar()
        self.filemenu=filemenu = wx.Menu()
        open=wx.MenuItem(filemenu,101,_("Open DXF"), _("Import a dxf file"))
        open.SetBitmap(wx.Bitmap(self.bitmapdirectory + "/open.png"))
        filemenu.AppendItem(open)
        
        filemenu.AppendSeparator()
        quit=wx.MenuItem(filemenu,102, _("&Quit\tCtrl+Q"), _("Close this frame"))
        quit.SetBitmap(wx.Bitmap(self.bitmapdirectory + "/exit.png"))
        filemenu.AppendItem(quit)
        menuBar.Append(filemenu, _("File"))
             

        #Exportmenu erstellen
        self.exportmenu=exportmenu = wx.Menu()
        export=wx.MenuItem(exportmenu,201, _("Write G-Code"), _("Write G-Code in file / stdout to EMC"))
        export.SetBitmap(wx.Bitmap(self.bitmapdirectory + "/export.png"))
        exportmenu.AppendItem(export)
        menuBar.Append(exportmenu, _("Export"))
        
        #Viewmenu erstellen
        self.viewmenu=viewmenu= wx.Menu()
        shwpz = viewmenu.Append(301, _("Show workpiece zero"),\
                    _("Show a symbol for the workpiece zero in the drawing"), kind=wx.ITEM_CHECK)
        viewmenu.Check(301, True)
        shapd = viewmenu.Append(302, _("Show all path directions"),\
                    _("Show the path direction of all shapes"), kind=wx.ITEM_CHECK)
        viewmenu.Check(302, False)

        
        shsds = viewmenu.Append(303, _("Show disabled shapes"),\
                    _("Show the disabled shapes grayed out"), kind=wx.ITEM_CHECK)
        viewmenu.Check(303, True) 
        viewmenu.AppendSeparator()
        viewmenu.Append(304, _("Autoscale"), _("Fit the drawing to the screen"))
        viewmenu.AppendSeparator()
        viewmenu.Append(305, _("Delete Route"), _("Delete the route which was drawn during export"))               
        menuBar.Append(viewmenu, _("View"))
        
        self.optionmenu=optionmenu= wx.Menu()
        optionmenu.Append(401, _("Set tolerances"), _("Set the tolerances for the dxf import"))
        optionmenu.AppendSeparator()
        optionmenu.Append(402, _("Move workpiece zero"), _("Offset the workpiece zero of the drawing"))
        
        menuBar.Append(optionmenu, _("Options"))
                
        helpmenu = wx.Menu()
        helpmenu.Append(501, "About", "Show the About dialog")
        menuBar.Append(helpmenu, "Help")    

        self.SetMenuBar(menuBar)
        
    def BindMenuEvents(self):
        #Filemenu 
        self.Bind(wx.EVT_MENU, self.GetLoadFile, id=101)
        self.Bind(wx.EVT_MENU, self.CloseWindow, id=102)
        
        #Exportmenu
        self.Bind(wx.EVT_MENU, self.WriteGCode, id=201)
        
        #Viewmenu
        #self.Bind(wx.EVT_MENU, self.CanvasContent.plot_wp_zero, id=301)
        #self.Bind(wx.EVT_MENU, self.CanvasContent.plot_cut_info, id=302)
        #self.Bind(wx.EVT_MENU, self.CanvasContent.show_disabled, id=303)
        #self.Bind(wx.EVT_MENU, self.Canvas.autoscale, id=304)
        #self.Bind(wx.EVT_MENU, self.del_route_and_menuentry, id=305)
        
        #Optionsmenu
        self.Bind(wx.EVT_MENU, self.GetContTol, id=401)
        self.Bind(wx.EVT_MENU, self.MoveWpZero, id=402)
        
        #Helpmenu
        self.Bind(wx.EVT_MENU, self.ShowAbout, id=501)
        
    def DisableAllMenues(self):
        
        #Exportmenu
        self.exportmenu.Enable(201,False)
        
        #Viewmenu
        self.viewmenu.Enable(301,False)
        self.viewmenu.Enable(302,False)
        self.viewmenu.Enable(303,False)
        self.viewmenu.Enable(304,False)
        self.viewmenu.Enable(305,False)
        
        #Optionsmenu
        self.optionmenu.Enable(401,False)
        self.optionmenu.Enable(402,False)
        
    def EnableAllMenues(self):
        #Exportmenu
        self.exportmenu.Enable(201,True)
        
        #Viewmenu
        self.viewmenu.Enable(301,True)
        self.viewmenu.Enable(302,True)
        self.viewmenu.Enable(303,True)
        self.viewmenu.Enable(304,True)
        #self.viewmenu.Enable(305,True)
        
        #Optionsmenu
        self.optionmenu.Enable(401,True)
        self.optionmenu.Enable(402,True)
    # Callback des Menu Punkts File Laden
    def GetLoadFile(self,event):
                
        #Auswahl des zu ladenden Files
        myFormats = _('Supported files')+'|*.dxf;*.ps;*.pdf|'+ \
                     _('AutoCAD / QCAD Drawing')+'|*.dxf|'+\
                     _('Postscript File')+'|*.ps|'+\
                     _('PDF File')+'|*.pdf|'+\
                     _('All File')+'|*.*' 
                          
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=os.getcwd(), 
            defaultFile="",
            wildcard=myFormats,
            style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)

        # Wenn OK dann weiter ausführen
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            paths = dlg.GetPaths()
            
            self.load_filename=paths[0]
            self.LoadFile()

    def LoadFile(self):

        #Dateiendung pruefen
        (name,ext)=os.path.splitext(self.load_filename)

        if ext.lower()==".dxf":
            filename=self.load_filename
            
        elif (ext.lower()==".ps")or(ext.lower()==".pdf"):
            self.MyMessages.prt(_("\nSending Postscript/PDF to pstoedit"))
            
            # temporäre Datei erzeugen
            filename=os.path.join(tempfile.gettempdir(),'dxf2gcode_temp.dxf').encode("cp1252")
            
            pstoedit_cmd=self.config.pstoedit_cmd.encode("cp1252") #"C:\Program Files (x86)\pstoedit\pstoedit.exe"
            pstoedit_opt=eval(self.config.pstoedit_opt) #['-f','dxf','-mm']
            
            #print pstoedit_opt
            
            ps_filename=os.path.normcase(self.load_filename.encode("cp1252"))

            cmd=[(('%s')%pstoedit_cmd)]+pstoedit_opt+[(('%s')%ps_filename),(('%s')%filename)]

            print cmd
    
            retcode=subprocess.call(cmd)
            print retcode
            
        #self.MyMessages.TextDelete(None)
        self.MyMessages.prt(_('\nLoading file: %s') %self.load_filename)
        
        self.values=dxfimport.LoadDXF(filename,self.config,self.MyMessages)
        
        #Ausgabe der Informationen im Text Fenster
        self.MyMessages.prt(_('\nLoaded layers: %s') %len(self.values.layers))
        self.MyMessages.prt(_('\nLoaded blocks: %s') %len(self.values.blocks.Entities))
        for i in range(len(self.values.blocks.Entities)):
            layers=self.values.blocks.Entities[i].get_used_layers()
            self.MyMessages.prt(_('\nBlock %i includes %i Geometries, reduced to %i Contours, used layers: %s ')\
                               %(i,len(self.values.blocks.Entities[i].geo),len(self.values.blocks.Entities[i].cont),layers))
        layers=self.values.entities.get_used_layers()
        insert_nr=self.values.entities.get_insert_nr()
        self.MyMessages.prt(_('\nLoaded %i Entities geometries, reduced to %i Contours, used layers: %s ,Number of inserts: %i') \
                             %(len(self.values.entities.geo),len(self.values.entities.cont),layers,insert_nr))

        #Skalierung der Kontur
        self.cont_scale=1.0
        
        #Verschiebung der Kontur
        self.cont_dx=0.0
        self.cont_dy=0.0
        
        #Einschalten der disabled Menus
        self.EnableAllMenues()

        #Ausdrucken der Werte        
        #self.CanvasContent.makeplot(self.values)

        #Loeschen alter Route Menues
        #self.del_route_and_menuentry()
            
    def GetContTol(self):
        pass
#
#        #Dialog fuer die Toleranzvoreinstellungen oeffnen      
#        title=_('Contour tolerances')
#        label=(_("Tolerance for common points [mm]:"),\
#               _("Tolerance for curve fitting [mm]:"))
#        value=(self.config.points_tolerance.get(),self.config.fitting_tolerance.get())
#        dialog=Tkinter_Variable_Dialog(self.master,title,label,value)
#        self.config.points_tolerance.set(dialog.result[0])
#        self.config.fitting_tolerance.set(dialog.result[1])
#        
#        #Falls noch kein File geladen wurde nichts machen
#        if self.load_filename is None:
#            return
#        self.Load_File()
#        self.textbox.prt(_("\nSet new Contour tolerances (Pts: %0.3f, Fit: %0.3f) reloaded file")\
#                              %(dialog.result[0],dialog.result[1]))
#        
#    def Get_Cont_Scale(self):
#        #Abspeichern der alten Werte
#        old_scale=self.cont_scale
#                
#        value=askfloat(_('Scale Contours'),_('Set the scale factor'),\
#                                initialvalue=self.cont_scale)
#        #Abfrage ob Cancel gedrueckt wurde
#        if value is None:
#            return
#        
#        self.cont_scale=value
#
#        #Falls noch kein File geladen wurde nichts machen
#        self.textbox.prt(_("\nScaled Contours by factor %0.3f") %self.cont_scale)
#
#        self.Canvas.scale_contours(self.cont_scale/old_scale)        
#        
    def MoveWpZero(self):
        pass
#        #Die alten Werte zwischenspeichern fuer das verschieben des Canvas
#        old_dx=self.cont_dx
#        old_dy=self.cont_dy
#
#        #Dialog mit den definierten Parametern oeffnen       
#        title=_('Workpiece zero offset')
#        label=((_("Offset %s axis by mm:") %self.config.ax1_letter),\
#               (_("Offset %s axis by mm:") %self.config.ax2_letter))
#        value=(self.cont_dx,self.cont_dy)
#        dialog=Tkinter_Variable_Dialog(self.master,title,label,value)
#
#        #Abbruch wenn nicht uebergeben wurde
#        if dialog.result==False:
#            return
#        
#        self.cont_dx=dialog.result[0]
#        self.cont_dy=dialog.result[1]
#
#        #Falls noch kein File geladen wurde nichts machen
#        self.textbox.prt(_("\nWorpiece zero offset: %s %0.2f; %s %0.2f") \
#                              %(self.config.ax1_letter,self.cont_dx,
#                                self.config.ax2_letter,self.cont_dy))
#
#        #Verschieben des Canvas WP zero
#        self.Canvas.move_wp_zero(self.cont_dx-old_dx,self.cont_dy-old_dy)
#
#    def Get_Save_File(self):
#
#        #Abbruch falls noch kein File geladen wurde.
#        if self.load_filename==None:
#            showwarning(_("Export G-Code"), _("Nothing to export!"))
#            return
#        
#        #Auswahl des zu ladenden Files
#        myFormats = [(_('G-Code for EMC2'),'*.ngc'),\
#        (_('All File'),'*.*') ]
#
#        (beg, ende)=os.path.split(self.load_filename)
#        (fileBaseName, fileExtension)=os.path.splitext(ende)
#
#        inidir=self.config.save_path
#        self.save_filename = asksaveasfilename(initialdir=inidir,\
#                               initialfile=fileBaseName +'.ngc',filetypes=myFormats)
#
    # Callback des Menu Punkts Exportieren
    def WriteGCode(self):
        pass
#        #Funktion zum optimieren des Wegs aufrufen
#        self.opt_export_route()
#
#        #Initial Status fuer den Export
#        status=1
#
#        #Config & postpro in einen kurzen Namen speichern
#        config=self.config
#        postpro=self.postpro
#
#        #Schreiben der Standardwert am Anfang        
#        postpro.write_gcode_be(self.ExportParas,self.load_filename)
#
#        #Maschine auf die Anfangshoehe bringen
#        postpro.rap_pos_z(config.axis3_retract.get())
#
#        #Bei 1 starten da 0 der Startpunkt ist
#        for nr in range(1,len(self.TSP.opt_route)):
#            shape=self.shapes_to_write[self.TSP.opt_route[nr]]
#            self.textbox.prt((_("\nWriting Shape: %s") %shape),1)
#                
#
#
#            #Drucken falls die Shape nicht disabled ist
#            if not(shape.nr in self.CanvasContent.Disabled):
#                #Falls sich die Fräserkorrektur verändert hat diese in File schreiben
#                stat =shape.Write_GCode(config,postpro)
#                status=status*stat
#
#        #Maschine auf den Endwert positinieren
#        postpro.rap_pos_xy(PointClass(x=config.axis1_st_en.get(),\
#                                              y=config.axis2_st_en.get()))
#
#        #Schreiben der Standardwert am Ende        
#        string=postpro.write_gcode_en(self.ExportParas)
#
#        if status==1:
#            self.textbox.prt(_("\nSuccessfully generated G-Code"))
#            self.master.update_idletasks()
#
#        else:
#            self.textbox.prt(_("\nError during G-Code Generation"))
#            self.master.update_idletasks()
#
#                    
#        #Drucken in den Stdout, speziell fuer EMC2 
#        if postpro.write_to_stdout:
#            #print(string)
#            self.ende()     
#        else:
#            #Exportieren der Daten
#                try:
#                    #Abfrage des Namens um das File zu speichern
#                    self.Get_Save_File()
#                    
#                    #Wenn Cancel gedrueckt wurde
#                    if not self.save_filename:
#                        return
#                    
#                    #Das File oeffnen und schreiben    
#                    f = open(self.save_filename, "w")
#                    f.write(string)
#                    f.close()    
#                      
#                except IOError:
#                    showwarning(_("Save As"), _("Cannot save the file."))
#            
#
#    def opt_export_route(self):
#        
#        #Errechnen der Iterationen
#        iter =min(self.config.max_iterations,len(self.CanvasContent.Shapes)*20)
#        
#        #Anfangswerte fuer das Sortieren der Shapes
#        self.shapes_to_write=[]
#        shapes_st_en_points=[]
#        
#        #Alle Shapes die geschrieben werden zusammenfassen
#        for shape_nr in range(len(self.CanvasContent.Shapes)):
#            shape=self.CanvasContent.Shapes[shape_nr]
#            if not(shape.nr in self.CanvasContent.Disabled):
#                self.shapes_to_write.append(shape)
#                shapes_st_en_points.append(shape.get_st_en_points())
#                
#
#        #Hinzufuegen des Start- Endpunkte ausserhalb der Geometrie
#        x_st=self.config.axis1_st_en.get()
#        y_st=self.config.axis2_st_en.get()
#        start=PointClass(x=x_st,y=y_st)
#        ende=PointClass(x=x_st,y=y_st)
#        shapes_st_en_points.append([start,ende])
#
#        #Optimieren der Reihenfolge
#        self.textbox.prt(_("\nTSP Starting"),1)
#                
#        self.TSP=tsp.TSPoptimize(shapes_st_en_points,self.textbox,self.master,self.config)
#        self.textbox.prt(_("\nTSP start values initialised"),1)
#        #self.CanvasContent.path_hdls=[]
#        #self.CanvasContent.plot_opt_route(shapes_st_en_points,self.TSP.opt_route)
#
#        for it_nr in range(iter):
#            #Jeden 10ten Schrit rausdrucken
#            if (it_nr%10)==0:
#                self.textbox.prt((_("\nTSP Iteration nr: %i") %it_nr),1)
#                for hdl in self.CanvasContent.path_hdls:
#                    self.Canvas.canvas.delete(hdl)
#                self.CanvasContent.path_hdls=[]
#                self.CanvasContent.plot_opt_route(shapes_st_en_points,self.TSP.opt_route)
#                self.master.update_idletasks()
#                
#            self.TSP.calc_next_iteration()
#            
#        self.textbox.prt(_("\nTSP done with result:"),1)
#        self.textbox.prt(("\n%s" %self.TSP),1)
#
#        self.viewmenu.entryconfig(6,state=NORMAL)        
#
#    def del_route_and_menuentry(self):
#        try:
#            self.viewmenu.entryconfig(6,state=DISABLED)
#            self.CanvasContent.delete_opt_path()
#        except:
#            pass
#        
    def ShowAbout(self,event):
        ShowAboutInfoClass(self) 

    def CloseWindow(self,event):
        #Framemanager deinitialisieren
        self._mgr.UnInit()
        #Den Frame löschen
        self.Destroy()
      
        
class MyTreeClass(wx.TreeCtrl):
    def __init__(self,parent,id):
        wx.TreeCtrl.__init__(self, parent, id,wx.DefaultPosition, wx.Size(200,150))
        self.AddElements()
    
    def AddElements(self):
    
        root = self.AddRoot("AUI Project") 
        for i in range(5): 
            item = self.AppendItem(root, "Item " + str(i)) 
            for ii in range(5): 
                self.AppendItem(item, "Subitem " + str(ii)) 
        
        self.Expand(root) 
        
        
class MyMessagesClass(wx.TextCtrl):
    def __init__(self,parent,id):
        wx.TextCtrl.__init__(self,parent,id,'',
                            wx.DefaultPosition, wx.Size(200,100),
                            wx.SUNKEN_BORDER | wx.TE_MULTILINE | wx.TE_READONLY)
                            

        self.DEBUG=DEBUG
                            

        
        self.prt(_('%s, Version: %s' %(APPNAME.capitalize(),VERSION)))
        self.begpos=self.GetLastPosition()

  
        #Binding fuer Contextmenu
        self.Bind(wx.EVT_RIGHT_DOWN, self.TextContextmenu)

    def SetDebuglevel(self,DEBUG=0):
        self.DEBUG=DEBUG
#        if DEBUG:
#            self.MyMessages.config(height=15)
            
    def prt(self,text='',DEBUGLEVEL=0):

        if self.DEBUG>=DEBUGLEVEL:
            self.AppendText(text) 
            
    #Contextmenu Text mit Bindings beim Rechtsklick
    def TextContextmenu(self,event):

        # only do this part the first time so the events are only bound once
        # Yet another anternate way to do IDs. Some prefer them up top to
        # avoid clutter, some prefer them close to the object of interest
        # for clarity. 
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.TextDelete, id=self.popupID1)

        # make a menu
        menu = wx.Menu()
        menu.Append(self.popupID1, _('Delete text entries'),_('Delete all messages up to line one'))
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()
     
    def TextDelete(self,event):    
        self.Remove(self.begpos,self.GetLastPosition())


class MyLayersClass(wx.TextCtrl):
    def __init__(self,parent,id):
        wx.TextCtrl.__init__(self,parent,id,'Layers - sample text',
                            wx.DefaultPosition, wx.Size(200,50),
                            wx.NO_BORDER | wx.TE_MULTILINE)



class MyGraphicClass(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id,  style=wx.SUNKEN_BORDER)

  
        # Add the Canvas
        NC = NavCanvas.NavCanvas(self,
                                     Debug = 0,
                                     BackgroundColor = "WHITE")

        self.Canvas = NC.Canvas # reference the contained FloatCanvas

        self.MsgWindow = wx.TextCtrl(self, wx.ID_ANY,
                                     "Look Here for output from events\n",
                                     style = (wx.TE_MULTILINE |
                                              wx.TE_READONLY |
                                              wx.SUNKEN_BORDER))
                                            
        MainSizer = wx.BoxSizer(wx.VERTICAL)
        MainSizer.Add(NC, 6, wx.EXPAND)
        MainSizer.Add(self.MsgWindow, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(MainSizer)

        self.Canvas.Bind(FloatCanvas.EVT_MOTION, self.OnMove) 
        self.Canvas.Bind(FloatCanvas.EVT_MOUSEWHEEL, self.OnWheel) 

        self.EventsAreBound = False
        
        self.BindAllMouseEvents()
        
        ## getting all the colors for random objects
        wx.lib.colourdb.updateColourDB()
        self.colors = wx.lib.colourdb.getColourList()
        
        self.DrawTest(None)
        
        return None

    def Log(self, text):
        self.MsgWindow.AppendText(text)
        if not text[-1] == "\n":
            self.MsgWindow.AppendText("\n")
        

    def BindAllMouseEvents(self):
        if not self.EventsAreBound:
            ## Here is how you catch FloatCanvas mouse events
            self.Canvas.Bind(FloatCanvas.EVT_LEFT_DOWN, self.OnLeftDown) 
            self.Canvas.Bind(FloatCanvas.EVT_LEFT_UP, self.OnLeftUp)
            self.Canvas.Bind(FloatCanvas.EVT_LEFT_DCLICK, self.OnLeftDouble) 

            self.Canvas.Bind(FloatCanvas.EVT_MIDDLE_DOWN, self.OnMiddleDown) 
            self.Canvas.Bind(FloatCanvas.EVT_MIDDLE_UP, self.OnMiddleUp) 
            self.Canvas.Bind(FloatCanvas.EVT_MIDDLE_DCLICK, self.OnMiddleDouble) 

            self.Canvas.Bind(FloatCanvas.EVT_RIGHT_DOWN, self.OnRightDown) 
            self.Canvas.Bind(FloatCanvas.EVT_RIGHT_UP, self.OnRightUp) 
            self.Canvas.Bind(FloatCanvas.EVT_RIGHT_DCLICK, self.OnRightDouble) 

        self.EventsAreBound = True


    def UnBindAllMouseEvents(self):
        ## Here is how you unbind FloatCanvas mouse events
        self.Canvas.Unbind(FloatCanvas.EVT_LEFT_DOWN)
        self.Canvas.Unbind(FloatCanvas.EVT_LEFT_UP)
        self.Canvas.Unbind(FloatCanvas.EVT_LEFT_DCLICK)

        self.Canvas.Unbind(FloatCanvas.EVT_MIDDLE_DOWN)
        self.Canvas.Unbind(FloatCanvas.EVT_MIDDLE_UP)
        self.Canvas.Unbind(FloatCanvas.EVT_MIDDLE_DCLICK)

        self.Canvas.Unbind(FloatCanvas.EVT_RIGHT_DOWN)
        self.Canvas.Unbind(FloatCanvas.EVT_RIGHT_UP)
        self.Canvas.Unbind(FloatCanvas.EVT_RIGHT_DCLICK)

        self.EventsAreBound = False


    def PrintCoords(self,event):
        self.Log("coords are: %s"%(event.Coords,))
        self.Log("pixel coords are: %s\n"%(event.GetPosition(),))

    def OnSavePNG(self, event=None):
        import os
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir=os.getcwd(), 
            defaultFile="", wildcard="*.png", style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not(path[-4:].lower() == ".png"):
                path = path+".png"
            self.Canvas.SaveAsImage(path)

                
    def OnLeftDown(self, event):
        self.Log("LeftDown")
        self.PrintCoords(event)

    def OnLeftUp(self, event):
        self.Log("LeftUp")
        self.PrintCoords(event)

    def OnLeftDouble(self, event):
        self.Log("LeftDouble")
        self.PrintCoords(event)

    def OnMiddleDown(self, event):
        self.Log("MiddleDown")
        self.PrintCoords(event)

    def OnMiddleUp(self, event):
        self.Log("MiddleUp")
        self.PrintCoords(event)

    def OnMiddleDouble(self, event):
        self.Log("MiddleDouble")
        self.PrintCoords(event)

    def OnRightDown(self, event):
        self.Log("RightDown")
        self.PrintCoords(event)

    def OnRightUp(self, event):
        self.Log("RightUp")
        self.PrintCoords(event)

    def OnRightDouble(self, event):
        self.Log("RightDouble")
        self.PrintCoords(event)

    def OnWheel(self, event):
        self.Log("Mouse Wheel")
        self.PrintCoords(event)
        Rot = event.GetWheelRotation()
        Rot = Rot / abs(Rot) * 0.1
        if event.ControlDown(): # move left-right
            self.Canvas.MoveImage( (Rot, 0), "Panel" )
        else: # move up-down
            self.Canvas.MoveImage( (0, Rot), "Panel" )
            
    def OnMove(self, event):
        """
        Updates the status bar with the world coordinates
        """
        #self.SetStatusText("%.2f, %.2f"%tuple(event.Coords))
        event.Skip()


    def ZoomToFit(self,event):
        self.Canvas.ZoomToBB()

    def Clear(self,event = None):
        self.UnBindAllMouseEvents()
        self.Canvas.InitAll()
        self.Canvas.Draw()

    def OnQuit(self,event):
        self.Close(True)

    def OnCloseWindow(self, event):
        self.Destroy()

    def DrawTest(self,event=None):
        """
        This demo draws a few of everything

        """
        
        wx.GetApp().Yield(True)

        Range = (-10,10)
        colors = self.colors

        Canvas = self.Canvas

        Canvas.InitAll()
        #            
        ## these set the limits for how much you can zoom in and out
        Canvas.MinScale = 14
        Canvas.MaxScale = 500
        

        ############# Random tests of everything ##############

        # Rectangles
        for i in range(3):
            xy = (random.uniform(Range[0],Range[1]),random.uniform(Range[0],Range[1]))
            lw = random.randint(1,5)
            cf = random.randint(0,len(colors)-1)
            wh = (random.randint(1,5), random.randint(1,5))
            Canvas.AddRectangle(xy, wh, LineWidth = lw, FillColor = colors[cf])

        # Ellipses
        for i in range(3):
            xy = (random.uniform(Range[0],Range[1]),random.uniform(Range[0],Range[1]))
            lw = random.randint(1,5)
            cf = random.randint(0,len(colors)-1)
            h = random.randint(1,5)
            w = random.randint(1,5)
            Canvas.AddEllipse(xy, (h,w), LineWidth = lw,FillColor = colors[cf])

        # Points
        for i in range(5):
            xy = (random.uniform(Range[0],Range[1]),random.uniform(Range[0],Range[1]))
            D = random.randint(1,50)
            cf = random.randint(0,len(colors)-1)
            Canvas.AddPoint(xy, Color = colors[cf], Diameter = D)

        # SquarePoints
        for i in range(500):
            xy = (random.uniform(Range[0],Range[1]),random.uniform(Range[0],Range[1]))
            S = random.randint(1, 50)
            cf = random.randint(0,len(colors)-1)
            Canvas.AddSquarePoint(xy, Color = colors[cf], Size = S)

        # Circles
        for i in range(5):
            xy = (random.uniform(Range[0],Range[1]),random.uniform(Range[0],Range[1]))
            D = random.randint(1,5)
            lw = random.randint(1,5)
            cf = random.randint(0,len(colors)-1)
            cl = random.randint(0,len(colors)-1)
            Canvas.AddCircle(xy, D, LineWidth = lw, LineColor = colors[cl], FillColor = colors[cf])
            Canvas.AddText("Circle # %i"%(i), xy, Size = 12, BackgroundColor = None, Position = "cc")
        # Lines
        for i in range(5):
            points = []
            for j in range(random.randint(2,10)):
                point = (random.randint(Range[0],Range[1]),random.randint(Range[0],Range[1]))
                points.append(point)
            lw = random.randint(1,10)
            cf = random.randint(0,len(colors)-1)
            cl = random.randint(0,len(colors)-1)
            Canvas.AddLine(points, LineWidth = lw, LineColor = colors[cl])
        # Polygons
        for i in range(3):
            points = []
            for j in range(random.randint(2,6)):
                point = (random.uniform(Range[0],Range[1]),random.uniform(Range[0],Range[1]))
                points.append(point)
            lw = random.randint(1,6)
            cf = random.randint(0,len(colors)-1)
            cl = random.randint(0,len(colors)-1)
            Canvas.AddPolygon(points,
                                   LineWidth = lw,
                                   LineColor = colors[cl],
                                   FillColor = colors[cf],
                                   FillStyle = 'Solid')


        # Text
        String = "Unscaled text"
        for i in range(3):
            ts = random.randint(10,40)
            cf = random.randint(0,len(colors)-1)
            xy = (random.uniform(Range[0],Range[1]),random.uniform(Range[0],Range[1]))
            Canvas.AddText(String, xy, Size = ts, Color = colors[cf], Position = "cc")

        # Scaled Text
        String = "Scaled text"
        for i in range(3):
            ts = random.random()*3 + 0.2
            cf = random.randint(0,len(colors)-1)
            Point = (random.uniform(Range[0],Range[1]),random.uniform(Range[0],Range[1]))
            Canvas.AddScaledText(String, Point, Size = ts, Color = colors[cf], Position = "cc")


        # ArrowLines
        for i in range(5):
            points = []
            for j in range(random.randint(2,10)):
                point = (random.randint(Range[0],Range[1]),random.randint(Range[0],Range[1]))
                points.append(point)
            lw = random.randint(1,10)
            cf = random.randint(0,len(colors)-1)
            cl = random.randint(0,len(colors)-1)
            Canvas.AddArrowLine(points, LineWidth = lw, LineColor = colors[cl], ArrowHeadSize= 16)


        Canvas.ZoomToBB()

#
#class ExportParasClass:
#    def __init__(self,master=None,config=None,postpro=None):
#        self.master=master
#  
#        self.nb = NotebookClass(self.master,width=240)
#
#        # uses the notebook's frame
#        self.nb_f1 = Frame(self.nb())
#        self.nb_f2 = Frame(self.nb())
#
#        # keeps the reference to the radiobutton (optional)
#        self.nb.add_screen(self.nb_f1, _("Coordinates"))
#        self.nb.add_screen(self.nb_f2, _("File Beg. & End"))
#
#        self.nb_f1.columnconfigure(0,weight=1)
#        self.nb_f2.columnconfigure(0,weight=1)        
#    
#        self.erstelle_eingabefelder(config)
#        self.erstelle_textfelder(config)
#
#        self.gcode_be.insert(END,postpro.gcode_be)
#        self.gcode_en.insert(END,postpro.gcode_en)
#
#
#    def erstelle_eingabefelder(self,config):
#       
#        f1=Frame(self.nb_f1,relief = GROOVE,bd = 2)
#        f1.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
#        f2=Frame(self.nb_f1,relief = GROOVE,bd = 2)
#        f2.grid(row=1,column=0,padx=2,pady=2,sticky=N+W+E)
#        f3=Frame(self.nb_f1,relief = GROOVE,bd = 2)
#        f3.grid(row=2,column=0,padx=2,pady=2,sticky=N+W+E)
#    
#        f1.columnconfigure(0,weight=1)
#        f2.columnconfigure(0,weight=1)
#        f3.columnconfigure(0,weight=1)        
#   
#        Label(f1, text=_("Tool diameter [mm]:"))\
#                .grid(row=0,column=0,sticky=N+W,padx=4)
#        Entry(f1,width=7,textvariable=config.tool_dia)\
#                .grid(row=0,column=1,sticky=N+E)
#
#        Label(f1, text=_("Start radius (for tool comp.) [mm]:"))\
#                .grid(row=1,column=0,sticky=N+W,padx=4)
#        Entry(f1,width=7,textvariable=config.start_rad)\
#                .grid(row=1,column=1,sticky=N+E)        
#
#        Label(f2, text=(_("Start at %s [mm]:") %config.ax1_letter))\
#                .grid(row=0,column=0,sticky=N+W,padx=4)
#        Entry(f2,width=7,textvariable=config.axis1_st_en)\
#                .grid(row=0,column=1,sticky=N+E)
#
#        Label(f2, text=(_("Start at %s [mm]:") %config.ax2_letter))\
#                .grid(row=1,column=0,sticky=N+W,padx=4)
#        Entry(f2,width=7,textvariable=config.axis2_st_en)\
#                .grid(row=1,column=1,sticky=N+E)
#
#        Label(f2, text=(_("%s retraction area [mm]:") %config.ax3_letter))\
#                .grid(row=2,column=0,sticky=N+W,padx=4)
#        Entry(f2,width=7,textvariable=config.axis3_retract)\
#                .grid(row=2,column=1,sticky=N+E)
#
#        Label(f2, text=(_("%s safety margin [mm]:") %config.ax3_letter))\
#                .grid(row=3,column=0,sticky=N+W,padx=4)
#        Entry(f2,width=7,textvariable=config.axis3_safe_margin)\
#                .grid(row=3,column=1,sticky=N+E)
#
#        Label(f2, text=(_("%s infeed depth [mm]:") %config.ax3_letter))\
#                .grid(row=4,column=0,sticky=N+W,padx=4)
#        Entry(f2,width=7,textvariable=config.axis3_slice_depth)\
#                .grid(row=4,column=1,sticky=N+E)
#
#        Label(f2, text=(_("%s mill depth [mm]:") %config.ax3_letter))\
#                .grid(row=5,column=0,sticky=N+W,padx=4)
#        Entry(f2,width=7,textvariable=config.axis3_mill_depth)\
#                .grid(row=5,column=1,sticky=N+E)
#
#        Label(f3, text=(_("G1 feed %s-direction [mm/min]:") %config.ax3_letter))\
#                .grid(row=1,column=0,sticky=N+W,padx=4)
#        Entry(f3,width=7,textvariable=config.F_G1_Depth)\
#                .grid(row=1,column=1,sticky=N+E)
#
#        Label(f3, text=(_("G1 feed %s%s-direction [mm/min]:") %(config.ax1_letter,config.ax2_letter)))\
#                .grid(row=2,column=0,sticky=N+W,padx=4)
#        Entry(f3,width=7,textvariable=config.F_G1_Plane)\
#                .grid(row=2,column=1,sticky=N+E)
#
#    def erstelle_textfelder(self,config):
#        f22=Frame(self.nb_f2,relief = FLAT,bd = 1)
#        f22.grid(row=0,column=0,padx=2,pady=2,sticky=N+W+E)
#        f22.columnconfigure(0,weight=1)        
#
#        Label(f22 , text=_("G-Code at the begin of file"))\
#                .grid(row=0,column=0,columnspan=2,sticky=N+W,padx=2)
#        self.gcode_be = Text(f22,width=10,height=8)
#        self.gcode_be_sc = Scrollbar(f22)
#        self.gcode_be.grid(row=1,column=0,pady=2,sticky=E+W)
#        self.gcode_be_sc.grid(row=1,column=1,padx=2,pady=2,sticky=N+S)
#        self.gcode_be_sc.config(command=self.gcode_be.yview)
#        self.gcode_be.config(yscrollcommand=self.gcode_be_sc.set)
#
#        Label(f22, text=_("G-Code at the end of file"))\
#                .grid(row=2,column=0,columnspan=2,sticky=N+W,padx=2)
#        self.gcode_en = Text(f22,width=10,height=5)
#        self.gcode_en_sc = Scrollbar(f22)
#        self.gcode_en.grid(row=3,column=0,pady=2,sticky=E+W)
#        self.gcode_en_sc.grid(row=3,column=1,padx=2,pady=2,sticky=N+S)
#        self.gcode_en_sc.config(command=self.gcode_en.yview)
#        self.gcode_en.config(yscrollcommand=self.gcode_en_sc.set)
#
#        f22.columnconfigure(0,weight=1)
#        f22.rowconfigure(1,weight=0)
#        f22.rowconfigure(3,weight=0)
#         
##Klasse zum Erstellen des Plots
#class CanvasClass:
#    def __init__(self, master = None,text=None):
#        
#        #Übergabe der Funktionswerte
#        self.master=master
#        self.Content=[]
#
#        #Erstellen der Standardwerte
#        self.lastevent=[]
#        self.sel_rect_hdl=[]
#        self.dir_var = IntVar()
#        self.dx=0.0
#        self.dy=0.0
#        self.scale=1.0
#
#        #Wird momentan nicht benoetigt, eventuell fuer Beschreibung von Aktionen im Textfeld #self.text=text
#
#        #Erstellen des Labels am Unteren Rand fuer Status Leiste        
#        self.label=Label(self.master, text=_("Curser Coordinates: X=0.0, Y=0.0, Scale: 1.00"),bg="white",anchor="w")
#        self.label.grid(row=1,column=0,sticky=E+W)
#
#        #Canvas Erstellen und Fenster ausfuellen        
#        self.canvas=Canvas(self.master,width=650,height=500, bg = "white")
#        self.canvas.grid(row=0,column=0,sticky=N+E+S+W)
#        self.master.columnconfigure(0,weight=1)
#        self.master.rowconfigure(0,weight=1)
#
#
#        #Binding fuer die Bewegung des Mousezeigers
#        self.canvas.bind("<Motion>", self.moving)
#
#        #Bindings fuer Selektieren
#        self.canvas.bind("<Button-1>", self.select_cont)
#        
#        #Eventuell mit Abfrage probieren???????????????????????????????????????????
#        self.canvas.bind("<Shift-Button-1>", self.multiselect_cont)
#        self.canvas.bind("<B1-Motion>", self.select_rectangle)
#        self.canvas.bind("<ButtonRelease-1>", self.select_release)
#
#        #Binding fuer Contextmenu
#        self.canvas.bind("<Button-3>", self.make_contextmenu)
#
#        #Bindings fuer Zoom und Bewegen des Bilds        
#        self.canvas.bind("<Control-Button-1>", self.mouse_move)
#        self.canvas.bind("<Control-B1-Motion>", self.mouse_move_motion)
#        self.canvas.bind("<Control-ButtonRelease-1>", self.mouse_move_release)
#        self.canvas.bind("<Control-Button-3>", self.mouse_zoom)
#        self.canvas.bind("<Control-B3-Motion>", self.mouse_zoom_motion)
#        self.canvas.bind("<Control-ButtonRelease-3>", self.mouse_zoom_release)   
#
#    #Callback fuer das Bewegen der Mouse mit Darstellung in untere Leiste
#    def moving(self,event):
#        x=self.dx+(event.x/self.scale)
#        y=self.dy+(self.canvas.winfo_height()-event.y)/self.scale
#
#        if self.scale<1:
#            self.label['text']=(_("Curser Coordinates: X= %5.0f Y= %5.0f , Scale: %5.3f") \
#                                %(x,y,self.scale))
#            
#        elif (self.scale>=1)and(self.scale<10):      
#            self.label['text']=(_("Curser Coordinates: X= %5.1f Y= %5.1f , Scale: %5.2f") \
#                                %(x,y,self.scale))
#        elif self.scale>=10:      
#            self.label['text']=(_("Curser Coordinates: X= %5.2f Y= %5.2f , Scale: %5.1f") \
#                                %(x,y,self.scale))
#        
#    #Callback fuer das Auswählen von Elementen
#    def select_cont(self,event):
#        #Abfrage ob ein Contextfenster offen ist, speziell fuer Linux
#        self.schliesse_contextmenu()
#        
#        self.moving(event)
#        self.Content.deselect()
#        self.sel_rect_hdl=Rectangle(self.canvas,event.x,event.y,event.x,event.y,outline="grey") 
#        self.lastevent=event
#
#    def multiselect_cont(self,event):
#        #Abfrage ob ein Contextfenster offen ist, speziell fuer Linux
#        self.schliesse_contextmenu()
#        
#        self.sel_rect_hdl=Rectangle(self.canvas,event.x,event.y,event.x,event.y,outline="grey") 
#        self.lastevent=event
#
#    def select_rectangle(self,event):
#        self.moving(event)
#        self.canvas.coords(self.sel_rect_hdl,self.lastevent.x,self.lastevent.y,\
#                           event.x,event.y)
#
#    def select_release(self,event):
# 
#        dx=self.lastevent.x-event.x
#        dy=self.lastevent.y-event.y
#        self.canvas.delete(self.sel_rect_hdl)
#        
#        #Beim Auswählen sollen die Direction Pfeile geloescht werden!!!!!!!!!!!!!!!!!!        
#        #self.Content.delete_opt_path()   
#        
#        #Wenn mehr als 6 Pixel gezogen wurde Enclosed        
#        if (abs(dx)+abs(dy))>6:
#            items=self.canvas.find_overlapping(event.x,event.y,event.x+dx,event.y+dy)
#            mode='multi'
#        else:
#            #items=self.canvas.find_closest(event.x, event.y)
#            items=self.canvas.find_overlapping(event.x-3,event.y-3,event.x+3,event.y+3)
#            mode='single'
#            
#        self.Content.addselection(items,mode)
#
#    #Callback fuer Bewegung des Bildes
#    def mouse_move(self,event):
#        self.master.config(cursor="fleur")
#        self.lastevent=event
#
#    def mouse_move_motion(self,event):
#        self.moving(event)
#        dx=event.x-self.lastevent.x
#        dy=event.y-self.lastevent.y
#        self.dx=self.dx-dx/self.scale
#        self.dy=self.dy+dy/self.scale
#        self.canvas.move(ALL,dx,dy)
#        self.lastevent=event
#
#    def mouse_move_release(self,event):
#        self.master.config(cursor="")      
#
#    #Callback fuer das Zoomen des Bildes     
#    def mouse_zoom(self,event):
#        self.canvas.focus_set()
#        self.master.config(cursor="sizing")
#        self.firstevent=event
#        self.lastevent=event
#
#    def mouse_zoom_motion(self,event):
#        self.moving(event)
#        dy=self.lastevent.y-event.y
#        sca=(1+(dy*3)/float(self.canvas.winfo_height()))
#       
#        self.dx=(self.firstevent.x+((-self.dx*self.scale)-self.firstevent.x)*sca)/sca/-self.scale
#        eventy=self.canvas.winfo_height()-self.firstevent.y
#        self.dy=(eventy+((-self.dy*self.scale)-eventy)*sca)/sca/-self.scale
#        
#        self.scale=self.scale*sca
#        self.canvas.scale( ALL, self.firstevent.x,self.firstevent.y,sca,sca)
#        self.lastevent=event
#
#        self.Content.plot_cut_info() 
#        self.Content.plot_wp_zero()
#
#    def mouse_zoom_release(self,event):
#        self.master.config(cursor="")
#                
#    #Contextmenu mit Bindings beim Rechtsklick
#    def make_contextmenu(self,event):
#        self.lastevent=event
#
#        #Abfrage ob das Contextfenster schon existiert, speziell fuer Linux
#        self.schliesse_contextmenu()
#            
#        #Contextmenu erstellen zu der Geometrie        
#        popup = Menu(self.canvas,tearoff=0)
#        self.popup=popup
#        popup.add_command(label=_('Invert Selection'),command=self.Content.invert_selection)
#        popup.add_command(label=_('Disable Selection'),command=self.Content.disable_selection)
#        popup.add_command(label=_('Enable Selection'),command=self.Content.enable_selection)
#
#        popup.add_separator()
#        popup.add_command(label=_('Switch Direction'),command=self.Content.switch_shape_dir)
#        
#        #Untermenu fuer die Fräserkorrektur
#        self.dir_var.set(self.Content.calc_dir_var())
#        cut_cor_menu = Menu(popup,tearoff=0)
#        cut_cor_menu.add_checkbutton(label=_("G40 No correction"),\
#                                     variable=self.dir_var,onvalue=0,\
#                                     command=lambda:self.Content.set_cut_cor(40))
#        cut_cor_menu.add_checkbutton(label=_("G41 Cutting left"),\
#                                     variable=self.dir_var,onvalue=1,\
#                                     command=lambda:self.Content.set_cut_cor(41))
#        cut_cor_menu.add_checkbutton(label=_("G42 Cutting right"),\
#                                     variable=self.dir_var,onvalue=2,\
#                                     command=lambda:self.Content.set_cut_cor(42))
#        popup.add_cascade(label=_('Set Cutter Correction'),menu=cut_cor_menu)
#
#        #Menus Disablen wenn nicht ausgewählt wurde        
#        if len(self.Content.Selected)==0:
#            popup.entryconfig(0,state=DISABLED)
#            popup.entryconfig(1,state=DISABLED)
#            popup.entryconfig(2,state=DISABLED)
#            popup.entryconfig(4,state=DISABLED)
#            popup.entryconfig(5,state=DISABLED)
#
#        popup.post(event.x_root, event.y_root)
#        
#    #Speziell fuer Linux falls das Contextmenu offen ist dann schliessen
#    def schliesse_contextmenu(self):
#        try:
#            self.popup.destroy()
#            del(self.popup)
#        except:
#            pass
#
#    def autoscale(self):
#
#        #Rand der um die Extreme des Elemente dargestellt wird        
#        rand=20
#
#        #Alles auf die 0 Koordinaten verschieben, dass später DX und DY Berechnung richtig erfolgt       
#        self.canvas.move(ALL,self.dx*self.scale,-self.canvas.winfo_height()-self.dy*self.scale)
#        self.dx=0;
#        self.dy=-self.canvas.winfo_height()/self.scale
#
#        #Umriss aller Elemente
#        d=self.canvas.bbox(ALL)
#        cx=(d[0]+d[2])/2
#        cy=(d[1]+d[3])/2
#        dx=d[2]-d[0]
#        dy=d[3]-d[1]
#
#        #Skalierung des Canvas errechnen
#        xs=float(dx)/(self.canvas.winfo_width()-rand)
#        ys=float(dy)/(self.canvas.winfo_height()-rand)
#        scale=1/max(xs,ys)
#        
#        #Skalieren der Elemente        
#        self.canvas.scale( ALL,0,0,scale,scale)
#        self.scale=self.scale*scale
#
#        #Verschieben der Elemente zum Mittelpunkt        
#        dx=self.canvas.winfo_width()/2-cx*scale
#        dy=self.canvas.winfo_height()/2-cy*scale
#        self.dy=self.dy/scale
#        self.dx=self.dx/scale
#        self.canvas.move(ALL,dx,dy)
#        
#        #Mouse Position errechnen
#        self.dx=self.dx-dx/self.scale
#        self.dy=self.dy+dy/self.scale
#
#        self.Content.plot_cut_info()
#        self.Content.plot_wp_zero()
#        
#    def get_can_coordinates(self,x_st,y_st):
#        x_ca=(x_st-self.dx)*self.scale
#        y_ca=(y_st-self.dy)*self.scale-self.canvas.winfo_height()
#        return x_ca, y_ca
#
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
#        
##Klasse mit den Inhalten des Canvas & Verbindung zu den Konturen
#class CanvasContentClass:
#    def __init__(self,Canvas,textbox,config):
#        self.Canvas=Canvas
#        self.textbox=textbox
#        self.config=config
#        self.Shapes=[]
#        self.LayerContents=[]
#        self.EntitieContents=[]
#        self.Selected=[]
#        self.Disabled=[]
#        self.wp_zero_hdls=[]
#        self.dir_hdls=[]
#        self.path_hdls=[]
#        
#
#        #Anfangswert fuer das Ansicht Toggle Menu
#        self.toggle_wp_zero=IntVar()
#        self.toggle_wp_zero.set(1)
#
#        self.toggle_start_stop=IntVar()
#        self.toggle_start_stop.set(0)
#
#        self.toggle_show_disabled=IntVar()
#        self.toggle_show_disabled.set(0)  
#        
#    def __str__(self):
#        s='\nNr. of Shapes -> %s' %len(self.Shapes)
#        for lay in self.LayerContents:
#            s=s+'\n'+str(lay)
#        for ent in self.EntitieContents:
#            s=s+'\n'+str(ent)
#        s=s+'\nSelected -> %s'%(self.Selected)\
#           +'\nDisabled -> %s'%(self.Disabled)
#        return s
#
#    def calc_dir_var(self):
#        if len(self.Selected)==0:
#            return -1
#        dir=self.Shapes[self.Selected[0]].cut_cor
#        for shape_nr in self.Selected[1:len(self.Selected)]: 
#            if not(dir==self.Shapes[shape_nr].cut_cor):
#                return -1   
#        return dir-40
#                
#    #Erstellen des Gesamten Ausdrucks      
#    def makeplot(self,values):
#        self.values=values
#
#        #Loeschen des Inhalts
#        self.Canvas.canvas.delete(ALL)
#        
#        #Standardwerte fuer scale, dx, dy zuweisen
#        self.Canvas.scale=1
#        self.Canvas.dx=0
#        self.Canvas.dy=-self.Canvas.canvas.winfo_height()
#
#        #Zuruecksetzen der Konturen
#        self.Shapes=[]
#        self.LayerContents=[]
#        self.EntitieContents=[]
#        self.Selected=[]
#        self.Disabled=[]
#        self.wp_zero_hdls=[]
#        self.dir_hdls=[]
#        self.path_hdls=[]
#
#        #Start mit () bedeutet zuweisen der Entities -1 = Standard
#        self.make_shapes(p0=PointClass(x=0,y=0),sca=[1,1,1],rot=0.0)
#        self.plot_shapes()
#        self.LayerContents.sort()
#        self.EntitieContents.sort()
#
#        #Autoscale des Canvas        
#        self.Canvas.autoscale()
#
#    def make_shapes(self,EntName="Entities",p0=PointClass(x=0,y=0),sca=[1,1,1],rot=0.0):
#
#        if EntName=="Entities":
#            ent_nr=-1
#            entities=self.values.entities
#        else:
#            ent_nr=self.values.Get_Block_Nr(EntName)
#            entities=self.values.blocks.Entities[ent_nr]
#        #Zuweisen der Geometrien in die Variable geos & Konturen in cont
#        ent_geos=entities.geo
#        cont=entities.cont
#        basep=entities.basep
#        
#        #Schleife fuer die Anzahl der Konturen 
#        for c_nr in range(len(cont)):
#            #Abfrage falls es sich bei der Kontur um ein Insert eines Blocks handelt
#            if ent_geos[cont[c_nr].order[0][0]].Typ=="Insert":
#                ent_geo=ent_geos[cont[c_nr].order[0][0]]
#                self.make_shapes(ent_geo.BlockName,\
#                                    p0-basep+ent_geo.Point,\
#                                    [ent_geo.Scale[0]*sca[0],ent_geo.Scale[1]*sca[1],ent_geo.Scale[2]*sca[2]],\
#                                    ent_geo.rot)
#            else:
#                #Schleife fuer die Anzahl der Geometrien
#                self.Shapes.append(ShapeClass(len(self.Shapes),\
#                                                ent_nr,\
#                                                c_nr,\
#                                                cont[c_nr].closed,\
#                                                p0,\
#                                                basep,\
#                                                sca[:],\
#                                                rot,\
#                                                40,\
#                                                cont[c_nr].length*sca[0],\
#                                                [],\
#                                                []))
#                for ent_geo_nr in range(len(cont[c_nr].order)):
#                    ent_geo=ent_geos[cont[c_nr].order[ent_geo_nr][0]]
#                    if cont[c_nr].order[ent_geo_nr][1]:
#                        ent_geo.geo.reverse()
#                        for geo in ent_geo.geo:
#                            geo=copy(geo)
#                            geo.reverse()
#                            self.Shapes[-1].geos.append(geo)
#
#                        ent_geo.geo.reverse()
#                    else:
#                        for geo in ent_geo.geo:
#                            self.Shapes[-1].geos.append(copy(geo))
#                        
#                self.addtoLayerContents(self.Shapes[-1].nr,ent_geo.Layer_Nr)
#                self.addtoEntitieContents(self.Shapes[-1].nr,ent_nr,c_nr)
#
#    def plot_shapes(self):
#        for shape in self.Shapes:
#            shape.plot2can(self.Canvas.canvas)
#            
#    #Drucken des Werkstuecknullpunkts
#    def plot_wp_zero(self):
#        for hdl in self.wp_zero_hdls:
#            self.Canvas.canvas.delete(hdl) 
#        self.wp_zero_hdls=[]
#        if self.toggle_wp_zero.get(): 
#            x_zero,y_zero=self.Canvas.get_can_coordinates(0,0)
#            xy=x_zero-8,-y_zero-8,x_zero+8,-y_zero+8
#            hdl=Oval(self.Canvas.canvas,xy,outline="gray")
#            self.wp_zero_hdls.append(hdl)
#
#            xy=x_zero-6,-y_zero-6,x_zero+6,-y_zero+6
#            hdl=Arc(self.Canvas.canvas,xy,start=0,extent=180,style="pieslice",outline="gray")
#            self.wp_zero_hdls.append(hdl)
#            hdl=Arc(self.Canvas.canvas,xy,start=90,extent=180,style="pieslice",outline="gray")
#            self.wp_zero_hdls.append(hdl)
#            hdl=Arc(self.Canvas.canvas,xy,start=270,extent=90,style="pieslice",outline="gray",fill="gray")
#            self.wp_zero_hdls.append(hdl)
#    def plot_cut_info(self):
#        for hdl in self.dir_hdls:
#            self.Canvas.canvas.delete(hdl) 
#        self.dir_hdls=[]
#
#        if not(self.toggle_start_stop.get()):
#            draw_list=self.Selected[:]
#        else:
#            draw_list=range(len(self.Shapes))
#               
#        for shape_nr in draw_list:
#            if not(shape_nr in self.Disabled):
#                self.dir_hdls+=self.Shapes[shape_nr].plot_cut_info(self.Canvas,self.config)
#
#
#    def plot_opt_route(self,shapes_st_en_points,route):
#        #Ausdrucken der optimierten Route
#        for en_nr in range(len(route)):
#            if en_nr==0:
#                st_nr=-1
#                col='gray'
#            elif en_nr==1:
#                st_nr=en_nr-1
#                col='gray'
#            else:
#                st_nr=en_nr-1
#                col='peru'
#                
#            st=shapes_st_en_points[route[st_nr]][1]
#            en=shapes_st_en_points[route[en_nr]][0]
#
#            x_ca_s,y_ca_s=self.Canvas.get_can_coordinates(st.x,st.y)
#            x_ca_e,y_ca_e=self.Canvas.get_can_coordinates(en.x,en.y)
#
#            self.path_hdls.append(Line(self.Canvas.canvas,x_ca_s,-y_ca_s,x_ca_e,-y_ca_e,fill=col,arrow='last'))
#        self.Canvas.canvas.update()
#
#
#    #Hinzufuegen der Kontur zum Layer        
#    def addtoLayerContents(self,shape_nr,lay_nr):
#        #Abfrage of der gesuchte Layer schon existiert
#        for LayCon in self.LayerContents:
#            if LayCon.LayerNr==lay_nr:
#                LayCon.Shapes.append(shape_nr)
#                return
#
#        #Falls er nicht gefunden wurde neuen erstellen
#        LayerName=self.values.layers[lay_nr].name
#        self.LayerContents.append(LayerContentClass(lay_nr,LayerName,[shape_nr]))
#        
#    #Hinzufuegen der Kontur zu den Entities
#    def addtoEntitieContents(self,shape_nr,ent_nr,c_nr):
#        
#        for EntCon in self.EntitieContents:
#            if EntCon.EntNr==ent_nr:
#                if c_nr==0:
#                    EntCon.Shapes.append([])
#                
#                EntCon.Shapes[-1].append(shape_nr)
#                return
#
#        #Falls er nicht gefunden wurde neuen erstellen
#        if ent_nr==-1:
#            EntName='Entities'
#        else:
#            EntName=self.values.blocks.Entities[ent_nr].Name
#            
#        self.EntitieContents.append(EntitieContentClass(ent_nr,EntName,[[shape_nr]]))
#
#    def delete_opt_path(self):
#        for hdl in self.path_hdls:
#            self.Canvas.canvas.delete(hdl)
#            
#        self.path_hdls=[]
#        
#    def deselect(self): 
#        self.set_shapes_color(self.Selected,'deselected')
#        
#        if not(self.toggle_start_stop.get()):
#            for hdl in self.dir_hdls:
#                self.Canvas.canvas.delete(hdl) 
#            self.dir_hdls=[]
#        
#    def addselection(self,items,mode):
#        for item in items:
#            try:
#                tag=int(self.Canvas.canvas.gettags(item)[-1])
#                if not(tag in self.Selected):
#                    self.Selected.append(tag)
#
#                    self.textbox.prt(_('\n\nAdded shape to selection %s:')%(self.Shapes[tag]),3)
#                    
#                    if mode=='single':
#                        break
#            except:
#                pass
#            
#        self.plot_cut_info()
#        self.set_shapes_color(self.Selected,'selected')
# 
#    def invert_selection(self):
#        new_sel=[]
#        for shape_nr in range(len(self.Shapes)):
#            if (not(shape_nr in self.Disabled)) & (not(shape_nr in self.Selected)):
#                new_sel.append(shape_nr)
#
#        self.deselect()
#        self.Selected=new_sel
#        self.set_shapes_color(self.Selected,'selected')
#        self.plot_cut_info()
#
#        self.textbox.prt(_('\nInverting Selection'),3)
#        
#
#    def disable_selection(self):
#        for shape_nr in self.Selected:
#            if not(shape_nr in self.Disabled):
#                self.Disabled.append(shape_nr)
#        self.set_shapes_color(self.Selected,'disabled')
#        self.Selected=[]
#        self.plot_cut_info()
#
#    def enable_selection(self):
#        for shape_nr in self.Selected:
#            if shape_nr in self.Disabled:
#                nr=self.Disabled.index(shape_nr)
#                del(self.Disabled[nr])
#        self.set_shapes_color(self.Selected,'deselected')
#        self.Selected=[]
#        self.plot_cut_info()
#
#    def show_disabled(self):
#        if (self.toggle_show_disabled.get()==1):
#            self.set_hdls_normal(self.Disabled)
#            self.show_dis=1
#        else:
#            self.set_hdls_hidden(self.Disabled)
#            self.show_dis=0
#
#    def switch_shape_dir(self):
#        for shape_nr in self.Selected:
#            self.Shapes[shape_nr].reverse()
#            self.textbox.prt(_('\n\nSwitched Direction at Shape: %s')\
#                             %(self.Shapes[shape_nr]),3)
#        self.plot_cut_info()
#        
#    def set_cut_cor(self,correction):
#        for shape_nr in self.Selected: 
#            self.Shapes[shape_nr].cut_cor=correction
#            
#            self.textbox.prt(_('\n\nChanged Cutter Correction at Shape: %s')\
#                             %(self.Shapes[shape_nr]),3)
#        self.plot_cut_info() 
#        
#    def set_shapes_color(self,shape_nrs,state):
#        s_shape_nrs=[]
#        d_shape_nrs=[]
#        for shape in shape_nrs:
#            if not(shape in self.Disabled):
#                s_shape_nrs.append(shape)
#            else:
#                d_shape_nrs.append(shape)
#        
#        s_hdls=self.get_shape_hdls(s_shape_nrs)
#        d_hdls=self.get_shape_hdls(d_shape_nrs)
#    
#        if state=='deselected':
#            s_color='black'
#            d_color='gray'
#            self.Selected=[]
#        elif state=='selected':
#            s_color='red'
#            d_color='blue'
#        elif state=='disabled':
#            s_color='gray'
#            d_color='gray'
#            
#        self.set_color(s_hdls,s_color)
#        self.set_color(d_hdls,d_color)
#
#        if (self.toggle_show_disabled.get()==0):
#            self.set_hdls_hidden(d_shape_nrs)
#        
#    def set_color(self,hdls,color):
#        for hdl in hdls:
#            if (self.Canvas.canvas.type(hdl)=="oval") :
#                self.Canvas.canvas.itemconfig(hdl, outline=color)
#            else:
#                self.Canvas.canvas.itemconfig(hdl, fill=color)
#
#    def set_hdls_hidden(self,shape_nrs):
#        hdls=self.get_shape_hdls(shape_nrs)
#        for hdl in hdls:
#            self.Canvas.canvas.itemconfig(hdl,state='hidden')
#
#    def set_hdls_normal(self,shape_nrs):
#        hdls=self.get_shape_hdls(shape_nrs)
#        for hdl in hdls:
#            self.Canvas.canvas.itemconfig(hdl,state='normal')            
#        
#    def get_shape_hdls(self,shape_nrs):        
#        hdls=[]
#        for s_nr in shape_nrs:
#            if type(self.Shapes[s_nr].geos_hdls[0]) is list:
#                for subcont in self.Shapes[s_nr].geos_hdls:
#                    hdls=hdls+subcont
#            else:
#                hdls=hdls+self.Shapes[s_nr].geos_hdls
#        return hdls      
#                                       
#       
#class LayerContentClass:
#    def __init__(self,LayerNr=None,LayerName='',Shapes=[]):
#        self.LayerNr=LayerNr
#        self.LayerName=LayerName
#        self.Shapes=Shapes
#        
#    def __cmp__(self, other):
#         return cmp(self.LayerNr, other.LayerNr)
#
#    def __str__(self):
#        return '\nLayerNr ->'+str(self.LayerNr)+'\nLayerName ->'+str(self.LayerName)\
#               +'\nShapes ->'+str(self.Shapes)
#    
#class EntitieContentClass:
#    def __init__(self,EntNr=None,EntName='',Shapes=[]):
#        self.EntNr=EntNr
#        self.EntName=EntName
#        self.Shapes=Shapes
#
#    def __cmp__(self, other):
#         return cmp(self.EntNr, other.EntNr)        
#        
#    def __str__(self):
#        return '\nEntNr ->'+str(self.EntNr)+'\nEntName ->'+str(self.EntName)\
#               +'\nShapes ->'+str(self.Shapes)
#
class MyConfigClass:
    def __init__(self,MyMessages):
        # Das Standard App Verzeichniss fuer das Betriebssystem abfragen
        self.make_settings_folder()

        # eine ConfigParser Instanz oeffnen und evt. vorhandenes Config File Laden        
        self.parser = ConfigParser.ConfigParser()
        self.cfg_file_name=APPNAME+'_config.cfg'
        self.parser.read(os.path.join(FOLDER,self.cfg_file_name))

        # Falls kein Config File vorhanden ist oder File leer ist neue File anlegen und neu laden
        if len(self.parser.sections())==0:
            self.make_new_Config_file()
            self.parser.read(os.path.join(FOLDER,self.cfg_file_name))
            MyMessages.prt((_('\nNo config file found generated new on at: %s') \
                             %os.path.join(FOLDER,self.cfg_file_name)))
        else:
            MyMessages.prt((_('\nLoading config file:%s') \
                             %os.path.join(FOLDER,self.cfg_file_name)))

        #Tkinter Variablen erstellen zur späteren Verwendung in den Eingabefeldern        
        self.get_all_vars()

        #DEBUG INFORMATIONEN
        #Übergeben des geladenen Debug Level
        MyMessages.SetDebuglevel(DEBUG=self.debug)
        MyMessages.prt(_('\nDebug Level: %i') %(self.debug),1)
        MyMessages.prt(str(self),1)

    def make_settings_folder(self): 
        # create settings folder if necessary 
        try: 
            os.mkdir(FOLDER) 
        except OSError: 
            pass 

    def make_new_Config_file(self):
        self.parser.add_section('Paths') 
        self.parser.set('Paths', 'load_path', 'C:\Users\Christian Kohloeffel\Documents\DXF2GCODE\trunk\dxf')
        self.parser.set('Paths', 'save_path', 'C:\Users\Christian Kohloeffel\Documents')

        self.parser.add_section('Import Parameters') 
        self.parser.set('Import Parameters', 'point_tolerance', 0.01)
        self.parser.set('Import Parameters', 'fitting_tolerance', 0.01)   
                   
        self.parser.add_section('Tool Parameters') 
        self.parser.set('Tool Parameters', 'diameter', 2.0)
        self.parser.set('Tool Parameters', 'start_radius', 0.2)

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

        self.parser.add_section('Axis letters')
        self.parser.set('Axis letters', 'ax1_letter', 'X')
        self.parser.set('Axis letters', 'ax2_letter', 'Y')
        self.parser.set('Axis letters', 'ax3_letter', 'Z')                  

        self.parser.add_section('Route Optimisation')
        self.parser.set('Route Optimisation', 'Begin art','heurestic')
        self.parser.set('Route Optimisation', 'Max. population', 20)
        self.parser.set('Route Optimisation', 'Max. iterations', 300)  
        self.parser.set('Route Optimisation', 'Mutation Rate', 0.95)

        self.parser.add_section('Filters')
        self.parser.set('Filters', 'pstoedit_cmd','C:\Program Files (x86)\pstoedit\pstoedit')
        self.parser.set('Filters', 'pstoedit_opt', ['-f','dxf','-mm'])
                     
        self.parser.add_section('Debug')
        self.parser.set('Debug', 'global_debug_level', 0)         
                
        open_file = open(os.path.join(FOLDER,self.cfg_file_name), "w") 
        self.parser.write(open_file) 
        open_file.close()
            
    def get_all_vars(self):
        try:               
            self.tool_dia=(float(self.parser.get('Tool Parameters','diameter')))

            self.start_rad=(float(self.parser.get('Tool Parameters','start_radius')))        
           
            self.axis1_st_en=(float(self.parser.get('Plane Coordinates','axis1_start_end')))

            self.axis2_st_en=(float(self.parser.get('Plane Coordinates','axis2_start_end')))        
            
            self.axis3_retract=(float(self.parser.get('Depth Coordinates','axis3_retract')))
            
            self.axis3_safe_margin=(float(self.parser.get('Depth Coordinates','axis3_safe_margin')))

            self.axis3_slice_depth=(float(self.parser.get('Depth Coordinates','axis3_slice_depth')))        

            self.axis3_mill_depth=(float(self.parser.get('Depth Coordinates','axis3_mill_depth')))        
            
            self.F_G1_Depth=(float(self.parser.get('Feed Rates','f_g1_depth')))

            self.F_G1_Plane=(float(self.parser.get('Feed Rates','f_g1_plane')))

            self.points_tolerance=(float(self.parser.get('Import Parameters','point_tolerance')))

            self.fitting_tolerance=(float(self.parser.get('Import Parameters','fitting_tolerance')))

            #Zuweisen der Werte fuer die TSP Optimierung
            self.begin_art=self.parser.get('Route Optimisation', 'Begin art')
            self.max_population=int((int(self.parser.get('Route Optimisation', 'Max. population'))/4)*4)
            self.max_iterations=int(self.parser.get('Route Optimisation', 'Max. iterations'))  
            self.mutate_rate=float(self.parser.get('Route Optimisation', 'Mutation Rate', 0.95))

            #Zuweisen der Axis Letters
            self.ax1_letter=self.parser.get('Axis letters', 'ax1_letter')
            self.ax2_letter=self.parser.get('Axis letters', 'ax2_letter')
            self.ax3_letter=self.parser.get('Axis letters', 'ax3_letter')

            #Holen der restlichen Variablen
            #Verzeichnisse
            self.load_path=self.parser.get('Paths','load_path')
            self.save_path=self.parser.get('Paths','save_path')

            #Holen der Commandos fuer pstoedit
            self.pstoedit_cmd=self.parser.get('Filters','pstoedit_cmd')
            self.pstoedit_opt=self.parser.get('Filters','pstoedit_opt')

            #Setzen des Globalen Debug Levels
            self.debug=int(self.parser.get('Debug', 'global_debug_level'))
            
        except:
            dial=wx.MessageDialog(None, _("Please delete or correct\n %s")\
                      %(os.path.join(FOLDER,self.cfg_file_name)),_("Error during reading config file"), wx.OK | 
            wx.ICON_ERROR)
            dial.ShowModal()

            raise Exception, _("Problem during import from INI File") 
            
    def __str__(self):

        str=''
        for section in self.parser.sections(): 
            str= str +"\nSection: "+section 
            for option in self.parser.options(section): 
                str= str+ "\n   -> %s=%s" % (option, self.parser.get(section, option))
        return str
class MyPostprocessorClass:
    def __init__(self,config=None,MyMessages=None):
        self.string=''
        self.MyMessages=MyMessages
        self.config=config

        # eine ConfigParser Instanz oeffnen und evt. vorhandenes Config File Laden        
        self.parser = ConfigParser.ConfigParser()
        self.postpro_file_name=APPNAME+'_postprocessor.cfg'
        self.parser.read(os.path.join(FOLDER,self.postpro_file_name))

        # Falls kein Postprocessor File vorhanden ist oder File leer ist neue File anlegen und neu laden
        if len(self.parser.sections())==0:
            self.make_new_postpro_file()
            self.parser.read(os.path.join(FOLDER,self.postpro_file_name))
            MyMessages.prt((_('\nNo postprocessor file found generated new on at: %s') \
                             %os.path.join(FOLDER,self.postpro_file_name)))
        else:
            MyMessages.prt((_('\nLoading postprocessor file: %s') \
                             %os.path.join(FOLDER,self.postpro_file_name)))

        #Variablen erstellen zur späteren Verwendung im Postprozessor        
        self.get_all_vars()

        MyMessages.prt(str(self),1)        

    def get_all_vars(self):
        try:
            self.abs_export=int(self.parser.get('General', 'abs_export'))
            self.write_to_stdout=int(self.parser.get('General', 'write_to_stdout'))
            self.cancel_cc_for_depth=int(self.parser.get('General', 'cancel_cc_for_depth'))
            self.gcode_be=self.parser.get('General', 'code_begin')
            self.gcode_en=self.parser.get('General', 'code_end')

            self.pre_dec=int(self.parser.get('Number format','pre_decimals'))
            self.post_dec=int(self.parser.get('Number format','post_decimals'))
            self.dec_sep=self.parser.get('Number format','decimal_seperator')
            self.pre_dec_z_pad=int(self.parser.get('Number format','pre_decimal_zero_padding'))
            self.post_dec_z_pad=int(self.parser.get('Number format','post_decimal_zero_padding'))
            self.signed_val=int(self.parser.get('Number format','signed_values'))

            self.use_line_nrs=int(self.parser.get('Line numbers','use_line_nrs'))
            self.line_nrs_begin=int(self.parser.get('Line numbers','line_nrs_begin'))
            self.line_nrs_step=int(self.parser.get('Line numbers','line_nrs_step'))

            self.tool_ch_str=self.parser.get('Program','tool_change')
            self.feed_ch_str=self.parser.get('Program','feed_change')
            self.rap_pos_plane_str=self.parser.get('Program','rap_pos_plane')
            self.rap_pos_depth_str=self.parser.get('Program','rap_pos_depth')
            self.lin_mov_plane_str=self.parser.get('Program','lin_mov_plane')
            self.lin_mov_depth_str=self.parser.get('Program','lin_mov_depth')
            self.arc_int_cw=self.parser.get('Program','arc_int_cw')
            self.arc_int_ccw=self.parser.get('Program','arc_int_ccw')
            self.cut_comp_off_str=self.parser.get('Program','cutter_comp_off')
            self.cut_comp_left_str=self.parser.get('Program','cutter_comp_left')
            self.cut_comp_right_str=self.parser.get('Program','cutter_comp_right')                        
                            
            self.feed=0
            self.x=self.config.axis1_st_en
            self.y=self.config.axis2_st_en
            self.z=self.config.axis3_retract
            self.lx=self.x
            self.ly=self.y
            self.lz=self.z
            self.i=0.0
            self.j=0.0

            self.vars={"%feed":'self.iprint(self.feed)',\
                       "%nl":'self.nlprint()',\
                       "%X":'self.fnprint(self.x)',\
                       "%-X":'self.fnprint(-self.x)',\
                       "%Y":'self.fnprint(self.y)',\
                       "%-Y":'self.fnprint(-self.y)',\
                       "%Z":'self.fnprint(self.z)',\
                       "%-Z":'self.fnprint(-self.z)',\
                       "%I":'self.fnprint(self.i)',\
                       "%-I":'self.fnprint(-self.i)',\
                       "%J":'self.fnprint(self.j)',\
                       "%-J":'self.fnprint(-self.j)'}

        except:
            dial=wx.MessageDialog(None, _("Please delete or correct\n %s")\
                      %(os.path.join(FOLDER,self.postpro_file_name)),_("Error during reading postprocessor file"), wx.OK | 
            wx.ICON_ERROR)
            dial.ShowModal()
            raise Exception, _("Problem during import from postprocessor File") 

    def make_new_postpro_file(self):
            
        self.parser.add_section('General')
        self.parser.set('General', 'abs_export', 1)
        self.parser.set('General', 'write_to_stdout', 0)
        self.parser.set('General', 'cancel_cc_for_depth', 0)
   
        self.parser.set('General', 'code_begin',\
                        'G21 (Unit in mm) \nG90 (Absolute distance mode)'\
                        +'\nG64 P0.01 (Exact Path 0.001 tol.)'\
                        +'\nG17'
                        +'\nG40 (Cancel diameter comp.) \nG49 (Cancel length comp.)'\
                        +'\nT1M6 (Tool change to T1)\nM8 (Coolant flood on)'\
                        +'\nS5000M03 (Spindle 5000rpm cw)')
        self.parser.set('General', 'code_end','M9 (Coolant off)\nM5 (Spindle off)\nM2 (Prgram end)')    

        self.parser.add_section('Number format')
        self.parser.set('Number format','pre_decimals',4)
        self.parser.set('Number format','post_decimals',3)
        self.parser.set('Number format','decimal_seperator','.')
        self.parser.set('Number format','pre_decimal_zero_padding',0)
        self.parser.set('Number format','post_decimal_zero_padding',1)
        self.parser.set('Number format','signed_values',0)

        self.parser.add_section('Line numbers')
        self.parser.set('Line numbers','use_line_nrs',0)
        self.parser.set('Line numbers','line_nrs_begin',10)
        self.parser.set('Line numbers','line_nrs_step',10)

        self.parser.add_section('Program')
        self.parser.set('Program','tool_change',\
                        ('T%tool_nr M6%nl S%speed M3%nl'))
        self.parser.set('Program','feed_change',\
                        ('F%feed%nl'))
        self.parser.set('Program','rap_pos_plane',\
                        ('G0 X%X Y%Y%nl'))
        self.parser.set('Program','rap_pos_depth',\
                        ('G0 Z%Z %nl'))
        self.parser.set('Program','lin_mov_plane',\
                        ('G1 X%X Y%Y%nl'))
        self.parser.set('Program','lin_mov_depth',\
                        ('G1 Z%Z%nl'))
        self.parser.set('Program','arc_int_cw',\
                        ('G2 X%X Y%Y I%I J%J%nl'))
        self.parser.set('Program','arc_int_ccw',\
                        ('G3 X%X Y%Y I%I J%J%nl'))
        self.parser.set('Program','cutter_comp_off',\
                        ('G40%nl'))
        self.parser.set('Program','cutter_comp_left',\
                        ('G41%nl'))
        self.parser.set('Program','cutter_comp_right',\
                        ('G42%nl'))                      
                        
        open_file = open(os.path.join(FOLDER,self.postpro_file_name), "w") 
        self.parser.write(open_file) 
        open_file.close()

    def write_gcode_be(self,ExportParas,load_filename):
        #Schreiben in einen String
        str=("(Generated with dxf2code)\n(Created from file: %s)\n" %load_filename)
        self.string=(str.encode("utf-8"))
        
        #Daten aus dem Textfelder an string anhängen
        self.string+=("%s\n" %ExportParas.gcode_be.get(1.0,END).strip())

    def write_gcode_en(self,ExportParas):
        #Daten aus dem Textfelder an string anhängen   
        self.string+=ExportParas.gcode_en.get(1.0,END)

        self.make_line_numbers()        
        
        return self.string

    def make_line_numbers(self):
        line_format='N%i ' 
        if self.use_line_nrs:
            nr=0
            line_nr=self.line_nrs_begin
            self.string=((line_format+'%s') %(line_nr,self.string))
            nr=self.string.find('\n',nr)
            while not(nr==-1):
                line_nr+=self.line_nrs_step  
                self.string=(('%s'+line_format+'%s') %(self.string[0:nr+1],\
                                          line_nr,\
                                          self.string[nr+1:len(self.string)]))
                
                nr=self.string.find('\n',nr+len(((line_format) %line_nr))+2)
                          
            
            
    def chg_feed_rate(self,feed):
        self.feed=feed
        self.string+=self.make_print_str(self.feed_ch_str) 
        
    def set_cut_cor(self,cut_cor,newpos):
        self.cut_cor=cut_cor

        if not(self.abs_export):
            self.x=newpos.x-self.lx
            self.lx=newpos.x
            self.y=newpos.y-self.ly
            self.ly=newpos.y
        else:
            self.x=newpos.x
            self.y=newpos.y  

        if cut_cor==41:
            self.string+=self.make_print_str(self.cut_comp_left_str)
        elif cut_cor==42:
            self.string+=self.make_print_str(self.cut_comp_right_str)

    def deactivate_cut_cor(self,newpos):
        if not(self.abs_export):
            self.x=newpos.x-self.lx
            self.lx=newpos.x
            self.y=newpos.y-self.ly
            self.ly=newpos.y
        else:
            self.x=newpos.x
            self.y=newpos.y   
        self.string+=self.make_print_str(self.cut_comp_off_str)
            
    def lin_pol_arc(self,dir,ende,IJ):
        if not(self.abs_export):
            self.x=ende.x-self.lx
            self.y=ende.y-self.lx
            self.lx=ende.x
            self.ly=ende.y
        else:
            self.x=ende.x
            self.y=ende.y

        self.i=IJ.x
        self.j=IJ.y

        if dir=='cw':
            self.string+=self.make_print_str(self.arc_int_cw)
        else:
            self.string+=self.make_print_str(self.arc_int_ccw)

          
    def rap_pos_z(self,z_pos):
        if not(self.abs_export):
            self.z=z_pos-self.lz
            self.lz=z_pos
        else:
            self.z=z_pos

        self.string+=self.make_print_str(self.rap_pos_depth_str)           
         
    def rap_pos_xy(self,newpos):
        if not(self.abs_export):
            self.x=newpos.x-self.lx
            self.lx=newpos.x
            self.y=newpos.y-self.ly
            self.ly=newpos.y
        else:
            self.x=newpos.x
            self.y=newpos.y

        self.string+=self.make_print_str(self.rap_pos_plane_str)         
    
    def lin_pol_z(self,z_pos):
        if not(self.abs_export):
            self.z=z_pos-self.lz
            self.lz=z_pos
        else:
            self.z=z_pos

        self.string+=self.make_print_str(self.lin_mov_depth_str)      
    def lin_pol_xy(self,newpos):
        if not(self.abs_export):
            self.x=newpos.x-self.lx
            self.lx=newpos.x
            self.y=newpos.y-self.ly
            self.ly=newpos.y
        else:
            self.x=newpos.x
            self.y=newpos.y

        self.string+=self.make_print_str(self.lin_mov_plane_str)       

    def make_print_str(self,string):
        new_string=string
        for key_nr in range(len(self.vars.keys())):
            new_string=new_string.replace(self.vars.keys()[key_nr],\
                                          eval(self.vars.values()[key_nr]))
        return new_string

    #Funktion welche den Wert als formatierter integer zurueck gibt
    def iprint(self,interger):
        return ('%i' %interger)

    #Funktion gibt den String fuer eine neue Linie zurueck
    def nlprint(self):
        return '\n'

    #Funktion welche die Formatierte Number  zurueck gibt
    def fnprint(self,number):
        string=''
        #+ oder - Zeichen Falls noetig/erwuenscht und Leading 0er
        if (self.signed_val)and(self.pre_dec_z_pad):
            numstr=(('%+0'+str(self.pre_dec+self.post_dec+1)+\
                     '.'+str(self.post_dec)+'f') %number)
        elif (self.signed_val==0)and(self.pre_dec_z_pad):
            numstr=(('%0'+str(self.pre_dec+self.post_dec+1)+\
                    '.'+str(self.post_dec)+'f') %number)
        elif (self.signed_val)and(self.pre_dec_z_pad==0):
            numstr=(('%+'+str(self.pre_dec+self.post_dec+1)+\
                    '.'+str(self.post_dec)+'f') %number)
        elif (self.signed_val==0)and(self.pre_dec_z_pad==0):
            numstr=(('%'+str(self.pre_dec+self.post_dec+1)+\
                    '.'+str(self.post_dec)+'f') %number)
            
        #Setzen des zugehoerigen Dezimal Trennzeichens            
        string+=numstr[0:-(self.post_dec+1)]
        
        string_end=self.dec_sep
        string_end+=numstr[-(self.post_dec):]

        #Falls die 0er am Ende entfernt werden sollen
        if self.post_dec_z_pad==0:
            while (len(string_end)>0)and((string_end[-1]=='0')or(string_end[-1]==self.dec_sep)):
                string_end=string_end[0:-1]                
        return string+string_end
    
    def __str__(self):

        str=''
        for section in self.parser.sections(): 
            str= str +"\nSection: "+section 
            for option in self.parser.options(section): 
                str= str+ "\n   -> %s=%s" % (option, self.parser.get(section, option))
        return str

class ShowAboutInfoClass:
    def __init__(self,master):

        info = wx.AboutDialogInfo()
        info.Name = APPNAME.capitalize()
        info.Version = VERSION
        info.Copyright = "(C) 2009 Programmers and Coders Everywhere"
        info.Description = wordwrap(
            "\"DXF2GCODE\" is a software program that converts dxf files " +\
            "into G-Code which can be used for milling. The software is only 2,5D," +\
            "which means the depth can not be read from the dxf-file. A special feature " +\
            "of the software ist that it converts Splines and Ellipses into Arc Elements " +\
            "and not into Line Elements like the most softwares",
            450, wx.ClientDC(master))
            
        info.WebSite = ("www.christian-kohloeffel.homepage.t-online.de", "The Home of DXF2GCODE")
        info.Developers = [ "Vinzenz Schulz",
                           "Christian Kohlöffel" ]


        licenseText =   "Distributed under the terms of the GPL (GNU Public License)"+\
                        "dxf2gcode is free software; you can redistribute it and/or modify "+\
                        "it under the terms of the GNU General Public License as published by "+\
                        "the Free Software Foundation; either version 2 of the License, or "+\
                        "at your option) any later version.\n\n"+\
                        "This program is distributed in the hope that it will be useful, "+\
                        "but WITHOUT ANY WARRANTY; without even the implied warranty of, "+\
                        "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "+\
                        "GNU General Public License for more details. \n\n"+\
                        "You should have received a copy of the GNU General Public License "+\
                        "along with this program; if not, write to the Free Software "+\
                        "Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA "
                        
        info.License = wordwrap(licenseText, 450, wx.ClientDC(master))

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)


##Hauptfunktion zum Aufruf des Fensters und Mainloop     
if __name__ == '__main__':  
    
    app = wx.App(False,None)
    #Falls das Programm mit Parametern von EMC gestartet wurde
    if len(sys.argv) > 1:
        frame=FrameClass(None,load_filename=sys.argv[1])
    else:
        frame=MyFrameClass(None)

    frame.Show()
    app.MainLoop()

