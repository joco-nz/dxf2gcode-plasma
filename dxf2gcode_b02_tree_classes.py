#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_tree_classes.py
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
import os, sys

import ConfigParser

PROGRAMDIRECTORY = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
BITMAPDIRECTORY = PROGRAMDIRECTORY + "/bitmaps"

import wx
#import wx.aui
import wx.lib.customtreectrl as CT
import  wx.lib.mixins.listctrl  as  listmix

class MyNotebookClass(wx.Notebook):
    def __init__(self, parent, id=wx.ID_ANY, MyPostpro=None, MyConfig=None, MyCanvasContent=None):
        wx.Notebook.__init__(self, parent, id, size=(250,180), style=
                             wx.BK_DEFAULT)
                    
        self.MyConfig=MyConfig
        self.MyPostpro=MyPostpro
                
        self.MyEntPanel = wx.Panel(self, -1)
        self.MyLayPanel= wx.Panel(self,-1)
        
        #Erstellen des Baums für die Entities
        self.MyEntTree=MyEntitieTreeClass(self.MyEntPanel, -1, self)       
        self.MySelectionInfo = MySelectionInfoClass(self.MyEntPanel, -1, self)   
        
        self.MyEntTree.MySelectionInfo=self.MySelectionInfo
        self.MySelectionInfo.MyEntTree=self.MyEntTree
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.MyEntTree, 2, wx.EXPAND)
        sizer1.Add(self.MySelectionInfo, 1, wx.EXPAND)
        
        self.MyEntPanel.SetSizer(sizer1)
       
        #Erstellen des Baums für die verwendeten Layers
        self.MyLayersTree = MyLayersTreeClass(self.MyLayPanel, -1, self)
        self.MyExportParas =MyExportParasClass(self.MyLayPanel,-1, self)
        
        self.MyExportParas.MyLayersTree=self.MyLayersTree
        self.MyLayersTree.MyExportParas=self.MyExportParas

        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(self.MyLayersTree, 1, wx.EXPAND)
        sizer2.Add(self.MyExportParas.sboxSizer, 0, wx.EXPAND)
        
        self.MyLayPanel.SetSizer(sizer2)
        
        self.AddPage(self.MyEntPanel, "Entitie Tree")
        self.AddPage(self.MyLayPanel, "Layer Tree")
                               
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnPageChanging)

    def OnPageChanging(self, event):
        pass
    
    def change_selection(self,sel_items=None):
        #print "bin da"
        self.MyCanvasContent.change_selection(sel_items)
        
    def selection_changed(self,sel_items=None):
        #self.MySelectionInfo.change_selection(sel_items)
        self.MyLayersTree.selection_changed(sel_items)


class MyEntitieTreeClass(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, MyNotebook=None):

        CT.CustomTreeCtrl.__init__(self, parent, id, pos=wx.DefaultPosition,
                                 size=wx.Size(250,180),
                                 style=wx.SUNKEN_BORDER |  
                                 CT.TR_HAS_VARIABLE_ROW_HEIGHT | wx.WANTS_CHARS |
                                 CT.TR_FULL_ROW_HIGHLIGHT |CT.TR_HIDE_ROOT| CT.TR_NO_LINES |
                                 CT.TR_MULTIPLE |CT.TR_TWIST_BUTTONS |CT.TR_HAS_BUTTONS)      
        
        self.MyNotebook=MyNotebook
        
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
        #self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

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
        
    def OnKillFocus(self, event):
        self.UnselectAll()

    def OnDisableItem(self, event):
        self.EnableItem(self.current,False)
        
        
    def OnSelChanged(self, event):
        sel_items=[]
        for selection in self.GetSelections():
            item=self.GetItemPyData(selection)
            sel_items+=self.GetItemShapes(item)

                  
        self.MyNotebook.change_selection(sel_items)
    
    def GetItemShapes(self,item):
        SelShapes=[]
        if item.type=="Shape":
            SelShapes.append(item)
            
        elif item.type=="Entitie":
            for child in item.children:
                SelShapes+=self.GetItemShapes(child)
          
        return SelShapes
        
   

class MySelectionInfoClass(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, MyNotebook=None):
        
        wx.ListCtrl.__init__(
            self, parent, ID, pos=wx.DefaultPosition,size=wx.Size(300,150),
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)
            
        self.MyNotebook=MyNotebook
            
        self.InsertColumn(0, "Entitie Type")
        self.InsertColumn(1, "Name:")
        self.InsertColumn(2, "Name:")
        
      
        
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

        try:
            strs=self.SelectionStr[col]
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
            
        return str
    
