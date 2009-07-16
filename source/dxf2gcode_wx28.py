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

#Loeschen aller Module aus dem Speicher---------------------------------------------------------------
import sys, os, string

# Globale Konstanten
APPNAME     = "dxf2gcode"
VERSION     = "2.0 beta1"
DEBUG       = 3
DOT_PER_MM  = 3.5

PROGRAMDIRECTORY = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
BITMAPDIRECTORY = PROGRAMDIRECTORY + "/bitmaps"


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
if wx.VERSION<(2, 8, 9, 1, ''):
    raise Exception, ("VERSION of wx need to be 2.8.9.1 and higher") 
    
import wx.aui
import wx.lib.customtreectrl as CT
import  wx.lib.mixins.listctrl  as  listmix

from wx.lib.wordwrap import wordwrap

from wx.lib.floatcanvas import FloatCanvas, Resources
from wx.lib.floatcanvas.Utilities import BBox
import dxf2gcode_b02_FloatCanvas_mod as NavCanvas
#import wx_lib_floatcanvas_Utilities as GUI
import wx.lib.colourdb

import locale
import gettext, tempfile, subprocess
from copy import copy
from math import radians, degrees, log, ceil

from dxf2gcode_inputdlg import VarDlg
from dxf2gcode_b02_point import PointClass, LineGeo, ArcGeo
from dxf2gcode_b02_shape import ShapeClass, EntitieContentClass
import dxf2gcode_b02_dxf_import as dxfimport 
import dxf2gcode_b02_tsp_opt as tsp
from dxf2gcode_b02_config import MyConfigClass, MyPostprocessorClass

import time, random

# Config Verzeichnisse----------------------------------------------------------------------------------
if os.name == 'posix': 
    FOLDER = os.path.join(os.environ.get('HOME'), "." + APPNAME.lower()) 
elif os.name == 'nt': 
    FOLDER = os.path.join(os.environ.get('APPDATA'), APPNAME.capitalize()) 

#Das momentane Verzeichnis herausfinden
local_path = os.path.realpath(os.path.dirname(sys.argv[0]))


#Übersetzungen initialisieren----------------------------------------------------------------------------
# Liste der unterstützuden Sprachen anlegen und die dementsprchende Reihenfolge der default Sprachen
langs = ['DE_de']

#Default Sprache des Systems herausfinden
lc, encoding = locale.getdefaultlocale()

if (lc):
    #Wenn wir eine haben diese als Default setzen
    langs = [lc]

# Herausfinden welche sprachen wir haben
language = os.environ.get('LANGUAGE', None)
if (language):
    #Die sprachen kommen in folgender Form vom Linzy System zurück:
    #en_CA:en_US:en_GB:en bei Windows nichts. Für Linux muß beim : gespliete werden
    langs += language.split(":")

# "Installieren" der Übersetzung fpr die Funktion _(string)
gettext.bindtextdomain("dxf2gcode", local_path)
gettext.textdomain("dxf2gcode")
trans = gettext.translation("dxf2gcode", localedir='languages', languages=langs, fallback = True)
trans.install()


class MyFrameClass(wx.Frame):
    def __init__(self, parent, load_filename=None,id=-1, title='%s, Version: %s' %(APPNAME.capitalize(),VERSION),
                 pos=wx.DefaultPosition, size=(1024, 768),
                 style=wx.DEFAULT_FRAME_STYLE):  
                
         #Skalierung der Kontur
        self.cont_scale=1.0
        
        #Verschiebung der Kontur
        self.cont_dx=0.0
        self.cont_dy=0.0
        
        #Rotieren um den WP zero
        self.rotate=0.0
        
        #Uebergabe des load_filenames falls von EMC gestartet
        self.load_filename=load_filename
        
        #Erstellen des Fenster
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self._mgr = wx.aui.AuiManager(self)

        #Erstellen der Status Bar am unteren Ende
        self.statusbar = self.CreateStatusBar(4)
        self.statusbar.SetStatusWidths([-1,100, 100, 100])
        self.SetStatusText("This is the statusbar",0)     

        #Erstellen des Fenster Menus
        self.CreateMenues()
        self.DisableAllMenues()
            
        #Erstellen der Messagebox für die Meldungen
        self.MyMessages = MyMessagesClass(self, -1)
        
        #Erstellen des Zeichenbereichs (früher Canvas?!)
        self.MyGraphic = MyGraphicClass(self,-1)
        
        #Voreininstellungen fuer das Programm laden
        self.MyConfig=MyConfigClass(self.MyMessages,PROGRAMDIRECTORY,APPNAME)

        #PostprocessorClass initialisieren (Voreinstellungen aus Config)
        self.MyPostpro=MyPostprocessorClass(self.MyConfig,self.MyMessages,PROGRAMDIRECTORY,APPNAME)
            
#        #Erstellen de Eingabefelder und des Canvas
#        self.ExportParas =ExportParasClass(self.frame_l,self.config,self.postpro)
     
        #Erstellen des Baums für die Entities
        self.MyEntTree = MyEntitieTreeClass(self, wx.ID_ANY)   
        
        #Erstellen des Baums für die verwendeten Layers
        self.MyLayersTree = MyLayersTreeClass(self, -1)

        #Erstellen des Baums für die verwendeten Layers
        self.MySelectionInfo = MySelectionInfoClass(self, wx.ID_ANY)                                 
        
        #Erstellen der Canvas Content Klasse & Bezug in Canvas Klasse
        self.MyCanvasContent=MyCanvasContentClass(self.MyGraphic,self.MyMessages,
                                                self.MyConfig,
                                                self.MyLayersTree,
                                                self.MyEntTree,
                                                self.MySelectionInfo)
        
        
