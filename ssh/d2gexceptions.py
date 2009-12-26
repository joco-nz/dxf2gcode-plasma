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

user defined exceptions

Michael Haberler  20.12.2009
'''


class BadConfigFileError(Exception):
    """
    syntax error in .cfg file
    """
class VersionMismatchError(Exception):
    """
    config file version doesnt match internal version
    """
    
class OptionError(Exception):
    """
    conflicting command line option
    """

class PluginError(Exception):
    """
    something went wrong during plugin loading or initialization
    """

class PathError(Exception):
    """
    typically an OSError during makedirs, with associated more detailed
    message
    """
