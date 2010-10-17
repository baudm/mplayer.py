# -*- coding: utf-8 -*-

"""Lightweight, out-of-source wrapper for MPlayer

Classes:

Player -- provides a basic and low-level interface to MPlayer
AsyncPlayer -- Player subclass with asyncore integration (POSIX only)
GPlayer -- Player subclass with GTK/GObject integration
QtPlayer -- Player subclass with Qt integration
GtkPlayerView -- provides a basic (as of now) PyGTK widget that embeds MPlayer
QPlayerView -- provides a PyQt4 widget similar to GtkPlayerView in functionality

Constants:

PIPE -- subprocess.PIPE, provided here for convenience
STDOUT -- subprocess.STDOUT, provided here for convenience
"""

__version__ = '0.6.0'
__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'
__all__ = ['PIPE', 'STDOUT', 'Player', 'StepSize']


# Import here for convenience.
from subprocess import PIPE, STDOUT

from mplayer.core import Player, StepSize
