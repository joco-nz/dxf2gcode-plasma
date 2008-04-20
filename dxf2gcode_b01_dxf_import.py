#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b01_dxf_import
#Programmer: Christian Kohlöffel
#E-mail:     n/A
#
#Copyright 2008 Christian Kohlöffel
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

# About Dialog
# First Version of dxf2gcode_b01 Hopefully all works as it should

import sys, os
from Tkconstants import END
from tkMessageBox import showwarning
from Canvas import Oval, Arc, Line
from copy import deepcopy, copy
from string import find, strip
from math import sqrt, sin, cos, atan2, radians, degrees

class Load_DXF:
    #Initialisierung der Klasse
    def __init__(self, filename='C:/Users/Christian Kohlöffel/Documents/Python/vdr_Fraeskontur_Fraesermitte.dxf',tol=0.01,debug=0,text=None):

        #Setzen des Debug Levels
        if debug<=1:
            self.debug=0
        else:
            self.debug=debug-1

        self.text=text            
        
        #Laden der Kontur und speichern der Werte in die Klassen  
        str=self.Read_File(filename)

        if self.debug:
            self.text.insert(END,("\n\nFile has   %0.0f Lines" %len(str)))
            self.text.yview(END)        
            
        self.line_pairs=self.Get_Line_Pairs(str)
        
        if self.debug:
            self.text.insert(END,("\nFile has   %0.0f Linepairs" %self.line_pairs.nrs))
            self.text.yview(END)        

        sections_pos=self.Get_Sections_pos()
        self.layers=self.Read_Layers(sections_pos)

        blocks_pos=self.Get_Blocks_pos(sections_pos)
        self.blocks=self.Read_Blocks(blocks_pos)
        self.entities=self.Read_Entities(sections_pos)

        #Aufruf der Klasse um die Konturen zur suchen
        #Schleife für die Anzahl der Blöcke und den Layern
        for i in range(len(self.blocks.Entities)):
            # '\n'
            #print self.blocks.Entities[i]
            self.blocks.Entities[i].cont=self.Get_Contour(self.blocks.Entities[i],tol)
        self.entities.cont=self.Get_Contour(self.entities,tol)
   
    #Laden des ausgewählten DXF-Files
    def Read_File(self,filename ):
        file = open(filename,'r')
        str = file.readlines()
        file.close()
        return str
    
    #Die Geladenene Daten in Linien Pare mit Code & Value umwandeln.
    def Get_Line_Pairs(self,str):
        line=0
        line_pairs=dxflinepairsClass([])
        #Start bei der ersten SECTION
        while (find(str[line],"SECTION")<0):
            line+=1
        line-=1

        #Durchlauf bis zum Ende falls kein Fehler auftritt. Ansonsten abbruch am Fehler
        try:
            while line < len(str):
                line_pairs.line_pair.append(dxflinepairClass(int(strip(str[line])),strip(str[line+1])))
                line+=2

        except:
            
            showwarning("Read Linepairs",("Found Failure in Line %0.0f \nstopping to read lines" %(line)))
            self.text.insert(END,("\nFound Failure in Line %0.0f" %(line)))
            
            
        line_pairs.nrs=len(line_pairs.line_pair)
        return line_pairs
        
    #Suchen der Sectionen innerhalb des DXF-Files nötig um Blöcke zu erkennen.
    def Get_Sections_pos(self):
        sections=[]
        
        start=self.line_pairs.index_both(0,"SECTION",0)

        #Wenn eine Gefunden wurde diese anhängen        
        while (start != None):
            #Wenn eine Gefunden wurde diese anhängen
            sections.append(SectionClass(len(sections)))
            sections[-1].begin=start
            name_pos=self.line_pairs.index_code(2,start+1)
            sections[-1].name=self.line_pairs.line_pair[name_pos].value
            end=self.line_pairs.index_both(0,"ENDSEC",start+1)
            #Falls Section nicht richtig beendet wurde
            if end==None:
                end=self.line_pairs.nrs-1
                
            sections[-1].end=end
            
            start=self.line_pairs.index_both(0,"SECTION",end)
            
        if self.debug:
            self.text.insert(END,("\n\nSections found:" ))
            for sect in sections:
                self.text.insert(END,str(sect))
            self.text.yview(END)      
                
        return sections

    #Suchen der TABLES Section innerhalb der Sectionen diese beinhaltet die LAYERS
    def Read_Layers(self,section):
        layer_nr=-1
        for sect_nr in range(len(section)):
            if(find(section[sect_nr].name,"TABLES") == 0):
                tables_section=section[sect_nr]
                break

        #Falls das DXF Bloecke hat diese einlesen
        layers=[]
        if vars().has_key('tables_section'):
            tables_section=section[sect_nr]
            start=tables_section.begin
            
            while (start != None):
                start=self.line_pairs.index_both(0,"LAYER",start+1,tables_section.end)
                if(start != None):
                    start=self.line_pairs.index_code(2,start+1)
                    layers.append(LayerClass(len(layers)))
                    layers[-1].name=self.line_pairs.line_pair[start].value
                    
        if self.debug:
            self.text.insert(END,("\n\nLayers found:" ))
            for lay in layers:
                self.text.insert(END,str(lay))
            self.text.yview(END)
            
        return layers
                    
            
    #Suchen der BLOCKS Section innerhalb der Sectionen
    def Get_Blocks_pos(self,section):
        for sect_nr in range(len(section)):
            if(find(section[sect_nr].name,"BLOCKS") == 0):
                blocks_section=section[sect_nr]
                break

        #Falls das DXF Bloecke hat diese einlesen
        blocks=[]
        if vars().has_key('blocks_section'):
            start=blocks_section.begin
            start=self.line_pairs.index_both(0,"BLOCK",blocks_section.begin,blocks_section.end)
            while (start != None):
                blocks.append(SectionClass())
                blocks[-1].Nr=len(blocks)
                blocks[-1].begin=start
                name_pos=self.line_pairs.index_code(2,start+1,blocks_section.end)
                blocks[-1].name=self.line_pairs.line_pair[name_pos].value
                end=self.line_pairs.index_both(0,"ENDBLK",start+1,blocks_section.end)
                blocks[-1].end=end
                start=self.line_pairs.index_both(0,"BLOCK",end+1,blocks_section.end)

        if self.debug:
            self.text.insert(END,("\n\nBlocks found:" ))
            for bl in blocks:
                self.text.insert(END,str(bl))
            self.text.yview(END)
            
        return blocks

    #Lesen der Blocks Geometrien
    def Read_Blocks(self,blocks_pos):
        blocks=BlocksClass([])
        for block_nr in range(len(blocks_pos)):
            if self.debug:
                self.text.insert(END,("\n\nReading Block Nr: %0.0f" % block_nr ))
                self.text.yview(END)
            blocks.Entities.append(EntitiesClass(block_nr,blocks_pos[block_nr].name,[]))
            blocks.Entities[-1].geo=self.Get_Geo(blocks_pos[block_nr].begin+1, blocks_pos[block_nr].end-1)
        return blocks
    #Lesen der Entities Geometrien
    def Read_Entities(self,sections):
        for section_nr in range(len(sections)):
            if (find(sections[section_nr-1].name,"ENTITIES") == 0):
                if self.debug:
                    self.text.insert(END,"\n\nReading Entities")
                    self.text.yview(END)
                entities=EntitiesClass(0,'Entities',[])
                entities.geo=self.Get_Geo(sections[section_nr-1].begin+1, sections[section_nr-1].end-1)
        return entities

    #Lesen der Geometrien von Blöcken und Entities         
    def Get_Geo(self,begin, end):
        geo= []
        warn=0
        self.start=self.line_pairs.index_code(0,begin,end)
        old_start=self.start
        
        while self.start!=None:
            name=self.line_pairs.line_pair[self.start].value

