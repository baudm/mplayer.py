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

import gtk
import gobject

from mplayer.core import Player


__all__ = ['GPlayer', 'GtkPlayerView']


class GPlayer(Player):
    """Player subclass with GTK/GObject integration."""

    def __init__(self, args=(), stdout=PIPE, stderr=None, autospawn=True):
        self._tags = []
        super(GPlayer, self).__init__(args, stdout, stderr, autospawn)

    def spawn(self):
        retcode = super(GPlayer, self).spawn()
        if self._stdout._file is not None:
            tag = gobject.io_add_watch(self._stdout.fileno(),
                gobject.IO_IN | gobject.IO_PRI, self._stdout.publish)
            self._tags.append(tag)
        if self._stderr._file is not None:
            tag = gobject.io_add_watch(self._stderr.fileno(),
                gobject.IO_IN | gobject.IO_PRI, self._stderr.publish)
            self._tags.append(tag)
        return retcode

    def quit(self, retcode=0):
        map(gobject.source_remove, self._tags)
        self._tags = []
        return super(GPlayer, self).quit(retcode)


class GtkPlayerView(gtk.Socket):

    __gsignals__ = {
        'complete': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        super(GtkPlayerView, self).__init__()
        self._mplayer = GPlayer(['-idx', '-fs', '-osdlevel', '0',
            '-really-quiet', '-msglevel', 'global=6', '-fixed-vo'], autospawn=False)
        self._mplayer.stdout.hook(self._handle_data)
        self.connect('destroy', self._on_destroy)
        self.connect('hierarchy-changed', self._on_hierarchy_changed)

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

    def _on_hierarchy_changed(self, *args):
        if self.parent is not None:
            self._mplayer.args += ['-wid', str(self.get_id())]
            self._mplayer.spawn()
        else:
            self._on_destroy()

    def _on_destroy(self, *args):
        self._mplayer.quit()

    def _handle_data(self, data):
        if data.startswith('EOF code'):
            self.emit('complete')


# Register as a PyGTK type.
gobject.type_register(GtkPlayerView)


if __name__ == '__main__':
    import sys

    w = gtk.Window()
    w.set_size_request(640, 480)
    w.set_title('GtkPlayer')
    w.connect('destroy', gtk.main_quit)
    p = GtkPlayerView()
    p.connect('complete', gtk.main_quit)
    w.add(p)
    w.show_all()
    p.loadfile(sys.argv[1])
    gtk.main()
