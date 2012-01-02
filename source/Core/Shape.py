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

import Core.Globals as g

from Core.Point import Point
from Core.BoundingBox import BoundingBox
from math import cos, sin, degrees
from copy import deepcopy


#from Canvas import Line



class ShapeClass(QtGui.QGraphicsItem):
    def __init__(self, nr='None', closed=0,
                cut_cor=40, length=0.0,
                parent=None,
                geos=[],
                plotoption=0):
        """ 
        Standard method to initialize the class
        """
        QtGui.QGraphicsItem.__init__(self) 
        self.pen=QtGui.QPen(QtCore.Qt.black,2)
        self.pen.setCosmetic(True)
        self.sel_pen=QtGui.QPen(QtCore.Qt.red,2,QtCore.Qt.DashLine)
        self.sel_pen.setCosmetic(True)
        self.dis_pen=QtGui.QPen(QtCore.Qt.gray,2,QtCore.Qt.DotLine)
        self.dis_pen.setCosmetic(True)
        self.sel_dis_pen=QtGui.QPen(QtCore.Qt.blue,2,QtCore.Qt.DotLine)
        self.sel_dis_pen.setCosmetic(True)
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)

        
        self.disabled=False
        self.type = "Shape"
        self.nr = nr
        self.closed = closed
        self.cut_cor = 40
        self.length = length
        self.parent = parent
        self.geos = geos
        self.BB = BoundingBox(Pa=None, Pe=None)
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
               ('\ngeos:        %s' % self.geos)

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
        
        if self.isSelected() and not(self.isDisabled()):
            painter.setPen(self.sel_pen)
        elif not(self.isDisabled()):
            painter.setPen(self.pen)
        elif self.isSelected() and self.isDisabled():
            painter.setPen(self.sel_dis_pen)
        else:
            painter.setPen(self.dis_pen)
    
            
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
        self.stmove.setSelected(flag)

        super(ShapeClass, self).setSelected(flag)

    def setDisable(self,flag=False):
        """
        New implemented function which is in parallel to show and hide. 
        @param flag: The flag to enable or disable Selection
        """
        self.disabled=flag
        scene=self.scene()

        if not(scene.showDisabled) and flag:
            self.hide()
            self.starrow.setSelected(False)
            self.enarrow.setSelected(False)
            self.stmove.setSelected(False)
        else:
            self.show()
        
    def isDisabled(self):
        """
        Returns the state of self.Disabled
        """
        return self.disabled
        
    def AnalyseAndOptimize(self, MyConfig=None):
        """ 
        This method is called after the shape has been generated before it gets
        plotted to change all shape direction to a CW shape.
        FIXME
        """ 
        
        g.logger.logger.debug("Analysing the shape for CW direction %s:" % (self))
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
                        ende = Point(x=(geo.O.x + cos(ang) * abs(geo.r)), y=(geo.O.y + sin(ang) * abs(geo.r)))
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
            
        start, start_ang = self.get_st_en_points(0)
        end, end_ang = self.get_st_en_points(1)

        self.update(self.boundingRect())
        self.enarrow.reverseshape(end,end_ang)
        self.starrow.reverseshape(start,start_ang)
        self.stmove.reverseshape(start,start_ang)
        
    def switch_cut_cor(self):
        """ 
        Switches the cutter direction between 41 and 42.
        """ 
        if self.cut_cor == 41:
            self.cut_cor = 42
        elif self.cut_cor == 42:
            self.cut_cor = 41
            
        self.updateCutCor()

    def get_st_en_points(self, dir=None):
        """
        Returns the start/end Point and its direction
        @param direction: 0 to return start Point and 1 to return end Point
        @return: a list of Point and angle 
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
        
        g.logger.logger.debug("Adding shape to Scene Nr: %i" % (self.nr))
        
        for geo in self.geos:
            geo.add2path(papath=self.path,parent=self.parent)
            
            
    def updateCutCor(self):
        """
        This function is called to update the Cutter Correction and therefore 
        the  startmoves if smth. has changed or it shall be generated for 
        first time.
        """
        
        self.stmove.updateCutCor(self.cut_cor)
            
            

    def Write_GCode(self, config, postpro):

        #Erneutes erstellen der Einlaufgeometrien
        self.make_start_moves(config)
        
        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad = config.tool_dia.get() / 2

        #BaseEntitie erstellen um auf oberster Ebene zu Fr�sen
        BaseEntitie = EntitieContentClass(Nr= -1, Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=Point(x=0.0, y=0.0),
                                        pb=Point(x=0.0, y=0.0),
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
    

    