##            try:            
            if(name=="POLYLINE"):
                geo.append(self.Read_Polyline(len(geo)))
            elif (name=="SPLINE"):
                warn=1
                geo.append(self.Read_Spline(len(geo)))
                #Umwandeln zu einer Polyline
                geo[-1].calculate_nurbs_points()
                self.text.insert(END,("\n!!!! WARNING: SPLINE imported as POLYLINE with 200 Points !!!!" ))        
            elif (name=="ARC"):
                geo.append(self.Read_Arc(len(geo)))                
            elif (name=="CIRCLE"):
                geo.append(self.Read_Circle(len(geo)))
            elif (name=="LINE"):
                geo.append(self.Read_Line(len(geo)))
            elif (name=="INSERT"):
                geo.append(self.Read_Insert(len(geo)))
            else:  
                warn=1
                self.text.insert(END,("\n!!!!WARNING Found unsupported Geometry: %s !!!!" %name))
                self.text.yview(END)
                self.start+=1 #Eins hochzählen sonst gibts ne dauer Schleife
            #self.text.insert(END,("\n%s" %name))
            #Die nächste Suche Starten nach dem gerade gefundenen
            self.start=self.line_pairs.index_code(0,self.start,end)

                
##            except:
##                showwarning("Save As",("Found %s at Linepair %0.0f with Failure!!!! (Line %0.0f till %0.0f)" \
##                            %(name, old_start,old_start*2+4,end*2+4)))
##                
##                self.text.insert(END,("\nFound %s at Linepair %0.0f with Failure!!!! (Line %0.0f till %0.0f)" \
##                                            %(name, old_start,old_start*2+4,end*2+4)))
                
                        
            if self.debug:
                if self.start==None:
                    self.text.insert(END,("\nFound %s at Linepair %0.0f (Line %0.0f till %0.0f)" \
                                            %(name, old_start,old_start*2+4,end*2+4)))
                else:
                    self.text.insert(END,("\nFound %s at Linepair %0.0f (Line %0.0f till %0.0f)" \
                                            %(name, old_start,old_start*2+4,self.start*2+4)))
            
                self.text.yview(END)

            if (self.debug>1)and(len(geo)>0):
                self.text.insert(END,str(geo[-1]))
                self.text.yview(END)

            old_start=self.start

        if warn:
            showwarning("Import Warning","Found unsupported or only\npartly supported geometry.\nFor details see status messages!")
            
        del(self.start)
        return geo

    def Read_Spline(self, geo_nr):
        Spline=SplineClass(geo_nr,0,[],0)
        Old_Point=PointClass(0,0)

        #Kürzere Namen zuweisen        
        lp=self.line_pairs
        e=lp.index_code(0,self.start+1)

        #Layer zuweisen        
        s=lp.index_code(8,self.start+1)
        Spline.Layer_Nr=self.Get_Layer_Nr(lp.line_pair[s].value)

        #Spline Flap zuweisen
        s=lp.index_code(70,s+1)
        Spline.Spline_flag=int(lp.line_pair[s].value) 

        #Spline Ordnung zuweisen
        s=lp.index_code(71,s+1)
        Spline.Spline_order=int(lp.line_pair[s].value)

        #Number of CPts
        s=lp.index_code(73,s+1)
        nCPts=int(lp.line_pair[s].value)          


        #Lesen der Knoten
        while 1:
            #Knoten Wert
            sk=lp.index_code(40,s+1,e)
            if sk==None:
                break
            Spline.Knots.append(float(lp.line_pair[sk].value))
            s=sk

        #Lesen der Gewichtungen
        while 1:
            #Knoten Gewichtungen
            sg=lp.index_code(41,s+1,e)
            if sg==None:
                break
            Spline.Weights.append(float(lp.line_pair[sg].value))
            s=sg
            
        if len(Spline.Weights)==0:
            for nr in range(nCPts):
                Spline.Weights.append(1)
                
        #Lesen der Kontrollpunkte
        while 1:  
            #XWert
            s=lp.index_code(10,s+1,e)
            #Wenn kein neuer Punkt mehr gefunden wurde abbrechen ...
            if s==None:
                break
            
            x=float(lp.line_pair[s].value)
            #YWert
            s=lp.index_code(20,s+1,e)
            y=float(lp.line_pair[s].value)

            Spline.CPoints.append(PointClass(x,y))             

            if (Old_Point==Spline.CPoints[-1]):
               # add to boundary if not zero-length segment
               Old_Point=Spline.CPoints[-1]
               if len(Spline.CPoints)>1:
                   Spline.length+=Spline.CPoints[-2].distance(Spline.CPoints[-1])            

        self.start=e
        return Spline
    
    def Read_Polyline(self, geo_nr):
        Polyline=PolylineClass(geo_nr,0,[],0)
        Old_Point=PointClass(0,0)

        #Kürzere Namen zuweisen        
        lp=self.line_pairs
        e=lp.index_both(0,"SEQEND",self.start+1)+1

        #Layer zuweisen        
        s=lp.index_code(8,self.start+1)
        Polyline.Layer_Nr=self.Get_Layer_Nr(lp.line_pair[s].value)        
        
        while 1:
            s=lp.index_both(0,"VERTEX",s+1,e)
            if s==None:
                break
            
            #XWert
            s=lp.index_code(10,s+1,e)
            x=float(lp.line_pair[s].value)
            #YWert
            s=lp.index_code(20,s+1,e)
            y=float(lp.line_pair[s].value)

            Polyline.Points.append(PointClass(x,y))             

            if (Old_Point==Polyline.Points[-1]):
               # add to boundary if not zero-length segment
               Old_Point=Polyline.Points[-1]
               if len(Polyline.Points)>1:
                   Polyline.length+=Polyline.Points[-2].distance(Polyline.Points[-1])            

        self.start=e
        return Polyline

    def Read_Line(self, geo_nr):
        Line=LineClass(geo_nr,0,[],0)

        #Kürzere Namen zuweisen
        lp=self.line_pairs

        #Layer zuweisen        
        s=lp.index_code(8,self.start+1)
        Line.Layer_Nr=self.Get_Layer_Nr(lp.line_pair[s].value)
        #XWert
        s=lp.index_code(10,s+1)
        x0=float(lp.line_pair[s].value)
        #YWert
        s=lp.index_code(20,s+1)
        y0=float(lp.line_pair[s].value)
        #XWert2
        s=lp.index_code(11,s+1)
        x1 = float(lp.line_pair[s].value)
        #YWert2
        s=lp.index_code(21,s+1)
        y1 = float(lp.line_pair[s].value)

        Line.Points.append(PointClass(x0,y0))
        Line.Points.append(PointClass(x1,y1))                
        #Berechnen der Vektorlänge
        Line.length=Line.Points[0].distance(Line.Points[1])
        
        self.start=s
        return Line        
        
    def Read_Circle(self, geo_nr):
        Circle=CircleClass(geo_nr,0,[],0,0)

        #Kürzere Namen zuweisen
        lp=self.line_pairs

        #Layer zuweisen        
        s=lp.index_code(8,self.start+1)
        Circle.Layer_Nr=self.Get_Layer_Nr(lp.line_pair[s].value)
        #XWert
        s=lp.index_code(10,s+1)
        x0=float(lp.line_pair[s].value)
        #YWert
        s=lp.index_code(20,s+1)
        y0=float(lp.line_pair[s].value)
        Circle.Points.append(PointClass(x0,y0))
        #Radius
        s=lp.index_code(40,s+1)
        Circle.Radius = float(lp.line_pair[s].value)
                        
        #Berechnen des Kreisumfangs                
        Circle.length=Circle.Radius*radians(360)
        
        #Berechnen der Start und Endwerte des Kreises ohne Überschneidung              
        xs=cos(radians(0))*Circle.Radius+x0
        ys=sin(radians(0))*Circle.Radius+y0
        Circle.Points.append(PointClass(xs,ys))
        
        xe=cos(radians(0))*Circle.Radius+x0
        ye=sin(radians(0))*Circle.Radius+y0
        Circle.Points.append(PointClass(xe,ye))

        self.start=s        
        return Circle
    
    def Read_Arc(self, geo_nr):
        Arc=ArcClass(geo_nr,0,[],0,0,0,0)

        #Kürzere Namen zuweisen
        lp=self.line_pairs

        #Layer zuweisen        
        s=lp.index_code(8,self.start+1)
        Arc.Layer_Nr=self.Get_Layer_Nr(lp.line_pair[s].value)
        #XWert
        s=lp.index_code(10,s+1)
        x0=float(lp.line_pair[s].value)
        #YWert
        s=lp.index_code(20,s+1)
        y0=float(lp.line_pair[s].value)
        Arc.Points.append(PointClass(x0,y0))
        #Radius
        s=lp.index_code(40,s+1)
        Arc.Radius = float(lp.line_pair[s].value)
        #Start Winkel
        s=lp.index_code(50,s+1)
        Arc.Start_Ang= float(lp.line_pair[s].value)
        #End Winkel
        s=lp.index_code(51,s+1)
        Arc.End_Ang= float(lp.line_pair[s].value)        

        #Berechnen der Start und Endwerte des Arcs
        xs=cos(radians(Arc.Start_Ang))*Arc.Radius+x0
        ys=sin(radians(Arc.Start_Ang))*Arc.Radius+y0
        Arc.Points.append(PointClass(xs,ys))
        xe=cos(radians(Arc.End_Ang))*Arc.Radius+x0
        ye=sin(radians(Arc.End_Ang))*Arc.Radius+y0
        Arc.Points.append(PointClass(xe,ye))

        #Korrektur des Endwinkels bei Werten <= 0
        if Arc.End_Ang<=0:
            EA_cor=Arc.End_Ang+360
        else:
            EA_cor=Arc.End_Ang
            
        Arc.length=Arc.Radius*abs(radians(EA_cor-Arc.Start_Ang))

        self.start=s
        return Arc
    
    def Read_Insert(self, geo_nr):
        Insert=InsertClass(geo_nr,0,'',[],[1,1,1])
        
        #Kürzere Namen zuweisen
        lp=self.line_pairs
        e=lp.index_code(0,self.start+1)

        #Block Name        
        ind=lp.index_code(2,self.start+1,e)
        Insert.Block=self.Get_Block_Nr(lp.line_pair[ind].value)
        #Layer zuweisen        
        s=lp.index_code(8,self.start+1,e)
        Insert.Layer_Nr=self.Get_Layer_Nr(lp.line_pair[s].value)
        #XWert
        s=lp.index_code(10,s+1,e)
        x0=float(lp.line_pair[s].value)
        #YWert
        s=lp.index_code(20,s+1,e)
        y0=float(lp.line_pair[s].value)
        Insert.Point=PointClass(x0,y0)
        
        
        s=lp.index_code(41,s+1,e)
        if s!=None:
            #XScale
            Insert.Scale[0]=float(lp.line_pair[s].value)
            #YScale
            s=lp.index_code(42,s+1,e)
            Insert.Scale[1]=float(lp.line_pair[s].value)
            #ZScale
            s=lp.index_code(43,s+1,e)
            Insert.Scale[2]=float(lp.line_pair[s].value)

        self.start=e      
        return Insert

    #Findet die Nr. des Geometrie Layers
    def Get_Layer_Nr(self,Layer_Name):
        layer_nr=-1
        for i in range(len(self.layers)):
            if (find(self.layers[i].name,Layer_Name)==0):
                layer_nr=i
                break  
        return layer_nr
    
    #Findet die Nr. des Blocks
    def Get_Block_Nr(self,Block_Name):
        block_nr=-1
        for i in range(len(self.blocks.Entities)):
            if (find(self.blocks.Entities[i].Name,Block_Name)==0):
                block_nr=i
                break  
        return block_nr

    #Findet die beste Kontur der zusammengesetzen Geometrien
    def Get_Contour(self,entities=None,tol=0.01):
        cont=[]

        points=self.Calc_Int_Points(entities.geo,cont,tol)
        points=self.Find_Common_Points(points,tol)
        cont=self.Search_Contours(entities.geo,points,cont)
        
        return cont    
    
    #Berechnen bzw. Zuweisen der Anfangs und Endpunkte
    def Calc_Int_Points(self,geo=None,cont=None,tol=0.01):
        points=[]
        points_nr=-1
        #Durchlaufen und errechnen der Werte für alle Elemente die eine zusammengesetzte
        #Kontur ergeben können (Circle ist bereits eine geschlossene Kontur)
       
        for i in range(len(geo)) :
            if geo[i].Typ=='Arc':
                points_nr+=1
                points.append(PointsClass(points_nr,i,geo[i].Layer_Nr,[],[],[],[]))
                points[-1].be=geo[i].Points[-2]
                points[-1].en=geo[i].Points[-1]

            elif geo[i].Typ=='Circle':
                cont.append(ContourClass(len(cont),1,[[i,0]],geo[i].length))

            elif geo[i].Typ=='Line':
                points_nr+=1
                points.append(PointsClass(points_nr,i,geo[i].Layer_Nr,[],[],[],[]))
                points[-1].be=geo[i].Points[0]
                points[-1].en=geo[i].Points[-1]
                
            elif geo[i].Typ=='Polyline':
                #Hinzufügen falls es keine geschlossene Polyline ist
                if geo[i].Points[0].isintol(geo[i].Points[-1],tol):
                    geo[i].analyse_and_opt()
                    cont.append(ContourClass(len(cont),1,[[i,0]],geo[i].length))
                else:
                    points_nr+=1
                    points.append(PointsClass(points_nr,i,geo[i].Layer_Nr,[],[],[],[]))
                    points[-1].be=geo[i].Points[0]
                    points[-1].en=geo[i].Points[-1]

            elif geo[i].Typ=='Spline':
                #Hinzufügen falls es keine geschlossener Spline ist
                if geo[i].Points[0].isintol(geo[i].Points[-1],tol):
                    geo[i].analyse_and_opt()
                    cont.append(ContourClass(len(cont),1,[[i,0]],geo[i].length)) 
                else:
                    points_nr+=1
                    points.append(PointsClass(points_nr,i,geo[i].Layer_Nr,[],[],[],[]))
                    points[-1].be=geo[i].Points[0]
                    points[-1].en=geo[i].Points[-1]
                    
            elif geo[i].Typ=='Insert':
                layer_nr=1
                cont.append(ContourClass(len(cont),0,[[i,0]],0))
            else:
                print 'unknown geometrie: ' + geo[i].Typ
        return points
       
    #Suchen von gemeinsamen Punkten
    def Find_Common_Points(self,points=None,tol=0.01):

        p_list=[]
        
        #Einen List aus allen Punkten generieren
        for p in points:
           p_list.append([p.Layer_Nr,p.be.x,p.be.y,p.point_nr,0])
           p_list.append([p.Layer_Nr,p.en.x,p.en.y,p.point_nr,1])

        #Den List sortieren        
        p_list.sort()
        #print p_list

        #Eine Schleife für die Anzahl der List Elemente durchlaufen
        #Start = wo die Suche der gleichen Elemente beginnen soll
        anf=[]
        
        for l_nr in range(len(p_list)):
            inter=[]
            #print ("Suche Starten für Geometrie Nr: %i, Punkt %i" %(p_list[l_nr][3],l_nr))
            
            if type(anf) is list:
                c_nr=0
            else:
                c_nr=anf
                
            anf=[]

            #Schleife bis nächster X Wert Größer ist als selbst +tol  und Layer Größer gleich
            while (p_list[c_nr][0]<p_list[l_nr][0]) | \
                  (p_list[c_nr][1]<=(p_list[l_nr][1]+tol)):
                #print ("Suche Punkt %i" %(c_nr))
                

                #Erstes das Übereinstimmt is der nächste Anfang
                if (type(anf) is list) & \
                   (p_list[c_nr][0]==p_list[l_nr][0]) & \
                   (abs(p_list[c_nr][1]-p_list[l_nr][1])<=tol):
                    anf=c_nr
                    #print ("Nächste Suche starten bei" +str(anf))
                    
                #Falls gleich anhängen                
                if  (p_list[c_nr][0]==p_list[l_nr][0]) &\
                    (abs(p_list[c_nr][1]-p_list[l_nr][1])<=tol) &\
                    (abs(p_list[c_nr][2]-p_list[l_nr][2])<=tol) &\
                    (c_nr!=l_nr):
                    inter.append(c_nr)
                    #print ("Gefunden" +str(inter))
                c_nr+=1

                if c_nr==len(p_list):
                    break

            #Anhängen der gefundenen Punkte an points
            for int_p in inter:
                #Common Anfangspunkt
                if p_list[l_nr][-1]==0:
                    points[p_list[l_nr][-2]].be_cp.append(p_list[int_p][3:5])
                #Common Endpunkt
                else:
                    points[p_list[l_nr][-2]].en_cp.append(p_list[int_p][3:5])

        #for p in points:
            #print p
        
        return points

    #Suchen nach den besten zusammenhängenden Konturen
    def Search_Contours(self,geo=None,all_points=None,cont=None):
        
        points=deepcopy(all_points)
        
        while(len(points))>0:
            #print '\n Neue Suche'
            #Wenn nichts gefunden wird dann einfach die Kontur hochzählen
            if (len(points[0].be_cp)==0)&( len(points[0].en_cp)==0):
                #print '\nGibt Nix'
                cont.append(ContourClass(len(cont),0,[[points[0].point_nr,0]],0))
            elif (len(points[0].be_cp)==0) & (len(points[0].en_cp)>0):
                #print '\nGibt was Rückwärts (Anfang in neg dir)'
                new_cont_pos=self.Search_Paths(0,[],points[0].point_nr,0,points)
                cont.append(self.Get_Best_Contour(len(cont),new_cont_pos,geo,points))
            elif (len(points[0].be_cp)>0) & (len(points[0].en_cp)==0):
                #print '\nGibt was Vorwärt (Ende in pos dir)'
                new_cont_neg=self.Search_Paths(0,[],points[0].point_nr,1,points)
                cont.append(self.Get_Best_Contour(len(cont),new_cont_neg,geo,points))
            elif (len(points[0].be_cp)>0) & (len(points[0].en_cp)>0):
                #print '\nGibt was in beiden Richtungen'
                #Suchen der möglichen Pfade                
                new_cont_pos=self.Search_Paths(0,[],points[0].point_nr,1,points)
                #Bestimmen des besten Pfades und übergabe in cont                
                cont.append(self.Get_Best_Contour(len(cont),new_cont_pos,geo,points))

                #Falls der Pfad nicht durch den ersten Punkt geschlossen ist
                if cont[-1].closed==0:
                    #print '\Pfad nicht durch den ersten Punkt geschlossen'
                    cont[-1].reverse()
                    new_cont_neg=self.Search_Paths(0,[cont[-1]],points[0].point_nr,0,points)
                    cont[-1]=self.Get_Best_Contour(len(cont)-1,new_cont_neg,geo,points)
                    
            else:
                print 'FEHLER !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            points=self.Remove_Used_Points(cont[-1],points)
            cont[-1]=self.Contours_Points2Geo(cont[-1],all_points)
            cont[-1].analyse_and_opt(geo)

        return cont

    #Suchen die Wege duch die Konturn !!! REKURSIVE SCHLEIFE WAR SAU SCHWIERIG
    def Search_Paths(self,c_nr=None,c=None,p_nr=None,dir=None,points=None):

        #Richtung der Suche definieren (1= pos, 0=neg bedeutet mit dem Ende Anfangen)
            
        #Wenn es der erste Aufruf ist und eine neue Kontur angelegt werden muss         
        if len(c)==0:
            c.append(ContourClass(cont_nr=0,order=[[p_nr,dir]]))    
            
        #Suchen des Punktes innerhalb der points List (nötig da verwendete Punkte gelöscht werden)
        for new_p_nr in range(len(points)):
                if points[new_p_nr].point_nr==p_nr:
                    break
        
        #Nächster Punkt abhängig von der Richtung
        if dir==0:
            weiter=points[new_p_nr].en_cp
        elif dir==1:
            weiter=points[new_p_nr].be_cp
            
        #Schleife für die Anzahl der Abzweig Möglichkeiten      
        for i in range(len(weiter)):
            #Wenn es die erste Möglichkeit ist Hinzufügen zur aktuellen Kontur
            if i==0:
                if not(c[c_nr].is_contour_closed()):
                    c[c_nr].order.append(weiter[0])
                    
            #Es gibt einen Abzweig, es wird die aktuelle Kontur kopiert und dem
            #anderen Zweig gefolgt
            elif i>0:
                if not(c[c_nr].is_contour_closed()):
                    #print 'Abzweig ist möglich'
                    c.append(deepcopy(c[c_nr]))
                    del c[-1].order[-1]
                    c[-1].order.append(weiter[i])
                          
        for i in range(len(weiter)):
            #print 'I ist: ' +str(i)
            if i ==0:
                new_c_nr = c_nr
            else:
                new_c_nr=len(c)-len(weiter)+i
                
            new_p_nr = c[new_c_nr].order[-1][0]
            new_dir  = c[new_c_nr].order[-1][1]
            if not(c[new_c_nr].is_contour_closed()):
                c=self.Search_Paths(copy(new_c_nr),c,copy(new_p_nr),copy(new_dir),points)        
        return c 
    #Sucht die beste Kontur unter den gefunden aus (Meiner Meinung nach die Beste)
    def Get_Best_Contour(self,c_nr,c=None,geo=None,points=None):
      
        #Hinzufügen der neuen Kontur  
        best=None
        best_open=None
        #print ("Es wurden %0.0f Konturen gefunden" %len(c))
        for i in range(len(c)):
            #if len(c)>1:
                #print ("Kontur Nr %0.0f" %i)
                #print c[i]
                
            #Korrigieren der Kontur falls sie nicht in sich selbst geschlossen ist
            if c[i].closed==2:
                c[i].remove_other_closed_contour()
                c[i].closed=0
                c[i].calc_length(geo)
            #Suchen der besten Geometrie
            if c[i].closed==1:
                c[i].calc_length(geo)
                if best==None:
                    best=i
                else:
                    if c[best].length<c[i].length:
                        best=i
            elif c[i].closed==0:
                c[i].calc_length(geo)
                if best_open==None:
                    best_open=i
                else:
                    if c[best_open].length<c[i].length:
                        best_open=i

            #Falls keine Geschschlossene dabei ist Beste = Offene
        if best==None:
            best=best_open
                
        best_c=c[best]
        best_c.cont_nr=c_nr

        return best_c
    
    #Alle Punkte im Pfad aus Points löschen um nächte Suche zu beschleunigen               
    def Remove_Used_Points(self,cont=None,points=None):
        for i in range(len(cont.order)):
            for j in range(len(points)):
                if cont.order[i][0]==points[j].point_nr:
                    del points[j]
                    break
                for k in range(len(points[j].be_cp)):
                    if cont.order[i][0]==points[j].be_cp[k][0]:
                        del points[j].be_cp[k]
                        break
                
                for k in range(len(points[j].en_cp)):
                    if cont.order[i][0]==points[j].en_cp[k][0]:
                        del points[j].en_cp[k]
                        break
                    
        #Rückgabe der Kontur       
        return points
    #Alle Punkte im Pfad aus Points löschen um nächte Suche zu beschleunigen               
    def Contours_Points2Geo(self,cont=None,points=None):
        for c_nr in range(len(cont.order)):
                cont.order[c_nr][0]=points[cont.order[c_nr][0]].geo_nr
        return cont
            