#        self.nb = wx.aui.AuiNotebook(self)
#        page = wx.TextCtrl(self.nb, -1, 'asdfals', style=wx.TE_MULTILINE)
#        self.nb.AddPage(page, "Welcome")
#
#        for num in range(1, 5):
#            page = wx.TextCtrl(self.nb, -1, "This is page %d" % num ,
#                               style=wx.TE_MULTILINE)
#            self.nb.AddPage(page, "Tab Number %d" % num)
        
        
        #Erstellen der Bindings fürs gesamte Fenster
        self.BindMenuEvents()
        
        #Die Verschiedeneen Objecte zum Sizer AUIManager hinzufügen
        self._mgr.AddPane(self.MyEntTree, wx.aui.AuiPaneInfo(). 
                          Caption(_("Entities")).
                          Left().CloseButton(False))            
        self._mgr.AddPane(self.MyLayersTree,wx.aui.AuiPaneInfo(). 
                          Caption(_("Layers")).Floatable(True). 
                          Resizable(False).
                          Left().CloseButton(False))
        self._mgr.AddPane(self.MySelectionInfo,wx.aui.AuiPaneInfo(). 
                          Caption(_("Selection Info")).Floatable(True). 
                          Resizable(False).
                          Left().Bottom().CloseButton(False))
        self._mgr.AddPane(self.MyMessages, wx.aui.AuiPaneInfo(). 
                          Caption(_("Messages")).Floatable(False).
                          Bottom().CloseButton(False))
        self._mgr.AddPane(self.MyGraphic, wx.aui.AuiPaneInfo(). 
                          CaptionVisible(False). 
                          Center())

        #Dem Manager sagen er soll alles auf Stand bringen
        self._mgr.Update()

        #Den Event Schliessen hinzufügen
        self.Bind(wx.EVT_CLOSE, self.CloseWindow)
        
        #Falls ein load_filename_uebergeben wurde
        if not(self.load_filename is None):
            #Zuerst alle ausstehenden Events und Callbacks ausfuehren (sonst klappts beim Laden nicht)
            self.Load_File()
     
    def CreateMenues(self):
        #Filemenu erstellen
        menuBar = wx.MenuBar()
        self.filemenu=filemenu = wx.Menu()
        open=wx.MenuItem(filemenu,101,_("Open DXF"), _("Import a dxf file"))
        open.SetBitmap(wx.Bitmap(BITMAPDIRECTORY + "/Open.png"))
        filemenu.AppendItem(open)
        
        filemenu.AppendSeparator()
        quit=wx.MenuItem(filemenu,102, _("&Quit\tCtrl+Q"), _("Close this frame"))
        quit.SetBitmap(wx.Bitmap(BITMAPDIRECTORY + "/Exit.png"))
        filemenu.AppendItem(quit)
        menuBar.Append(filemenu, _("File"))
             

        #Exportmenu erstellen
        self.exportmenu=exportmenu = wx.Menu()
        export=wx.MenuItem(exportmenu,201, _("Write G-Code"), _("Write G-Code in file / stdout to EMC"))
        export.SetBitmap(wx.Bitmap(BITMAPDIRECTORY + "/Export.png"))
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
        shgrid = viewmenu.Append(303, _("Show Grid"),\
                    _("Show the Grid"), kind=wx.ITEM_CHECK)
        viewmenu.Check(303, True)
        shsds = viewmenu.Append(304, _("Show disabled shapes"),\
                    _("Show the disabled shapes grayed out"), kind=wx.ITEM_CHECK)
        viewmenu.Check(304, False) 
        viewmenu.AppendSeparator()
