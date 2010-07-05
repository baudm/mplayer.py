# -*- coding: utf-8 -*-

"""Lightweight, out-of-source wrapper for MPlayer

Classes:

MPlayer -- provides a basic and low-level interface to MPlayer
AsyncMPlayer -- MPlayer subclass with asyncore integration (POSIX only)
GtkMPlayer -- provides a basic (as of now) PyGTK widget that embeds MPlayer
QtMPlayer -- provides a PyQt4 widget similar to GtkMPlayer in functionality
"""

__all__ = ['MPlayer']


from mplayer.core import MPlayer
try:
    from mplayer.async import AsyncMPlayer
except AttributeError: # asyncore.file_dispatcher is undefined in non-POSIX
    pass
else:
    __all__.append('AsyncMPlayer')
try:
    from mplayer.gtk2 import GtkMPlayer
except ImportError: # PyGTK not available
    pass
else:
    __all__.append('GtkMPlayer')
try:
    from mplayer.qt4 import QtMPlayer
except ImportError: # PyQt4 not available
    pass
else:
    __all__.append('QtMPlayer')


__version__ = '0.5.0'
__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'
