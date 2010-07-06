# -*- coding: utf-8 -*-

"""Lightweight, out-of-source wrapper for MPlayer

Classes:

MPlayer -- provides a basic and low-level interface to MPlayer
AsyncMPlayer -- MPlayer subclass with asyncore integration (POSIX only)
GtkMPlayer -- provides a basic (as of now) PyGTK widget that embeds MPlayer
QtMPlayer -- provides a PyQt4 widget similar to GtkMPlayer in functionality
"""

__version__ = '0.5.0'
__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'
__all__ = ['MPlayer']


from mplayer.core import MPlayer
try:
    from mplayer.async import AsyncMPlayer
except ImportError: # fcntl unavailable in non-Unix systems
    pass
else:
    __all__.append('AsyncMPlayer')
