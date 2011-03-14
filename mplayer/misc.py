# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2011  Darwin M. Bautista <djclue917@gmail.com>
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

try:
    import queue
except ImportError:
    import Queue as queue


__all__ = ['CmdPrefix']


class CmdPrefix(object):
    """MPlayer command prefixes"""

    NONE = ''
    PAUSING = 'pausing'
    PAUSING_TOGGLE = 'pausing_toggle'
    PAUSING_KEEP = 'pausing_keep'
    PAUSING_KEEP_FORCE = 'pausing_keep_force'


class _StdErr(object):

    def __init__(self):
        super(_StdErr, self).__init__()
        self._file = None

    def _attach(self, fobj):
        self._file = fobj

    def _detach(self):
        self._file = None

    def _publish(self, line):
        raise NotImplementedError('need to implement _publish()')

    def _process_output(self, *args):
        line = self._file.readline().decode().rstrip()
        if line:
            self._publish(line)
        return True


class _StdOut(_StdErr):

    def __init__(self):
        super(_StdOut, self).__init__()
        self._answers = None

    def _attach(self, fobj):
        super(_StdOut, self)._attach(fobj)
        self._answers = queue.Queue()

    def _detach(self):
        super(_StdOut, self)._detach()
        self._answers = None

    def _process_output(self, *args):
        line = self._file.readline().decode().rstrip()
        if line.startswith('ANS_'):
            self._answers.put_nowait(line)
        elif line:
            self._publish(line)
        return True