class dxflinepairClass:
    def __init__(self,code=None,value=None):
        self.code=code
        self.value=value
    def __str__(self):
        return '\nCode ->'+str(self.code)+'\nvalue ->'+self.value
    
class dxflinepairsClass:
    def __init__(self,line_pair=[]):
        self.nrs=0
        self.line_pair=line_pair
    def __str__(self):
        return '\nNumber of Line Pairs: '+str(self.nrs)

    #Sucht nach beiden Angaben in den Line Pairs code & value
    #optional mit start und endwert für die Suche
    def index_both(self,code=0,value=0,start=0,stop=-1):

        #Wenn bei stop -1 angegeben wird stop am ende der pairs        
        if stop==-1:
            stop=len(self.line_pair)
            
        #Starten der Suche innerhalb mit den angegeben parametern        
        for i in range(start,stop):
            if (self.line_pair[i].code==code) & (self.line_pair[i].value==value):
                return i
                
            
        #Wenn nicht gefunden wird None ausgeben
        return None
    
    #Sucht nach Code Angaben in den Line Pairs code & value
    #optional mit start und endwert für die Suche
    def index_code(self,code=0,start=0,stop=-1):

        #Wenn bei stop -1 angegeben wird stop am ende der pairs        
        if stop==-1:
            stop=len(self.line_pair)
            
        #Starten der Suche innerhalb mit den angegeben parametern        
        for i in range(start,stop):
            if (self.line_pair[i].code==code):
                return i
            
        #Wenn nicht gefunden wird None ausgeben
        return None
            
