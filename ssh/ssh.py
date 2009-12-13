'''
Created on 07.12.2009

@author: mah
'''

import os,sys

from varspace import  VarSpace

# see http://www.voidspace.org.uk/python/configobj.html and
# http://www.voidspace.org.uk/python/validate.html 

# you make any changes to specname
# always increment specversion default so an old .ini file
# can be detected

SPECVERSION = "v23.6"

specname = str('''
# do not edit the following section name:
    [Version]

    # do not edit the following value:
    specversion = string(default="'''  + \
    str(SPECVERSION) + '")\n' + \
'''
    
    [Variables]
    
    # persistent variables

    instance_name = string(default="someinstance")
    tool_dia = float(default=63.0)
    start_radius = float(default=0.0)
    axis3_safe_margin = float(default=20.0)
    axis3_slice_depth = float(default=0.5)
    axis3_mill_depth = float(default=10.0)
    f_g1_depth = float(default=50.0)
    f_g1_plane = float(default=150.0)
    # Tests
    booltrue = boolean(default=True)
    boolfalse = boolean(default=False)
    option    = string(default='bar')

    unframed_int = integer(default=50)

             
             
    [UI]
    # Variables listed here are displayed in the UI and are editable
    # the string value is the descriptive text displayed in a Label
    # variables from the global configuration can be interpolated into the text
    
    [[FRAMED]]
        instance_name = string(default="Name this instance:")
        
    [[UNFRAMED]]
        unframed_int = string(default="Edit int value:")
        
        
    #named frames:
    [[Tool Parameters]]
        tool_dia = string(default= "Tool diameter [mm]:")
        start_radius = string(default= "Start radius (for tool comp.) [mm]:")
    [[Depth Coordinates]]
        axis3_safe_margin = string(default= "%(ax3_letter)s safety margin [mm]:")
        axis3_slice_depth = string(default= "%(ax3_letter)s infeed depth [mm]:")
        axis3_mill_depth = string(default=  "%(ax3_letter)s mill depth [mm]:")
    [[Feed Rates]]
        f_g1_depth = string(default= "G1 feed %(ax3_letter)s-direction [mm/min]:")
        f_g1_plane = string(default= "G1 feed %(ax1_letter)s%(ax2_letter)s-direction [mm/min]:")
        
    [[Test]]
        # pre-set boolean variables
        booltrue = string(default = "Checked")
        boolfalse = string(default = "Unchecked")
        
        # a OptionMenu - labeltext is first element, rest is choices:
        option = string_list(default=list('Tick one of:','foo', 'bar', 'baz'))

''').splitlines()  
    
class ShapeSetHandler:
    '''
    classdocs
    '''

    def __init__(self,parentframe,config):
        '''
        called once the module is loaded and verified
        frame - the handlers's parameter frame (a tab, left side)
        config - global confguration from ConfigParser(config.cfg)
        '''
        
        directory = "."
        basename = "vspace"
        instancename = "foo"
        self.vs = VarSpace(specname, directory, basename, instancename=instancename,specversion=SPECVERSION)
        # layout variables as per INI file
        self.vs.create_pane(parentframe,config)
        # manually add buttons at bottom
        self.vs.add_button(parentframe,"","Show variables", self._show_params,config)
        self.vs.add_button(parentframe,"","Save config", self._save_params,config)
        self.vs.add_button(parentframe,"demonstrate interpolation: %(ax1_letter)s%(ax2_letter)s",
                           "Save %(ax3_letter)s", self._buttonCallback,config)
        self.vs.add_button(parentframe,"","quit", self._quit,config)

#        # read cfg file
#        folder = "/Users/mah/Documents/workspace/dxf2gcode-tkinter-haberler-gc/ssh"
#        file_name = 'mill_export.cfg'
#        self.pathname = os.path.join(folder,file_name)

 
    def _buttonCallback(self,name):
        print "Button '%(name)s' pressed" %(locals())
        
    def _quit(self,name):
        sys.exit(0)
        
    def _save_params(self,name):
        self.vs.save_cfg() #self.pathname)
    
    def _show_params(self,name):
        self.vs.print_vars()

    
    
    def short_name(self):
        return "Mill"
    
#    def menu_entry(self):
#        pass
#    
#    def parameter_frame(self):
#        pass
#    
#    def generate(self,shapeset):
#        pass


