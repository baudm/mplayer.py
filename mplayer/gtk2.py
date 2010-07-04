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


class GtkMPlayer(gtk.Socket):
    
    __gsignals__ = {
        'complete': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self):
        super(GtkMPlayer, self).__init__()
        self._mplayer = MPlayer(args=['-idx', '-fs', '-osdlevel', '0',
            '-really-quiet', '-msglevel', 'global=6', '-fixed-vo'])
        self._tag = None
        self.source = ''
        self.connect('show', self._on_show)
        self.connect('destroy', self._on_destroy)
        
    def _on_show(self, *args):
        if self.get_id():
            self._mplayer.args += ['-wid', str(self.get_id())]
            self._mplayer.stdout.attach(self._handle_data)
            self._mplayer.start()
            fd = self._mplayer.stdout.fileno()
            cb = self._mplayer.stdout.publish
            self._tag = gobject.io_add_watch(fd, gobject.IO_IN|gobject.IO_PRI, cb)
    
    def _on_destroy(self, *args):
        if self._tag is not None:
            gobject.source_remove(self._tag)
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
gobject.type_register(GtkMPlayer)


if __name__ == '__main__':
    m = GtkMPlayer()
    m.source = '/path/to/video.mkv'
    w = gtk.Window()
    w.set_size_request(640, 480)
    def destroy(*args):
        gtk.main_quit()
    w.connect('destroy', destroy)
    w.add(m)
    w.show_all()
    m.play()
    gtk.main()