class LayerClass:
    def __init__(self,Nr=0, name=''):
        self.Nr= Nr
        self.name = name
    def __str__(self):
        # how to print the object
        return '\nNr ->'+str(self.Nr)+'\nName ->'+self.name
    def __len__(self):
        return self.__len__

class InsertClass:
    def __init__(self,Nr=0,Layer_Nr=0,Block='',Point=[], Scale=[1,1,1]):
        self.Typ='Insert'
        self.Nr = Nr
        self.Layer_Nr = Layer_Nr
        self.Block = Block
        self.Point = Point
        self.Scale=Scale
        self.length=0
        
    def __str__(self):
        # how to print the object
        return '\nTyp: Insert\nNr ->'+str(self.Nr)\
            +'\nLayer Nr: ->'+str(self.Layer_Nr)+'\nBlock ->' +str(self.Block) \
            +str(self.Point) \
            +'\nScale ->'+str(self.Scale) 

class CircleClass:
    def __init__(self,Nr=0,Layer_Nr=0,Points=[], Radius=0,length=0):
        self.Typ='Circle'
        self.Nr = Nr
        self.Layer_Nr = Layer_Nr
        self.Points = Points
        self.Radius= Radius
        self.length=length
    def __str__(self):
        # how to print the object
        s='\nType: Circle\nNr ->'+str(self.Nr) +'\nLayer Nr: ->'+str(self.Layer_Nr)
        for point in self.Points:
            s=s+str(point)
        s=s+'\nRadius ->'+str(self.Radius)+'\nLength ->'+str(self.length)
        return s
    def plot2can(self,canvas,p0,sca,tag):
        xy=p0[0]+(self.Points[0].x-self.Radius)*sca[0],-p0[1]-(self.Points[0].y-self.Radius)*sca[1],\
            p0[0]+(self.Points[0].x+self.Radius)*sca[0],-p0[1]-(self.Points[0].y+self.Radius)*sca[1]
        hdl=Oval(canvas,xy,tag=tag)
        return hdl

    def get_start_end_points(self,direction):
        punkt=self.Points[-1]
        if direction==0:
            angle=270
        else:
            angle=90
            
        return punkt,angle
    
    def Write_GCode(self,string,paras,sca,p0,dir,axis1,axis2):
        st_point, st_angle=self.get_start_end_points(dir)
        I=(self.Points[0].x-st_point.x)*sca[0]
        J=(self.Points[0].y-st_point.y)*sca[0]
        en_point, en_angle=self.get_start_end_points(not(dir))
        x_en=(en_point.x*sca[0])+p0[0]
        y_en=(en_point.y*sca[1])+p0[1]
        

        #Vorsicht geht nicht für Ovale
        if dir==0:
            string+=("G2 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,x_en,axis2,y_en,I,J))
        else:
            string+=("G3 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,x_en,axis2,y_en,I,J))

        return string    
        
class ArcClass:
    def __init__(self,Nr=0,Layer_Nr=0,Points=[], Radius=0, Start_Ang=0, End_Ang=0,length=0):
        self.Typ='Arc'
        self.Nr = Nr
        self.Layer_Nr = Layer_Nr
        self.Points=Points
        self.Radius= Radius
        self.Start_Ang=Start_Ang
        self.End_Ang=End_Ang
        self.length=length

    def __str__(self):
        # how to print the object
        s='\nTyp: Arc \nNr ->'+str(self.Nr) \
            +'\nLayer Nr: ->'+str(self.Layer_Nr)
        for point in self.Points:
            s=s+str(point)
        s=s+'\nRadius ->'+str(self.Radius)+'\nStart Angle ->'+str(self.Start_Ang) \
           +'\nEnd Angle ->'+str(self.End_Ang) \
           +'\nLength ->'+str(self.length)
        return s
    def plot2can(self,canvas,p0,sca,tag):
        if self.End_Ang==0:
            ext=360-self.Start_Ang
        else:            
            ext=self.End_Ang-self.Start_Ang

        if ext<0:
            ext+=360

        xy=p0[0]+(self.Points[0].x-self.Radius)*sca[0],-p0[1]-(self.Points[0].y-self.Radius)*sca[1],\
            p0[0]+(self.Points[0].x+self.Radius)*sca[0],-p0[1]-(self.Points[0].y+self.Radius)*sca[1]
        hdl=Arc(canvas,xy,start=self.Start_Ang,extent=ext,style="arc",\
            tag=tag)
        return hdl

    def get_start_end_points(self,direction):
        if direction==0:
            punkt=self.Points[1]
            angle=self.Start_Ang+90
        elif direction==1:
            punkt=self.Points[2]
            angle=self.End_Ang-90
        return punkt,angle
    
    def Write_GCode(self,string,paras,sca,p0,dir,axis1,axis2):
        st_point, st_angle=self.get_start_end_points(dir)
        I=(self.Points[0].x-st_point.x)*sca[0]
        J=(self.Points[0].y-st_point.y)*sca[0]
        en_point, en_angle=self.get_start_end_points(not(dir))
        x_en=(en_point.x*sca[0])+p0[0]
        y_en=(en_point.y*sca[1])+p0[1]
        

        #Vorsicht geht nicht für Ovale
        if dir==0:
            string+=("G3 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,x_en,axis2,y_en,I,J))
        else:
            string+=("G2 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,x_en,axis2,y_en,I,J))

        return string
            
class LineClass:
    def __init__(self,Nr=0,Layer_Nr=0,Points=[],length=0):
        self.Typ='Line'
        self.Nr = Nr
        self.Layer_Nr = Layer_Nr
        self.Points = Points
        self.length= length
    def __str__(self):
        # how to print the object
        s= '\nTyp: Line \nNr ->'+str(self.Nr) +'\nLayer Nr: ->'+str(self.Layer_Nr)
        for point in self.Points:
            s=s+str(point)
        s=s+'\nLength ->'+str(self.length)
        return s
    def plot2can(self,canvas,p0,sca,tag):
        hdl=Line(canvas,p0[0]+self.Points[0].x*sca[0],-p0[1]-self.Points[0].y*sca[1],\
             p0[0]+self.Points[1].x*sca[0],-p0[1]-self.Points[1].y*sca[1],\
             tag=tag)
        return hdl
    
    def get_start_end_points(self,direction):
        if direction==0:
            punkt=self.Points[0]
            dx=self.Points[1].x-self.Points[0].x
            dy=self.Points[1].y-self.Points[0].y
            angle=degrees(atan2(dy, dx))
        elif direction==1:
            punkt=self.Points[-1]
            dx=self.Points[-2].x-self.Points[-1].x
            dy=self.Points[-2].y-self.Points[-1].y
            angle=degrees(atan2(dy, dx))

        return punkt, angle
    
    def Write_GCode(self,string,paras,sca,p0,dir,axis1,axis2):
        en_point, en_angle=self.get_start_end_points(not(dir))
        x_en=(en_point.x*sca[0])+p0[0]
        y_en=(en_point.y*sca[1])+p0[1]
        string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,x_en,axis2,y_en))
        return string
        
class PolylineClass:
    def __init__(self,Nr=0,Layer_Nr=0,Points=[],length=0):
        self.Typ='Polyline'
        self.Nr = Nr
        self.Layer_Nr = Layer_Nr
        self.Points=Points
        self.length= length
    def __str__(self):
        # how to print the object
        s= '\nTyp: Polyline \nNr ->'+str(self.Nr) +'\nLayer Nr: ->'+str(self.Layer_Nr)
        for point in self.Points:
            s=s+str(point)
        s=s+'\nLength ->'+str(self.length)
        return s


    def analyse_and_opt(self):
        summe=0
        #Berechnung der Fläch nach Gauß-Elling Positive Wert bedeutet CW
        #negativer Wert bedeutet CCW geschlossenes Polygon            
        for p_nr in range(1,len(self.Points)):
            summe+=(self.Points[p_nr-1].x*self.Points[p_nr].y-self.Points[p_nr].x*self.Points[p_nr-1].y)/2
        if summe>0.0:
            self.Points.reverse()

        #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
        min_point=self.Points[0]
        min_p_nr=0
        del(self.Points[-1])
        for p_nr in range(1,len(self.Points)):
            #Geringster Abstand nach unten Unten Links
            if (min_point.x+min_point.y)>=(self.Points[p_nr].x+self.Points[p_nr].y):
                min_point=self.Points[p_nr]
                min_p_nr=p_nr
        #Kontur so anordnen das neuer Startpunkt am Anfang liegt
        self.Points=self.Points[min_p_nr:len(self.Points)]+self.Points[0:min_p_nr]+[self.Points[min_p_nr]]
 
    def plot2can(self,canvas,p0,sca,tag):
        hdl=[]
        for i in range(1,len(self.Points)):
            hdl.append(Line(canvas,p0[0]+self.Points[i-1].x*sca[0],-p0[1]-self.Points[i-1].y*sca[1],\
                            p0[0]+self.Points[i].x*sca[0],-p0[1]-self.Points[i].y*sca[1],\
                            tag=tag))
        return hdl
    
    def get_start_end_points(self,direction=0,nr=0):
        if direction==0:
            punkt=self.Points[nr]
            dx=self.Points[1].x-self.Points[0].x
            dy=self.Points[1].y-self.Points[0].y
            angle=degrees(atan2(dy, dx))
        elif direction==1:
            punkt=self.Points[len(self.Points)-nr-1]
            dx=self.Points[-2].x-self.Points[-1].x
            dy=self.Points[-2].y-self.Points[-1].y
            angle=degrees(atan2(dy, dx))

        return punkt,angle
    
    def Write_GCode(self,string,paras,sca,p0,dir,axis1,axis2):
        
        for p_nr in range(len(self.Points)-1):
            en_point, en_angle=self.get_start_end_points(not(dir),p_nr+1)
            x_en=(en_point.x*sca[0])+p0[0]
            y_en=(en_point.y*sca[1])+p0[1]
            string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,x_en,axis2,y_en))
        return string
        
