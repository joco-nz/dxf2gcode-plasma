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


import matplotlib
matplotlib.use('TkAgg')

from matplotlib.numerix import arange, sin, pi
from matplotlib.axes import Subplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

from Tkconstants import TOP, BOTH, BOTTOM, LEFT, RIGHT,GROOVE
from Tkinter import Tk, Button, Frame
from math import radians, cos, sin, sqrt, pow
import sys

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

            u=u_nxt            

        self.Points=Points            



    def calc_Point(self,u):
        
        #                        sum(i = 0, n){w_i * P_i * N_i,k(u)}
        #  C(u) = map( C'(u) ) = -----------------------------------
        #			             sum(i = 0, n){w_i * N_i,k(u)}
        basis,base_m1=self.calc_Basis(u)
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

    #N(i,p)(u)              
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
        base_m1=[]
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
                if (k==self.order-2)
                    base_m1.append(temp[i])
                temp[i]=d+e

        #basis=sum(i = 0, n){w_i  * N(i,p)(u)}/ sum(i = 0, n){w_i * N(i,p)(u)}
        return temp, base_m1

 
    def __str__(self):
        string=("\nControlpoints Nr: %i" %self.nCPts)\
                +("\nOrder: %s" %self.order)
        for nr in range(self.nCPts):
            string+=("%s  Weight ->%6.1f" %(self.CPoints[nr], self.Weights[nr]))
        string+=("\nPoints to calculate: %s" %self.Calc_Pts)
        for Point in self.Points:
            string+=str(Point)
        
        return string      

