'''


Test shapesethandler

Created on 13.12.2009

@author: mah
'''
from Tkinter import *
from ssh import *

class junk:
    def __init__(self):
        pass
    
if __name__ == "__main__":
#    config = ConfigParser.ConfigParser()
    config = junk()
    config.ax1_letter = 'X'
    config.ax2_letter = 'Y'
    config.ax3_letter = 'Z'
    root = Tk()
    w = Frame (root) 
    ssh = ShapeSetHandler(w, config)
    
    w.pack()
    root.mainloop()
    