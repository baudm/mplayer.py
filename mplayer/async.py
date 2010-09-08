# -*- coding: utf-8 -*-
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

from mplayer.core import Player


__all__ = ['AsyncPlayer']


class AsyncPlayer(Player):
    """AsyncPlayer(args=(), socket_map=None)

    Player subclass with asyncore integration.
    """

    def __init__(self, args=(), socket_map=None):
        super(AsyncPlayer, self).__init__(args)
        self._fd = []
        self._map = socket_map

    def start(self, stdout=None, stderr=None):
        retcode = super(AsyncPlayer, self).start(stdout, stderr)
        if self._stdout._file is not None:
            self._fd.append(_FileDispatcher(self._stdout, self._map).fileno())
        if self._stderr._file is not None:
            self._fd.append(_FileDispatcher(self._stderr, self._map).fileno())
        return retcode

    def quit(self, retcode=0):
        socket_map = (self._map if self._map is not None else asyncore.socket_map)
        try:
            map(socket_map.pop, self._fd)
        except KeyError:
            pass
        self._fd = []
        return super(AsyncPlayer, self).quit(retcode)


class _FileDispatcher(asyncore.file_dispatcher):
    """file_dispatcher-like class with blocking fd"""

    def __init__(self, file_wrapper, socket_map):
        self.handle_read = file_wrapper
        fd = file_wrapper.fileno()
        asyncore.file_dispatcher.__init__(self, fd, socket_map)
        # Set fd back to blocking mode since
        # a blocking fd causes problems with MPlayer.
        flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)


if __name__ == '__main__':
    import sys

    player = AsyncPlayer()
    player.args = ['-really-quiet', '-msglevel', 'global=6'] + sys.argv[1:]

    def handle_data(data):
        if not data.startswith('EOF code'):
            print('log: %s' % (data, ))
        else:
            player.quit()

    player.stdout.hook(handle_data)
    player.start()
    asyncore.loop()
