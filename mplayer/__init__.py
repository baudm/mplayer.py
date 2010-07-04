# -*- coding: utf-8 -*-

"""Thin, out-of-source wrapper for MPlayer

Classes:

MPlayer -- provides a basic and low-level interface to MPlayer
AsyncMPlayer -- MPlayer subclass with asyncore integration (NOT for MS Windows)
GtkMPlayer -- provides a very basic (as of now) GTK2 widget that embeds MPlayer
"""


from mplayer.core import MPlayer
from mplayer.gtk2 import GtkMPlayer
import sys
if sys.platform != 'win32':
    from mplayer.async import AsyncMPlayer


__version__ = '0.5.0'
__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'
__all__ = ['MPlayer', 'GtkMPlayer']
if sys.platform != 'win32':
    __all__.append('AsyncMPlayer')
