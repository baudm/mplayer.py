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

import gtk
import gobject

from mplayer.core import MPlayer


__all__ = ['GtkMPlayer', 'GtkMPlayerWidget']


class GtkMPlayer(MPlayer):
    """GtkMPlayer(args=())

    MPlayer subclass with GTK+ integration.
    """

    def __init__(self, args=()):
        super(GtkMPlayer, self).__init__(args)
        self._tags = []

    def start(self, stdout=None, stderr=None):
        retcode = super(GtkMPlayer, self).start(stdout, stderr)
        if self._stdout._file is not None:
            tag = gobject.io_add_watch(self._stdout.fileno(),
                gobject.IO_IN | gobject.IO_PRI, self._stdout)
            self._tags.append(tag)
        if self._stderr._file is not None:
            tag = gobject.io_add_watch(self._stderr.fileno(),
                gobject.IO_IN | gobject.IO_PRI, self._stderr)
            self._tags.append(tag)
        return retcode

    def quit(self, retcode=0):
        map(gobject.source_remove, self._tags)
        self._tags = []
        return super(GtkMPlayer, self).quit(retcode)


class GtkMPlayerWidget(gtk.Socket):

    __gsignals__ = {
        'complete': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        super(GtkMPlayerWidget, self).__init__()
        self._mplayer = GtkMPlayer(args=['-idx', '-fs', '-osdlevel', '0',
            '-really-quiet', '-msglevel', 'global=6', '-fixed-vo'])
        self._mplayer.stdout.hook(self._handle_data)
        self.source = ''
        self.connect('destroy', self._on_destroy)
        self.connect('hierarchy-changed', self._on_hierarchy_changed)

    def __del__(self):
        self._on_destroy()

    def _on_hierarchy_changed(self, *args):
        if self.parent is not None:
            self._mplayer.args += ['-wid', str(self.get_id())]
            self._mplayer.start()
        else:
            self._on_destroy()

    def _on_destroy(self, *args):
        self._mplayer.quit()

    def _handle_data(self, data):
        if data.startswith('EOF code'):
            self.emit('complete')

    def pause(self):
        self._mplayer.command('pause')

    def play(self):
        if self.source:
            self._mplayer.command('loadfile', self.source)


# Register as a PyGTK type.
gobject.type_register(GtkMPlayerWidget)


if __name__ == '__main__':
    import sys

    w = gtk.Window()
    w.set_size_request(640, 480)
    w.set_title('GtkMPlayer')
    w.connect('destroy', gtk.main_quit)
    m = GtkMPlayerWidget()
    m.source = sys.argv[1]
    w.add(m)
    w.show_all()
    m.play()
    gtk.main()
