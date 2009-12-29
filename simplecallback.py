# -*- coding: iso-8859-15 -*-
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
'''
SimpleCallback - helper class to pass arguments to Tkinter callbacks

Tkinter callbacks do not pass optional arguments to callbacks. This function 
enables callback arguments::

    def doButton(buttonName):
        print buttonName, "pressed"

    root = Tkinter.Tk()
    
    buttonNames = ("Button 1", "Button 2", "Button 3")
    for name in buttonNames:
    callback = SimpleCallback(doButton, name)
    Tkinter.Button(root, text=name, command=callback).pack()
    
    root.mainloop()

see U{http://www.astro.washington.edu/users/rowen/TkinterSummary.html#CallbackShims}

Michael Haberler  20.12.2009
'''

class SimpleCallback:
    """Create a callback shim. Based on code by Scott David Daniels
    (which also handles keyword arguments).
    """
    def __init__(self, callback, *firstArgs):
        self.__callback = callback
        self.__firstArgs = firstArgs
    
    def __call__(self, *args):
        return self.__callback (*(self.__firstArgs + args))