#        viewmenu.Append(304, _("Autoscale"), _("Fit the drawing to the screen"))
#        viewmenu.AppendSeparator()
        viewmenu.Append(305, _("Delete Route"), _("Delete the route which was drawn during export"))               
        menuBar.Append(viewmenu, _("View"))
        
        
        self.optionmenu=optionmenu= wx.Menu()
        optionmenu.Append(401, _("Set tolerances"), _("Set the tolerances for the dxf import"))
        optionmenu.AppendSeparator()
        optionmenu.Append(402,_("Scale contours"), _("Scale all elements by factor"))
        optionmenu.Append(403, _("Move workpiece zero"), _("Offset the workpiece zero of the drawing"))
        optionmenu.Append(404, _("Rotate workpiece zero"), _("Rotate all elements about workpiece zero"))
        
        menuBar.Append(optionmenu, _("Options"))
                
        helpmenu = wx.Menu()
        helpmenu.Append(501, _("About"),_("Show the About dialog"))
        menuBar.Append(helpmenu, _("Help"))    

        self.SetMenuBar(menuBar)
        
    def BindMenuEvents(self): 
        #Filemenu 
        self.Bind(wx.EVT_MENU, self.GetLoadFile, id=101)
        self.Bind(wx.EVT_MENU, self.CloseWindow, id=102)
        
        #Exportmenu
        self.Bind(wx.EVT_MENU, self.GetSaveFile, id=201)
        
        #Viewmenu
        self.Bind(wx.EVT_MENU, self.MyCanvasContent.plot_wp_zero, id=301)
        self.Bind(wx.EVT_MENU, self.MyCanvasContent.plot_cut_info, id=302)
        self.Bind(wx.EVT_MENU, self.MyCanvasContent.plot_grid, id=303)
        self.Bind(wx.EVT_MENU, self.MyCanvasContent.show_disabled, id=304)
        self.Bind(wx.EVT_MENU, self.del_route_and_menuentry, id=305)
        
        #Optionsmenu
        self.Bind(wx.EVT_MENU, self.GetContTol, id=401)
        self.Bind(wx.EVT_MENU, self.GetContScale, id=402)
        self.Bind(wx.EVT_MENU, self.MoveWpZero, id=403)
        self.Bind(wx.EVT_MENU, self.RotateWpZero, id=404)
        
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
        self.optionmenu.Enable(403,False)
        self.optionmenu.Enable(404,False)
        
    def EnableAllMenues(self):
        #Exportmenu
        self.exportmenu.Enable(201,True)
        
        #Viewmenu
        self.viewmenu.Enable(301,True)
        self.viewmenu.Enable(302,True)
        self.viewmenu.Enable(303,True)
        self.viewmenu.Enable(304,True)
        self.viewmenu.Enable(305,True)
        
        #Optionsmenu
        self.optionmenu.Enable(401,True)
        self.optionmenu.Enable(402,True)
        self.optionmenu.Enable(403,True)
        self.optionmenu.Enable(404,True)
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
            defaultDir=self.MyConfig.load_path, 
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
            
            pstoedit_cmd=self.MyConfig.pstoedit_cmd.encode("cp1252") #"C:\Program Files (x86)\pstoedit\pstoedit.exe"
            pstoedit_opt=eval(self.MyConfig.pstoedit_opt) #['-f','dxf','-mm']
            
            ps_filename=os.path.normcase(self.load_filename.encode("cp1252"))
            cmd=[(('%s')%pstoedit_cmd)]+pstoedit_opt+[(('%s')%ps_filename),(('%s')%filename)]
            retcode=subprocess.call(cmd)
            
        #self.MyMessages.TextDelete(None)
        self.MyMessages.prt(_('\nLoading file: %s') %self.load_filename)
        
        self.values=dxfimport.LoadDXF(filename,self.MyConfig,self.MyMessages)
        
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
 
        #Einschalten der disabled Menus
        self.EnableAllMenues()

        #Ausdrucken der Werte        
        self.MyCanvasContent.makeplot(self.values,
                                    p0=PointClass(x=self.cont_dx,y=self.cont_dy),
                                    pb=PointClass(x=0,y=0),
                                    sca=[self.cont_scale,self.cont_scale,self.cont_scale],
                                    rot=self.rotate)

        #Loeschen alter Route Menues
        self.del_route_and_menuentry(None)
            
    def GetContTol(self,event):
        
        #Dialog fuer die Toleranzvoreinstellungen oeffnen      
        title=_('Contour tolerances')
        label=(_("Tolerance for common points [mm]:"),\
               _("Tolerance for curve fitting [mm]:"))
        value=("%0.5f" %self.MyConfig.points_tolerance, "%0.5f" %self.MyConfig.fitting_tolerance)
        
        chform = VarDlg(None, -1,title,label,value)
        chform.ShowModal()
        
        #Abbruch falls Cancel gedrückt wurde
        if chform.ReturnCode==wx.ID_CANCEL:
            return
        
        values=chform.GetValue()

        
        self.MyConfig.points_tolerance=float(values[0])
        self.MyConfig.fitting_tolerance=float(values[1])

        #Falls noch kein File geladen wurde nichts machen
        if self.load_filename is None:
            return
        self.LoadFile()
        self.MyMessages.prt(_("\nSet new Contour tolerances (Pts: %0.3f, Fit: %0.3f) reloaded file")\
                              %(self.MyConfig.points_tolerance,self.MyConfig.fitting_tolerance))
                                    
    def GetContScale(self,event):

        chform = VarDlg(None, -1, _('Scale Contours'),[_('Set the scale factor')],[("%0.3f") %self.cont_scale])
        chform.ShowModal()
        
        #Abbruch falls Cancel gedrückt wurde
        if chform.ReturnCode==wx.ID_CANCEL:
            return
        
        values=chform.GetValue()

        self.cont_scale=float(values[0])

        #Falls noch kein File geladen wurde nichts machen
        if self.load_filename is None:
            return
        self.MyCanvasContent.makeplot(self.values,
                                    p0=PointClass(x=self.cont_dx,y=self.cont_dy),
                                    pb=PointClass(0,0),
                                    sca=[self.cont_scale,self.cont_scale,self.cont_scale],
                                    rot=self.rotate)
        self.MyMessages.prt(_("\nScaled Contours by factor %0.3f") %self.cont_scale)
      
       
    def MoveWpZero(self,event):
  
        title=_('Workpiece zero offset')
        label=((_("Offset %s axis by mm:") %self.MyConfig.ax1_letter),\
               (_("Offset %s axis by mm:") %self.MyConfig.ax2_letter))
        value=("%0.3f" %self.cont_dx, "%0.3f" %self.cont_dy)
        chform = VarDlg(None, -1,title,label,value)
        chform.ShowModal()
        
        #Abbruch falls Cancel gedrückt wurde
        if chform.ReturnCode==wx.ID_CANCEL:
            return
        
        values=chform.GetValue()

        self.cont_dx=float(values[0])
        self.cont_dy=float(values[1])

        #Falls noch kein File geladen wurde nichts machen
        if self.load_filename is None:
            return
  
        #Falls noch kein File geladen wurde nichts machen
        if self.load_filename is None:
            return
        self.MyCanvasContent.makeplot(self.values,
                                    p0=PointClass(x=self.cont_dx,y=self.cont_dy),
                                    pb=PointClass(x=0,y=0),
                                    sca=[self.cont_scale,self.cont_scale,self.cont_scale],
                                    rot=self.rotate)
        
        self.MyMessages.prt(_("\nMoved worpiece zero  by offset: %s %0.2f; %s %0.2f") \
                              %(self.MyConfig.ax1_letter,self.cont_dx,
                                self.MyConfig.ax2_letter,self.cont_dy))

    def RotateWpZero(self,event):
  
        title=_('Rotate about WP zero')
        label=[_("Rotate by deg:")]
        value=["%0.2f" %degrees(self.rotate)]

        chform = VarDlg(None, -1,title,label,value)
        chform.ShowModal()
        
        #Abbruch falls Cancel gedrückt wurde
        if chform.ReturnCode==wx.ID_CANCEL:
            return
        
        values=chform.GetValue()

        self.rotate=radians(float(values[0]))

        #Falls noch kein File geladen wurde nichts machen
        if self.load_filename is None:
            return
  
        #Falls noch kein File geladen wurde nichts machen
        if self.load_filename is None:
            return
        self.MyCanvasContent.makeplot(self.values,
                                    p0=PointClass(x=self.cont_dx,y=self.cont_dy),
                                    pb=PointClass(x=0,y=0),
                                    sca=[self.cont_scale,self.cont_scale,self.cont_scale],
                                    rot=self.rotate)
        
        self.MyMessages.prt(_("\nRotated about WP zero: %0.2fdeg") \
                              %(degrees(self.rotate)))

    def GetSaveFile(self,event):
        
        if self.MyPostpro.output_format=='g-code':
            format='.ngc'
            saveformat = _('EMC2 GCode Files')+'|*.ngc'
        elif self.MyPostpro.output_format=='dxf':
            format='_simplified.dxf'
            saveformat = _('DXF File')+'|*.dxf'
        
        if not(self.MyPostpro.write_to_stdout):     

            #Abbruch falls noch kein File geladen wurde.
            if self.load_filename==None:
                showwarning(_("Export G-Code"), _("Nothing to export!"))
                return
 
            (beg, ende)=os.path.split(self.load_filename)
            (fileBaseName, fileExtension)=os.path.splitext(ende)
          
            dlg = wx.FileDialog(
                self, message=_("Save file as ..."), defaultDir=self.MyConfig.load_path, 
                defaultFile=fileBaseName + format, wildcard=saveformat, style=wx.SAVE)
                
            #dlg.SetFilterIndex(filterIndex) 

            # This sets the default filter that the user will initially see. Otherwise,
            # the first filter in the list will be used by default.
            #dlg.SetFilterIndex(2)

            # Show the dialog and retrieve the user response. If it is the OK response, 
            # process the data.
            if dlg.ShowModal() == wx.ID_OK:
                paths = dlg.GetPaths()
                self.save_filename=paths[0]
            else:
                return
            
            self.WriteGCode()

    # Callback des Menu Punkts Exportieren
    def WriteGCode(self):
        pass
        #Funktion zum optimieren des Wegs aufrufen
        self.opt_export_route()

        #Initial Status fuer den Export
        status=1

        #Config & postpro in einen kurzen Namen speichern
        config=self.MyConfig
        postpro=self.MyPostpro

        #Schreiben der Standardwert am Anfang        
        postpro.write_gcode_be(self.load_filename)

        #Maschine auf die Anfangshoehe bringen
        postpro.rap_pos_z(config.axis3_retract)

        #Bei 1 starten da 0 der Startpunkt ist
        for nr in range(1,len(self.TSP.opt_route)):
            shape=self.shapes_to_write[self.TSP.opt_route[nr]]
            self.MyMessages.prt((_("\nWriting Shape: %s") %shape),1)
                
            #Drucken falls die Shape nicht disabled ist
            if not(shape in self.MyCanvasContent.Disabled):
                #Falls sich die Fräserkorrektur verändert hat diese in File schreiben
                stat =shape.Write_GCode(config,postpro)
                status=status*stat

        #Maschine auf den Endwert positinieren
        postpro.rap_pos_xy(PointClass(x=config.axis1_st_en,\
                                      y=config.axis2_st_en))

        #Schreiben der Standardwert am Ende        
        string=postpro.write_gcode_en()

        if status==1:
            self.MyMessages.prt(_("\nSuccessfully generated G-Code"))

        else:
            self.MyMessages.prt(_("\nError during G-Code Generation"))

                    
        #Drucken in den Stdout, speziell fuer EMC2 
        if postpro.write_to_stdout:
            self.ende()     
        else:
            try:
                #Das File oeffnen und schreiben    
                f = open(self.save_filename, "w")
                f.write(string)
                f.close()       
            except IOError:
                dial=wx.MessageDialog(None, _("Cannot save the file."),
                        _("Error during saving"), wx.OK |
                        wx.ICON_ERROR)
                dial.ShowModal()
            
    def opt_export_route(self):
        
        #Errechnen der Iterationen
        iter =min(self.MyConfig.max_iterations,len(self.MyCanvasContent.Shapes)*20)
        
        #Anfangswerte fuer das Sortieren der Shapes
        self.shapes_to_write=[]
        shapes_st_en_points=[]
        
        #Alle Shapes die geschrieben werden zusammenfassen
        for shape_nr in range(len(self.MyCanvasContent.Shapes)):
            shape=self.MyCanvasContent.Shapes[shape_nr]
            if not(shape.nr in self.MyCanvasContent.Disabled):
                self.shapes_to_write.append(shape)
                shapes_st_en_points.append(shape.get_st_en_points())
                

        #Hinzufuegen des Start- Endpunkte ausserhalb der Geometrie
        x_st=self.MyConfig.axis1_st_en
        y_st=self.MyConfig.axis2_st_en
        start=PointClass(x=x_st,y=y_st)
        ende=PointClass(x=x_st,y=y_st)
        shapes_st_en_points.append([start,ende])

        #Optimieren der Reihenfolge
        self.MyMessages.prt(_("\nTSP Starting"),1)
                
        self.TSP=tsp.TSPoptimize(shapes_st_en_points,self.MyMessages,self.MyConfig)
        self.MyMessages.prt(_("\nTSP start values initialised"),1)
        
        self.MyCanvasContent.path_hdls=[]
        self.MyCanvasContent.plot_opt_route(shapes_st_en_points,self.TSP.opt_route)
        
        for it_nr in range(iter):
            #Jeden 10ten Schrit rausdrucken
            if (it_nr%10)==0:
                self.MyMessages.prt((_("\nTSP Iteration nr: %i") %it_nr),1)
                self.MyCanvasContent.delete_opt_path()
                self.MyCanvasContent.plot_opt_route(shapes_st_en_points,self.TSP.opt_route)
                
            self.TSP.calc_next_iteration()
            
        self.MyMessages.prt(_("\nTSP done with result:"),1)
        self.MyMessages.prt(("\n%s" %self.TSP),1)
            
        #Einschlaten des Menupunkts zum löschen des optimierten Pfads.
        self.viewmenu.Enable(305,True)

    def del_route_and_menuentry(self,event):
        try:
            self.viewmenu.Enable(305,False)
            self.MyCanvasContent.delete_opt_path()
            self.MyGraphic.Canvas.Draw(Force=True)
        except:
            pass
        
    def ShowAbout(self,event):
        ShowAboutInfoClass(self) 

    def CloseWindow(self,event):
        #Framemanager deinitialisieren
        self._mgr.UnInit()
        #Den Frame löschen
        self.Destroy()
              
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

