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

"""PyMPlayer Server Daemon"""

import sys
import socket
import signal
import pymplayer


def main():
    player = pymplayer.MPlayer()
    try:
        server = pymplayer.Server(player, 1025)
    except socket.error, msg:
        sys.exit(msg)

    def handle_data(data):
        print 'mplayer: ', data

    player.args = sys.argv[1:]
    player.stdout.add_handler(handle_data)
    player.start()

    def term(*args):
        server.stop()
        player.quit()

    signal.signal(signal.SIGTERM, term)
    signal.signal(signal.SIGINT, term)
    pymplayer.loop()


if __name__ == '__main__':
    main()
