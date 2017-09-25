DXF2GCODE: 2D drawings to CNC machine compatible G-Code converter
=================================================================


Getting Started
---------------
These instructions will guide you how to compile install and run the project
on your local machine for system-wide installation as well as for development
and testing purposes.


Prerequisites
-------------

- Unix machines:
  - Build dependencies:
    - /usr/bin/python3 and development package (>=3.5),
    - PyQt5 (>=5.7),
    - PyOpenGL (>=3.1),
    - /usr/bin/lrelease-qt5 or /usr/bin/lrelease5 or /usr/bin/lrelease,
    - /usr/bin/pylupdate5,
    - /usr/bin/pyuic5,
    - /usr/bin/pyrcc5

  - Runtime dependencies:
    - /usr/bin/python3 (>=3.5),
    - PyQt5 (>=5.7),
    - PyOpenGL (>=3.1),
    - /usr/bin/pdftops (>=0.45),
    - /usr/bin/pstoedit (>=3.70).

    Note: Depending you used operating system flavour different package names
    might provides required dependencies. Please use package manager to retrieve
    those names (e.g. on Fedora Linux use: $ dnf provides /usr/bin/python3).

- Windows machine
  - Build dependencies:
    - python3 (>=3.6.2),
    - setuptools (>=28.8.0),
    - sip     (>=4.19.3),
    - pip     (>=9.0.1),
    - PyQt5   (>=5.9),
    - PyOpenGL (>=3.1),
    - pyqt5-tools (>=5.9.0.1.2),
    - cx-Freeze   (>=5.0.2).

    Python 3 should be installed from: https://www.python.org/downloads/,
    during installation pip package should be installed which should install
    sip, and setuptools packages. Using pip remaining python dependencies like:
    PyQt5, PyOpenGL, pyqt5-tools and cx-Freeze should be installed.

  - Runtime dependencies:
    - python3 (>=3.6.2),
    - PyQt5 (>=5.9),
    - PyOpenGL (>=3.1),
    - pdftops (>=4.00) [http://www.xpdfreader.com/download.html] (Xpdf-tools package),
    - pstoedit (>=3.70) [https://sourceforge.net/projects/pstoedit/],
    - gswin32c (>=9.09) [https://sourceforge.net/projects/ghostscript/].

    Note: if gswin32c is not on the PATH then -gs option needs to be added to
    pstoedit tool in Options->Configuration->Software config->pstoedit
    e.g.: -gs, C:/Program Files (x86)/gs/gs9.09/bin/gswin32c.exe
    (above assumes v9.09 and default path installation).

    Note(2): pstoedit needs C++ runtime libraries if you don't have it please search for:
    "Microsoft Visual C++ 2010 Redistributable Package (x64)" and install it.
    It is recommended to run both pdftops and pstoedit from command line (CMD)
    to verify the installation correctness.


Building and Installing
-----------------------
  - Unix (assumes bash shell):
    $ ./make_tr.py     # generates .qm translation files in i18 directory
    $ ./make_py_uic.py # generates: dxf2gcode_ui5.py and dxf2gcode_images.qrc
    $ python3 ./st-setup.py build
    # python3 ./st-setup.py install
    $ dxf2gcode

    Note(1): depending on used desktop environment you might need to run:
    # /bin/touch --no-create /usr/share/icons/hicolor
    and/or re-login to make application’s shortcut appears in the system menu.

    Note(2): On Fedora Linux distribution (version >=26) dxf2gode can be
    installed directly either by using: dnf install dxf2gcode or from
    your preferred graphical package manager (e.g. GNOME Software)
    (see also: https://src.fedoraproject.org/rpms/dxf2gcode).

  - Windows (assumes python.exe v3 is on PATH):
    python.exe ./make_tr.py
    python.exe ./make_py_uic.py
    python.exe setup.py bdist_msi
    Install DXF2GCODE-<version>-win32.msi (located in dist sub-directory).
    Launch it from Start Menu by typing: dxf2gcode

  - macOS (not tested at all):
    $ python3 ./make_tr.py
    $ python3 ./make_py_uic.py
    $ python3 ./setup.py bdist_dmg # this should create Mac disk image


Configuration
-------------
  - Unix, Windows:
    Basic configuration requires verification of location of pdftops and
    pstoedit executables in menu Options->Configuration-Software config.

  - Configuration files are stored on all platforms at the following directory:
        ~/.config/dxf2gcode

    Alternatively the following python code can be used to determine it as well:
        import os; print(os.path.join(os.path.expanduser("~"),
        ".config/dxf2gcode").replace("\\", "/"))

  - Additional information can be found in the projects' wiki page at:
    https://sourceforge.net/p/dxf2gcode/wiki/Home/


Development
-----------

  - Development:
    For development/debugging purposes you may run the program directly from
    the source code directory by typing (depending on operating system):
      - Unix: $ python3 ./dxf2gcode
      - Windows: python.exe ./dxf2gcode

  - New releases:
    - Source tarball (for both Unix and Windows) can be prepared by running:
    $ python3 ./st-setup.py sdist --formats=zip

  - Binary packages (installers) can be prepared either directly from checked
    out sources from git repository or based on previously generated source
    tarballs (see above: "Building and Installing" - build part).


Contributing
------------
  More information can be found in the projects' wiki page at:
  https://sourceforge.net/p/dxf2gcode/wiki/Home/


Authors
-------
  Christian Kohlöffel,
  Jean-Paul Schouwstra,
  John Bradshaw,
  Vinzenz Schulz,
  Robert Lichtenberger.


License
-------
This project is licensed under the GPLv3 License - see the COPYING file for details.
