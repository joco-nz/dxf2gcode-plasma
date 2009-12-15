'''

VarSpace implements:

- a persistent, typed  variable store (self.cfg_vars) using ConfigObj 
    (including automatic type conversion when reading from INI file)
    plus some basic type and range checking on the INI file 
- a method to create a default INI file from the specifification
- a user interface abstraction so ShapeSetHandler may remain UI-agnostic
     this is a minimal interface to create parameter entry fields & buttons for
     Tkinter, driven by config file contents
     

Created on 07.12.2009

@author: Michael Haberler
'''

from Tkconstants import  N, E, W, GROOVE
from Tkinter import OptionMenu, Frame, Checkbutton, Button, Label, Entry,LabelFrame
from Tkinter import StringVar, DoubleVar, IntVar,BooleanVar

import os

from configobj import ConfigObj, flatten_errors
from validate import Validator

debug = 1

class VarSpace:
    def __init__(self, specname, directory, basename, instancename=None, specversion=None):
        #       self.supported = ('double', 'string', 'bool', 'list')
        #       self.ui_items = []
        self.path = None
        self.cfg_vars = dict()
        self.tkVars = dict()
        self.groupcount = 0
        self.spec = ConfigObj(specname, interpolation=False, list_values=False, _inspec=True)
        self.directory = directory
        self.basename = basename
        self.instancename = instancename
        self.configsuffix = 'cfg'    # FIXME add2 global config ref
        self._initialize(specversion)

        
    def _initialize(self,specversion):
        '''
        construct path
        if file exists, try to read it and populate variables, type-converted
        if file doesnt exist or has errors, bail out
        '''
        
        if self.instancename:
            fn = "%(basename)s-%(instancename)s.%(configsuffix)s" % (self.__dict__)
        else:
            fn = "%(basename)s.%(configsuffix)s" % (self.__dict__)
            
        self.path = os.path.join(self.directory, fn)
        
        if os.path.isfile(self.path):
            # file exists, read & validate it
            self.cfg_vars = ConfigObj(self.path, configspec=self.spec, interpolation=False)
            _vdt = Validator()
            result = self.cfg_vars.validate(_vdt, preserve_errors=True)
            validate_errors = flatten_errors(self.cfg_vars, result)
            if validate_errors:
                print "errors reading %(path)s:" % (self.__dict__)
            for entry in validate_errors:
                # each entry is a tuple
                section_list, key, error = entry
                if key is not None:
                    section_list.append(key)
                else:
                    section_list.append('[missing section]')
                section_string = ', '.join(section_list)
                if error == False:
                    error = 'Missing value or section.'
                print section_string, ' = ', error            
            
            if validate_errors:
                raise BadConfigFileError 
                # print "Errors reading %(path)s - delete file to recreate defaults" % (self.__dict__)
                
            # check config file version against internal version
            if specversion:
                fileversion = self.cfg_vars['Version']['specversion']
                if fileversion != specversion:
                    print 'config file vesions do not match - internal: "%(specversion)s", config file "%(fileversion)s"' %(locals())
                    raise BadConfigFileError         
        else:
            self.create_default_cfg()
            
    def create_default_cfg(self):
        # derive config file with defaults from spec
        self.cfg_vars = ConfigObj(configspec=self.spec)
        _vdt = Validator()
        self.cfg_vars.validate(_vdt, copy=True)
        self.cfg_vars.filename = self.path
        self.cfg_vars.write()
    
    def save_cfg(self):
        #self.cfg_vars.filename = self.path
        self.cfg_vars.write()   
    
    def print_vars(self):
        for frame,content in self.cfg_vars['UI'].items():
            #print " frame=%(frame)s" %(locals())
            for varname,text in content.items():
                value  = self.cfg_vars['Variables'][varname]
                print "%(varname)s = %(value)s" %(locals())

    def _scalarChanged(self,varname,name,index,mode):
        try:
            value = self.tkVars[varname].get()
        except ValueError:
            pass
        else:
            if debug:
                print "%s changed from %s to %s" %(varname,self.cfg_vars['Variables'][varname],value)
            self.cfg_vars['Variables'][varname] = value

    def create_pane(self,parent,config):
        currgroup = None
        groupcount = 0
        linecount = 0
        current_frame = None
        self.cfg_vars.main.interpolation = False # avoid ConfigObj getting too clever
        for group,content in self.cfg_vars['UI'].items():            
            for k,v in content.items():
                optionlist = None
                if isinstance(v, list):  # OptionMenu = 'labeltext','choice1,'choice2'....
                    varname = k
                    labelvar = v[0]
                    optionlist = v[1:]
                else:                   # scalars just have varname = labeltext
                    (varname,labelvar) = (k,v)
                value = self.cfg_vars['Variables'][varname]
                # print "    varname=%(varname)s value=%(value)s labeltext=%(labeltext)s labelvar=%(labelvar)s" %(locals())
                if group != currgroup:
                    currgroup = group
                    groupcount += 1
                    linecount = 0
                    if currgroup == 'UNFRAMED':       # no frame
                        current_frame = Frame(parent,bd = 0)
                    else:
                        if currgroup == 'FRAMED' :    # unnamed frame
                            current_frame = Frame(parent,relief = GROOVE,bd = 2)
                        else:                   # named frame
                            current_frame = LabelFrame(parent,relief = GROOVE,bd = 2, labelanchor='nw',text = group)
                    current_frame.grid(row=groupcount, column=0, padx=2, pady=2, sticky=N + W + E)
                    current_frame.columnconfigure(0, weight=1)
                    
                labeltext = labelvar % (config.__dict__)
                label = Label(current_frame, text=labeltext)
                label.grid(row=linecount, column=0, sticky=N + W, padx=4) 
                width = 7
                # generate appropriate widget for type
                if  isinstance(value, float):
                    self.tkVars[varname] = DoubleVar()
                    self.tkVars[varname].set(value)
                    entry = Entry(current_frame, width=width, textvariable=self.tkVars[varname])
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))
                    
                if  isinstance(value, int):
                    self.tkVars[varname] = IntVar()
                    self.tkVars[varname].set(value)
                    entry = Entry(current_frame, width=width, textvariable=self.tkVars[varname])
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))

                if  isinstance(value, basestring):
                    if len(value) > width:
                        width = len(value)
                    self.tkVars[varname] = StringVar()
                    self.tkVars[varname].set(value)
                    entry = Entry(current_frame, width=width, textvariable=self.tkVars[varname])
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))

                if  isinstance(value, bool):
                    self.tkVars[varname] = BooleanVar()
                    self.tkVars[varname].set(value)
                    entry = Checkbutton(current_frame, variable=self.tkVars[varname])#, offvalue=False, onvalue=True)  
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))

                if  optionlist:
                    self.tkVars[varname] = StringVar()
                    self.tkVars[varname].set(value) 
                    entry = OptionMenu(current_frame, self.tkVars[varname], *optionlist)     
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))

                entry.grid(row=linecount, column=1, sticky=N + E)
                linecount += 1   
            self.groupcount = groupcount
            

    def add_button(self,parent, text,name, callback,config):
        self.groupcount += 1
        col = 0
        current_frame = Frame(parent,bd = 0)
        labeltext = text % (config.__dict__)
        buttontext = name % (config.__dict__)
        if len(text) > 0:
            label = Label(current_frame, text=labeltext)
            label.grid(row=0, column=0, sticky=N + W, padx=4) 
            col += 1   
        current_frame.grid(row=self.groupcount, column=0, padx=2, pady=2, sticky=N + W + E) 
        button = Button(current_frame,text=buttontext,command=SimpleCallback(callback,name))
        button.grid(row=0, column=col, sticky=N )
        current_frame.columnconfigure(0, weight=1)

# http://www.astro.washington.edu/users/rowen/TkinterSummary.html#CallbackShims
class SimpleCallback:
    """Create a callback shim. Based on code by Scott David Daniels
    (which also handles keyword arguments).
    """
    def __init__(self, callback, *firstArgs):
        self.__callback = callback
        self.__firstArgs = firstArgs
    
    def __call__(self, *args):
        return self.__callback (*(self.__firstArgs + args))


if __name__ == "__main__":
    pass