class SplineClass:
    def __init__(self,Nr=0,Layer_Nr=0,CPoints=[],length=0):
        self.Typ='Spline'
        self.Nr = Nr
        self.Layer_Nr = Layer_Nr
        self.Spline_flag=[]
        self.Spline_order=1
        self.Knots=[]
        self.Weights=[]
        self.CPoints=CPoints
        self.Points=[]
        self.length= length
    def __str__(self):
        # how to print the object
        s= ('\nTyp: Spline \nNr -> %i' %self.Nr)+\
           ('\nLayer Nr -> %i' %self.Layer_Nr)+\
           ('\nSpline flag -> %i' %self.Spline_flag)+\
           ('\nSpline order -> %i' %self.Spline_order)+\
           ('\nKnots -> %s' %self.Knots)+\
           ('\nWeights -> %s' %self.Weights)+\
           ('\nCPoints ->')
           
        for point in self.CPoints:
            s=s+str(point)
        s+='\nPoints: ->'
        for point in self.Points:
            s=s+str(point)
        s=s+'\nLength ->'+str(self.length)
        return s

    #Berechnen der NURBS Punkte
    def calculate_nurbs_points(self):
        import dxf2gcode_b01_nurbs_calc as NURBS
        reload(NURBS)

        nurb=NURBS.NURBSClass(order=self.Spline_order,Knots=self.Knots,\
                   Weights=self.Weights,CPoints=self.CPoints,Calc_Pts=200)

        self.Points=nurb.Points      

    def analyse_and_opt(self):     
        summe=0
        #Berechnung der Fläch nach Gauß-Elling Positive Wert bedeutet CW
        #negativer Wert bedeutet CCW geschlossenes Polygon            
        for p_nr in range(1,len(self.Points)):
            summe+=(self.Points[p_nr-1].x*self.Points[p_nr].y-self.Points[p_nr].x*self.Points[p_nr-1].y)/2
        if summe>0.0:
            self.Points.reverse()

        #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
        min_point=self.Points[0]
        min_p_nr=0
        del(self.Points[-1])
        for p_nr in range(1,len(self.Points)):
            #Geringster Abstand nach unten Unten Links
            if (min_point.x+min_point.y)>=(self.Points[p_nr].x+self.Points[p_nr].y):
                min_point=self.Points[p_nr]
                min_p_nr=p_nr
        #Kontur so anordnen das neuer Startpunkt am Anfang liegt
        self.Points=self.Points[min_p_nr:len(self.Points)]+self.Points[0:min_p_nr]+[self.Points[min_p_nr]]
 
    def plot2can(self,canvas,p0,sca,tag):
        hdl=[]
        for i in range(1,len(self.Points)):
            hdl.append(Line(canvas,p0[0]+self.Points[i-1].x*sca[0],-p0[1]-self.Points[i-1].y*sca[1],\
                            p0[0]+self.Points[i].x*sca[0],-p0[1]-self.Points[i].y*sca[1],\
                            tag=tag))     
        return hdl
    
    def get_start_end_points(self,direction=0,nr=0):
        if direction==0:
            punkt=self.Points[nr]
            dx=self.Points[1].x-self.Points[0].x
            dy=self.Points[1].y-self.Points[0].y
            angle=degrees(atan2(dy, dx))
        elif direction==1:
            punkt=self.Points[len(self.Points)-nr-1]
            dx=self.Points[-2].x-self.Points[-1].x
            dy=self.Points[-2].y-self.Points[-1].y
            angle=degrees(atan2(dy, dx))

        return punkt,angle

        return punkt,angle
    
    def Write_GCode(self,string,paras,sca,p0,dir,axis1,axis2):
        
        for p_nr in range(len(self.Points)-1):
            en_point, en_angle=self.get_start_end_points(not(dir),p_nr+1)
            x_en=(en_point.x*sca[0])+p0[0]
            y_en=(en_point.y*sca[1])+p0[1]
            string+=("G1 %s%0.3f %s%0.3f\n" %(axis1,x_en,axis2,y_en))
        return string   

