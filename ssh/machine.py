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
"""
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose:  TBD

@author: Michael Haberler 
@since:  23.12.2009
@license: GPL
"""


from varspace import  VarSpace
import globals as g
import constants as c

class Plugin(VarSpace):




    def __init__(self):
        
        self.shapeset_handlers = {}
        self.DESCRIPTION =   'machine settings'
        self.VERSION =       '0.01'
        self.CLONABLE = False
        """ just one instance of this plugin may exist"""
        self.HIDDEN_AT_STARTUP = False
        """ displayed at startup """
        self.SPECVERSION =   3
        self.SPECNAME = str('''
        # do not edit the following section name:
            [Version]
        
            # do not edit the following value:
            specversion =  integer(default='''  + 
            str(self.SPECVERSION) + ''')
    
            
            [''' + c.VARIABLES +
            
            ''']
            
            tool_dia = float(default=63.0)
            start_radius = float(default=0.0)
            
            axis3_safe_margin = float(default=20.0)
            axis3_slice_depth = float(default=0.5)
            axis3_mill_depth = float(default=10.0)
            
            f_g1_depth = float(default=50.0)
            f_g1_plane = float(default=150.0)       
            
            ax1_letter = string(default='X')
            ax2_letter = string(default='Y')
            ax3_letter = string(default='Z')
                           
            [''' + c.UI_VARIABLES +
            ''']
            
            
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
                
            [[Axis]]
                ax1_letter = string_list(default=list('Axis 1:','X', 'Y', 'Z','A','B','C','U','V','W'))
                ax2_letter = string_list(default=list('Axis 2:','X', 'Y', 'Z','A','B','C','U','V','W'))
                ax3_letter = string_list(default=list('Axis 3:','X', 'Y', 'Z','A','B','C','U','V','W'))
    
        ''').splitlines()
        """ format, type and default value specification of the global config file"""
            
            
    def cleanup(self):
        g.logger.logger.debug("cleanup plugin %s" %(self.instance_name))

    def initialize(self):

        self.create_pane()
        self.add_config_items()
        self.display_pane(self.instance_name)
        return True


