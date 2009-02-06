#!/usr/bin/env python
# -*- coding: utf-8 -*-
# $Id$
#
# Copyright (C) 2007-2008  UP EEEI Computer Networks Laboratory
# Copyright (C) 2007-2009  Darwin M. Bautista <djclue917@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""GTK-based PyMPlayer Client"""

try:
    import pygtk
    pygtk.require('2.0')
    import gtk.glade
    import gobject
    import pymplayer
    import asyncore
    from threading import Thread
except ImportError, msg:
    exit(msg)


class GTKClient(object):

    def __init__(self):
        self.client = None
        self.wTree = gtk.glade.XML('gtkclient.glade')
        self.statusbar = self.wTree.get_widget('statusbar')
        self.progress_bar = self.wTree.get_widget('progressbar')
        self.wTree.get_widget('window').show_all()
        self.wTree.signal_autoconnect(self)

    def quit(self, *args):
        self.disconnect()
        gtk.main_quit()

    def connect(self, *args):
        if self.client is not None:
            return
        self.client = pymplayer.Client()
        self.client.handle_data = self.handle_data
        self.client.connect('', 1025)
        t = Thread(target=asyncore.loop)
        t.setDaemon(True)
        t.start()
        self.timer = gobject.timeout_add(1000, self.query)
        self.paused = False
        self.time_length = None
        self.query_per_file()

    def disconnect(self, *args):
        if self.client is None:
            return
        self.client.send_command('quit')
        self.statusbar.set_text("")
        self.progress_bar.set_text("")
        self.progress_bar.set_fraction(0.0)
        gobject.source_remove(self.timer)
        self.client = None

    def refresh(self, *args):
        if self.client is not None:
            self.client.send_command('reload')

    def previous(self, *args):
        if self.client is not None:
            self.client.send_command('pt_step -1')

    def pause(self, *args):
        if self.client is None:
            return
        status = self.statusbar.get_text()
        if self.paused:
            self.timer = gobject.timeout_add(1000, self.query)
            self.statusbar.set_text(status.rstrip(' [PAUSED]'))
        else:
            gobject.source_remove(self.timer)
            self.statusbar.set_text("".join([status, ' [PAUSED]']))
        self.client.send_command('pause')
        self.paused = not self.paused

    def next(self, *args):
        if self.client is not None:
            self.client.send_command('pt_step +1')

    def query_per_file(self):
        if self.client is not None:
            self.client.send_command('get_file_name')
            self.client.send_command('get_time_length')

    def query(self):
        self.client.send_command('get_time_pos')
        return True

    def handle_data(self, data):
        if data.startswith("ANS_TIME_POSITION"):
            time = float(data.split('=')[1])
            self.set_progress(time)
            if int(time) in (0, int(self.time_length)):
                self.query_per_file()
        elif data.startswith("ANS_FILENAME"):
            filename = data.split('=')[1].strip("'")
            self.statusbar.set_text("".join(['Now playing: ', filename]))
        elif data.startswith("ANS_LENGTH"):
            self.time_length = float(data.split('=')[1])

    def seek(self, widget, event):
        x = event.get_coords()[0]
        width = widget.get_allocation().width
        percent = 100.0 * x / width
        self.client.send_command("seek %s 1" % (percent, ))
        self.query()

    def set_progress(self, time):
        if self.time_length is not None:
            minutes1, seconds1 = int(time / 60), int(time % 60)
            minutes2, seconds2 = int(self.time_length / 60), int(self.time_length % 60)
            self.progress_bar.set_text("%d:%02d / %d:%02d" % (minutes1, seconds1, minutes2, seconds2))
            self.progress_bar.set_fraction(time/self.time_length)


if __name__ == "__main__":
    gtk.gdk.threads_init()
    GTKClient()
    gtk.main()
