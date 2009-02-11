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

"""PyMPlayer Client"""

__version__ = "$Revision$"


import os
import sys
import socket
import asyncore
from time import sleep
from threading import Thread
from optparse import OptionParser
import pymplayer
try:
    import curses
except ImportError:
    curses = None
else:
    command_map = {
        ord('q'): "quit", ord('Q'): "quit", 27: "quit",
        ord('p'): "pause", ord('P'): "pause", ord(' '): "pause",
        ord('m'): "mute", ord('M'): "mute",
        ord('f'): "vo_fullscreen", ord('F'): "vo_fullscreen",
        ord('o'): "osd", ord('O'): "osd",
        ord('r'): "reload", ord('R'): "reload",
        curses.KEY_LEFT: "seek -5",
        curses.KEY_RIGHT: "seek +5",
        curses.KEY_NPAGE: "pt_step -1",
        curses.KEY_PPAGE: "pt_step +1",
        curses.KEY_UP: "volume +2",
        curses.KEY_DOWN: "volume -2",
        curses.KEY_HOME: "seek 0 1",
        curses.KEY_END: "seek 100 1"}


MAX_CMD_LEN = 256


def init_ui(peername):
    stdscr = curses.initscr()

    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)

    stdscr.addstr("".join([os.path.basename(__file__), ' ', pymplayer.__version__, '+r', __version__.split()[1], '\n']))
    stdscr.addstr("Connected to %s at port %d\n" % peername)

    stdscr.addstr("\n     Controls:\n")
    stdscr.addstr("\t     Esc, q - quit\n")
    stdscr.addstr("\tspacebar, p - pause\n")
    stdscr.addstr("\t          m - mute\n")
    stdscr.addstr("\t          o - osd\n")
    stdscr.addstr("\t          f - fullscreen\n")
    stdscr.addstr("\t          r - restart MPlayer\n")
    stdscr.addstr("\t          : - input command\n")

    stdscr.addstr(3, 38, "\t        up - volume up\n")
    stdscr.addstr(4, 38, "\t      down - volume down\n")
    stdscr.addstr(5, 38, "\t      left - seek -5s\n")
    stdscr.addstr(6, 38, "\t     right - seek +5s\n")
    stdscr.addstr(7, 38, "\t      home - go to beginning of track\n")
    stdscr.addstr(8, 38, "\t       end - go to end of track\n")
    stdscr.addstr(9, 38, "\t   page up - next track\n")
    stdscr.addstr(10, 38, "\t page down - previous track\n")
    return stdscr


def end_ui(stdscr):
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()


def main():
    cl_usage = "%prog [OPTIONS] [COMMAND]"
    cl_ver = "".join(['%prog ', pymplayer.__version__, '+r', __version__.split()[1]])

    parser = OptionParser(usage=cl_usage, version=cl_ver)

    parser.add_option("-c", "--command", dest="command", help="send CMD to the MPlayer server", metavar='"CMD"')
    parser.add_option("-n", "--no-curses", dest="curses", default=True, action="store_false", help="don't use curses interface")
    parser.add_option("-H", "--host", dest="host", default="localhost", help="server to connect to")
    parser.add_option("-p", "--port", dest="port", type="int", help="server port to connect to")

    (options, args) = parser.parse_args()

    if curses is None:
        options.curses = False
    if not options.port:
        parser.error("specify port")
    if not options.curses and options.command is None:
        parser.error("not using curses but no command specified")

    client = pymplayer.Client()
    try:
        client.connect((options.host, options.port))
    except socket.gaierror, error:
        client.close()
        sys.exit(error[1])
    t = Thread(target=asyncore.loop)
    t.setDaemon(True)
    t.start()
    if not client.connected:
        print "Trying to connect..."
        attempts = 5
    while not client.connected and attempts:
        sleep(0.5)
        attempts -= 1
    try:
        # Check for connectivity by sending a blank string
        # (the Server won't respond to it anyway)
        client.send("")
    except socket.error, msg:
        sys.exit(msg[1])

    if options.curses and options.command is None:
        stdscr = init_ui(client.getpeername())
        # Just a string of spaces
        spaces = "         ".join(["         " for x in range(10)])

    while True:
        if options.curses and options.command is None:
            stdscr.addstr(12, 0, "Command: ")
            try:
                c = stdscr.getch()
            except KeyboardInterrupt:
                c = ord('q')
            if c == ord(':'):
                curses.echo()
                stdscr.addstr(12, 0, "".join(['Command: ', spaces]))
                try:
                    cmd = stdscr.getstr(12, 9, MAX_CMD_LEN)
                except KeyboardInterrupt:
                    cmd = ""
                curses.noecho()
            else:
                try:
                    cmd = command_map[c]
                except KeyError:
                    continue
            if c != ord(':'):
                stdscr.addstr(12, 9, "".join([cmd, spaces]))
                stdscr.move(12, 9)
        else:
            cmd = options.command
        # Zero-length command
        if not cmd:
            if options.curses and options.command is None:
                continue
            else:
                break

        try:
            if not client.send_command(cmd):
                break
        except socket.error, msg:
            break
        if options.command is not None:
            break

    if options.curses and options.command is None:
        end_ui(stdscr)

    client.close()

    try:
        print >> sys.stderr, msg
    except NameError:
        pass


if __name__ == "__main__":
    main()