class MyLayersTreeClass(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, MyNotebook=None):

        CT.CustomTreeCtrl.__init__(self, parent, id, pos=wx.DefaultPosition,
                                 size=wx.Size(250,180),
                                 style=wx.SUNKEN_BORDER |  
                                 CT.TR_HAS_VARIABLE_ROW_HEIGHT | wx.WANTS_CHARS |
                                 CT.TR_FULL_ROW_HIGHLIGHT |CT.TR_HIDE_ROOT| CT.TR_NO_LINES |
                                 CT.TR_TWIST_BUTTONS |CT.TR_HAS_BUTTONS)
        
        self.MyNotebook=MyNotebook
        
        il = wx.ImageList(16, 16)
        il.Add(wx.Bitmap(BITMAPDIRECTORY + "/Layer.ico"))
        il.Add(wx.Bitmap(BITMAPDIRECTORY + "/Polylinie.ico"))

        self.AssignImageList(il)
        #self.root = self.AddRoot("The Root Item")

        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(CT.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        
        self.LayerContents=None

    def MakeLayerList(self,LayerContents=None):
        self.LayerContents=LayerContents
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
                self.EnableItem(last,False)
                    
        


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
        
    def OnKillFocus(self, event):
        pass
        #self.UnselectAll()

    def OnDisableItem(self, event):
        self.EnableItem(self.current, False)
        
        
    def OnSelChanged(self, event):
        sel_items=[]
        for selection in self.GetSelections():
            item=self.GetItemPyData(selection)
            sel_items+=self.GetItemShapes(item)
        
        #Wenn nichts ausgewählt ist die Edit Felder ausschalten.
        if len(sel_items)==0:
            self.MyExportParas.EnableEdit(flag=0)
        #Sonst Werte anzeigen
        else:
            self.MyExportParas.ShowParas(item)
          
        self.MyNotebook.change_selection(sel_items)
    
    def GetItemShapes(self,item):
        SelShapes=[]

        if item is None:
            return []
        elif item.type=="Shape":
            SelShapes.append(item)  
        elif item.type=="Layer":
            for shape in item.Shapes:
                SelShapes+=self.GetItemShapes(shape)
          
        return SelShapes
    
    def selection_changed(self,sel_items=None):
        
        #self.Update()
        print self.GetSelection()
        if len(self.GetSelections())>0:
            self.Unbind(CT.EVT_TREE_SEL_CHANGED)
            self.UnselectAll()
            self.Bind(CT.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        #print dir(self)
        #self.Update()
        
        

class MyExportParasClass():
    def __init__(self,parent=None,id=-1,MyNotebook=None):
        self.MyNotebook=MyNotebook
        
        self.Sbox=wx.StaticBox(parent, id,'Layer Export Parameters',(3,3))
        self.MakeInputDlg(parent,self.MyNotebook.MyConfig)
        self.BindInputDlg()
        self.EnableEdit(0)
    
    def MakeInputDlg(self,parent,config):

        self.sboxSizer       = wx.StaticBoxSizer(self.Sbox, wx.VERTICAL)
        gridSizer       = wx.FlexGridSizer(rows=2, cols=2, hgap=3, vgap=3)

        label_tool_dia=wx.StaticText(parent, wx.ID_ANY, _('Tool diameter [mm]:'),size=(180,-1))
        self.edit_tool_dia=wx.TextCtrl(parent, wx.ID_ANY, '',size=(45,-1))

        label_start_rad=wx.StaticText(parent, wx.ID_ANY, _("Start radius (for tool comp.) [mm]:"),size=(180,-1))
        self.edit_start_rad=wx.TextCtrl(parent, wx.ID_ANY, '',size=(45,-1))
        
        label_axis3_safe_margin=wx.StaticText(parent, wx.ID_ANY, _("%s safety margin [mm]:") %config.ax3_letter,size=(180,-1))
        self.edit_axis3_safe_margin=wx.TextCtrl(parent, wx.ID_ANY, '',size=(45,-1))
        
        label_axis3_slice_depth=wx.StaticText(parent, wx.ID_ANY, _("%s infeed depth [mm]:") %config.ax3_letter,size=(180,-1))
        self.edit_axis3_slice_depth=wx.TextCtrl(parent, wx.ID_ANY, '',size=(45,-1))
         
        label_axis3_mill_depth=wx.StaticText(parent, wx.ID_ANY, _("%s mill depth [mm]:") %config.ax3_letter,size=(180,-1))
        self.edit_axis3_mill_depth=wx.TextCtrl(parent, wx.ID_ANY, '',size=(45,-1))
        
        label_F_G1_Depth=wx.StaticText(parent, wx.ID_ANY, _("G1 feed %s-direction [mm/min]:") %config.ax3_letter,size=(180,-1))
        self.edit_F_G1_Depth=wx.TextCtrl(parent, wx.ID_ANY, '',size=(45,-1))
    
        label_F_G1_Plane=wx.StaticText(parent, wx.ID_ANY, _("G1 feed %s%s-direction [mm/min]:") %(config.ax1_letter,config.ax2_letter),size=(180,-1))
        self.edit_F_G1_Plane=wx.TextCtrl(parent, wx.ID_ANY, '',size=(45,-1))
    
        gridSizer.Add(label_tool_dia, 0, wx.EXPAND)
        gridSizer.Add(self.edit_tool_dia, 0, wx.EXPAND|wx.ALIGN_LEFT)
        
        gridSizer.Add(label_start_rad, 0, wx.EXPAND)
        gridSizer.Add(self.edit_start_rad, 0, wx.EXPAND|wx.ALIGN_LEFT)
        
        gridSizer.Add(label_axis3_safe_margin, 0, wx.EXPAND)
        gridSizer.Add(self.edit_axis3_safe_margin, 0, wx.EXPAND|wx.ALIGN_LEFT)
        
        gridSizer.Add(label_axis3_slice_depth, 0, wx.EXPAND)
        gridSizer.Add(self.edit_axis3_slice_depth, 0, wx.EXPAND|wx.ALIGN_LEFT)
        
        gridSizer.Add(label_axis3_mill_depth, 0, wx.EXPAND)
        gridSizer.Add(self.edit_axis3_mill_depth, 0, wx.EXPAND|wx.ALIGN_LEFT)
        
        gridSizer.Add(label_F_G1_Depth, 0, wx.EXPAND)
        gridSizer.Add(self.edit_F_G1_Depth, 0, wx.EXPAND|wx.ALIGN_LEFT)
        
        gridSizer.Add(label_F_G1_Plane, 0, wx.EXPAND)
        gridSizer.Add(self.edit_F_G1_Plane, 0, wx.EXPAND|wx.ALIGN_LEFT)
        
        self.sboxSizer.Add(gridSizer, 0, wx.ALL|wx.EXPAND, 5)

    def BindInputDlg(self):
        self.edit_tool_dia.Bind(wx.EVT_TEXT, self.Get_tool_dia)
        self.edit_start_rad.Bind(wx.EVT_TEXT, self.Get_start_rad)
        self.edit_axis3_safe_margin.Bind(wx.EVT_TEXT, self.Get_axis3_safe_margin)
        self.edit_axis3_slice_depth.Bind(wx.EVT_TEXT, self.Get_axis3_slice_depth)
        self.edit_axis3_mill_depth.Bind(wx.EVT_TEXT, self.Get_axis3_mill_depth)
        self.edit_F_G1_Depth.Bind(wx.EVT_TEXT, self.Get_F_G1_Depth)
        self.edit_F_G1_Plane.Bind(wx.EVT_TEXT, self.Get_F_G1_Plane)
        
    def EnableEdit(self,flag=1):
        self.edit_tool_dia.Enable(flag)
        self.edit_start_rad.Enable(flag)
        self.edit_axis3_safe_margin.Enable(flag)
        self.edit_axis3_slice_depth.Enable(flag)
        self.edit_axis3_mill_depth.Enable(flag)
        self.edit_F_G1_Depth.Enable(flag)
        self.edit_F_G1_Plane.Enable(flag)
        
    def ShowParas(self,LayerContent):
        self.EnableEdit(1)
        self.LayerContent=LayerContent
        
        self.edit_tool_dia.ChangeValue('%0.2f' %LayerContent.tool_dia)
        self.edit_start_rad.ChangeValue('%0.2f' %LayerContent.start_rad)
        self.edit_axis3_safe_margin.ChangeValue('%0.2f' %LayerContent.axis3_safe_margin)
        self.edit_axis3_slice_depth.ChangeValue('%0.2f' %LayerContent.axis3_slice_depth)
        self.edit_axis3_mill_depth.ChangeValue('%0.2f' %LayerContent.axis3_mill_depth)
        self.edit_F_G1_Depth.ChangeValue('%0.0f' %LayerContent.F_G1_Depth)
        self.edit_F_G1_Plane.ChangeValue('%0.0f' %LayerContent.F_G1_Plane)
       
    def Get_tool_dia(self, event):
        self.LayerContent.tool_dia=float(event.GetString())
        self.LayerContent.SafeLayerContentFile()

    def Get_start_rad(self, event):
        self.LayerContent.start_rad=float(event.GetString())
        self.LayerContent.SafeLayerContentFile()

    def Get_axis3_safe_margin(self, event):
        self.LayerContent.axis3_safe_margin=float(event.GetString())
        self.LayerContent.SafeLayerContentFile()
        
    def Get_axis3_slice_depth(self, event):
        self.LayerContent.axis3_slice_depth=float(event.GetString())
        self.LayerContent.SafeLayerContentFile()
        
    def Get_axis3_mill_depth(self, event):
        self.LayerContent.axi3_mill_depth=float(event.GetString())
        self.LayerContent.SafeLayerContentFile()

    def Get_F_G1_Depth(self, event):
        self.LayerContent.F_G1_Depth=float(event.GetString())
        self.LayerContent.SafeLayerContentFile()
        
    def Get_F_G1_Plane(self, event):
        self.LayerContent.F_G1_Plane=float(event.GetString())
        self.LayerContent.SafeLayerContentFile()

class MyLayerContentClass:
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
        self.SafeLayerContentFile()
        
    def MakeSettingFolder(self): 
        # create settings folder if necessary 
        try: 
            os.mkdir(self.folder) 
        except OSError: 
            pass     
    
    def SafeLayerContentFile(self):
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
            dial=wx.MessageDialog(None, _("Please delete or correct\n %s")\
                      %(os.path.join(self.folder,self.cfg_file_name)),_("Error during reading config file"), wx.OK | 
            wx.ICON_ERROR)
            dial.ShowModal()

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
