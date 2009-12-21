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
    Example dxf2gcode export plugin

    Michael Haberler  20.12.2009
'''

from varspace import  VarSpace
import globals as g

class Plugin(object):
    '''
     Plugin class variables:
            TAG - the short name (for tab riders, varspace subdir, varspace default prefix
            MENU_ENTRY - description for menu item
            DESCRIPTION -  verbose plugin description  (for user interface 'About)
            VERSION string
            SPECVERSION string
            SPECNAME  - variable and UI description   
    '''
    
    TAG =           'mill'
    MENU_ENTRY =    "milling exporter"
    DESCRIPTION =   'milling export plugin for DXF2gcode'
    VERSION =       '0.01'
    SPECVERSION =   '25'        # increment this whenever you edit SPECNAME
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
        # variables from the Variables section can be interpolated into
        # e.g. Label names
        
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

    def __init__(self):
        '''
        required but should not do anything clever
        real initialisation happens through initialize(self,...) which is 
        called as soon as the plugin looks syntactically OK
        '''
        pass
    
    def cleanup(self,remove=False):
        '''
        cleanup when deleting a plugin instance
        add any cleanup statements as needed
        '''
        g.logger.logger.info("cleanup plugin %s" %(self.vs.instance_name))

    
#    def initialize(self,parent,varspaces_path,instance_tag,pluginloader):
    def initialize(self,parent,varspace):
        
        self.vs = varspace
        
        # create parameter pane with instance edit, save button
        # parent is the notebook widget
        self.vs.create_pane(parent)
        # layout variables as per INI file
        self.vs.add_config_items()
        # manually add buttons at bottom
        self.vs.add_button("",_("Show variables"), self._show_params)
        # and display as notebook screen
        self.vs.display_pane(parent,self.vs.instance_name)
        

    def export(self,shapes):
        '''
        main export function 
        '''
        g.logger.logger.info("%s exporter() instance %s called",self.MENU_ENTRY,self.vs.instance_name)


#    def transform(self,shapes):
#        """
#        do some transformation on shapes and
#        return modified shapes
#        """
#        g.logger.logger.info("%s exporter() instance %s called",self.MENU_ENTRY,self.vs.instance_name)
#        return self.my_transform(shapes)

# ---- opional user defined functions
    def my_transform(self,shapes):
        """
        do some transformation on shapes
        and return the result as shapes
        """
        return shapes
    
    def _show_params(self,name):
        """ 
        demonstrate a button callback 
        """
        self.vs.print_vars()
                 