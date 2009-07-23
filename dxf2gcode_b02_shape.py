#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_shape.py
#Programmers:   Christian Kohlöffel
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
from dxf2gcode_b02_point import PointClass, LineGeo, ArcGeo, MySelectionStrClass
from math import cos, sin, radians, degrees
import wx
from wx.lib.expando import ExpandoTextCtrl

class ShapeClass:
    def __init__(self,nr='None',closed=0,
                cut_cor=40,length=0.0,
                parent=None,
                geos=[],geos_hdls=[]):
                
                    
        self.type="Shape"
        self.nr=nr
        self.closed=closed
        self.cut_cor=40
        self.length=length
        self.parent=parent
        self.geos=geos
        self.geos_hdls=geos_hdls

    def __str__(self):
        return ('\ntype:        %s' %self.type)+\
               ('\nnr:          %i' %self.nr)+\
               ('\nclosed:      %i' %self.closed)+\
               ('\ncut_cor:     %s' %self.cut_cor)+\
               ('\nlen(geos):   %i' %len(self.geos))+\
               ('\nlength:      %0.2f' %self.length)+\
               ('\ngeos:        %s' %self.geos)+\
               ('\ngeos_hdls:   %s' %self.geos_hdls)
               #+\
               #('\nparent: %s' %self.parent)

    def makeSelectionStr(self):
        SelectionStr=[]
        SelectionStr.append(MySelectionStrClass(Name=('Shape %s'%self.nr),\
                                    Type=self.type,\
                                    Closed=self.closed))
        for geo in self.geos:
            SelectionStr.append(geo.makeSelectionStr())
        return SelectionStr

    def reverse(self):
        self.geos.reverse()
        for geo in self.geos: 
            geo.reverse()

    def switch_cut_cor(self):
        if self.cut_cor==41:
            self.cut_cor=42
        elif self.cut_cor==42:
            self.cut_cor=41

    def get_st_en_points(self,dir=None):
        start, start_ang=self.geos[0].get_start_end_points(0,self.parent)
        ende, end_ang=self.geos[-1].get_start_end_points(1,self.parent)
        
        if dir==None:
            return start,ende
        elif dir==0:
            return start,start_ang
        elif dir==1:
            return ende, end_ang
        

    def plot2can(self,Canvas=None,tag=None,col='Black'):
        
        for i in range(len(self.geos)):
            cur_pts=self.geos[i].plot2can(self.parent)

            if i==0:
                points=cur_pts
            else:
                points+=cur_pts[1:len(cur_pts)]
                       
        self.geo_hdl=Canvas.AddLine(points, LineWidth = 2, LineColor = col)
