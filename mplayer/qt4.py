# -*- coding: utf-8 -*-
# $Id$
#
# Copyright (C) 2010  Darwin M. Bautista <djclue917@gmail.com>
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

from PyQt4 import QtCore, QtGui

from mplayer.core import MPlayer


__all__ = ['QtMPlayer', 'QtMPlayerWidget']


class QtMPlayer(MPlayer):
    """QtMPlayer(args=())

    MPlayer subclass with Qt integration.
    """

    def __init__(self, args=()):
        super(QtMPlayer, self).__init__(args)
        self._notifiers = []

    def start(self, stdout=None, stderr=None):
        retcode = super(QtMPlayer, self).start(stdout, stderr)
        if self._stdout._file is not None:
            sn = QtCore.QSocketNotifier(self._stdout.fileno(),
                QtCore.QSocketNotifier.Read)
            sn.activated.connect(self._stdout)
            self._notifiers.append(sn)
        if self._stderr._file is not None:
            sn = QtCore.QSocketNotifier(self._stderr.fileno(),
                QtCore.QSocketNotifier.Read)
            sn.activated.connect(self._stderr)
            self._notifiers.append(sn)
        return retcode

    def quit(self, retcode=0):
        for sn in self._notifiers:
            sn.setEnabled(False)
        self._notifiers = []
        return super(QtMPlayer, self).quit(retcode)


class QtMPlayerWidget(QtGui.QX11EmbedContainer):

    complete = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(QtMPlayerWidget, self).__init__(parent)
        self._mplayer = QtMPlayer(['-idx', '-fs', '-osdlevel', '0',
            '-really-quiet', '-msglevel', 'global=6', '-fixed-vo',
            '-wid', str(self.winId())])
        self._mplayer.stdout.hook(self._handle_data)
        self._mplayer.start()
        self.source = ''
        self.destroyed.connect(self._on_destroy)

    def __del__(self):
        self._on_destroy()

    def _on_destroy(self, *args):
        self._mplayer.quit()

    def _handle_data(self, data):
        if data.startswith('EOF code'):
            self.complete.emit()

    def pause(self):
        self._mplayer.command('pause')

    def play(self):
        if self.source:
            self._mplayer.command('loadfile', self.source)


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    w = QtGui.QWidget()
    w.resize(640, 480)
    w.setWindowTitle('QtMPlayer')
    w.destroyed.connect(app.quit)
    m = QtMPlayerWidget(w)
    m.source = sys.argv[1]
    m.resize(640, 480)
    w.show()
    m.play()
    sys.exit(app.exec_())