class SectionClass:
    def __init__(self,Nr=0, name='',begin=0,end=1):
        self.Nr= Nr
        self.name = name
        self.begin= begin
        self.end = end  
    def __str__(self):
        # how to print the object
        return '\nNr ->'+str(self.Nr)+'\nName ->'+self.name+'\nBegin ->'+str(self.begin)+'\nEnd: ->'+str(self.end)
    def __len__(self):
        return self.__len__
class EntitiesClass:
    def __init__(self,Nr=0, Name='',geo=[],cont=[]):
        self.Nr= Nr
        self.Name = Name
        self.geo=geo
        self.cont=cont
    def __str__(self):
        # how to print the object
        return '\nNr ->'+str(self.Nr)+'\nName ->'+self.Name\
               +'\nNumber or Geometries ->'+str(len(self.geo))\
               +'\nNumber of Contours ->'+str(len(self.cont))\
               
    def __len__(self):
        return self.__len__
    
    #Gibt einen List mit den Benutzten Layers des Blocks oder Entities zurück
    def get_used_layers(self):
        used_layers=[]
        for i in range(len(self.geo)):
            if (self.geo[i].Layer_Nr in used_layers)==0:
                used_layers.append(self.geo[i].Layer_Nr)
        return used_layers
      #Gibt die Anzahl der Inserts in den Entities zurück
    def get_insert_nr(self):
        insert_nr=0
        for i in range(len(self.geo)):
            if ("Insert" in self.geo[i].Typ):
                insert_nr+=1
        return insert_nr
    