class MyEntitieTreeClass(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                size=wx.Size(250,180),
                 style=wx.SUNKEN_BORDER |  
                 CT.TR_HAS_VARIABLE_ROW_HEIGHT | wx.WANTS_CHARS |
                 CT.TR_FULL_ROW_HIGHLIGHT |CT.TR_HIDE_ROOT| CT.TR_NO_LINES |
                 CT.TR_MULTIPLE |CT.TR_TWIST_BUTTONS |CT.TR_HAS_BUTTONS):

        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)      
        
        il = wx.ImageList(16, 16)
        il.Add(wx.Bitmap(BITMAPDIRECTORY + "/Layer.ico"))
        il.Add(wx.Bitmap(BITMAPDIRECTORY + "/Polylinie.ico"))
        il.Add(wx.Bitmap(BITMAPDIRECTORY + "/Linie.ico"))
        il.Add(wx.Bitmap(BITMAPDIRECTORY + "/Bogen.ico"))

        self.AssignImageList(il)
        #self.root = self.AddRoot("The Root Item")

        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(CT.EVT_TREE_SEL_CHANGED, self.OnSelChanged)

    def MakeEntitieList(self,EntitieContents=None):
        self.DeleteAllItems()
        self.root = self.AddRoot("The Root Item")
        self.AddEntitietoList(EntitieContents,self.root)
        

    def AddEntitietoList(self,EntitieContents,parent):
        
        #Darstellen der Werte für das jeweilige Entitie
        textctrl=EntitieContents.MakeTreeText(self)
        treechild = self.AppendItem(parent,'', wnd=textctrl)
        self.EnableItem(treechild,False)
        
        for Entitie in EntitieContents.children:
            
            #Wenn es ein Insert ist
            if Entitie.type=="Entitie":
                treechild = self.AppendItem(parent,('Insert: %s' %(Entitie.Name)))
                self.SetPyData(treechild, Entitie)
                self.SetItemImage(treechild, 0, CT.TreeItemIcon_Normal)
                self.SetItemImage(treechild, 0, CT.TreeItemIcon_Expanded)

                
                #Nochmalier Aufruf für die darunter liegenden Entities
                self.AddEntitietoList(Entitie,treechild)
                
            #Wenn es ein Shape ist
            else:
                treechild = self.AppendItem(parent,'%s Nr: %i' %(Entitie.type,Entitie.nr))
                self.SetPyData(treechild, Entitie)
                self.SetItemImage(treechild, 1, CT.TreeItemIcon_Normal)
                self.SetItemImage(treechild, 1, CT.TreeItemIcon_Expanded)
                
                for geo in Entitie.geos:             
                    if geo.type=='LineGeo':
                             
                        #textctrl=geo.MakeTreeText(self)
                        
                        
                        treechild1 = self.AppendItem(treechild,'%s' %(geo.type))
                        #child2 = self.AppendItem(child,'', wnd=textctrl)
                        self.SetPyData(treechild1, geo)
                        
                        self.SetItemImage(treechild1, 2, CT.TreeItemIcon_Normal)
                        self.SetItemImage(treechild1, 2, CT.TreeItemIcon_Expanded)
                        self.EnableItem(treechild1,False)
                        
                        
                    else:
                        #textctrl=geo.MakeTreeText(self)
                        
                        
                        treechild1 = self.AppendItem(treechild,'%s' %(geo.type))
                        #child2 = self.AppendItem(child,'', wnd=textctrl)
                        self.SetPyData(treechild1, geo)
                        
                        self.SetItemImage(treechild1, 3, CT.TreeItemIcon_Normal)
                        self.SetItemImage(treechild1, 3, CT.TreeItemIcon_Expanded)
                        self.EnableItem(treechild1,False)

           
    #Item hinzufügen falls es noch nicht selektiert ist
    def OnRightDown(self, event):
        pt = event.GetPosition()
        self.item, flags = self.HitTest(pt)

        #Wenn nicht mit Ctrl gedrück den Rest aus Selection nehmen
        if not(event.ControlDown()):
            self.UnselectAll()

        if not(self.item in self.GetSelections()) and not(self.item==None):
            self.SelectItem(self.item)
     
    #Menu aufmachen falls ein Item selektiert ist
    def OnRightUp(self, event):

        item = self.item
        
        if item==None:
            event.Skip()
            return

        #Contextmenu zu den ausgewählten Items
        menu = wx.Menu()
        item1 = menu.Append(wx.ID_ANY, "Change Item Background Colour")
        item2 = menu.Append(wx.ID_ANY, "Modify Item Text Colour")
        self.PopupMenu(menu)
        menu.Destroy()
        

    def OnDisableItem(self, event):
        self.EnableItem(self.current,False)
        
        
    def OnSelChanged(self, event):
        sel_items=[]
        for selection in self.GetSelections():
            item=self.GetItemPyData(selection)
            sel_items+=self.GetItemShapes(item)

                  
        self.MyCanvasContent.change_selection(sel_items)
        self.MySelectionInfo.change_selection(sel_items)
    
    def GetItemShapes(self,item):
        SelShapes=[]
        if item.type=="Shape":
            SelShapes.append(item)
            
        elif item.type=="Entitie":
            for child in item.children:
                SelShapes+=self.GetItemShapes(child)
          
        return SelShapes
        
        
