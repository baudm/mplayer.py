# -*- coding: utf-8 -*-

"""Lightweight, out-of-source wrapper for MPlayer

Classes:

Player -- provides a basic and low-level interface to MPlayer
AsyncPlayer -- Player subclass with asyncore integration (POSIX only)
GtkPlayer -- provides a basic (as of now) PyGTK widget that embeds MPlayer
QtPlayer -- provides a PyQt4 widget similar to GtkPlayer in functionality

Constants:

PIPE -- subprocess.PIPE, provided here for convenience
STDOUT -- subprocess.STDOUT, provided here for convenience
"""

__version__ = '0.5.0'
__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'
__all__ = ['PIPE', 'STDOUT', 'Player']


# Import here for convenience.
from subprocess import PIPE, STDOUT

from mplayer.core import Player
try:
    from mplayer.async import AsyncPlayer
except ImportError: # fcntl unavailable in non-Unix systems
    pass
else:
    __all__.append('AsyncPlayer')