class PlotClass:
    def __init__(self,master=[]):

        order, CPoints, Weights, Knots=self.get_closed_spline2()
        self.master=master
        self.Nurbs=NURBSClass(order=order,Knots=Knots,CPoints=CPoints,Weights=Weights,Calc_Pts=150)
        #print self.Nurbs
        
        #Erstellen des Fensters mit Rahmen und Canvas
        self.figure = Figure(figsize=(7,7), dpi=100)
        self.frame_c=Frame(relief = GROOVE,bd = 2)
        self.frame_c.pack(fill=BOTH, expand=1,)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame_c)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=1)

        #Erstellen der Toolbar unten
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.frame_c)
        self.toolbar.update()
        self.canvas._tkcanvas.pack( fill=BOTH, expand=1)

        #Erstellen des Ausdrucks        
        self.ini_plot()

    def get_closed_spline1(self):
        order=3
        Knots=[0.0, 0.0, 0.0, 0.0, 0.25, 0.25, 0.25, 0.25, 0.5, 0.5, 0.5,\
               0.5, 0.75, 0.75, 0.75, 0.75, 1.0, 1.0, 1.0, 1.0]
        
        Weights= [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        CPoints=[]        
        CPoints.append(PointClass(x=-105.00,y=147.25))
        CPoints.append(PointClass(x=-104.31,y=147.25))
        CPoints.append(PointClass(x=-103.75,y=147.81))
        CPoints.append(PointClass(x=-103.75,y=148.50))
        CPoints.append(PointClass(x=-103.75,y=148.50))
        CPoints.append(PointClass(x=-103.75,y=149.19))
        CPoints.append(PointClass(x=-104.31,y=149.75))
        CPoints.append(PointClass(x=-105.00,y=149.75))
        CPoints.append(PointClass(x=-105.00,y=149.75))
        CPoints.append(PointClass(x=-105.69,y=149.75))
        CPoints.append(PointClass(x=-106.25,y=149.19))
        CPoints.append(PointClass(x=-106.25,y=148.50))
        CPoints.append(PointClass(x=-106.25,y=148.50))
        CPoints.append(PointClass(x=-106.25,y=147.81))
        CPoints.append(PointClass(x=-105.69,y=147.25))
        CPoints.append(PointClass(x=-105.00,y=147.25))

        return order, CPoints, Weights, Knots   

    def get_closed_spline2(self):
        order=3
        Knots=[0.0, 0.0, 0.0, 0.0, 0.10000000000000001, 0.10000000000000001, 0.10000000000000001,\
               0.10000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001,\
               0.20000000000000001, 0.29999999999999999, 0.29999999999999999, 0.29999999999999999,\
               0.29999999999999999, 0.40000000000000002, 0.40000000000000002, 0.40000000000000002,\
               0.40000000000000002, 0.5, 0.5, 0.5, 0.5, 0.59999999999999998, 0.59999999999999998,\
               0.59999999999999998, 0.59999999999999998, 0.69999999999999996, 0.69999999999999996,\
               0.69999999999999996, 0.69999999999999996, 0.79999999999999993, 0.79999999999999993,\
               0.79999999999999993, 0.79999999999999993, 0.89999999999999991, 0.89999999999999991,\
               0.89999999999999991, 0.89999999999999991, 1.0, 1.0, 1.0, 1.0]
        
        Weights= [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,\
                    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        CPoints=[]
     
        CPoints.append(PointClass(x=-69.25,y=92.00))
        CPoints.append(PointClass(x=-69.25,y=92.00))
        CPoints.append(PointClass(x=-69.25,y=92.00))
        CPoints.append(PointClass(x=-69.25,y=92.00))
        CPoints.append(PointClass(x=-69.25,y=92.00))
        CPoints.append(PointClass(x=-64.98,y=92.00))
        CPoints.append(PointClass(x=-61.00,y=93.30))
        CPoints.append(PointClass(x=-57.69,y=95.53))
        CPoints.append(PointClass(x=-57.69,y=95.53))
        CPoints.append(PointClass(x=-57.69,y=95.53))
        CPoints.append(PointClass(x=-60.22,y=98.06))
        CPoints.append(PointClass(x=-60.22,y=98.06))
        CPoints.append(PointClass(x=-60.22,y=98.06))
        CPoints.append(PointClass(x=-62.85,y=96.44))
        CPoints.append(PointClass(x=-65.94,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-69.25,y=95.50))
        CPoints.append(PointClass(x=-72.56,y=95.50))
        CPoints.append(PointClass(x=-75.65,y=96.44))
        CPoints.append(PointClass(x=-78.28,y=98.06))
        CPoints.append(PointClass(x=-78.28,y=98.06))
        CPoints.append(PointClass(x=-78.28,y=98.06))
        CPoints.append(PointClass(x=-80.81,y=95.53))
        CPoints.append(PointClass(x=-80.81,y=95.53))
        CPoints.append(PointClass(x=-80.81,y=95.53))
        CPoints.append(PointClass(x=-77.50,y=93.30))
        CPoints.append(PointClass(x=-73.53,y=92.00))
        CPoints.append(PointClass(x=-69.25,y=92.00))
        CPoints.append(PointClass(x=-69.25,y=92.00))
        CPoints.append(PointClass(x=-69.25,y=92.00))
        CPoints.append(PointClass(x=-69.25,y=92.00))
        CPoints.append(PointClass(x=-69.25,y=92.00))
        return order, CPoints, Weights, Knots   

    def ini_plot(self):
        self.plot1 = self.figure.add_subplot(111)
        self.plot1.set_title("NURBS Calculation: ")
        xC=[]
        yC=[]
        xP=[]
        yP=[]
        for Cpt in self.Nurbs.CPoints:
            xC.append(Cpt.x)
            yC.append(Cpt.y)
        for Pt in self.Nurbs.Points:
            xP.append(Pt.x)
            yP.append(Pt.y)
        self.plot1.plot(xC,yC,'-.xr',xP,yP,'-ob')
        self.canvas.show()

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
 

master = Tk()
master.title("NURBS in Python berechnen")
#import profile     
#profile.run('ClassPlotFigure(master)',sort='cumulative')
PlotClass(master)
master.mainloop()

     