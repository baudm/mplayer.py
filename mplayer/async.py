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


__all__ = ['AsyncPlayer']


class AsyncPlayer(Player):
    """Player subclass with asyncore integration."""

    def __init__(self, args=(), stdout=PIPE, stderr=None, autospawn=True, socket_map=None):
        super(AsyncPlayer, self).__init__(args, stdout, stderr, False)
        self._stdout = _FileWithQueue()
        self._stderr = _File()
        self._map = socket_map
        self._fd = []
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
        if self._proc.stdout is not None:
            self._fd.append(_FileDispatcher(self._stdout, self._map).fileno())
        if self._proc.stderr is not None:
            self._stderr._attach(self._proc.stderr)
            self._fd.append(_FileDispatcher(self._stderr, self._map).fileno())
        return retcode

    def quit(self, retcode=0):
        try:
            socket_map = (self._map if self._map is not None else asyncore.socket_map)
        except AttributeError:
            socket_map = {}
        for fd in self._fd:
            if fd in socket_map:
                socket_map[fd].close()
        self._fd = []
        return super(AsyncPlayer, self).quit(retcode)


class _File(object):

    def __init__(self):
        self._file = None
        self._subscribers = []

    def _attach(self, fobj):
        self._file = fobj

    def _detach(self):
        self._file = None

    def _process_output(self):
        line = self._file.readline().decode().rstrip()
        if line:
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


class _FileWithQueue(_File):

    def _attach(self, fobj):
        super(_FileWithQueue, self)._attach(fobj)
        self._answers = queue.Queue()

    def _process_output(self):
        line = self._file.readline().decode().rstrip()
        if line.startswith('ANS_'):
            self._answers.put_nowait(line)
        elif line:
            for subscriber in self._subscribers:
                subscriber(line)


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
