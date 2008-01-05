#!/usr/bin/env python
# $Id$

from distutils.core import setup

from pymplayer import __version__


setup(
    name='PyMPlayer',
    version=__version__,
    description='MPlayer wrapper for Python',
    long_description='MPlayer wrapper for Python',
    author='Darwin M. Bautista',
    author_email='djclue917@gmail.com',
    url='http://bbs.eee.upd.edu.ph/',
    license='LGPL3',
    py_modules=['pymplayer'],
    scripts=['server.py', 'client.py']
)
