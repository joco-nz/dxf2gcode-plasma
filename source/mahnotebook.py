# -*- coding: iso-8859-1 -*-
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose:  Notebook widget for Tkinter

loosely based on http://code.activestate.com/recipes/188537/

added hide_screen, show_screen, rename methods
automatic button resizing on rename
bugfix - on changing/displaying screens the proper button wasnt displayed

@author: Michael Haberler 
@since:  24.12.2009
@license: GPL
"""

from Tkinter import IntVar, Frame, Radiobutton, N, E, W, RIDGE


class NotebookClass(Frame):    
    # initialization. receives the master widget
    # reference and the notebook orientation
    def __init__(self, master, width=0, height=0, xfuzz=0, **options):
        """ 
        create a new NoteBookClass instance
        @param master: master widget reference
        @param width: notebook width in pixels
        @param xfuzz: some platforms might need an extra character 
            to display buttons nicely
        """ 
        
        Frame.__init__(self, master, **options) 

        self.active_fr = None
        # track visible screens for sane switching
        self.visible_frames = []
        self.count = 0
        self.choice = IntVar(0)
        self.xfuzz = xfuzz
        

        self.dummy_x_fr = Frame(self, width=width, borderwidth=0)
        self.dummy_y_fr = Frame(self, height=height, borderwidth=0)
        self.dummy_x_fr.grid(row=0, column=1)
        self.dummy_x_fr.grid_propagate(0)
        self.dummy_y_fr.grid(row=1, rowspan=2, column=0)
        self.dummy_y_fr.grid_propagate(0)

        # creates notebook's frames structure
        self.rb_fr = Frame(self, borderwidth=0)
        self.rb_fr.grid(row=1, column=1, sticky=N + W)
         
        # fIXME make this a Scrolled Canvas  
        self.screen_fr = Frame(self, borderwidth=2, relief=RIDGE)
        self.screen_fr.grid(row=2, column=1, sticky=N + W + E)
        
        master.rowconfigure(2, weight=1)
        master.columnconfigure(1, weight=1)

    def __call__(self):
        """ 
        return a master frame reference for the external 
        frames (screens)"""
        return self.screen_fr

    def add_screen(self, fr, title, **kwargs):
        """ 
        Add a new frame (screen) to the notebook
        @param fr: a Frame() instance 
        @param title: name for this frame's button
        @sideeffect: the _button attribute is set on fr for later 
        reference when hiding/showing screens
        """ 
        
        # button stays on frame instance so we can rename and properly
        # select it later
        fr._button = Radiobutton(self.rb_fr, kwargs, text=title, indicatoron=0, bd=1,
                        variable=self.choice, value=self.count,
                        width=len(title) + self.xfuzz,
                        command=lambda: self.display(fr))
        
        fr._button.grid(column=self.count, row=0, sticky=N + E + W)
        self.rb_fr.columnconfigure(self.count, weight=1)

        fr.grid(sticky=N + W + E)
        self.screen_fr.columnconfigure(0, weight=1)
        fr.grid_remove()

        # ensures the first frame will be
        # the first selected/enabled
#        if not self.active_fr:
#            fr.grid()
#            self.active_fr = fr
#        
#        self.visible_frames.append(fr)
            
        self.count += 1
        # add button to fr so we can rename and properly
        # select it later



    def rename(self, fr, new_title):
        """ 
        rename button on screen fr
        
        The button's width is adjusted accordingly
        
        @param fr: a Frame() instance 
        @param title: new name for this frame's button
        """ 
        fr._button['text'] = new_title
        fr._button['width'] = len(new_title) + self.xfuzz
        
    def hide(self, fr):
        """ 
        hide screen fr from notebook - fr can be reactived later
        by display
        
        @param fr: a Frame() instance to be temporily removed from
            the notebook
        @sideeffect: switches to the last visible screen if the
            currently selected screen was deleted
        """ 
        if fr in self.visible_frames:
            self.visible_frames.remove(fr)
    
            fr._button.grid_remove()
            fr.grid_remove()
    
        if (fr == self.active_fr) and len(self.visible_frames) > 0:
            
            self.active_fr = self.visible_frames[-1]

            self.active_fr.grid()
            self.active_fr._button.grid()
            self.active_fr._button.select()         
            
    def  display(self, fr):
        """ 
        re-activate a hidden screen 
        
        @param fr: a Frame() instance to be added to
            the notebook
        @sideeffect: switches to fr
        """         
        if not fr in self.visible_frames:
            self.visible_frames.append(fr)
        if self.active_fr:
            self.active_fr.grid_remove()
        self.active_fr = fr

        self.active_fr.grid()
        self.active_fr._button.grid()
        self.active_fr._button.select() 
        

        
