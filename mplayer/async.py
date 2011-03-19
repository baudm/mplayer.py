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

from mplayer.core import Player
from mplayer import misc


__all__ = ['AsyncPlayer']


class AsyncPlayer(Player):
    """Player subclass with asyncore integration."""

    def __init__(self, args=(), stdout=PIPE, stderr=None, autospawn=True, socket_map=None):
        super(AsyncPlayer, self).__init__(args, autospawn=False)
        self._stdout = _StdoutWrapper(handle=stdout, socket_map=socket_map)
        self._stderr = _StderrWrapper(handle=stderr, socket_map=socket_map)
        if autospawn:
            self.spawn()


class _StderrWrapper(misc._StderrWrapper):

    def __init__(self, **kwargs):
        super(_StderrWrapper, self).__init__(**kwargs)
        self._socket_map = kwargs['socket_map']
        self._dispatcher = None

    def _attach(self, fobj):
        super(_StderrWrapper, self)._attach(fobj)
        self._dispatcher = _FileDispatcher(self)

    def _detach(self):
        self._dispatcher.close()
        super(_StderrWrapper, self)._detach()


class _StdoutWrapper(_StderrWrapper, misc._StdoutWrapper):
    pass


class _FileDispatcher(asyncore.file_dispatcher):
    """file_dispatcher-like class with blocking fd"""

    def __init__(self, file_wrapper):
        fd = file_wrapper._file.fileno()
        asyncore.file_dispatcher.__init__(self, fd, file_wrapper._socket_map)
        self.handle_read = file_wrapper._process_output
        # Set fd back to blocking mode since
        # a non-blocking fd causes problems with MPlayer.
        flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)

    def writable(self):
        return False


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
