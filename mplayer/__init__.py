# -*- coding: utf-8 -*-

"""Thin, out-of-source wrapper for MPlayer

Classes:

MPlayer -- provides a basic and low-level interface to MPlayer
AsyncMPlayer -- MPlayer subclass with asyncore integration (POSIX only)
GtkMPlayer -- provides a basic (as of now) PyGTK widget that embeds MPlayer
QtMPlayer -- provides a PyQt4 widget similar to GtkMPlayer in functionality
"""


from mplayer.core import MPlayer
from mplayer.gtk2 import GtkMPlayer
from mplayer.qt4 import QtMPlayer
import os
if os.name == 'posix':
    from mplayer.async import AsyncMPlayer


__version__ = '0.5.0'
__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'
__all__ = ['MPlayer', 'GtkMPlayer', 'QtMPlayer']
if os.name == 'posix':
    __all__.append('AsyncMPlayer')
