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


MPlayer Command Prefixes:

PAUSING
PAUSING_TOGGLE
PAUSING_KEEP
PAUSING_KEEP_FORCE
"""

__version__ = '0.6.0'
__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'
__all__ = [
    'PIPE',
    'STDOUT',
    'PAUSING',
    'PAUSING_TOGGLE',
    'PAUSING_KEEP',
    'PAUSING_KEEP_FORCE',
    'Player',
    'Step'
    ]

# Import here for convenience.
from subprocess import PIPE, STDOUT
from mplayer.core import *