class MyLayersTreeClass(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.Size(250,180),
                 style=wx.SUNKEN_BORDER |  
                 CT.TR_HAS_VARIABLE_ROW_HEIGHT | wx.WANTS_CHARS |
                 CT.TR_FULL_ROW_HIGHLIGHT |CT.TR_HIDE_ROOT| CT.TR_NO_LINES |
                 CT.TR_MULTIPLE |CT.TR_TWIST_BUTTONS |CT.TR_HAS_BUTTONS):

        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)
        
        il = wx.ImageList(16, 16)
        il.Add(wx.Bitmap(BITMAPDIRECTORY + "/Layer.ico"))
        il.Add(wx.Bitmap(BITMAPDIRECTORY + "/Polylinie.ico"))

        self.AssignImageList(il)
        #self.root = self.AddRoot("The Root Item")

        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(CT.EVT_TREE_SEL_CHANGED, self.OnSelChanged)

    def MakeLayerList(self,LayerContents=None):
        self.DeleteAllItems()
        self.root = self.AddRoot("The Root Item")
        for LayerContent in LayerContents:
            child = self.AppendItem(self.root,('Layer Nr: %i, %s' 
                                    %(LayerContent.LayerNr, LayerContent.LayerName)))
            self.SetPyData(child, LayerContent)
            self.SetItemImage(child, 0, CT.TreeItemIcon_Normal)
            self.SetItemImage(child, 0, CT.TreeItemIcon_Expanded)


            for Shape in LayerContent.Shapes:
                
                last = self.AppendItem(child,('Shape Nr: %i' %Shape.nr))  
                self.SetPyData(last, Shape)
                self.SetItemImage(last, 1, CT.TreeItemIcon_Normal)
                self.SetItemImage(last, 1, CT.TreeItemIcon_Expanded)
                    

    #Item hinzufügen falls es noch nicht selektiert ist
    def OnRightDown(self, event):
        pt = event.GetPosition()
        self.item, flags = self.HitTest(pt)

        #Wenn nicht mit Ctrl gedrück den Rest aus Selection nehmen
        if not(event.ControlDown()):
            self.UnselectAll()

        if not(self.item in self.GetSelections()) and not(self.item==None):
            self.SelectItem(self.item)
     
    #Menu aufmachen falls ein Item selektiert ist
    def OnRightUp(self, event):

        item = self.item
        
        if item==None:
            event.Skip()
            return

        #Contextmenu zu den ausgewählten Items
        menu = wx.Menu()
        item1 = menu.Append(wx.ID_ANY, "Change Item Background Colour")
        item2 = menu.Append(wx.ID_ANY, "Modify Item Text Colour")
        self.PopupMenu(menu)
        menu.Destroy()
        

    def OnDisableItem(self, event):
        self.EnableItem(self.current, False)
        
        
    def OnSelChanged(self, event):
        sel_items=[]
        for selection in self.GetSelections():
            item=self.GetItemPyData(selection)
            sel_items+=self.GetItemShapes(item)

                  
        self.MyCanvasContent.change_selection(sel_items)
        self.MySelectionInfo.change_selection(sel_items)
        
    def GetItemShapes(self,item):
        SelShapes=[]
        if item.type=="Shape":
            SelShapes.append(item)
            
        elif item.type=="Layer":
            for shape in item.Shapes:
                SelShapes+=self.GetItemShapes(shape)
          
        return SelShapes

