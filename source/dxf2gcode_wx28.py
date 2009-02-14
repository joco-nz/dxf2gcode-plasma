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
APPNAME     = "dxf2gcode"
VERSION     = "2.0 beta1"
DEBUG       = 3
DOT_PER_MM  = 3.5

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

from wx.lib.floatcanvas import FloatCanvas, Resources
from wx.lib.floatcanvas.Utilities import BBox
import dxf2gcode_b02_FloatCanvas_mod as NavCanvas
#import wx_lib_floatcanvas_Utilities as GUI
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

                            
        #Erstellen der verschiedenen Verzeichnisse
        self.GetFoldernames()
        
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
                          Caption(_("Entities")).Floatable(False).
                          Left().CloseButton(False))            
        self._mgr.AddPane(self.MyLayers,wx.aui.AuiPaneInfo(). 
                          Caption(_("Layers")).Floatable(False). 
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
        
        #Voreininstellungen fuer das Programm laden
        self.MyConfig=MyConfigClass(self.MyMessages)

        #PostprocessorClass initialisieren (Voreinstellungen aus Config)
        self.MyPostpro=MyPostprocessorClass(self.MyConfig,self.MyMessages)
            
#        #Erstellen de Eingabefelder und des Canvas
#        self.ExportParas =ExportParasClass(self.frame_l,self.config,self.postpro)

        #Erstellen der Canvas Content Klasse & Bezug in Canvas Klasse
        self.MyCanvasContent=MyCanvasContentClass(self.MyGraphic,self.MyMessages,self.MyConfig)
        
        #Erstellen der Bindings fürs gesamte Fenster
        self.BindMenuEvents()
 
        
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
        self.Bind(wx.EVT_MENU, self.MyCanvasContent.show_disabled, id=303)
        self.Bind(wx.EVT_MENU, self.MyCanvasContent.autoscale, id=304)
        self.Bind(wx.EVT_MENU, self.del_route_and_menuentry, id=305)
        
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

        #Skalierung der Kontur
        self.cont_scale=1.0
        
        #Verschiebung der Kontur
        self.cont_dx=0.0
        self.cont_dy=0.0
        
        #Einschalten der disabled Menus
        self.EnableAllMenues()

        #Ausdrucken der Werte        
        self.MyCanvasContent.makeplot(self.values)

        #Loeschen alter Route Menues
        self.del_route_and_menuentry()
            
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
    def GetSaveFile(self,event):
        
        if not(self.MyPostpro.write_to_stdout):     

            #Abbruch falls noch kein File geladen wurde.
            if self.load_filename==None:
                showwarning(_("Export G-Code"), _("Nothing to export!"))
                return
            
            saveformat = _('EMC2 GCode Files')+'|ngc.*' 

            (beg, ende)=os.path.split(self.load_filename)
            (fileBaseName, fileExtension)=os.path.splitext(ende)
          
            dlg = wx.FileDialog(
                self, message=_("Save file as ..."), defaultDir=self.MyConfig.load_path, 
                defaultFile=fileBaseName +'.ngc', wildcard=saveformat, style=wx.SAVE)

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
                #for hdl in self.MyCanvasContent.path_hdls:
                #    self.Canvas.canvas.delete(hdl)
                self.MyCanvasContent.path_hdls=[]
                self.MyCanvasContent.plot_opt_route(shapes_st_en_points,self.TSP.opt_route)
                
            self.TSP.calc_next_iteration()
            
        self.MyMessages.prt(_("\nTSP done with result:"),1)
        self.MyMessages.prt(("\n%s" %self.TSP),1)
            
        #Einschlaten des Menupunkts zum löschen des optimierten Pfads.
        self.viewmenu.Enable(305,True)

    def del_route_and_menuentry(self):
        pass
        try:
            self.viewmenu.Enable(305,False)
            self.MyCanvasContent.delete_opt_path()
        except:
            pass
        
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
    
        root = self.AddRoot(_("AUI Project")) 
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
        wx.TextCtrl.__init__(self,parent,id,_('Layers - sample text'),
                            wx.DefaultPosition, wx.Size(200,50),
                            wx.NO_BORDER | wx.TE_MULTILINE)



class MyGraphicClass(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id,  style=wx.SUNKEN_BORDER)
        wx.GetApp().Yield(True)  

        #Referenz zum davor liegenden Hauptfenster
        self.parent=parent
        
        self.lastkey=0
        
        # Add the Canvas
        NC = NavCanvas.NavCanvas(self,self.MultiSelect,
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
    def __init__(self,MyGraphic,MyMessages,MyConfig):
        self.MyGraphic=MyGraphic
        self.Canvas=MyGraphic.Canvas
        self.MyMessages=MyMessages
        self.config=MyConfig
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitieContents=[]
        self.Selected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]
        
        #Zuweisen der Verbindung zwischen den zwei Klassen
        MyGraphic.MyCanvasContent=self


        #Anfangswert fuer das Ansicht Toggle Menu
#        self.toggle_wp_zero=IntVar()
#        self.toggle_wp_zero.set(1)
#
#        self.toggle_start_stop=IntVar()
#        self.toggle_start_stop.set(0)
#
#        self.toggle_show_disabled=IntVar()
#        self.toggle_show_disabled.set(0)  
        
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
    def makeplot(self,values):
        self.values=values

        #Loeschen des Inhalts     
        self.Canvas.InitAll()
        
        #Standardwerte fuer scale, dx, dy zuweisen
        ## these set the limits for how much you can zoom in and out
        #self.Canvas.MinScale = 14
        #self.Canvas.MaxScale = 500

        #Zuruecksetzen der Konturen
        self.Shapes=[]
        self.LayerContents=[]
        self.EntitieContents=[]
        self.Selected=[]
        self.Deselected=[]
        self.Disabled=[]
        self.wp_zero_hdls=[]
        self.dir_hdls=[]
        self.path_hdls=[]
        self.show_dis=1

        #Start mit () bedeutet zuweisen der Entities -1 = Standard
        self.make_shapes(p0=PointClass(x=0,y=0),sca=[1,1,1],rot=0.0)
        self.plot_shapes()
        
        #Autoskalieren des Canvas Bereichs
        self.autoscale()
        #self.canvas.SetMode(GUIMode.GUIMouse(self.canvas))
        
        #wx.CallAfter(self.autoscale())
        
        #Sortieren der Listen mit den Layers
        self.LayerContents.sort()
        self.EntitieContents.sort()

    def autoscale(self):
        self.Canvas.ZoomToBB()

    def make_shapes(self,EntName="Entities",p0=PointClass(x=0,y=0),sca=[1,1,1],rot=0.0):

        if EntName=="Entities":
            ent_nr=-1
            entities=self.values.entities
        else:
            ent_nr=self.values.Get_Block_Nr(EntName)
            entities=self.values.blocks.Entities[ent_nr]
        #Zuweisen der Geometrien in die Variable geos & Konturen in cont
        ent_geos=entities.geo
        cont=entities.cont
        basep=entities.basep
        
        #Schleife fuer die Anzahl der Konturen 
        for c_nr in range(len(cont)):
            #Abfrage falls es sich bei der Kontur um ein Insert eines Blocks handelt
            if ent_geos[cont[c_nr].order[0][0]].Typ=="Insert":
                ent_geo=ent_geos[cont[c_nr].order[0][0]]
                self.make_shapes(ent_geo.BlockName,\
                                    p0-basep+ent_geo.Point,\
                                    [ent_geo.Scale[0]*sca[0],ent_geo.Scale[1]*sca[1],ent_geo.Scale[2]*sca[2]],\
                                    ent_geo.rot)
            else:
                #Schleife fuer die Anzahl der Geometrien
                self.Shapes.append(ShapeClass(len(self.Shapes),\
                                                ent_nr,\
                                                c_nr,\
                                                cont[c_nr].closed,\
                                                p0,\
                                                basep,\
                                                sca[:],\
                                                rot,\
                                                40,\
                                                cont[c_nr].length*sca[0],\
                                                [],\
                                                []))
                for ent_geo_nr in range(len(cont[c_nr].order)):
                    ent_geo=ent_geos[cont[c_nr].order[ent_geo_nr][0]]
                    if cont[c_nr].order[ent_geo_nr][1]:
                        ent_geo.geo.reverse()
                        for geo in ent_geo.geo:
                            geo=copy(geo)
                            geo.reverse()
                            self.Shapes[-1].geos.append(geo)

                        ent_geo.geo.reverse()
                    else:
                        for geo in ent_geo.geo:
                            self.Shapes[-1].geos.append(copy(geo))
                        
                self.addtoLayerContents(self.Shapes[-1].nr,ent_geo.Layer_Nr)
                self.addtoEntitieContents(self.Shapes[-1].nr,ent_nr,c_nr)

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
             
    #Drucken des Werkstuecknullpunkts
    def plot_wp_zero(self):
        pass
#        for hdl in self.wp_zero_hdls:
#            self.Canvas.canvas.delete(hdl) 
#        self.wp_zero_hdls=[]
#        if self.toggle_wp_zero: 
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
    def plot_cut_info(self):
        pass
#        for hdl in self.dir_hdls:
#            self.Canvas.canvas.delete(hdl) 
#        self.dir_hdls=[]
#
#        if not(self.toggle_start_stop):
#            draw_list=self.Selected[:]
#        else:
#            draw_list=range(len(self.Shapes))
#               
#        for shape_nr in draw_list:
#            if not(shape_nr in self.Disabled):
#                self.dir_hdls+=self.Shapes[shape_nr].plot_cut_info(self.Canvas,self.MyConfig)
#

    def plot_opt_route(self,shapes_st_en_points,route):
        #Ausdrucken der optimierten Route
        pass
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
    #Hinzufuegen der Kontur zum Layer        
    def addtoLayerContents(self,shape_nr,lay_nr):
        #Abfrage of der gesuchte Layer schon existiert
        for LayCon in self.LayerContents:
            if LayCon.LayerNr==lay_nr:
                LayCon.Shapes.append(shape_nr)
                return

        #Falls er nicht gefunden wurde neuen erstellen
        LayerName=self.values.layers[lay_nr].name
        self.LayerContents.append(MyLayerContentClass(lay_nr,LayerName,[shape_nr]))
        
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
            
        self.EntitieContents.append(MyEntitieContentClass(ent_nr,EntName,[[shape_nr]]))
        
    def delete_opt_path(self):
        pass
#        for hdl in self.path_hdls:
#            self.Canvas.canvas.delete(hdl)
#            
#        self.path_hdls=[]
  
    def change_selection(self,sel_shapes):
        if self.MyGraphic.lastkey==0:
            
            self.Deselected=self.Selected[:]
            self.Selected=sel_shapes[:]

            self.MyMessages.prt(_('\nAdded all shapes to selection'),3)
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
    
    def disable(self):
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

    def show_disabled(self):
        if (self.toggle_show_disabled==1):
            self.set_hdls_normal(self.Disabled)
            self.show_dis=1
        else:
            self.set_hdls_hidden(self.Disabled)
            self.show_dis=0

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

      
class MyLayerContentClass:
    def __init__(self,LayerNr=None,LayerName='',Shapes=[]):
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.Shapes=Shapes
        
    def __cmp__(self, other):
         return cmp(self.LayerNr, other.LayerNr)

    def __str__(self):
        return '\nLayerNr ->'+str(self.LayerNr)+'\nLayerName ->'+str(self.LayerName)\
               +'\nShapes ->'+str(self.Shapes)
    
class MyEntitieContentClass:
    def __init__(self,EntNr=None,EntName='',Shapes=[]):
        self.EntNr=EntNr
        self.EntName=EntName
        self.Shapes=Shapes

    def __cmp__(self, other):
         return cmp(self.EntNr, other.EntNr)        
        
    def __str__(self):
        return '\nEntNr ->'+str(self.EntNr)+'\nEntName ->'+str(self.EntName)\
               +'\nShapes ->'+str(self.Shapes)
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

    def write_gcode_be(self,load_filename):
        #Schreiben in einen String
        str=("(Generated with dxf2code)\n(Created from file: %s)\n" %load_filename)
        self.string=(str.encode("utf-8"))
        
        #Daten aus dem Textfelder an string anhängen
        self.string+=("%s\n" %self.gcode_be)

    def write_gcode_en(self):
        #Daten aus dem Textfelder an string anhängen   
        self.string+=self.gcode_en

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

