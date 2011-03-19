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

from subprocess import PIPE

from PyQt4 import QtCore, QtGui

from mplayer.core import Player
from mplayer import misc


__all__ = ['QtPlayer', 'QPlayerView']


class QtPlayer(Player):
    """Player subclass with Qt integration."""

    def __init__(self, args=(), stdout=PIPE, stderr=None, autospawn=True):
        super(QtPlayer, self).__init__(args, autospawn=False)
        self._stdout = _StdoutWrapper(handle=stdout)
        self._stderr = _StderrWrapper(handle=stderr)
        if autospawn:
            self.spawn()


class QPlayerView(QtGui.QX11EmbedContainer):

    eof_next_entry = QtCore.pyqtSignal()
    eof_prev_entry = QtCore.pyqtSignal()
    eof_next_src = QtCore.pyqtSignal()
    eof_prev_src = QtCore.pyqtSignal()
    eof_up_next = QtCore.pyqtSignal()
    eof_up_prev = QtCore.pyqtSignal()
    eof_stop = QtCore.pyqtSignal()
    _eof_map = {
        '1': 'eof_next_entry', '-1': 'eof_prev_entry',
        '2': 'eof_next_src', '-2': 'eof_prev_src',
        '3': 'eof_up_next', '-3': 'eof_up_prev',
        '4': 'eof_stop'
    }

    def __init__(self, parent=None):
        super(QPlayerView, self).__init__(parent)
        self._mplayer = QtPlayer(['-idx', '-fs', '-osdlevel', '0',
            '-really-quiet', '-msglevel', 'global=6', '-fixed-vo',
            '-wid', self.winId()])
        self._mplayer.stdout.connect(self._handle_data)
        self.destroyed.connect(self._on_destroy)

    def __getattr__(self, name):
        # Don't expose some properties
        if name in ['args', 'spawn', 'quit']:
            # Raise an AttributeError
            return self.__getattribute__(name)
        try:
            attr = getattr(self._mplayer, name)
        except AttributeError:
            # Raise an AttributeError
            return self.__getattribute__(name)
        else:
            return attr

    def _on_destroy(self):
        self._mplayer.quit()

    def _handle_data(self, data):
        if data.startswith('EOF code:'):
            code = data.partition(':')[2].strip()
            signal = getattr(self, self._eof_map[code])
            signal.emit()


class _StderrWrapper(misc._StderrWrapper):

    def __init__(self, **kwargs):
        super(_StderrWrapper, self).__init__(**kwargs)
        self._notifier = None

    def _attach(self, fobj):
        super(_StderrWrapper, self)._attach(fobj)
        self._notifier = QtCore.QSocketNotifier(self._file.fileno(),
            QtCore.QSocketNotifier.Read)
        self._notifier.activated.connect(self._process_output)

    def _detach(self):
        self._notifier.setEnabled(False)
        super(_StderrWrapper, self)._detach()


class _StdoutWrapper(_StderrWrapper, misc._StdoutWrapper):
    pass


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    w = QtGui.QWidget()
    w.resize(640, 480)
    w.setWindowTitle('QtPlayer')
    p = QPlayerView(w)
    p.eof_next_entry.connect(app.closeAllWindows)
    p.resize(640, 480)
    w.show()
    p.loadfile(sys.argv[1])
    sys.exit(app.exec_())