class MyGraphicClass(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id,  style=wx.SUNKEN_BORDER)
        wx.GetApp().Yield(True)  

        #Referenz zum davor liegenden Hauptfenster
        self.parent=parent
        
        self.lastkey=0
        
        # Add the Canvas
        NC = NavCanvas.NavCanvas(parent=self,
                                BoxCallback=self.MultiSelect,
                                ZoomCallback=self.ZoomCallback,
                                Debug = 0,
                                BackgroundColor = "WHITE")
                                    
        self.Canvas = NC.Canvas # reference the contained FloatCanvas

        MainSizer = wx.BoxSizer(wx.VERTICAL)
        MainSizer.Add(NC, 6, wx.EXPAND)

        self.SetSizer(MainSizer)

        self.BindAllEvents()
        
        return None

    def BindAllEvents(self):             
        
        self.Canvas.Bind(FloatCanvas.EVT_LEFT_UP, self.OnLeftUp)
        
        self.Canvas.Bind(FloatCanvas.EVT_MOTION, self.OnMove) 
        self.Canvas.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        
        self.Canvas.Bind(FloatCanvas.EVT_RIGHT_DOWN, self.GraphicContextmenu)
        
        self.Canvas.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Canvas.Bind(wx.EVT_KEY_UP , self.OnKeyUp)

        self.SetFocus()
        
    def MultiSelect(self,BB):
        self.MyCanvasContent.ShapesInBB(BB)   
      
    def ZoomCallback(self):
        self.MyCanvasContent.plot_wp_zero()
        self.MyCanvasContent.plot_cut_info()
        self.MyCanvasContent.plot_grid()
        
    def OnLeftUp(self,event):
        self.MyCanvasContent.NothingGotHit()

    def GraphicContextmenu(self,event):

        # only do this part the first time so the events are only bound once
        # Yet another anternate way to do IDs. Some prefer them up top to
        # avoid clutter, some prefer them close to the object of interest
        # for clarity. 
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.MyCanvasContent.invert_selection, id=self.popupID1)
            
            self.popupID2 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.MyCanvasContent.disable_selection, id=self.popupID2)
            
            self.popupID3 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.MyCanvasContent.enable_selection, id=self.popupID3)
            
            self.popupID4 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.MyCanvasContent.switch_shape_dir, id=self.popupID4)
            
            self.popupID5 = wx.NewId()
            
            self.popupID6 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.MyCanvasContent.set_cor_40, id=self.popupID6)
            
            self.popupID7 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.MyCanvasContent.set_cor_41, id=self.popupID7)
            
            self.popupID8 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.MyCanvasContent.set_cor_42, id=self.popupID8)

        #Erstellen des Menus
        menu = wx.Menu()
        menu.Append(self.popupID1, _('Invert Selection'),_('Invert Selection'))
        menu.Append(self.popupID2, _('Disable Selection'),_('Disable Selection'))
        menu.Append(self.popupID3, _('Enable Selection'),_('Enable Selection'))
        menu.AppendSeparator()
        menu.Append(self.popupID4, _('Switch Direction'),_('Switch Direction'))
        
        #Submenu mit der Fräsradienkorrektur
        sm = wx.Menu()
        sm.Append(self.popupID6, _("G40 No correction"),_("G40 No correction"),wx.ITEM_CHECK)
        sm.Append(self.popupID7, _("G41 Cutting left"),_("G41 Cutting left"),wx.ITEM_CHECK)
        sm.Append(self.popupID8, _("G42 Cutting right"),_("G42 Cutting right"),wx.ITEM_CHECK)
        
        #Zuweisen ob nur eine CutterCorrection ausgewählt ist und darstellen
        x=self.MyCanvasContent.calc_dir_var()
        sm.Check(self.popupID6, 0==40-x)
        sm.Check(self.popupID7, 0==41-x)
        sm.Check(self.popupID8, 0==42-x)
        
        menu.AppendMenu(self.popupID5, _('Set Cutter Correction'), sm)
        
        #Menus Disablen wenn nicht ausgewählt wurde        
        if len(self.MyCanvasContent.Selected)==0:
            menu.Enable(self.popupID1,False)
            menu.Enable(self.popupID2,False)
            menu.Enable(self.popupID3,False)
            menu.Enable(self.popupID4,False)
            menu.Enable(self.popupID5,False)
                  
        
        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()

    def OnSavePNG(self, event=None):
        import os
        dlg = wx.FileDialog(
            self, message=_("Save file as ...)"), defaultDir=os.getcwd(), 
            defaultFile="", wildcard="*.png", style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not(path[-4:].lower() == ".png"):
                path = path+".png"
            self.Canvas.SaveAsImage(path)

    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        self.lastkey=keycode
        #print keycode
  
    def OnKeyUp(self, event):
        self.lastkey=0
      
    def OnMove(self, event):
                
        scale=self.Canvas.Scale/DOT_PER_MM
        
        if scale<1:
            x=_("X:")+(" %5.0f" %event.Coords[0])
            y=_("Y:")+(" %5.0f" %event.Coords[1])
            sc=_("Scale:")+(" %5.3f" %scale)
        elif (scale>=1)and(scale<10):
            x=_("X:")+(" %5.1f" %event.Coords[0])
            y=_("Y:")+(" %5.1f" %event.Coords[1])
            sc=_("Scale:")+(" %5.2f" %scale)
        elif scale>=10:  
            x=_("X:")+(" %5.2f" %event.Coords[0])
            y=_("Y:")+(" %5.2f" %event.Coords[1])
            sc=_("Scale:")+(" %5.1f" %scale)
   
        self.parent.SetStatusText(x,1)
        self.parent.SetStatusText(y,2)
        self.parent.SetStatusText(sc,3)

        event.Skip()

    def OnLeave(self, event):
        self.parent.SetStatusText("",1)
        self.parent.SetStatusText("",2)
        #self.parent.SetStatusText("",3)
        event.Skip()

    def Clear(self,event = None):
        self.UnBindAllMouseEvents()
        self.Canvas.InitAll()
        self.Canvas.Draw()
  
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
#




class MyCanvasContentClass:
    def __init__(self,MyGraphic,MyMessages,MyConfig,MyLayersTree, MyEntTree, MySelectionInfo):
        self.MyGraphic=MyGraphic
        self.Canvas=MyGraphic.Canvas
        self.MyMessages=MyMessages
        self.MyConfig=MyConfig
        self.MyLayersTree=MyLayersTree
        self.MyEntTree=MyEntTree
        self.MySelectionInfo=MySelectionInfo
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitiesRoot=EntitieContentClass()
        self.BaseEntities=EntitieContentClass()
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]
        
        #Zuweisen der Verbindung zwischen den zwei Klassen
        MyGraphic.MyCanvasContent=self
        MyEntTree.MyCanvasContent=self
        MyLayersTree.MyCanvasContent=self
        MySelectionInfo.MyCanvasContent=self

        self.MyEntTree.MySelectionInfo=MySelectionInfo
        self.MyLayersTree.MySelectionInfo=MySelectionInfo
        

        #Anfangswert fuer das Ansicht Toggle Menu
        self.toggle_wp_zero=1
        self.toggle_start_stop=0
        self.toggle_show_disabled=0

        
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
        dir=self.Selected[0].cut_cor
        for shape in self.Selected: 
            if not(dir==shape.cut_cor):
                return -1   
        return dir
                
    #Erstellen des Gesamten Ausdrucks      
    def makeplot(self,values,p0,pb,sca,rot):
        self.values=values

        #Loeschen des Inhalts     
        self.Canvas.InitAll()
        
        #Standardwerte fuer scale, dx, dy zuweisen
        ## these set the limits for how much you can zoom in and out
        #self.Canvas.MinScale = 14
        #self.Canvas.MaxScale = 500

        self.toggle_start_stop=0
        self.toggle_wp_zero=1
        self.toggle_grid=1

        #Zuruecksetzen der Konturen
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitiesRoot=EntitieContentClass(Nr=0,Name='Entities',parent=None,children=[],
                                            p0=p0,pb=pb,sca=sca,rot=rot)
        self.Selected=[]
        self.Deselected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]
        self.show_dis=0


        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        self.makeshapes(parent=self.EntitiesRoot)
        self.plot_shapes()
        
        #Erstellen des Werkstücknullpunkts
        self.autoscale()
        
        
        
        self.plot_wp_zero()
        self.plot_grid()
        
        #Autoskalieren des Canvas Bereichs
        self.autoscale()
       
        #Sortieren der Listen mit den Layers
        self.LayerContents.sort()
         
        #Erstellen der Layers Liste (Tree)
        self.MyLayersTree.MakeLayerList(self.LayerContents)
        self.MyEntTree.MakeEntitieList(self.EntitiesRoot)
        
    def autoscale(self):
        self.Canvas.ZoomToBB()

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
            shape.plot2can(self.Canvas)
            shape.geo_hdl.Name = shape   
            shape.geo_hdl.HitLineWidth=15
            shape.geo_hdl.Bind(FloatCanvas.EVT_FC_LEFT_UP, self.ShapeGotHit)

        return [0]
    
    def ShapeGotHit(self, Object):
        self.change_selection([Object.Name])
        #self.Canvas._RaiseMouseEvent(event, EventType)
        
    def NothingGotHit(self):
        self.change_selection([])
        
    def ShapesInBB(self,BB):
        InsideList=[]
        BB=BBox.asBBox(BB)
        for shape in self.Shapes:
            if BB.Inside(shape.geo_hdl.BoundingBox):
                InsideList.append(shape)
        self.change_selection(InsideList)
             
            
    def plot_grid(self,event=None):
        
        if not(event==None):
            self.toggle_grid=event.GetSelection()
          
        if self.toggle_grid:
            space=100.0/pow(10,float(ceil(log(self.Canvas.Scale/DOT_PER_MM,10))))
            Grid = FloatCanvas.DotGrid( Spacing=(space, space), Size=2, Color="Gray", Cross=True, CrossThickness=1)
            self.Canvas.GridUnder = Grid
        else:
            Grid=None
            self.Canvas.GridUnder = Grid
        
        #Nur neu malen wenn es aus dem Menu aufgerufen wurde
        if not(event==None):
            self.Canvas.Draw(Force=True)
            
    #Drucken des Werkstuecknullpunkts
    def plot_wp_zero(self,event=None):
        
        if not(event==None):
            self.toggle_wp_zero=event.GetSelection()
            
        self.Canvas.RemoveObjects(self.wp_zero_hdls)
        self.wp_zero_hdls=[]
        
        #Nicht zeichnen wenn er nicht dargestellt werden soll
        if self.toggle_wp_zero:
            radius=4/self.Canvas.Scale*DOT_PER_MM
            points=[]
            
            O=PointClass(x=0,y=0)
            P1=PointClass(x=radius,y=0)
            P2=PointClass(x=0,y=radius)
            P3=PointClass(x=-radius,y=0)
            P4=PointClass(x=0,y=-radius)
            
            arc1=ArcGeo(Pa=P1,Pe=P2,O=O,r=radius,dir=1)
            arc2=ArcGeo(Pa=P4,Pe=P3,O=O,r=radius,dir=-1)
            arc3=ArcGeo(Pa=P2,Pe=P3,O=O,r=radius,dir=1)
            arc4=ArcGeo(Pa=P1,Pe=P4,O=O,r=radius,dir=-1)
            
            points1=arc1.plot2can(self.BaseEntities)+\
                    arc2.plot2can(self.BaseEntities)
            points2=arc3.plot2can(self.BaseEntities)+\
                    arc4.plot2can(self.BaseEntities)
        
            hdl1=self.Canvas.AddPolygon(points1,
                               LineWidth = 2,
                               LineColor = "Black",
                               FillColor = "Black",
                               FillStyle = 'Solid')
                            
            hdl2=self.Canvas.AddPolygon(points2,
                               LineWidth = 2,
                               LineColor = "Black",
                               FillColor = "White",
                               FillStyle = 'Solid')
                            
            self.wp_zero_hdls=[hdl1,hdl2]
        
        #Nur neu malen wenn es aus dem Menu aufgerufen wurde
        if not(event==None):
            self.Canvas.Draw(Force=True)
              
                  
    def plot_cut_info(self,event=None):
        
        #Falls aus dem Callback aufgerufen wurde
        if not(event==None):
            self.toggle_start_stop=event.GetSelection()
   
        length=8/self.Canvas.Scale*DOT_PER_MM
        
        self.Canvas.RemoveObjects(self.dir_hdls)
        self.dir_hdls=[]

        if not(self.toggle_start_stop):
            draw_list=self.Selected[:]
        else:
            draw_list=self.Shapes
               
        for shape in draw_list:
            if not(shape in self.Disabled):
                self.dir_hdls+=shape.plot_cut_info(self.Canvas,self.MyConfig,length)
                
        #Nur neu malen wenn es aus dem Menu aufgerufen wurde
        if not(event==None):
            self.Canvas.Draw(Force=True)

    def show_disabled(self,event):
        if (event.IsChecked()):
            self.set_hdls_normal(self.Disabled)
            self.show_dis=1
        else:
            self.set_hdls_hidden(self.Disabled)
            self.show_dis=0
        self.Canvas.Draw(Force=True)

    def plot_opt_route(self,shapes_st_en_points,route):
        #Ausdrucken der optimierten Route
        for en_nr in range(len(route)):
            if en_nr==0:
                st_nr=-1
                col='Grey'
            elif en_nr==1:
                st_nr=en_nr-1
                col='Grey'
            else:
                st_nr=en_nr-1
                col=(225, 176, 98)
                
            st=shapes_st_en_points[route[st_nr]][1]
            en=shapes_st_en_points[route[en_nr]][0]

            self.path_hdls.append(self.Canvas.AddArrowLine([(st.x,st.y),
                                    (en.x,en.y)],
                                    LineWidth = 1, LineColor = col,
                                    ArrowHeadSize = 18,
                                    ArrowHeadAngle = 18))
                                    
        self.Canvas.Draw(Force=True)
        
    def delete_opt_path(self):
        self.Canvas.RemoveObjects(self.path_hdls)
        self.path_hdls=[]

    #Hinzufuegen der Kontur zum Layer        
    def addtoLayerContents(self,shape_nr,lay_nr):
        #Abfrage of der gesuchte Layer schon existiert
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.Shapes.append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(MyLayerContentClass(LayerNr=lay_nr,
                                                    LayerName=LayerName,
                                                    Shapes=[shape_nr]))
        
    def change_selection(self,sel_shapes):
        if self.MyGraphic.lastkey==0:
            
            self.Deselected=self.Selected[:]
            self.Selected=sel_shapes[:]

            self.MyMessages.prt(_('\nAdded all shapes to selection'),3)
            for shape in sel_shapes:
                self.MyMessages.prt(_('\n%s:')%(shape),3)
                #for geo in shape.geos:
                #    print geo
            
        else:
            self.Deselected=[]
            for shape in sel_shapes:
                if not(shape in self.Selected):
                    self.Selected.append(shape)
                    self.MyMessages.prt(_('\n\nAdded shape to selection %s:')%(shape),3)
                else:
                    self.Selected.remove(shape)
                    self.Deselected.append(shape)
                    self.MyMessages.prt(_('\n\Removed shape to selection %s:')%(shape),3)

        self.deselect()
        self.select()
        
        self.MySelectionInfo.change_selection(self.Selected)
        self.Canvas.Draw(Force=True)

    def deselect(self): 
        self.set_shapes_color(self.Deselected,'deselected')
        self.Deselected=[]
            
    def select(self):
        self.set_shapes_color(self.Selected,'selected')
        self.plot_cut_info()
    
    def disable(self):
        
        #Vorhandene Direction Pfeile löschen aus Canvas
        self.Canvas.RemoveObjects(self.dir_hdls)
        self.dir_hdls=[]
        
        self.set_shapes_color(self.Disabled,'disabled')
        if (self.show_dis==0):
            self.set_hdls_hidden(self.Disabled)
            
 
    def invert_selection(self,event):
        new_sel=[]
        for shape in self.Shapes:
            if (not(shape in self.Disabled)) & (not(shape in self.Selected)):
                new_sel.append(shape)

        self.deselect()
        self.Deselected=self.Selected[:]
        self.Selected=new_sel

        self.deselect()
        self.select()
        
        self.Canvas.Draw(Force=True)

        self.MyMessages.prt(_('\nInverting Selection'),3)
        

    def disable_selection(self,event):
        for shape in self.Selected:
            if not(shape in self.Disabled):
                self.Disabled.append(shape)
        self.disable()
        #self.Selected=[]
        self.Canvas.Draw(Force=True)

    def enable_selection(self,event):
        for shape in self.Selected:
            if shape in self.Disabled:
                nr=self.Disabled.index(shape)
                del(self.Disabled[nr])
        self.select()
        self.Canvas.Draw(Force=True)

    

    def switch_shape_dir(self,event):
        for shape in self.Selected:
            shape.reverse()
            self.MyMessages.prt(_('\n\nSwitched Direction at Shape: %s')\
                             %(shape),3)
        self.plot_cut_info()
        
    def set_cor_40(self,event):
        self.set_cut_cor(40)
        
    def set_cor_41(self,event):
        self.set_cut_cor(41)
        
    def set_cor_42(self,event):
        self.set_cut_cor(42)
        
    def set_cut_cor(self,correction):
        for shape in self.Selected: 
            shape.cut_cor=correction
            self.MyMessages.prt(_('\n\nChanged Cutter Correction at Shape: %s')\
                             %(shape),3)
        self.plot_cut_info()
        self.Canvas.Draw(Force=True)
        
    def set_shapes_color(self,shapes,state):
        s_shapes=[]
        d_shapes=[]
        for shape in shapes:
            if not(shape in self.Disabled):
                s_shapes.append(shape)
            else:
                d_shapes.append(shape)
        
        if state=='deselected':
            s_color='BLACK'
            d_color='GRAY'
        elif state=='selected':
            s_color='RED'
            d_color='BLUE'
        elif state=='disabled':
            s_color='GRAY'
            d_color='GRAY'
            
        #print 'disable: %s' %d_shapes
        #print 'enable: %s' %s_shapes
        
        self.set_color(d_shapes,d_color)
        self.set_color(s_shapes,s_color)
        

    def set_color(self,shapes,color):
        for shape in shapes:
            shape.geo_hdl.SetLineColor(color)

    def set_hdls_hidden(self,shapes):
        for shape in shapes:
            shape.geo_hdl.Visible = False

    def set_hdls_normal(self,shapes):
        for shape in shapes:
            shape.geo_hdl.Visible = True   
            
      
