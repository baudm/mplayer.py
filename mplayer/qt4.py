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


__all__ = ['QtPlayer', 'QPlayerView']


class QtPlayer(Player):
    """Player subclass with Qt integration."""

    def __init__(self, args=(), stdout=PIPE, stderr=None, autospawn=True):
        self._notifiers = []
        super(QtPlayer, self).__init__(args, stdout, stderr, autospawn)

    def spawn(self):
        retcode = super(QtPlayer, self).spawn()
        if self._stdout._file is not None:
            sn = QtCore.QSocketNotifier(self._stdout.fileno(),
                QtCore.QSocketNotifier.Read)
            sn.activated.connect(self._stdout.publish)
            self._notifiers.append(sn)
        if self._stderr._file is not None:
            sn = QtCore.QSocketNotifier(self._stderr.fileno(),
                QtCore.QSocketNotifier.Read)
            sn.activated.connect(self._stderr.publish)
            self._notifiers.append(sn)
        return retcode

    def quit(self, retcode=0):
        for sn in self._notifiers:
            sn.setEnabled(False)
        self._notifiers = []
        return super(QtPlayer, self).quit(retcode)


class QPlayerView(QtGui.QX11EmbedContainer):

    completed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(QPlayerView, self).__init__(parent)
        self._mplayer = QtPlayer(['-idx', '-fs', '-osdlevel', '0',
            '-really-quiet', '-msglevel', 'global=6', '-fixed-vo',
            '-wid', str(self.winId())])
        self._mplayer.stdout.hook(self._handle_data)
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

    def _handle_data(self, data):
        if data.startswith('EOF code'):
            self.completed.emit()


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
