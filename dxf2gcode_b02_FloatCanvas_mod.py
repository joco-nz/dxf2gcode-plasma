"""
A Panel that includes the FloatCanvas and Navigation controls

"""

import wx
import numpy as N
from wx.lib.floatcanvas import FloatCanvas, Resources, GUIMode
#import FloatCanvas, Resources, GUIMode

class NavCanvas(wx.Panel):
    """
    NavCanvas.py

    This is a high level window that encloses the FloatCanvas in a panel
    and adds a Navigation toolbar.

    """

    def __init__(self,
                   parent,
                   callback,
                   id = wx.ID_ANY,
                   size = wx.DefaultSize,
                   **kwargs): # The rest just get passed into FloatCanvas
        wx.Panel.__init__(self, parent, id, size=size)

        self.Modes = [("Pointer",  GUIMouseNew(None,callback),   Resources.getPointerBitmap()),
                      ("Zoom In",  GUIMode.GUIZoomIn(),  Resources.getMagPlusBitmap()),
                      ("Zoom Out", GUIMode.GUIZoomOut(), Resources.getMagMinusBitmap()),
                      ("Pan",      GUIMode.GUIMove(),    Resources.getHandBitmap()),
                      ]
        
        self.BuildToolbar()
        ## Create the vertical sizer for the toolbar and Panel
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.ToolBar, 0, wx.ALL | wx.ALIGN_LEFT | wx.GROW, 4)

        self.Canvas = FloatCanvas.FloatCanvas(self, **kwargs)
        box.Add(self.Canvas, 1, wx.GROW)

        self.SetSizerAndFit(box)

        # default to first mode
        #self.ToolBar.ToggleTool(self.PointerTool.GetId(), True)
        self.Canvas.SetMode(self.Modes[0][1])

        return None

    def BuildToolbar(self):
        """
        This is here so it can be over-ridden in a ssubclass, to add extra tools, etc
        """
        tb = wx.ToolBar(self)
        self.ToolBar = tb
        tb.SetToolBitmapSize((24,24))
        self.AddToolbarModeButtons(tb, self.Modes)
        self.AddToolbarZoomButton(tb)
        tb.Realize()
        ## fixme: remove this when the bug is fixed!
        #wx.CallAfter(self.HideShowHack) # this required on wxPython 2.8.3 on OS-X
    
    def AddToolbarModeButtons(self, tb, Modes):
        self.ModesDict = {}
        for Mode in Modes:
            tool = tb.AddRadioTool(wx.ID_ANY, shortHelp=Mode[0], bitmap=Mode[2])
            self.Bind(wx.EVT_TOOL, self.SetMode, tool)
            self.ModesDict[tool.GetId()]=Mode[1]
        #self.ZoomOutTool = tb.AddRadioTool(wx.ID_ANY, bitmap=Resources.getMagMinusBitmap(), shortHelp = "Zoom Out")
        #self.Bind(wx.EVT_TOOL, lambda evt : self.SetMode(Mode=self.GUIZoomOut), self.ZoomOutTool)

    def AddToolbarZoomButton(self, tb):
        tb.AddSeparator()

        self.ZoomButton = wx.Button(tb, label="Zoom To Fit")
        tb.AddControl(self.ZoomButton)
        self.ZoomButton.Bind(wx.EVT_BUTTON, self.ZoomToFit)


    def HideShowHack(self):
        #fixme: remove this when the bug is fixed!
        """
        Hack to hide and show button on toolbar to get around OS-X bug on
        wxPython2.8 on OS-X
        """
        self.ZoomButton.Hide()
        self.ZoomButton.Show()

    def SetMode(self, event):
        Mode = self.ModesDict[event.GetId()]
        self.Canvas.SetMode(Mode)

    def ZoomToFit(self,Event):
        self.Canvas.ZoomToBB()
        self.Canvas.SetFocus() # Otherwise the focus stays on the Button, and wheel events are lost.
   
#Klasse mit den Inhalten des Canvas & Verbindung zu den Konturen
class GUIMouseNew(GUIMode.GUIBase):
    """

    Mouse mode checks for a hit test, and if nothing is hit,
    raises a FloatCanvas mouse event for each event.

    """
    def __init__(self, canvas=None, Callback= None):
        GUIMode.GUIBase.__init__(self, canvas)
        self.Callback = Callback
        self.StartRBBox = None
        self.PrevRBBox = None
        self.Cursor = self.Cursors.MagPlusCursor
        self.Cursor = wx.NullCursor

    # Handlers
    def OnLeftDown(self, event):
        self.StartRBBox = N.array( event.GetPosition() )
        self.PrevRBBox = None
        self.Canvas.CaptureMouse()
