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
DATE        = "2009-08-17"
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
from dxf2gcode_b02_ccomp import InterSectionPoint, Polylines
from wx.lib.floatcanvas import FloatCanvas, Resources
from wx.lib.floatcanvas.Utilities import BBox
import wx.richtext as rt
import dxf2gcode_b02_FloatCanvas_mod as NavCanvas
#import wx_lib_floatcanvas_Utilities as GUI
import wx.lib.colourdb

import locale
import gettext, tempfile, subprocess
from copy import copy
from math import radians, degrees, log, ceil

from dxf2gcode_inputdlg import VarDlg
from dxf2gcode_b02_point import PointClass, LineGeo, ArcGeo
from dxf2gcode_b02_shape_mod import ShapeClass, EntitieContentClass #ANDERST####################################
import dxf2gcode_b02_dxf_import as dxfimport 
import dxf2gcode_b02_tsp_opt as tsp
from dxf2gcode_b02_config import MyConfigClass, MyPostprocessorClass
from dxf2gcode_b02_tree_classes import *

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
languages = ['DE_de']

#Default Sprache des Systems herausfinden
lc, encoding = locale.getdefaultlocale()

if (lc):
    #Wenn wir eine haben diese als Default setzen
    languages = [lc]

# Herausfinden welche sprachen wir haben
language = os.environ.get('LANGUAGE', None)
if (language):
    #Die sprachen kommen in folgender Form vom Linzy System zurück:
    #en_CA:en_US:en_GB:en bei Windows nichts. Für Linux muß beim : gespliete werden
    languages += language.split(":")

# "Installieren" der Übersetzung fpr die Funktion _(string)
gettext.bindtextdomain("dxf2gcode", local_path)
gettext.textdomain("dxf2gcode")
trans = gettext.translation("dxf2gcode", localedir='languages', languages=languages, fallback = True)
trans.install()


