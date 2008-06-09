#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_v01_geoent_insert
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

from dxf2gcode_v01_point import PointClass, ContourClass

class InsertClass:
    def __init__(self,Nr=0,caller=None):
        self.Typ='Insert'
        self.Nr = Nr

        #Initialisieren der Werte        
        self.Layer_Nr = 0
        self.Block = ''
        self.Point = []
        self.Scale=[1,1,1]
        self.length=0.0

        #Lesen der Geometrie
        self.Read(caller)         
        
    def __str__(self):
        # how to print the object
        return '\nTyp: Insert\nNr ->'+str(self.Nr)\
            +'\nLayer Nr: ->'+str(self.Layer_Nr)+'\nBlock ->' +str(self.Block) \
            +str(self.Point) \
            +'\nScale ->'+str(self.Scale) 

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol):
        cont.append(ContourClass(len(cont),0,[[i,0]],0))
    
    def Read(self, caller):
        #Kürzere Namen zuweisen
        lp=caller.line_pairs
        e=lp.index_code(0,caller.start+1)

        #Block Name        
        ind=lp.index_code(2,caller.start+1,e)
        self.Block=caller.Get_Block_Nr(lp.line_pair[ind].value)
        #Layer zuweisen        
        s=lp.index_code(8,caller.start+1,e)
        self.Layer_Nr=caller.Get_Layer_Nr(lp.line_pair[s].value)
        #XWert
        s=lp.index_code(10,s+1,e)
        x0=float(lp.line_pair[s].value)
        #YWert
        s=lp.index_code(20,s+1,e)
        y0=float(lp.line_pair[s].value)
        self.Point=PointClass(x0,y0)
        
        #XScale
        s_temp=lp.index_code(41,s+1,e)
        if s_temp!=None:
            self.Scale[0]=float(lp.line_pair[s_temp].value)
        #YScale
        s_temp=lp.index_code(42,s+1,e)
        if s_temp!=None:
            self.Scale[1]=float(lp.line_pair[s_temp].value) 
        #ZScale
        s_temp=lp.index_code(43,s+1,e)
        if s_temp!=None:
            self.Scale[2]=float(lp.line_pair[s_temp].value)

        #Neuen Startwert für die nächste Geometrie zurückgeben
        caller.start=e      

