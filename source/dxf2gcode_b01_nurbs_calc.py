#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b01_nurbs_calc
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

import sys, os, string
from dxf2gcode_b01_dxf_import import PointClass

class NURBSClass:
    def __init__(self,order=0,Knots=[],Weights=None,CPoints=None,Calc_Pts=10):
        self.order=order+1              #Spline order
        self.Knots=Knots                #Knoten Vektor
        self.CPoints=CPoints            #Kontrollpunkte des Splines
        self.Weights=Weights            #Gewichtung der Einzelnen Punkte
        self.Calc_Pts=Calc_Pts          #Anzahl der zu berechnenden Punkte
        self.height_min=0.005           #Toleranz für die min Höhe
        self.height_max=0.02            #Toleranz für die max Höhe
        self.nCPts=len(self.CPoints)    #Anzahl der Kontrollpunkte

        if len(self.CPoints) < self.order:
            raise ValueError, "Order greater than number of control points."
        if len(self.Knots) != (len(self.CPoints) + self.order):
            raise ValueError, "Knot/Control Point/Order number error."    

        #Anfangswerte für Step und u
        u=0
        step=self.Knots[-1]/(Calc_Pts-1)

        #Die ersten 2 Punkte errechnen
        Points=[]
        Points.append(self.calc_Point(u))
        u+=step
        Points.append(self.calc_Point(u))

        #Schleife bis ans Ende
        while u<1.0:
            #Nächsten Schritt errechnen und auf max. 1 begrenzen
            u_nxt=u+step
            if u_nxt>1:
                u_nxt=1

            #Neuen Punkt errechnen            
            Points.append(self.calc_Point(u_nxt))
##
##            #Höhe errechnen            
##            h=Points[-3].triangle_height(Points[-2],Points[-1])
##
##            #Wenn die Schrittweite zu klein ist Punkt so lassen und hochsetzen
##            if h<self.height_min:
##                step=step*2
##                print("New step increased to: %0.5f" %step)
##                u=u_nxt
##            #Wenn die Schrittweite OK ist
##            elif h<self.height_max:
##                u=u_nxt
##                pass
##            #Wenn die Schrittweit zu Groß ist
##            else:
##                del Points[-1]
##                Points.insert(len(Points)-1,self.calc_Point(u-step/2))
##                step=step/2
##                print("New step reduced to: %0.4f" %step)
##
##
##            print ("Heigth was: %0.4f" %h)
            

            u=u_nxt
            
        self.Points=Points



    def calc_Point(self,u):
        
        #                        sum(i = 0, n){w_i * P_i * N_i,k(u)}
        #  C(u) = map( C'(u) ) = -----------------------------------
        #			             sum(i = 0, n){w_i * N_i,k(u)}
        basis=self.calc_Basis(u)
        sum_nominator=PointClass(0.0,0.0)
        sum_denominator=0.0
        for p_nr in range(self.nCPts):
            sum_nominator+=(float(basis[p_nr])*float(self.Weights[p_nr]))*self.CPoints[p_nr]
            sum_denominator+=float(basis[p_nr]*self.Weights[p_nr])

        #            
        if not(sum_denominator==0.0):
            return((1.0/sum_denominator)*sum_nominator)
        #Wenn Null raus kommt dann heißt es ist ein mehrfacher Knoten am Schluß also Punkt == Knoten setzen
        else:
            return(self.CPoints[p_nr])
                
    def calc_Basis(self,u):
        basis=[]
        temp=[]
        #calculate the first order nonrational basis functions [N,i,0(u)]
        for nr in range(self.nCPts+self.order-1):
            if ((u>=self.Knots[nr])and(u<self.Knots[nr+1])):
                temp.append(1.0)
            else:
                temp.append(0.0)

        #calculate the higher order nonrational basis functions
        for k in range(1,self.order):
            for i in range(self.nCPts+self.order-k-1):
                #if the lower order basis function is zero skip the calculation
                #d=(u-u(1))/(u(1+p)-u(i))*N(i,p-1)(u)
                if not(temp[i]==0):
                    d=((u-self.Knots[i])*temp[i])\
                       /(self.Knots[i+k]-self.Knots[i])
                else:
                    d=0

                #if the lower order basis function is zero skip the calculation
                #e=(u(1+p+1)-u)/(u(i+p+1)-u(i+1))*N(i+1,p-1)(u)
                if not(temp[i+1]==0):
                    e=((self.Knots[i+k+1]-u)*temp[i+1])\
                       /(self.Knots[i+k+1]-self.Knots[i+1])
                else:
                    e=0
         
                temp[i]=d+e
        #temp=N(i,p)(u)
                
####        if (u == self.Knots[self.nCPts+self.order-1]):
####            temp[self.nCPts-1] = 1;
##
##        #calculate sum for denominator of rational basis functions
##        sum=0.0
##        for nr in range(self.nCPts):
##            sum+=temp[nr]*self.Weights[nr]
##                
##        #form rational basis functions and put in r vector */
##        for nr in range(self.nCPts):
##            if not(sum==0.0):
##                basis.append(temp[nr]*self.Weights[nr]/sum)
##            else:
##                basis.append(0.0)

        #basis=sum(i = 0, n){w_i  * N(i,p)(u)}/ sum(i = 0, n){w_i * N(i,p)(u)}

        return temp


        
    def __str__(self):
        string=("\nControlpoints Nr: %i" %self.nCPts)\
                +("\nOrder: %s" %self.order)
        for nr in range(self.nCPts):
            string+=("%s  Weight ->%6.1f" %(self.CPoints[nr], self.Weights[nr]))
        string+=("\nPoints to calculate: %s" %self.Calc_Pts)
        for Point in self.Points:
            string+=str(Point)
        
        return string
     