class MyFrameClass(wx.Frame):
    def __init__(self, parent, load_filename=None,id=-1, title="%s, Version: %s, Date: %s " %(APPNAME.capitalize(),VERSION,DATE),
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
        self.MyPostpro=MyPostprocessorClass(self.MyConfig,self.MyMessages,PROGRAMDIRECTORY,APPNAME, VERSION, DATE)
            
     
        #Erstellen des Notebooks zum Hinzufügen der zwei Bäume
        self.MyNotebook=MyNotebookClass( self, -1,MyPostpro=self.MyPostpro, MyConfig=self.MyConfig)
        
        #Erstellen der Canvas Content Klasse & Bezug in Canvas Klasse
        self.MyCanvasContent=MyCanvasContentClass(self.MyGraphic,self.MyMessages,
                                                self.MyConfig,
                                                self.MyNotebook)  
        
        #Erstellen der Bindings fürs gesamte Fenster
        self.BindMenuEvents()
        
        #Die Verschiedeneen Objecte zum Sizer AUIManager hinzufügen
        self._mgr.AddPane(self.MyNotebook, wx.aui.AuiPaneInfo(). 
                          Caption(_("Entities")).
                          Left().CloseButton(False))            

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
        optionmenu.AppendSeparator()
        optionmenu.Append(405, _("Open Preferences File"), _("Open the Preferences File"))
        optionmenu.Append(406, _("Open Postprocessor Folder"), _("Open the Postprocessor Folder"))
        
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
        self.Bind(wx.EVT_MENU, self.WriteGCode, id=201)
        
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
        
        self.Bind(wx.EVT_MENU, self.MoveWpZero, id=403)
        self.Bind(wx.EVT_MENU, self.RotateWpZero, id=404)
        
        self.Bind(wx.EVT_MENU, self.OpenConfigFile, id=405)
        self.Bind(wx.EVT_MENU, self.OpenPostproFolder, id=406)
        
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

        #Skalierung der Kontur
        self.cont_scale=1.0
        
        #Verschiebung der Kontur
        self.cont_dx=0.0
        self.cont_dy=0.0
        
        #Rotieren um den WP zero
        self.rotate=0.0

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


    def OpenConfigFile(self,event):
        os.startfile(os.path.join(self.MyConfig.folder,self.MyConfig.cfg_file_name))
        
    def OpenPostproFolder(self,event):
        os.startfile(self.MyPostpro.folder)      

    def GetSaveFile(self):
        MyFormats=''
       
        for i in range(len(self.MyPostpro.output_format)):
            if i>0:
                MyFormats+="|"
            name="%s" %(self.MyPostpro.output_text[i])
            format="*%s" %(self.MyPostpro.output_format[i])
            MyFormats+="%s|%s" %(name,format )         

        #Abbruch falls noch kein File geladen wurde.
        if self.load_filename==None:
            showwarning(_("Export G-Code"), _("Nothing to export!"))
            return
        
                
        if not(self.MyConfig.write_to_stdout):
            #Abbruch falls noch kein File geladen wurde.
            if self.load_filename==None:
                showwarning(_("Export G-Code"), _("Nothing to export!"))
                return
            (beg, ende)=os.path.split(self.load_filename)
            (fileBaseName, fileExtension)=os.path.splitext(ende)
            dlg = wx.FileDialog(self, message=_("Save file as ..."),
                                defaultDir=self.MyConfig.load_path,
                                defaultFile=fileBaseName,
                                wildcard=MyFormats, style=wx.SAVE)
            #dlg.SetFilterIndex(filterIndex)
            # This sets the default filter that the user will initially see. Otherwise,
            # the first filter in the list will be used by default.
            #dlg.SetFilterIndex(2)
            # Show the dialog and retrieve the user response. If it is the OK response,
            # process the data.             
            if dlg.ShowModal() == wx.ID_OK:
                paths = dlg.GetPaths()
                return paths[0]
            else:
                return        

    # Callback des Menu Punkts Exportieren
    def WriteGCode(self,event=None):

        #Initial Status fuer den Export
        status=1

        #Config & postpro in einen kurzen Namen speichern
        config=self.MyConfig
        postpro=self.MyPostpro

        if not(config.write_to_stdout):
           
                #Abfrage des Namens um das File zu speichern
                self.save_filename=self.GetSaveFile()
                
                
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
        if config.write_to_stdout:
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
        #self.MoveEnd()
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
  


class MyCanvasContentClass:
    def __init__(self,MyGraphic,MyMessages,MyConfig,MyNotebook):
        self.MyGraphic=MyGraphic
        self.Canvas=MyGraphic.Canvas
        self.MyMessages=MyMessages
        self.MyConfig=MyConfig
        self.MyNotebook=MyNotebook
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
        MyNotebook.MyCanvasContent=self


        #Anfangswert fuer das Ansicht Toggle Menu
        self.toggle_wp_zero=1
        self.toggle_start_stop=0
        self.toggle_show_disabled=0

        
    def __str__(self):
        s='\nNr. of Shapes -> %s' %len(self.Shapes)
        for lay in self.LayerContents:
            s=s+'\n'+str(lay)

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
        #self.plot_shapes()
        ISP=InterSectionPoint()
        pl=Polylines()
        
        for nr in range(len(self.Shapes)):
            self.plot_shapes()
            pl=ISP.do_compensation(self.Shapes[nr], 2, 41)
           # self.Shapes[nr].col=pl.col
            self.Shapes[nr].geos=pl.geos
            
        self.plot_shapes()
        self.Shapes=[]
        
        #Erstellen des Werkstücknullpunkts
        self.autoscale()
        
        
        
        self.plot_wp_zero()
        self.plot_grid()
        
        #Autoskalieren des Canvas Bereichs
        self.autoscale()
       
        #Sortieren der Listen mit den Layers
        self.LayerContents.sort()
         
        #Erstellen der Layers Liste (Tree)
        self.MyNotebook.MyLayersTree.MakeLayerList(self.LayerContents)
        self.MyNotebook.MyEntTree.MakeEntitieList(self.EntitiesRoot)
        
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
                
                self.Shapes[-1].AnalyseAndOptimize(MyConfig=self.MyConfig)

    def plot_shapes(self):
        for shape in self.Shapes:
            shape.plot2can(self.Canvas)
            #shape.geo_hdl.Name = shape   
            #shape.geo_hdl.HitLineWidth=15
            #shape.geo_hdl.Bind(FloatCanvas.EVT_FC_LEFT_UP, self.ShapeGotHit)

        return [0]
    
    def ShapeGotHit(self, Object):
        self.change_selection([Object.Name],caller=self)

        #self.Canvas._RaiseMouseEvent(event, EventType)
        
    def NothingGotHit(self):
        self.change_selection([],caller=self)

        
    def ShapesInBB(self,BB):
        InsideList=[]
        BB=BBox.asBBox(BB)
        for shape in self.Shapes:
            if BB.Inside(shape.geo_hdl.BoundingBox):
                InsideList.append(shape)
        self.change_selection(InsideList,caller=self)
             
            
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
    def addtoLayerContents(self,shape,lay_nr):
        #Abfrage of der gesuchte Layer schon existiert
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.Shapes.append(shape)
                shape.layer=LayCon
                return

        #Falls er nicht gefunden wurde neuen erstellen
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(MyLayerContentClass(LayerNr=lay_nr,
                                                    LayerName=LayerName,
                                                    Shapes=[shape],
                                                    MyMessages=self.MyMessages))
                              

                                                    
        shape.layer=self.LayerContents[-1]
        
    def change_selection(self,sel_shapes=[],caller=None):
        print type(caller)
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
        self.selection_changed()
        

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

    def selection_changed(self):
        pass
        #self.MyNotebook.selection_changed(self.Selected)
        

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

