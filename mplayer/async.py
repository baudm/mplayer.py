# -*- coding: utf-8 -*-
# $Id$
#
# Copyright (C) 2008-2010  Darwin M. Bautista <djclue917@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import fcntl
import asyncore

from mplayer.core import MPlayer, _File


__all__ = ['AsyncMPlayer']


class AsyncMPlayer(MPlayer):
    """AsyncMPlayer(args=())

    MPlayer subclass with asyncore integration.
    Use this in conjuction with asyncore.loop() (or a similar function)
    """

    def __init__(self, args=()):
        super(AsyncMPlayer, self).__init__(args)
        self._stdout = _AsyncFile()
        self._stderr = _AsyncFile()

    def start(self, stdout=None, stderr=None):
        if super(AsyncMPlayer, self).start(stdout, stderr):
            self._stdout._asyncore_add()
            self._stderr._asyncore_add()

    def quit(self, retcode=0):
        self._stdout._asyncore_del()
        self._stderr._asyncore_del()
        super(AsyncMPlayer, self).quit(retcode)


class _FileDispatcher(asyncore.file_dispatcher):
    """file_dispatcher-like class with blocking fd"""

    def __init__(self, fd, callback):
        asyncore.file_dispatcher.__init__(self, fd)
        # Set fd back to blocking mode since
        # a blocking fd causes problems with MPlayer.
        flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
        flags &= ~os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, flags)
        self.handle_read = callback


class _AsyncFile(_File):

    def __init__(self):
        super(_AsyncFile, self).__init__()
        self._fd = None

    def _asyncore_add(self):
        self._asyncore_del()
        if self._file is not None:
            self._fd = _FileDispatcher(self._file.fileno(),
                self.publish).fileno()

    def _asyncore_del(self):
        if self._fd in asyncore.socket_map:
            del asyncore.socket_map[self._fd]


if __name__ == '__main__':
    import sys
    import signal

    def handle_data(data):
        print('mplayer: %s' % (data, ))

    player = AsyncMPlayer()
    player.args = sys.argv[1:]
    player.stdout.attach(handle_data)
    player.start()

    signal.signal(signal.SIGTERM, lambda s, f: player.quit())
    signal.signal(signal.SIGINT, lambda s, f: player.quit())
    asyncore.loop()
