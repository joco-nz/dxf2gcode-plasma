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
                   parent=None,
                   BoxCallback=None,
                   ZoomCallback=None,
                   id = wx.ID_ANY,
                   size = wx.DefaultSize,
                   **kwargs): # The rest just get passed into FloatCanvas
        wx.Panel.__init__(self, parent, id, size=size)

        self.Modes = [("Pointer",  GUIMouseNew(None,BoxCallback),   Resources.getPointerBitmap()),
                      ("Zoom In",  GUIZoomInNew(None,ZoomCallback),  Resources.getMagPlusBitmap()),
                      ("Zoom Out", GUIZoomOutNew(None,ZoomCallback), Resources.getMagMinusBitmap()),
                      ("Pan",      GUIMoveNew(None,ZoomCallback),    Resources.getHandBitmap()),
                      ]
        
        self.ZoomCallback=ZoomCallback
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
        self.Canvas.ZoomToBB(DrawFlag=False)
        self.ZoomCallback()
        self.Canvas.ZoomToBB(DrawFlag=True)
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
        if not self.Callback is None:
            self.StartRBBox = N.array( event.GetPosition() )
            self.PrevRBBox = None
            self.Canvas.CaptureMouse()
        else:

            EventType = FloatCanvas.EVT_FC_LEFT_DOWN
            if not self.Canvas.HitTest(event, EventType):
                self.Canvas._RaiseMouseEvent(event, EventType)

    def OnLeftUp(self, event):
        if event.LeftUp() and not self.StartRBBox is None and not self.Callback is None:
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
            else:
                EventType = FloatCanvas.EVT_FC_LEFT_UP
                #print 'habs auch gekriegt'
                if not self.Canvas.HitTest(event, EventType):
                    self.Canvas._RaiseMouseEvent(event, EventType)
            self.StartRBBox = None
        if self.Callback is None:
                EventType = FloatCanvas.EVT_FC_LEFT_UP
                #print 'habs auch gekriegt'
                if not self.Canvas.HitTest(event, EventType):
                    self.Canvas._RaiseMouseEvent(event, EventType)
            


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


class GUIZoomInNew(GUIMode.GUIBase):
 
    def __init__(self, canvas=None,ZoomCallback=None):
        GUIMode.GUIBase.__init__(self, canvas)
        self.StartRBBox = None
        self.PrevRBBox = None
        self.ZoomCallback=ZoomCallback
        self.Cursor = self.Cursors.MagPlusCursor

    def OnLeftDown(self, event):
        self.StartRBBox = N.array( event.GetPosition() )
        self.PrevRBBox = None
        self.Canvas.CaptureMouse()

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
                
                self.Canvas.ZoomToBB(BB,DrawFlag=False)
                self.ZoomCallback()
                self.Canvas.Draw()
            else:
                Center = self.Canvas.PixelToWorld(StartRBBox)
                self.Zoom(1.5,Center)
            self.StartRBBox = None

    def OnMove(self, event):
        # Always raise the Move event.
        self.Canvas._RaiseMouseEvent(event,FloatCanvas.EVT_FC_MOTION)
        if event.Dragging() and event.LeftIsDown() and not (self.StartRBBox is None):
            xy0 = self.StartRBBox
            xy1 = N.array( event.GetPosition() )
            wh  = abs(xy1 - xy0)
            wh[0] = max(wh[0], int(wh[1]*self.Canvas.AspectRatio))
            wh[1] = int(wh[0] / self.Canvas.AspectRatio)
            xy_c = (xy0 + xy1) / 2
            dc = wx.ClientDC(self.Canvas)
            dc.BeginDrawing()
            dc.SetPen(wx.Pen('WHITE', 2, wx.SHORT_DASH))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetLogicalFunction(wx.XOR)
            if self.PrevRBBox:
                dc.DrawRectanglePointSize(*self.PrevRBBox)
            self.PrevRBBox = ( xy_c - wh/2, wh )
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

    def OnRightDown(self, event):
        self.Zoom(1/1.5, event.GetPosition(), centerCoords="pixel")

    def OnWheel(self, event):
        if event.GetWheelRotation() < 0:
            self.Zoom(0.9)
        else:
            self.Zoom(1.1)
            
    def Zoom(self, factor, center = None, centerCoords="world"):

        """
        Zoom(factor, center) changes the amount of zoom of the image by factor.
        If factor is greater than one, the image gets larger.
        If factor is less than one, the image gets smaller.

        center is a tuple of (x,y) coordinates of the center of the viewport, after zooming.
        If center is not given, the center will stay the same.

        centerCoords is a flag indicating whether the center given is in pixel or world 
        coords. Options are: "world" or "pixel"
        
        """
        self.Canvas.Scale = self.Canvas.Scale*factor
        if not center is None:
            if centerCoords == "pixel":
                center = self.Canvas.PixelToWorld( center )
            else:
                center = N.array(center,N.float)
            self.Canvas.ViewPortCenter = center

        self.Canvas.SetToNewScale(DrawFlag=False)
        self.ZoomCallback()
        self.Canvas.Draw()