#
#        EventType = FloatCanvas.EVT_FC_LEFT_DOWN
#        #print 'habs gekriegt'
#        if not self.Canvas.HitTest(event, EventType):
#            self.Canvas._RaiseMouseEvent(event, EventType)

    def OnLeftUp(self, event):
        if event.LeftUp() and not self.StartRBBox is None:
            self.PrevRBBox = None
            EndRBBox = event.GetPosition()
            StartRBBox = self.StartRBBox
            # if mouse has moved less that ten pixels, don't use the box.
            if ( abs(StartRBBox[0] - EndRBBox[0]) > 10
                    and abs(StartRBBox[1] - EndRBBox[1]) > 10 ):
                EndRBBox = self.Canvas.PixelToWorld(EndRBBox)
                StartRBBox = self.Canvas.PixelToWorld(StartRBBox)
                BB = N.array(((min(EndRBBox[0],StartRBBox[0]),
                                min(EndRBBox[1],StartRBBox[1])),
                            (max(EndRBBox[0],StartRBBox[0]),
                                max(EndRBBox[1],StartRBBox[1]))),N.float_)
                self.Callback(BB)
                #self.Canvas.ZoomToBB(BB)
            else:
                #Center = self.Canvas.PixelToWorld(StartRBBox)
                EventType = FloatCanvas.EVT_FC_LEFT_UP
                #print 'habs auch gekriegt'
                if not self.Canvas.HitTest(event, EventType):
                    self.Canvas._RaiseMouseEvent(event, EventType)
            self.StartRBBox = None



    def OnLeftDouble(self, event):
        EventType = FloatCanvas.EVT_FC_LEFT_DCLICK
        if not self.Canvas.HitTest(event, EventType):
                self.Canvas._RaiseMouseEvent(event, EventType)

    def OnMiddleDown(self, event):
        EventType = FloatCanvas.EVT_FC_MIDDLE_DOWN
        if not self.Canvas.HitTest(event, EventType):
            self.Canvas._RaiseMouseEvent(event, EventType)

    def OnMiddleUp(self, event):
        EventType = FloatCanvas.EVT_FC_MIDDLE_UP
        if not self.Canvas.HitTest(event, EventType):
            self.Canvas._RaiseMouseEvent(event, EventType)

    def OnMiddleDouble(self, event):
        EventType = FloatCanvas.EVT_FC_MIDDLE_DCLICK
        if not self.Canvas.HitTest(event, EventType):
            self.Canvas._RaiseMouseEvent(event, EventType)

    def OnRightDown(self, event):
        EventType = FloatCanvas.EVT_FC_RIGHT_DOWN
        if not self.Canvas.HitTest(event, EventType):
            self.Canvas._RaiseMouseEvent(event, EventType)

    def OnRightUp(self, event):
        EventType = FloatCanvas.EVT_FC_RIGHT_UP
        if not self.Canvas.HitTest(event, EventType):
            self.Canvas._RaiseMouseEvent(event, EventType)

    def OnRightDouble(self, event):
        EventType = FloatCanvas.EVT_FC_RIGHT_DCLICK
        if not self.Canvas.HitTest(event, EventType):
            self.Canvas._RaiseMouseEvent(event, EventType)

    def OnWheel(self, event):
        EventType = FloatCanvas.EVT_FC_MOUSEWHEEL
        self.Canvas._RaiseMouseEvent(event, EventType)

    def OnMove(self, event):
        # Always raise the Move event.
        self.Canvas.MouseOverTest(event)
        self.Canvas._RaiseMouseEvent(event,FloatCanvas.EVT_FC_MOTION)
        if event.Dragging() and event.LeftIsDown() and not (self.StartRBBox is None):
            xy0 = self.StartRBBox
            xy1 = N.array( event.GetPosition() )
            wh  = xy1 - xy0
            
            dc = wx.ClientDC(self.Canvas)
            dc.BeginDrawing()
            dc.SetPen(wx.Pen('WHITE', 2, wx.SHORT_DASH))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetLogicalFunction(wx.XOR)
            if self.PrevRBBox:
                dc.DrawRectanglePointSize(*self.PrevRBBox)
            self.PrevRBBox = ( xy0, wh )
            dc.DrawRectanglePointSize( *self.PrevRBBox )
            dc.EndDrawing()
            
    def UpdateScreen(self):
        """
        Update gets called if the screen has been repainted in the middle of a zoom in
        so the Rubber Band Box can get updated
        """
        if self.PrevRBBox is not None:
            dc = wx.ClientDC(self.Canvas)
            dc.SetPen(wx.Pen('WHITE', 2, wx.SHORT_DASH))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetLogicalFunction(wx.XOR)
            dc.DrawRectanglePointSize(*self.PrevRBBox)

