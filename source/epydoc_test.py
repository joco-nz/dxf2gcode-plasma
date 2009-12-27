#!/usr/bin/python
# coding: utf-8

if __name__ == '__main__':
    import sys
    from epydoc.cli import cli
    modules = ['dxf2gcode_b02','geoent_arc']
    sys.argv = ["epydoc.py", "--html",
    "--output", 
    "test_html"
    ] + sys.argv[1:]
    sys.argv += modules
    cli()
