'''
Test shapesethandler

Created on 13.12.2009

@author: mah
'''
from Tkinter import Tk,Frame,TOP
from ssh import ShapeSetHandler
from notebook import notebook

class junk:
    def __init__(self):
        pass
    
if __name__ == "__main__":

    config = junk()
    config.ax1_letter = 'X'
    config.ax2_letter = 'Y'
    config.ax3_letter = 'Z'
    
    config2 = junk()
    config2.ax1_letter = 'A'
    config2.ax2_letter = 'B'
    config2.ax3_letter = 'C'
    
    root = Tk()

    w = notebook (root, TOP) 
    f1 = Frame(w())
    f2 = Frame(w())

    ssh1 = ShapeSetHandler(f1, config, instancename="one")
    ssh2 = ShapeSetHandler(f2, config2, instancename="two")
    w.add_screen(f1, "mill1")
    w.add_screen(f2, "mill2")

    root.mainloop()
    