#    def plot2can(self,Canvas=None,tag=None,col='Black'):
#        
#        for i in range(len(self.geos)):
#            cur_pts=self.geos[i].plot2can(self.parent)
#            col=self.geos[i].col #################### Entfernen
#           
#            self.geo_hdl=Canvas.AddLine(cur_pts, LineWidth = 2, LineColor = col)
#        
#        print self.geo_hdl  ###Das Format von GeoHdl hat sich verändert 
        ###und somit sind die Linien nicht mehr anklickbar nur wenn ich die erste Linie einer 
        ###Kontur anklicke funzt das noch. Sollte alle Linien beinhalten Das ganze oben hab ich gemacht um 
        ###keinen Doppelten punkte bei zusammengesetzten Shapes zu erhalten. Somit ergibt sich daraus eine 
        ###gesamte Polyline für eine zusammengesetze Kontur. 
        ###Grund dafür sind auch Performance Gründe beim Ausdrucken.
    def plot_cut_info(self,Canvas,config,length):
        hdls=[]
        hdls.append(self.plot_start(Canvas,length))
        hdls.append(self.plot_end(Canvas,length))
        if self.cut_cor>40:
            self.make_start_moves(config)
            hdls+=self.plot_cut_cor(Canvas,length)         

        return hdls
            
    def plot_start(self,Canvas=None,length=20):
        #st_point, st_angle=self.geos[0].get_start_end_points(0,parent)
                
        start,start_ang=self.get_st_en_points(0)

        

        dx=cos(radians(start_ang))*length
        dy=sin(radians(start_ang))*length

        hdl=Canvas.AddArrowLine([[start.x,start.y],[start.x+dx,start.y+dy]],
                                LineWidth=2, 
                                LineColor= "BLUE",
                                ArrowHeadSize = 18,
                                ArrowHeadAngle = 18)
        return hdl
    
    
    #Funktion zum drucken der zu fräsenden Kontur mit den Richtungspfeilen usw.
    def plot_cut_cor(self,Canvas=None,length=20):
        start,start_ang=self.get_st_en_points(0)

        #BaseEntitie erstellen um auf oberster Ebene zu Fräsen
        BaseEntitie=EntitieContentClass(Nr=-1,Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=PointClass(x=0.0,y=0.0),
                                        pb=PointClass(x=0.0,y=0.0),
                                        sca=[1,1,1],
                                        rot=0.0)

        if self.cut_cor==41:
            start_ang=start_ang+90
        else:
            start_ang=start_ang-90
            
        dx=cos(radians(start_ang))*length
        dy=sin(radians(start_ang))*length

        hdl=[Canvas.AddArrowLine([[start.x,start.y],[start.x+dx,start.y+dy]],
                                LineWidth=2,
                                LineColor= "BLUE",
                                ArrowHeadSize = 18,
                                ArrowHeadAngle = 18)]
          
        points=[]
        for geo_nr in range(len(self.st_move)):
            cur_pts=self.st_move[geo_nr].plot2can(BaseEntitie)    
            if cur_pts==None:
                pass
            else:
                points+=cur_pts[1:len(cur_pts)]
                
        if len(self.st_move)>0:
            hdl.append(Canvas.AddLine(points, LineWidth = 2))
            
        return hdl
            
    def plot_end(self,Canvas=None,length=20):
        ende,en_angle=self.get_st_en_points(1)
      
        dx=cos(radians(en_angle))*length
        dy=sin(radians(en_angle))*length

        hdl=Canvas.AddArrowLine([[ende.x+dx,ende.y+dy],[ende.x,ende.y]],
                                LineWidth=2,
                                LineColor= "GREEN",
                                ArrowHeadSize = 18,
                                ArrowHeadAngle = 18)
        return hdl

    #Funktion zum erstellen der Einlaufradien usw. Hier könnte man später auch die Fräs
    #radienkorrektur unterbringen?!
    def make_start_moves(self,config):
        self.st_move=[]

        #Einlaufradius und Versatz 
        start_rad=config.start_rad
        start_ver=start_rad

        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=config.tool_dia/2
    
        #Errechnen des Startpunkts mit und ohne Werkzeug Kompensation        
        start,start_ang=self.get_st_en_points(0)
      
        if self.cut_cor==40:              
            self.st_move.append(start)

        #Fräsradiuskorrektur Links        
        elif self.cut_cor==41:
            #Mittelpunkts für Einlaufradius
            Oein=start.get_arc_point(start_ang+90,start_rad+tool_rad)
            #Startpunkts für Einlaufradius
            Pa_ein=Oein.get_arc_point(start_ang+180,start_rad+tool_rad)
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(start_ang+90,start_ver)
            
            #Eintauchpunkt errechnete Korrektur
            start_ein=Pg_ein.get_arc_point(start_ang,tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line=LineGeo(Pg_ein,Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad=ArcGeo(Pa=Pa_ein,Pe=start,O=Oein,r=start_rad+tool_rad,dir=1)
            self.st_move.append(start_rad)
            
        #Fräsradiuskorrektur Rechts        
        elif self.cut_cor==42:

            #Mittelpunkt für Einlaufradius
            Oein=start.get_arc_point(start_ang-90,start_rad+tool_rad)
            #Startpunkt für Einlaufradius
            Pa_ein=Oein.get_arc_point(start_ang+180,start_rad+tool_rad)
            #IJ=Oein-Pa_ein
            #Startwerts für Einlaufgerade
            Pg_ein=Pa_ein.get_arc_point(start_ang-90,start_ver)
            
            #Eintauchpunkts errechnete Korrektur
            start_ein=Pg_ein.get_arc_point(start_ang,tool_rad)
            self.st_move.append(start_ein)

            #Einlaufgerade mit Korrektur
            start_line=LineGeo(Pg_ein,Pa_ein)
            self.st_move.append(start_line)

            #Einlaufradius mit Korrektur
            start_rad=ArcGeo(Pa=Pa_ein,Pe=start,O=Oein,r=start_rad+tool_rad,dir=0)
            self.st_move.append(start_rad)
    
    def Write_GCode(self,config,postpro):

        #Erneutes erstellen der Einlaufgeometrien
        self.make_start_moves(config)
        
        #Werkzeugdurchmesser in Radius umrechnen        
        tool_rad=config.tool_dia/2

        #BaseEntitie erstellen um auf oberster Ebene zu Fräsen
        BaseEntitie=EntitieContentClass(Nr=-1,Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=PointClass(x=0.0,y=0.0),
                                        pb=PointClass(x=0.0,y=0.0),
                                        sca=[1,1,1],
                                        rot=0.0)
        

        depth=config.axis3_mill_depth
        max_slice=config.axis3_slice_depth

        #Scheibchendicke bei Frästiefe auf Frästiefe begrenzen
        if -abs(max_slice)<=depth:
            mom_depth=depth
        else:
            mom_depth=-abs(max_slice)


        #Positionieren des Werkzeugs über dem Anfang und Eintauchen
        self.st_move[0].Write_GCode(parent=BaseEntitie,postpro=postpro)
        
        postpro.rap_pos_z(config.axis3_safe_margin)
        postpro.chg_feed_rate(config.F_G1_Depth)
        postpro.lin_pol_z(mom_depth)
        postpro.chg_feed_rate(config.F_G1_Plane)

        #Wenn G41 oder G42 an ist Fräsradiuskorrektur        
        if self.cut_cor!=40:
            
            #Errechnen des Startpunkts ohne Werkzeug Kompensation
            #und einschalten der Kompensation     
            start,start_ang=self.get_st_en_points(0)
            postpro.set_cut_cor(self.cut_cor,start)
            
            self.st_move[1].Write_GCode(parent=BaseEntitie,postpro=postpro)
            self.st_move[2].Write_GCode(parent=BaseEntitie,postpro=postpro)

        #Schreiben der Geometrien für den ersten Schnitt
        for geo in self.geos:
            geo.Write_GCode(self.parent,postpro)

        #Ausschalten der Fräsradiuskorrektur
        if (not(self.cut_cor==40))&(postpro.cancel_cc_for_depth==1):
            ende,en_angle=self.get_st_en_points(1)
            if self.cut_cor==41:
                pos_cut_out=ende.get_arc_point(en_angle-90,tool_rad)
            elif self.cut_cor==42:
                pos_cut_out=ende.get_arc_point(en_angle+90,tool_rad)         
            postpro.deactivate_cut_cor(pos_cut_out)            

        #Zählen der Schleifen
        snr=0
        #Schleifen für die Anzahl der Schnitte
        while mom_depth>depth:
            snr+=1
            mom_depth=mom_depth-abs(max_slice)
            if mom_depth<depth:
                mom_depth=depth                

            #Erneutes Eintauchen
            postpro.chg_feed_rate(config.F_G1_Depth)
            postpro.lin_pol_z(mom_depth)
            postpro.chg_feed_rate(config.F_G1_Plane)

            #Falls es keine geschlossene Kontur ist    
            if self.closed==0:
                self.reverse()
                self.switch_cut_cor()
                
            #Falls cut correction eingeschaltet ist diese einschalten.
            if ((not(self.cut_cor==40))&(self.closed==0))or(postpro.cancel_cc_for_depth==1):
                #Errechnen des Startpunkts ohne Werkzeug Kompensation
                #und einschalten der Kompensation     
                postpro.set_cut_cor(self.cut_cor,start)
                
            for geo_nr in range(len(self.geos)):
                self.geos[geo_nr].Write_GCode(self.parent,postpro)

            #Errechnen des Konturwerte mit Fräsradiuskorrektur und ohne
            ende,en_angle=self.get_st_en_points(1)
            if self.cut_cor==41:
                pos_cut_out=ende.get_arc_point(en_angle-90,tool_rad)
            elif self.cut_cor==42:
                pos_cut_out=ende.get_arc_point(en_angle+90,tool_rad)

            #Ausschalten der Fräsradiuskorrektur falls benötigt          
            if (not(self.cut_cor==40))&(postpro.cancel_cc_for_depth==1):         
                postpro.deactivate_cut_cor(pos_cut_out)
     
        #Anfangswert für Direction wieder herstellen falls nötig
        if (snr%2)>0:
            self.reverse()
            self.switch_cut_cor()

        #Fertig und Zurückziehen des Werkzeugs
        postpro.lin_pol_z(config.axis3_safe_margin)
        postpro.rap_pos_z(config.axis3_retract)

        #Falls Fräsradius Korrektur noch nicht ausgeschaltet ist ausschalten.
        if (not(self.cut_cor==40))&(not(postpro.cancel_cc_for_depth)):
            postpro.deactivate_cut_cor(ende)        

        return 1    
    
class EntitieContentClass:
    def __init__(self,type="Entitie",Nr=None,Name='',parent=None,children=[],
                p0=PointClass(x=0.0,y=0.0),pb=PointClass(x=0.0,y=0.0),sca=[1,1,1],rot=0.0):
                    
        self.type=type
        self.Nr=Nr
        self.Name=Name
        self.children=children
        self.p0=p0
        self.pb=pb
        self.sca=sca
        self.rot=rot
        self.parent=parent

    def __cmp__(self, other):
         return cmp(self.EntNr, other.EntNr)        
        
    def __str__(self):
        return ('\ntype:        %s' %self.type) +\
               ('\nNr :      %i' %self.Nr) +\
               ('\nName:     %s' %self.Name)+\
               ('\np0:          %s' %self.p0)+\
               ('\npb:          %s' %self.pb)+\
               ('\nsca:         %s' %self.sca)+\
               ('\nrot:         %s' %self.rot)+\
               ('\nchildren:    %s' %self.children)
            
    #Hinzufuegen der Kontur zu den Entities
    def addchild(self,child):
        self.children.append(child)
        
    def MakeTreeText(self,parent):
        #font1 = wx.Font(8,wx.SWISS, wx.NORMAL, wx.NORMAL)
        textctrl = ExpandoTextCtrl(parent, -1, "", 
                            size=wx.Size(160,55))
                            
        
        #textctrl.SetFont(font1)
                                
        #dastyle = wx.TextAttr()
        #dastyle.SetTabs([100, 120])
        #textctrl.SetDefaultStyle(dastyle)
        textctrl.AppendText('Point:  X:%0.2f Y%0.2f\n' %(self.p0.x, self.p0.y))
        textctrl.AppendText('Offset: X:%0.2f Y%0.2f\n' %(self.pb.x, self.pb.y))
        textctrl.AppendText('rot: %0.1fdeg sca: %s' %(degrees(self.rot), self.sca))
        return textctrl
