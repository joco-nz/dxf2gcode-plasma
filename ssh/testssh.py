'''


Test shapesethandler

Created on 13.12.2009

@author: mah
'''
from Tkinter import *
from ssh import *
from notebook import *

class junk:
    def __init__(self):
        pass
    
if __name__ == "__main__":
#    config = ConfigParser.ConfigParser()
    config = junk()
    config.ax1_letter = 'X'
    config.ax2_letter = 'Y'
    config.ax3_letter = 'Z'
    
    config2 = junk()
    config2.ax1_letter = 'A'
    config2.ax2_letter = 'B'
    config2.ax3_letter = 'C'
    
    root = Tk()
#    w = Frame (root) 
    w = notebook (root, TOP) 
    f1 = Frame(w())
    f2 = Frame(w())
    f3 = Frame(w())

    b1 = Button(f3, text="Button 1")
    e1 = Entry(f3)
    b1.pack(fill=BOTH, expand=1)
    e1.pack(fill=BOTH, expand=1)

    ssh1 = ShapeSetHandler(f1, config, instancename="one")
    ssh2 = ShapeSetHandler(f2, config2, instancename="two")
    w.add_screen(f1, "mill1") # ssh1.short_name())
    w.add_screen(f2, "mill2")#  ssh2.short_name())
    w.add_screen(f3, "random")

    #w.pack()
    root.mainloop()
    