#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_shape.py
#Programmers:   Christian Kohl�ffel
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
#
#Main Class Shape



#import sys, os, string, ConfigParser 

from PyQt4 import QtCore, QtGui

import globals as g
import constants as c

from point import PointClass
from base_geometries import LineGeo, ArcGeo
from bounding_box import BoundingBoxClass
from math import cos, sin, radians, degrees
from copy import deepcopy


#from Canvas import Line



class ShapeClass(QtGui.QGraphicsItem):
    def __init__(self, nr='None', closed=0,
                cut_cor=40, length=0.0,
                parent=None,
                geos=[], geos_hdls=[],
                plotoption=0):
        """ 
        Standard method to initialize the class
        """
        QtGui.QGraphicsItem.__init__(self) 
        self.pen=QtGui.QPen(QtCore.Qt.black,2)
        self.pen.setCosmetic(True)
        self.sel_pen=QtGui.QPen(QtCore.Qt.red,2,QtCore.Qt.DashLine)
        self.sel_pen.setCosmetic(True)
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)

        
        #super(ShapeClass, self).__init__(parent)      
               
            
        self.type = "Shape"
        self.nr = nr
        self.closed = closed
        self.cut_cor = 40
        self.length = length
        self.parent = parent
        self.geos = geos
        self.geos_hdls = geos_hdls
        self.BB = BoundingBoxClass(Pa=None, Pe=None)
        self.plotoption = plotoption

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ('\ntype:        %s' % self.type) + \
               ('\nnr:          %i' % self.nr) + \
               ('\nclosed:      %i' % self.closed) + \
               ('\ncut_cor:     %s' % self.cut_cor) + \
               ('\nlen(geos):   %i' % len(self.geos)) + \
               ('\ngeos:        %s' % self.geos) + \
               ('\ngeo_hdls:    %s' % self.geos_hdls)

    def setPen(self,pen):
        """ 
        Method to change the Pen of the outline of the object and update the
        drawing
        """ 
        self.pen=pen
        self.update(self.boundingRect())

    def paint(self, painter, option, _widget):
        """ 
        Method will be triggered with each paint event. Possible to give
        options
        @param painter: Reference to std. painter
        @param option: Possible options here
        @param _widget: The widget which is painted on.
        """ 
        if self.isSelected():
            painter.setPen(self.sel_pen)
            #self.starrow.show()
        else:
            painter.setPen(self.pen)
            #self.starrow.hide()  
            
        painter.drawPath(self.path) 
        
    def boundingRect(self):
        """ 
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """ 
        return self.path.boundingRect()

    def shape(self):
        """ 
        Reimplemented function to select outline only.
        @return: Returns the Outline only
        """ 
        painterStrock=QtGui.QPainterPathStroker()
        painterStrock.setWidth(3.0)  

        stroke = painterStrock.createStroke(self.path)
        return stroke

    def mousePressEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left 
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """
        pass
        #scene=self.scene()
        #print 'habs erwischt shape'
     
#        if event.button() == QtCore.Qt.LeftButton:
#            super(ShapeClass, self).mousePressEvent(event)

    def setSelected(self,flag=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        self.starrow.setSelected(flag)
        self.enarrow.setSelected(flag)

        super(ShapeClass, self).setSelected(flag)

    def AnalyseAndOptimize(self, MyConfig=None):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        #Optimisation for closed shapes
        if self.closed:
            #Startwert setzen f�r die erste Summe
            start, dummy = self.geos[0].get_start_end_points(0)
            summe = 0.0
            for geo in self.geos:
                if geo.type == 'LineGeo':
                    ende, dummy = geo.get_start_end_points(1)
                    summe += (start.x + ende.x) * (ende.y - start.y) / 2
                    start = deepcopy(ende)
                elif geo.type == 'ArcGeo':
                    segments = int((abs(degrees(geo.ext)) // 90) + 1)
                    for i in range(segments): 
                        ang = geo.s_ang + (i + 1) * geo.ext / segments
                        ende = PointClass(x=(geo.O.x + cos(ang) * abs(geo.r)), y=(geo.O.y + sin(ang) * abs(geo.r)))
                        summe += (start.x + ende.x) * (ende.y - start.y) / 2
                        start = deepcopy(ende)
                                        
            if summe > 0.0:
                self.reverse()
                    
            
     
    def reverse(self):
        """ 
        Reverses the direction of the whole shape (switch direction).
        """ 
        self.geos.reverse()
        for geo in self.geos: 
            geo.reverse()

    def switch_cut_cor(self):
        """ 
        Switches the cutter direction between 41 and 42.
        """ 
        if self.cut_cor == 41:
            self.cut_cor = 42
        elif self.cut_cor == 42:
            self.cut_cor = 41

    def get_st_en_points(self, dir=None):
        """
        Returns the start/end point and its direction
        @param direction: 0 to return start point and 1 to return end point
        @return: a list of point and angle 
        """
        start, start_ang=self.geos[0].get_start_end_points(0,self.parent)
        ende, end_ang=self.geos[-1].get_start_end_points(1,self.parent)
        
        if dir==None:
            return start,ende
        elif dir==0:
            return start,start_ang
        elif dir==1:
            return ende, end_ang
        
    def make_papath(self):
        """
        To be called if a Shape shall be printed to the canvas
        @param canvas: The canvas to be printed in
        @param pospro: The color of the shape 
        """
        start, start_ang=self.get_st_en_points()
        
        self.path=QtGui.QPainterPath()
        self.path.moveTo(start.x,-start.y)
        
        g.logger.logger.debug("Adding shape %s:" % (self))
        
        for geo in self.geos:
            geo.add2path(papath=self.path,parent=self.parent)
            
        
            
#                                         tag=self.nr,
#                                         col=col,
#                                         plotoption=self.plotoption)
            
#        if DEBUG:
#            self.BB.plot2can(canvas=canvas, tag=self.nr, col='green', hdl=self.geos_hdls)
            
    def plot_cut_info(self, CanvasClass, config):
        hdls = []
        hdls.append(self.plot_start(CanvasClass))
        hdls.append(self.plot_end(CanvasClass))
        if self.cut_cor > 40:
            hdls.append(self.plot_cut_cor(CanvasClass))
          
            self.make_start_moves(config)
            
            
            #Versatz des Zeichnens durch Position
            P0 = PointClass(x= -CanvasClass.dx * CanvasClass.scale,
                        y= -CanvasClass.dy * CanvasClass.scale - CanvasClass.canvas.winfo_height())
                        
            #Korrektur der Skalierung
            sca = [CanvasClass.scale] * 3
            
            #BaseEntitie erstellen um auf oberster Ebene zu Fr�sen
            BaseEntitie = EntitieContentClass(Nr= -1, Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=P0,
                                        pb=PointClass(x=0.0, y=0.0),
                                        sca=sca,
                                        rot=0.0)
            
            
            hdls += self.st_move[1].plot2can(CanvasClass.canvas, BaseEntitie, tag=self.nr, col='SteelBlue3')
            hdls += self.st_move[2].plot2can(CanvasClass.canvas, BaseEntitie, tag=self.nr, col='SteelBlue3')
        return hdls
            
    def plot_start(self, Canvas=None, length=20):
        #st_point, st_angle=self.geos[0].get_start_end_points(0,parent)
                
        start, start_ang = self.get_st_en_points(0)

        x_ca, y_ca = Canvas.get_can_coordinates(start.x, start.y)

        dx = cos(radians(start_ang)) * length
        dy = sin(radians(start_ang)) * length

        hdl = Line(Canvas.canvas, x_ca, -y_ca, x_ca + dx, -y_ca - dy, fill='SteelBlue3', arrow='last')
        return hdl
    
    
    #Funktion zum drucken der zu fr�senden Kontur mit den Richtungspfeilen usw.
    def plot_cut_cor(self, Canvas=None, length=20):
        start, start_ang = self.get_st_en_points(0)

        #BaseEntitie erstellen um auf oberster Ebene zu Fr�sen
        BaseEntitie = EntitieContentClass(Nr= -1, Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=PointClass(x=0.0, y=0.0),
                                        pb=PointClass(x=0.0, y=0.0),
                                        sca=[1, 1, 1],
                                        rot=0.0)


        x_ca, y_ca = Canvas.get_can_coordinates(start.x, start.y)
        
        if self.cut_cor == 41:
            start_ang = start_ang + 90
        else:
            start_ang = start_ang - 90
            
        dx = cos(radians(start_ang)) * length
        dy = sin(radians(start_ang)) * length

        hdl = Line(Canvas.canvas, x_ca, -y_ca, x_ca + dx, -y_ca - dy, fill='SteelBlue3', arrow='last')
        return hdl
            
    def plot_end(self, Canvas=None, length=20):
        ende, en_angle = self.get_st_en_points(1)
      
        dx = cos(radians(en_angle)) * length
        dy = sin(radians(en_angle)) * length

        x_ca, y_ca = Canvas.get_can_coordinates(ende.x, ende.y)

        hdl = Line(Canvas.canvas, x_ca, -y_ca, x_ca + dx, -y_ca - dy, fill='PaleGreen2', arrow='first')
        return hdl

    def make_start_moves(self, config):
        self.st_move = []

        #Einlaufradius und Versatz 
        start_rad = config.start_rad.get()
        start_ver = start_rad

        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad = config.tool_dia.get() / 2
    
        #Errechnen des Startpunkts mit und ohne Werkzeug Kompensation        
        start, start_ang = self.get_st_en_points(0)
      
        if self.cut_cor == 40:              
            self.st_move.append(start)

        #Fr�sradiuskorrektur Links        
        elif self.cut_cor == 41:
            #Mittelpunkts f�r Einlaufradius
            Oein = start.get_arc_point(start_ang + 90, start_rad + tool_rad)
            #Startpunkts f�r Einlaufradius
            Pa_ein = Oein.get_arc_point(start_ang + 180, start_rad + tool_rad)
            #Startwerts f�r Einlaufgerade
            Pg_ein = Pa_ein.get_arc_point(start_ang + 90, start_ver)
            
            #Eintauchpunkt errechnete Korrektur
            start_ein = Pg_ein.get_arc_point(start_ang, tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line = LineGeo(Pg_ein, Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad = ArcGeo(Pa=Pa_ein, Pe=start, O=Oein, r=start_rad + tool_rad, dir=1)
            self.st_move.append(start_rad)
            
        #Fr�sradiuskorrektur Rechts        
        elif self.cut_cor == 42:

            #Mittelpunkt f�r Einlaufradius
            Oein = start.get_arc_point(start_ang - 90, start_rad + tool_rad)
            #Startpunkt f�r Einlaufradius
            Pa_ein = Oein.get_arc_point(start_ang + 180, start_rad + tool_rad)
            #IJ=Oein-Pa_ein
            #Startwerts f�r Einlaufgerade
            Pg_ein = Pa_ein.get_arc_point(start_ang - 90, start_ver)
            
            #Eintauchpunkts errechnete Korrektur
            start_ein = Pg_ein.get_arc_point(start_ang, tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line = LineGeo(Pg_ein, Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad = ArcGeo(Pa=Pa_ein, Pe=start, O=Oein, r=start_rad + tool_rad, dir=0)
            self.st_move.append(start_rad)
    
    def Write_GCode(self, config, postpro):

        #Erneutes erstellen der Einlaufgeometrien
        self.make_start_moves(config)
        
        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad = config.tool_dia.get() / 2

        #BaseEntitie erstellen um auf oberster Ebene zu Fr�sen
        BaseEntitie = EntitieContentClass(Nr= -1, Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=PointClass(x=0.0, y=0.0),
                                        pb=PointClass(x=0.0, y=0.0),
                                        sca=[1, 1, 1],
                                        rot=0.0)
        


        depth = config.axis3_mill_depth.get()
        max_slice = config.axis3_slice_depth.get()
        
        #Wenn Output Format DXF dann nur einmal Fr�sen
        if postpro.output_type == 'dxf':
            depth = max_slice

        #Scheibchendicke bei Fr�stiefe auf Fr�stiefe begrenzen
        if - abs(max_slice) <= depth:
            mom_depth = depth
        else:
            mom_depth = -abs(max_slice)


        #Positionieren des Werkzeugs �ber dem Anfang und Eintauchen
        self.st_move[0].Write_GCode(parent=BaseEntitie, postpro=postpro)
        
        postpro.rap_pos_z(config.axis3_safe_margin.get())
        postpro.chg_feed_rate(config.F_G1_Depth.get())
        postpro.lin_pol_z(mom_depth)
        postpro.chg_feed_rate(config.F_G1_Plane.get())

        #Wenn G41 oder G42 an ist Fr�sradiuskorrektur        
        if self.cut_cor != 40:
            
            #Errechnen des Startpunkts ohne Werkzeug Kompensation
            #und einschalten der Kompensation     
            start, start_ang = self.get_st_en_points(0)
            postpro.set_cut_cor(self.cut_cor, start)
            
            self.st_move[1].Write_GCode(parent=BaseEntitie, postpro=postpro)
            self.st_move[2].Write_GCode(parent=BaseEntitie, postpro=postpro)

        #Schreiben der Geometrien f�r den ersten Schnitt
        for geo in self.geos:
            geo.Write_GCode(self.parent, postpro)

        #Ausschalten der Fr�sradiuskorrektur
        if (not(self.cut_cor == 40)) & (postpro.cancel_cc_for_depth == 1):
            ende, en_angle = self.get_st_en_points(1)
            if self.cut_cor == 41:
                pos_cut_out = ende.get_arc_point(en_angle - 90, tool_rad)
            elif self.cut_cor == 42:
                pos_cut_out = ende.get_arc_point(en_angle + 90, tool_rad)         
            postpro.deactivate_cut_cor(pos_cut_out)            

        #Z�hlen der Schleifen
        snr = 0
        #Schleifen f�r die Anzahl der Schnitte
        while mom_depth > depth:
            snr += 1
            mom_depth = mom_depth - abs(max_slice)
            if mom_depth < depth:
                mom_depth = depth                

            #Erneutes Eintauchen
            postpro.chg_feed_rate(config.F_G1_Depth.get())
            postpro.lin_pol_z(mom_depth)
            postpro.chg_feed_rate(config.F_G1_Plane.get())

            #Falls es keine geschlossene Kontur ist    
            if self.closed == 0:
                self.reverse()
                self.switch_cut_cor()
                
            #Falls cut correction eingeschaltet ist diese einschalten.
            if ((not(self.cut_cor == 40)) & (self.closed == 0))or(postpro.cancel_cc_for_depth == 1):
                #Errechnen des Startpunkts ohne Werkzeug Kompensation
                #und einschalten der Kompensation     
                postpro.set_cut_cor(self.cut_cor, start)
                
            for geo_nr in range(len(self.geos)):
                self.geos[geo_nr].Write_GCode(self.parent, postpro)

            #Errechnen des Konturwerte mit Fr�sradiuskorrektur und ohne
            ende, en_angle = self.get_st_en_points(1)
            if self.cut_cor == 41:
                pos_cut_out = ende.get_arc_point(en_angle - 90, tool_rad)
            elif self.cut_cor == 42:
                pos_cut_out = ende.get_arc_point(en_angle + 90, tool_rad)

            #Ausschalten der Fr�sradiuskorrektur falls ben�tigt          
            if (not(self.cut_cor == 40)) & (postpro.cancel_cc_for_depth == 1):         
                postpro.deactivate_cut_cor(pos_cut_out)
     
        #Anfangswert f�r Direction wieder herstellen falls n�tig
        if (snr % 2) > 0:
            self.reverse()
            self.switch_cut_cor()

        #Fertig und Zur�ckziehen des Werkzeugs
        postpro.lin_pol_z(config.axis3_safe_margin.get())
        postpro.rap_pos_z(config.axis3_retract.get())

        #Falls Fr�sradius Korrektur noch nicht ausgeschaltet ist ausschalten.
        if (not(self.cut_cor == 40)) & (not(postpro.cancel_cc_for_depth)):
            #Errechnen des Konturwerte mit Fr�sradiuskorrektur und ohne
            ende, en_angle = self.get_st_en_points(1)
            postpro.deactivate_cut_cor(ende)        

        return 1    
    

    
