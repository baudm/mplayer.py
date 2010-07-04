#!/usr/bin/env python
# $Id: setup.py 361 2008-01-24 11:01:55Z darwin $

from distutils.core import setup

from pymplayer import __version__


setup(
    name='PyMPlayer',
    version=__version__,
    description='Thin, out-of-source wrapper and client/server for MPlayer',
    author='Darwin M. Bautista',
    author_email='djclue917@gmail.com',
    url='http://unplug.eee.upd.edu.ph/pymplayer/',
    license='GPL & LGPL',
    py_modules=['pymplayer'],
    platforms=['POSIX'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console :: Curses',
        'Environment :: No Input/Output (Daemon)',
        'Environment :: X11 Applications',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Topic :: Internet',
        'Topic :: Multimedia :: Video :: Display',
        'Topic :: Software Development :: Libraries :: Python Modules']
)
