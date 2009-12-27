#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_widgets.py
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
from Tkconstants import END, ALL, N, S, E, W, RIDGE, GROOVE, FLAT, DISABLED, NORMAL, ACTIVE, LEFT
from Tkinter import Tk, IntVar, DoubleVar, Frame, Radiobutton


class Notebook:    
    # initialization. receives the master widget
    # reference and the notebook orientation
    def __init__(self, master,width=0,height=0):

        self.active_fr = None
        self.count = 0
        self.choice = IntVar(0)

        self.dummy_x_fr = Frame(master, width=width, borderwidth=0)
        self.dummy_y_fr = Frame(master, height=height, borderwidth=0)
        self.dummy_x_fr.grid(row=0,column=1)
        self.dummy_x_fr.grid_propagate(0)
        self.dummy_y_fr.grid(row=1,rowspan=2,column=0)
        self.dummy_y_fr.grid_propagate(0)

        # creates notebook's frames structure
        self.rb_fr = Frame(master, borderwidth=0)
        self.rb_fr.grid(row=1,column=1, sticky=N+W)
        
        self.screen_fr = Frame(master, borderwidth=2, relief=RIDGE)
        self.screen_fr.grid(row=2,column=1,sticky=N+W+E)
        
        master.rowconfigure(2,weight=1)
        master.columnconfigure(1,weight=1)

    # return a master frame reference for the external frames (screens)
    def __call__(self):
        return self.screen_fr

    # add a new frame (screen) to the (bottom/left of the) notebook
    def add_screen(self, fr, title):

        b = Radiobutton(self.rb_fr,bd=1, text=title, indicatoron=0, \
                        variable=self.choice, value=self.count, \
                        command=lambda: self.display(fr))
        
        b.grid(column=self.count,row=0,sticky=N+E+W)
        self.rb_fr.columnconfigure(self.count,weight=1)

        fr.grid(sticky=N+W+E)
        self.screen_fr.columnconfigure(0,weight=1)
        fr.grid_remove()

        # ensures the first frame will be
        # the first selected/enabled
        if not self.active_fr:
            fr.grid()
            self.active_fr = fr

        self.count += 1

        # returns a reference to the newly created
        # radiobutton (allowing its configuration/destruction)
        return b


        # hides the former active frame and shows 
        # another one, keeping its reference
    def display(self, fr):
        self.active_fr.grid_remove()
        fr.grid()
        self.active_fr = fr
                  