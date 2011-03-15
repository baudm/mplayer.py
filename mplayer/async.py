# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011  Darwin M. Bautista <djclue917@gmail.com>
#
# This file is part of PyMPlayer.
#
# PyMPlayer is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyMPlayer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with PyMPlayer.  If not, see <http://www.gnu.org/licenses/>.

import os
import fcntl
import asyncore
from subprocess import PIPE
try:
    import queue
except ImportError:
    import Queue as queue

from mplayer.core import Player
from mplayer import misc


__all__ = ['AsyncPlayer']


class AsyncPlayer(Player):
    """Player subclass with asyncore integration."""

    def __init__(self, args=(), stdout=PIPE, stderr=None, autospawn=True, socket_map=None):
        super(AsyncPlayer, self).__init__(args, stdout, stderr, False)
        smap = socket_map if socket_map is not None else asyncore.socket_map
        self._stdout = _StdOut(smap)
        self._stderr = _StdErr(smap)
        if autospawn:
            self.spawn()

    @property
    def stdout(self):
        """stdout of the MPlayer process"""
        return self._stdout

    @property
    def stderr(self):
        """stderr of the MPlayer process"""
        return self._stderr

    def spawn(self):
        retcode = super(AsyncPlayer, self).spawn()
        if self._proc.stderr is not None:
            self._stderr._attach(self._proc.stderr)
        return retcode

    def quit(self, retcode=0):
        if self._proc.stderr is not None:
            self._stderr._detach()
        return super(AsyncPlayer, self).quit(retcode)


class _StdErr(misc._StdErr):

    def __init__(self, socket_map):
        super(_StdErr, self).__init__()
        self._map = socket_map
        self._fd = None
        self._subscribers = []

    def _attach(self, fobj):
        super(_StdErr, self)._attach(fobj)
        self._fd = _FileDispatcher(self, self._map).fileno()

    def _detach(self):
        self._map[self._fd].close()
        super(_StdErr, self)._detach()

    def _publish(self, line):
        for subscriber in self._subscribers:
            subscriber(line)

    def connect(self, subscriber):
        if not hasattr(subscriber, '__call__'):
            # Raise TypeError
            subscriber()
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)

    def disconnect(self, subscriber=None):
        if subscriber is None:
            self._subscribers = []
        elif subscriber in self._subscribers:
            self._subscribers.remove(subscriber)


class _StdOut(_StdErr, misc._StdOut):

    pass


class _FileDispatcher(asyncore.file_dispatcher):
    """file_dispatcher-like class with blocking fd"""

    def __init__(self, file_wrapper, socket_map):
        self.handle_read = file_wrapper._process_output
        fd = file_wrapper._file.fileno()
        asyncore.file_dispatcher.__init__(self, fd, socket_map)
        # Set fd back to blocking mode since
        # a blocking fd causes problems with MPlayer.
        flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)


if __name__ == '__main__':
    import sys
    import time
    from threading import Thread

    player = AsyncPlayer(['-really-quiet', '-msglevel', 'global=6'] + sys.argv[1:], stderr=PIPE)

    # Called for every line read from stdout
    def handle_data(line):
        if not line.startswith('EOF code'):
            print('LOG: {0}'.format(line))
        else:
            player.quit()
    # Called for every line read from stderr
    def log_error(msg):
        print('ERROR: {0}'.format(msg))
    # Connect subscribers
    player.stdout.connect(handle_data)
    player.stderr.connect(log_error)

    # Print time_pos every 1.0 second, just to demonstrate multithreading
    def status(p):
        while p.is_alive():
            print('time_pos = {0}'.format(p.time_pos))
            time.sleep(1.0)
    t = Thread(target=status, args=(player,))
    t.daemon = True
    t.start()
    # Enter loop
    asyncore.loop()