class GUIZoomOutNew(GUIMode.GUIBase):

    def __init__(self, Canvas=None, ZoomCallback=None):
        GUIMode.GUIBase.__init__(self, Canvas)
        self.ZoomCallback=ZoomCallback
        self.Cursor = self.Cursors.MagMinusCursor
        
    def OnLeftDown(self, event):
        self.Zoom(1/1.5, event.GetPosition(), centerCoords="pixel")

    def OnRightDown(self, event):
        self.Zoom(1.5, event.GetPosition(), centerCoords="pixel")

    def OnWheel(self, event):
        if event.GetWheelRotation() < 0:
            self.Zoom(0.9)
        else:
            self.Zoom(1.1)

    def OnMove(self, event):
        # Always raise the Move event.
        self.Canvas._RaiseMouseEvent(event,FloatCanvas.EVT_FC_MOTION)


    def Zoom(self, factor, center = None, centerCoords="world"):

        """
        Zoom(factor, center) changes the amount of zoom of the image by factor.
        If factor is greater than one, the image gets larger.
        If factor is less than one, the image gets smaller.

        center is a tuple of (x,y) coordinates of the center of the viewport, after zooming.
        If center is not given, the center will stay the same.

        centerCoords is a flag indicating whether the center given is in pixel or world 
        coords. Options are: "world" or "pixel"
        
        """
        self.Canvas.Scale = self.Canvas.Scale*factor
        if not center is None:
            if centerCoords == "pixel":
                center = self.Canvas.PixelToWorld( center )
            else:
                center = N.array(center,N.float)
            self.Canvas.ViewPortCenter = center
            
        self.Canvas.SetToNewScale(DrawFlag=False)
        self.ZoomCallback()
        self.Canvas.Draw()
        
class GUIMoveNew(GUIMode.GUIBase):
    def __init__(self, canvas=None, ZoomCallback=None):
        GUIMode.GUIBase.__init__(self, canvas)
        self.ZoomCallback=ZoomCallback
        self.Cursor = self.Cursors.HandCursor
        self.GrabCursor = self.Cursors.GrabHandCursor
        self.StartMove = None
        self.PrevMoveXY = None
        
        ## timer to give a delay when moving so that buffers aren't re-built too many times.
        self.MoveTimer = wx.PyTimer(self.OnMoveTimer)

    def OnLeftDown(self, event):
        self.Canvas.SetCursor(self.GrabCursor)
        self.Canvas.CaptureMouse()
        self.StartMove = N.array( event.GetPosition() )
        self.PrevMoveXY = (0,0)

    def OnLeftUp(self, event):
        self.Canvas.SetCursor(self.Cursor)

    def OnMove(self, event):
        # Always raise the Move event.
        self.Canvas._RaiseMouseEvent(event, FloatCanvas.EVT_FC_MOTION)
        if event.Dragging() and event.LeftIsDown() and not self.StartMove is None:
            self.MoveImage(event)
            self.EndMove = N.array(event.GetPosition())
            self.MoveTimer.Start(30, oneShot=True)

    def OnMoveTimer(self, event=None):
        DiffMove = self.StartMove-self.EndMove
        self.Canvas.MoveImage(DiffMove, 'Pixel')
        self.StartMove = self.EndMove
        
    def MoveImage(self, event):
        xy1 = N.array( event.GetPosition() )
        wh = self.Canvas.PanelSize
        xy_tl = xy1 - self.StartMove
        dc = wx.ClientDC(self.Canvas)
        dc.BeginDrawing()
        x1,y1 = self.PrevMoveXY
        x2,y2 = xy_tl
        w,h = self.Canvas.PanelSize
        ##fixme: This sure could be cleaner!
        ##   This is all to fill in the background with the background color
        ##   without flashing as the image moves.
        if x2 > x1 and y2 > y1:
            xa = xb = x1
            ya = yb = y1
            wa = w
            ha = y2 - y1
            wb = x2-  x1
            hb = h
        elif x2 > x1 and y2 <= y1:
            xa = x1
            ya = y1
            wa = x2 - x1
            ha = h
            xb = x1
            yb = y2 + h
            wb = w
            hb = y1 - y2
        elif x2 <= x1 and y2 > y1:
            xa = x1
            ya = y1
            wa = w
            ha = y2 - y1
            xb = x2 + w
            yb = y1
            wb = x1 - x2
            hb = h - y2 + y1
        elif x2 <= x1 and y2 <= y1:
            xa = x2 + w
            ya = y1
            wa = x1 - x2
            ha = h
            xb = x1
            yb = y2 + h
            wb = w
            hb = y1 - y2

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(self.Canvas.BackgroundBrush)
        dc.DrawRectangle(xa, ya, wa, ha)
        dc.DrawRectangle(xb, yb, wb, hb)
        self.PrevMoveXY = xy_tl
        if self.Canvas._ForeDrawList:
            dc.DrawBitmapPoint(self.Canvas._ForegroundBuffer,xy_tl)
        else:
            dc.DrawBitmapPoint(self.Canvas._Buffer,xy_tl)
        dc.EndDrawing()
        self.Canvas.Update()

    def OnWheel(self, event):
        """
           By default, zoom in/out by a 0.1 factor per Wheel event.
        """
        if event.GetWheelRotation() < 0:
            self.Zoom(0.9)
        else:
            self.Zoom(1.1)

    def Zoom(self, factor, center = None, centerCoords="world"):

        """
        Zoom(factor, center) changes the amount of zoom of the image by factor.
        If factor is greater than one, the image gets larger.
        If factor is less than one, the image gets smaller.

        center is a tuple of (x,y) coordinates of the center of the viewport, after zooming.
        If center is not given, the center will stay the same.

        centerCoords is a flag indicating whether the center given is in pixel or world 
        coords. Options are: "world" or "pixel"
        
        """
        self.Canvas.Scale = self.Canvas.Scale*factor
        if not center is None:
            if centerCoords == "pixel":
                center = self.Canvas.PixelToWorld( center )
            else:
                center = N.array(center,N.float)
            self.Canvas.ViewPortCenter = center
            
        self.Canvas.SetToNewScale(DrawFlag=False)
        self.ZoomCallback()
        self.Canvas.Draw()