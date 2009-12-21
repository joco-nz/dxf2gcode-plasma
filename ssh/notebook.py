'''
Created on 13.12.2009

@author: mah
'''
# file: notebook.py
# A simple notebook-like Tkinter widget.
# Copyright 2003, Iuri Wickert (iwickert yahoo.com)

from Tkinter import *

class notebook:
    
    
    # initialization. receives the master widget
    # reference and the notebook orientation
    def __init__(self, master, side=LEFT):
        
        self.active_fr = None
        self.count = 0
        self.choice = IntVar(0)

        # allows the TOP and BOTTOM
        # radiobuttons' positioning.
        if side in (TOP, BOTTOM):
            self.side = LEFT
        else:
            self.side = TOP

        # creates notebook's frames structure
        self.rb_fr = Frame(master, borderwidth=2, relief=RIDGE)
        self.rb_fr.pack(side=side, fill=BOTH)
        self.screen_fr = Frame(master, borderwidth=2, relief=RIDGE)
        self.screen_fr.pack(fill=BOTH)
        

    # return a master frame reference for the external frames (screens)
    def __call__(self):

        return self.screen_fr

    # add a new frame (screen) to the (bottom/left of the) notebook
    def add_screen(self, fr, title):
        

        tv = StringVar()
        b = Radiobutton(self.rb_fr, textvariable=tv, indicatoron=0, \
            variable=self.choice, value=self.count, \
            width=len(title),
            command=lambda: self.display(fr))
        tv.set(title)
        b.tv = tv
        b.pack(fill=BOTH, side=self.side)
        
        # ensures the first frame will be
        # the first selected/enabled
        if not self.active_fr:
            fr.pack(fill=BOTH, expand=1)
            self.active_fr = fr

        self.count += 1
        
        # returns a reference to the newly created
        # radiobutton (allowing its configuration/destruction)         
        return b


    # hides the former active frame and shows 
    # another one, keeping its reference
    def display(self, fr):
        
        self.active_fr.forget()
        fr.pack(fill=BOTH, expand=1)
        self.active_fr = fr