class MyLayerContentClass:
    def __init__(self,type='Layer',LayerNr=None,LayerName='',Shapes=[]):
        self.type=type
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

class MySelectionInfoClass(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,size=wx.Size(300,150)):
        
        wx.ListCtrl.__init__(
            self, parent, ID,size=size,pos=pos,
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES
            )
            
        self.InsertColumn(0, "Entitie Type")
        self.InsertColumn(1, "Name:")
        self.InsertColumn(2, "Name:")
        
        self.SetItemCount(100)
        
        #self.Append(('bdsafsla1','blsda2','blasaf3'))
        #self.Append(('blsa1','bla2','bla3'))

        #self.SetStringItem(0,1, 'WO')
        #self.SetStringItem(1,1, 'WO')
        #self.SetStringItem(1,1, 'WO')

        self.SelectionStr=[]
        #self.InsertColumn(4, "Name:")


    def change_selection(self,sel_shapes):
        SelectionStr=[]
        for shape in sel_shapes:
            SelectionStr.append(shape.makeSelectionStr())
            
        self.SelectionStr=self.SelectionStr
   
    def OnGetItemText(self, item, col):
        print item
        print col
        try:
            strs=self.SelectionStr[col]
            print strs
            if item==1:
                str=strs.Name
            elif item==2:
                str=strs.Type
            elif item==3:
                str=strs.Pa
            elif item==4:
                str=strs.Pe
        except:
            str='d'
            
        print str
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