class BlocksClass:
    def __init__(self,Entities=[]):
        self.Entities=Entities
    def __str__(self):
        # how to print the object
        s= '\nBlocks:\nNumber of Blocks ->'+str(len(self.Entities))
        for entitie in self.Entities:
            s=s+str(entitie)
        return s

class PointClass:
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
    def __str__(self):
        return ('\nPoint:   X ->%6.2f  Y ->%6.2f' %(self.x,self.y))
    def __cmp__(self, other) : 
      return (self.x == other.x) and (self.y == other.y)
    def __add__(self, other): # add to another point
        return PointClass(self.x+other.x, self.y+other.y)
    def __rmul__(self, other):
        return PointClass(other * self.x,  other * self.y)
    def distance(self,other):
        return sqrt(pow(self.x-other.x,2)+pow(self.y-other.y,2))
    def isintol(self,other,tol):
        return (abs(self.x-other.x)<=tol) & (abs(self.y-other.y)<tol)
    def triangle_height(self,other1,other2):
        #Die 3 Längen des Dreiecks ausrechnen
        a=self.distance(other1)
        b=other1.distance(other2)
        c=self.distance(other2)
        print a
        print b
        print c
        
        return sqrt(pow(b,2)-pow((pow(c,2)+pow(b,2)-pow(a,2))/(2*c),2))                
      
