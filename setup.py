#!/usr/bin/env python

import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

from mplayer import __version__


setuptools.setup(
    name='mplayer.py',
    version=__version__,
    description='Lightweight and dynamic MPlayer wrapper with a Pythonic API',
    author='Darwin M. Bautista',
    author_email='djclue917@gmail.com',
    url='https://github.com/baudm/mplayer.py',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: GTK',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Video :: Display',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
