'''
 Example plugin for pluginloader.py

 export(),verify(),version() and nicename() MUST be defined
 The classname MUST remain 'Plugin'


'''
import logging
import sys
from varspace import  VarSpace
from Tkinter import Frame #FIXME

import globals as g

SPECVERSION = "v23.9"

SPECNAME = str('''
# do not edit the following section name:
    [Version]

    # do not edit the following value:
    specversion = string(default="'''  + \
    str(SPECVERSION) + '")\n' + \
'''
    
    [Variables]
    
    # persistent variables
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
    
    ax1_letter = string(default="X")
    ax2_letter = string(default="Y")
    ax3_letter = string(default="Z")
          
    random_text    = string(default='ver random')
   
             
    [UI]
    # Variables listed here are displayed in the UI and are editable
    # the string value is the descriptive text displayed in a Label
    # variables from the global configuration can be interpolated into the text
    
    [[FRAMED]]
        random_text = string(default="Random Text")
        
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
    

class Plugin(object):
    def __init__(self):
        '''
        required but should not do anything permanent
        all initialisations go to initialize(self,...)
        '''
        pass
    
    def cleanup(self):
        '''
        cleanup when deleting a plugin instance
        '''
        g.logger.logger.info("cleanup plugin %s" %(self.vs.instance_name))

        if self.vs:
            self.vs.cleanup()
            
        #  g.logger.logger.info("the demo validplugin says 'Hi'!")
    
    def initialize(self,parent,varspaces_path,instance_tag,pluginloader):
        
        self.vs = VarSpace(SPECNAME, varspaces_path,instance_tag, 
                           specversion=SPECVERSION, pluginloader=pluginloader)
        
        # create parameter pane with instance edit, save button
        # parent is the notebook widget
        self.vs.create_pane(parent)
        # layout variables as per INI file
        self.vs.add_config_items()
#        # manually add buttons at bottom
        self.vs.add_button("","Show variables", self._show_params)
        
        self.vs.display_pane(parent,instance_tag)
        

    
    
    
    def plugin_tag(self):
        return 'mill'

    def export(self,shapes):
        '''
        main export function 
        '''
        g.logger.logger.info("mill exporter() varspace %s called",self.vs.instance_name)

        return "export successful"

    def menu_entry(self,shape):
        '''

        '''
        return "milling exporter"
    
    
    def version(self):
        '''
         a human-readable version/author/whatever notice string
        '''
        return "0.8.15"

    def describe(self):
        '''
        provide verbose plugin name for user interface
        '''
        return "milling export plugin for DXF2gcode"

# ---- opional user defined functions

    def _buttonCallback(self,name):
        print "Button pressed"
    
    def _show_params(self,name):
        self.vs.print_vars()
         

if __name__ == '__main__':
    print "who's calling validplugin in this odd way?"