class PointsClass:
    #Initialisieren der Klasse
    def __init__(self,point_nr=0, geo_nr=0,Layer_Nr=None,be=[],en=[],be_cp=[],en_cp=[]):
        self.point_nr=point_nr
        self.geo_nr=geo_nr
        self.Layer_Nr=Layer_Nr
        self.be=be
        self.en=en
        self.be_cp=be_cp
        self.en_cp=en_cp
        
    
    #Wie die Klasse ausgegeben wird.
    def __str__(self):
        # how to print the object
        return '\npoint_nr ->'+str(self.point_nr)+'\ngeo_nr ->'+str(self.geo_nr) \
               +'\nLayer_Nr ->'+str(self.Layer_Nr)\
               +'\nbe ->'+str(self.be)+'\nen ->'+str(self.en)\
               +'\nbe_cp ->'+str(self.be_cp)+'\nen_cp ->'+str(self.en_cp)

class ContourClass:
    #Initialisieren der Klasse
    def __init__(self,cont_nr=0,closed=0,order=[],length=0):
        self.cont_nr=cont_nr
        self.closed=closed
        self.order=order
        self.length=length
        

    #Komplettes umdrehen der Kontur
    def reverse(self):
        self.order.reverse()
        for i in range(len(self.order)):
            if self.order[i][1]==0:
                self.order[i][1]=1
            else:
                self.order[i][1]=0
        return

    #Ist die klasse geschlossen wenn ja dann 1 zurück geben
    def is_contour_closed(self):

        #Immer nur die Letzte überprüfen da diese neu ist        
        for j in range(len(self.order)-1):
            if self.order[-1][0]==self.order[j][0]:
                if j==0:
                    self.closed=1
                    return self.closed
                else:
                    self.closed=2
                    return self.closed
        return self.closed


    #Ist die klasse geschlossen wenn ja dann 1 zurück geben
    def remove_other_closed_contour(self):
        for i in range(len(self.order)):
            for j in range(i+1,len(self.order)):
                #print '\ni: '+str(i)+'j: '+str(j)
                if self.order[i][0]==self.order[j][0]:
                   self.order=self.order[0:i]
                   break
        return 
    #Berechnen der Zusammengesetzen Kontur Länge
    def calc_length(self,geos=None):        
        #Falls die beste geschlossen ist und erste Geo == Letze dann entfernen
        if (self.closed==1) & (len(self.order)>1):
            if self.order[0]==self.order[-1]:
                del(self.order[-1])

        self.length=0
        for i in range(len(self.order)):
            self.length+=geos[self.order[i][0]].length
        return


    
    def analyse_and_opt(self,geos=None):
        #Errechnen der Länge
        self.calc_length(geos)
        
        #Optimierung für geschlossene Konturen
        if self.closed==1:
            summe=0
            #Berechnung der Fläch nach Gauß-Elling Positive Wert bedeutet CW
            #negativer Wert bedeutet CCW geschlossenes Polygon
            geo_point_l, dummy=geos[self.order[-1][0]].get_start_end_points(self.order[-1][1])            
            for geo_order_nr in range(len(self.order)):
                geo_point, dummy=geos[self.order[geo_order_nr][0]].get_start_end_points(self.order[geo_order_nr][1])
                summe+=(geo_point_l.x*geo_point.y-geo_point.x*geo_point_l.y)/2
                geo_point_l=geo_point
            if summe>0.0:
                self.reverse()

            #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
            min_point=geo_point_l
            min_point_nr=None
            for geo_order_nr in range(len(self.order)):
                geo_point, dummy=geos[self.order[geo_order_nr][0]].get_start_end_points(self.order[geo_order_nr][1])
                #Geringster Abstand nach unten Unten Links
                if (min_point.x+min_point.y)>=(geo_point.x+geo_point.y):
                    min_point=geo_point
                    min_point_nr=geo_order_nr
            #Kontur so anordnen das neuer Startpunkt am Anfang liegt
            self.set_new_startpoint(min_point_nr)
            
        #Optimierung für offene Konturen
        else:
            geo_spoint, dummy=geos[self.order[0][0]].get_start_end_points(self.order[0][1])
            geo_epoint, dummy=geos[self.order[0][0]].get_start_end_points(not(self.order[0][1]))
            if (geo_spoint.x+geo_spoint.y)>=(geo_epoint.x+geo_epoint.y):
                self.reverse()


    #Neuen Startpunkt an den Anfang stellen
    def set_new_startpoint(self,st_p):
        self.order=self.order[st_p:len(self.order)]+self.order[0:st_p]
        
    #Wie die Klasse ausgegeben wird.
    def __str__(self):
        # how to print the object
        return '\ncont_nr ->'+str(self.cont_nr)+'\nclosed ->'+str(self.closed) \
               +'\norder ->'+str(self.order)+'\nlength ->'+str(self.length)        
        
            
        
            
