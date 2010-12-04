#!/usr/bin/python


from dxf2gcode_b02 import MyMainWindow
from Tkinter import Tk

master = Tk()
master.title("TEST")

import cProfile
cProfile.run('MyMainWindow()')

