mplayer.py: Lightweight and dynamic MPlayer wrapper with a Pythonic API

mplayer.py provides several classes for easily using MPlayer in Python.

* Features

  - Pythonic interfaces to MPlayer
  - Full support for MPlayer commands and properties (generated at runtime)
  - asyncore, PyGTK, and PyQt integration
  - MS Windows support
  - Python 3 compatibility

* Requirements

    - MPlayer >= 1.0rc3  http://www.mplayerhq.hu/
    - Python >= 2.6      http://www.python.org/

  Optional

    - PyGTK >= 2.12   http://www.pygtk.org/
    - PyQt >= 4.5    http://www.riverbankcomputing.co.uk/

* Installation

    To install (having made sure that the dependencies are installed and
    working) do (as root normally):

        python setup.py install

    (You can optionally provide a prefix using the following form,
    but if you do remember to setup PYTHONPATH accordingly)

        python setup.py install [--prefix=<prefix>]

* Documentation

    Consult the wiki pages at http://code.google.com/p/python-mplayer/

* Copyright and Licensing

    The mplayer.py package and submodules (mplayer/*.py) are released under
    the terms of LGPL 3. See LICENSE for the full license.

    mplayer.py is Copyright (C) 2007-2011  Darwin M. Bautista.

    The LGPL is Copyright (C) Free Software Foundation.

* Contact Info

    Project Page: http://code.google.com/p/python-mplayer/
    URL and download: http://pypi.python.org/pypi/mplayer.py/

    Author and Maintainer: Darwin M. Bautista <daruuin@gmail.com>
