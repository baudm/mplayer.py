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


class QtPlayer(Player, QtCore.QObject):
    """Player subclass with Qt integration."""

    stdout = QtCore.pyqtSignal(str)
    stderr = QtCore.pyqtSignal(str)

    def __init__(self, args=(), stdout=PIPE, stderr=None, autospawn=True):
        super(QtPlayer, self).__init__(args, stdout, stderr, False)
        self._stdout = _StdOut(self.stdout)
        self._stderr = _StdErr(self.stderr)
        if autospawn:
            self.spawn()

    def spawn(self):
        retval = super(QtPlayer, self).spawn()
        if self._proc.stderr is not None:
            self._stderr._attach(self._proc.stderr)
        return retval

    def quit(self, retcode=0):
        if self._proc.stderr is not None:
            self._stderr._detach()
        return super(QtPlayer, self).quit(retcode)


class QPlayerView(QtGui.QX11EmbedContainer):

    completed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(QPlayerView, self).__init__(parent)
        self._mplayer = QtPlayer(['-idx', '-fs', '-osdlevel', '0',
            '-really-quiet', '-msglevel', 'global=6', '-fixed-vo',
            '-wid', self.winId()])
        self._mplayer.stdout.connect(self._handle_data)
        @QtCore.pyqtSlot(QtCore.QObject)
        def on_destroy(obj):
            self._mplayer.quit()
        self.destroyed.connect(on_destroy)

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

    @QtCore.pyqtSlot(str)
    def _handle_data(self, data):
        if str(data).startswith('EOF code'):
            self.completed.emit()


class _StdErr(misc._BaseStdErr):

    def __init__(self, signal):
        super(_StdErr, self).__init__()
        self._publish = signal.emit
        self._notifier = None

    def _attach(self, fobj):
        super(_StdErr, self)._attach(fobj)
        self._notifier = QtCore.QSocketNotifier(self._file.fileno(),
            QtCore.QSocketNotifier.Read)
        self._notifier.activated.connect(self._process_output)

    def _detach(self):
        self._notifier.setEnabled(False)
        # FIXME: This doesn't work: super(_StdErr, self)._detach()
        misc._BaseStdErr._detach(self)


class _StdOut(_StdErr, misc._BaseStdOut):

    pass


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    w = QtGui.QWidget()
    w.resize(640, 480)
    w.setWindowTitle('QtPlayer')
    p = QPlayerView(w)
    p.completed.connect(app.closeAllWindows)
    p.resize(640, 480)
    w.show()
    p.loadfile(sys.argv[1])
    sys.exit(app.exec_())
