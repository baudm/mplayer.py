#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject
import pymplayer
from threading import Thread


class GTKClient(object):

    def __init__(self):
        self.paused = False
        self.time_length = None
        self.client = pymplayer.Client()
        self.client.handle_data = self.handle_data
        self.wTree = gtk.glade.XML('client.glade')
        self.statusbar = self.wTree.get_widget('statusbar')
        self.progress_bar = self.wTree.get_widget('progressbar')
        self.wTree.get_widget('window').show_all()
        self.wTree.signal_autoconnect(self)
        self.client.connect('', 50001)
        self.timer = gobject.timeout_add(1000, self.query)
        self.query_per_file()

    def quit(self, *args):
        self.client.close()
        gobject.source_remove(self.timer)
        gtk.main_quit()

    def previous(self, *args):
        self.client.send_command('pt_step -1')

    def pause(self, *args):
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
        self.client.send_command('pt_step +1')

    def query_per_file(self):
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


gobject.threads_init()
g = GTKClient()
t = Thread(target=pymplayer.loop)
t.setDaemon(True)
t.start()
gtk.main()
