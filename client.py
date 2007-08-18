#!/usr/bin/env python

#
# pymplayer-client.py: MPlayer remote control client
#    Copyright (C) 2007  The MA3X Project
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


version = "0.6.0"

host = 'bbs.eee.upd.edu.ph'
port = 50001

# Max command length (number of characters)
max_cmd_length = 150


try:
  import socket
  import sys
  import curses
  import cPickle
  import re
  from optparse import OptionParser
except ImportError, msg:
  exit(msg)


def connect_client():
  try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((globals()['host'], globals()['port']))
  except socket.error, msg:
    sys.exit(msg[1])
  except KeyboardInterrupt:
    sys.exit("Connection interrupted")

  return client


def start_ui(client):
  stdscr = curses.initscr()

  curses.noecho()
  curses.cbreak()
  stdscr.keypad(1)

  stdscr.addstr("client.py "+globals()['version']+"\n")
  stdscr.addstr("Connected to %s at port %d\n" % client.getpeername())

  stdscr.addstr("\n   Controls:\n")
  stdscr.addstr("\t          q - quit\n")
  stdscr.addstr("\tp, spacebar - pause\n")
  stdscr.addstr("\t          m - mute\n")
  stdscr.addstr("\t          o - osd\n")
  stdscr.addstr("\t          f - fullscreen\n")
  stdscr.addstr("\t          r - reload playlists\n")
  stdscr.addstr("\t          : - input command\n")

  stdscr.addstr(3, 38, "\t       up - volume up\n")
  stdscr.addstr(4, 38, "\t     down - volume down\n")
  stdscr.addstr(5, 38, "\t     left - seek -5s\n")
  stdscr.addstr(6, 38, "\t    right - seek +5s\n")
  stdscr.addstr(7, 38, "\t     home - go to beginning of track\n")
  stdscr.addstr(8, 38, "\t      end - go to end of track\n")
  stdscr.addstr(9, 38, "\t  page up - next track\n")
  stdscr.addstr(10, 38, "\tpage down - previous track\n")

  return stdscr


def end_ui(stdscr):
  curses.nocbreak()
  stdscr.keypad(0)
  curses.echo()
  curses.endwin()


def main():
  cl_usage = "%prog [OPTIONS] [COMMAND]"
  cl_ver = "%prog "+version

  parser = OptionParser(usage=cl_usage, version=cl_ver)

  parser.add_option("-c", "--command", dest="command", help="send CMD to the MPlayer server", metavar="\"CMD\"")

  (options, args) = parser.parse_args()

  client = connect_client()

  if options.command == None:
    stdscr = start_ui(client)

  # Just a string of spaces
  spaces = "     ".join(["     " for x in range(1,10)])

  # get_* commands
  #get = re.compile("get_*")

  quit_cmd = re.compile('^(qu?|qui?|quit?)( ?| .*)$')

  while True:
    if options.command == None:
      stdscr.addstr(12, 0, "Command: ")

      try:
        c = stdscr.getch()
      except KeyboardInterrupt:
        c = ord('q')

      if c in (ord('q'), ord('Q')):
        cmd = "quit"
      elif c == ord(':'):
        curses.echo()
        stdscr.addstr(12, 0, "Command: "+spaces)
        try:
          cmd = stdscr.getstr(12, 9, globals()['max_cmd_length'])
        except KeyboardInterrupt:
          cmd = ""
        curses.noecho()
      elif c == curses.KEY_LEFT:
        cmd = "seek -5"
      elif c == curses.KEY_RIGHT:
        cmd = "seek +5"
      elif c in (ord('p'), ord('P'), ord(' ')):
        cmd = "pause"
      elif c == curses.KEY_NPAGE:
        cmd = "pt_step -1"
      elif c == curses.KEY_PPAGE:
        cmd = "pt_step +1"
      elif c == curses.KEY_UP:
        cmd = "volume +2"
      elif c == curses.KEY_DOWN:
        cmd = "volume -2"
      elif c in (ord('m'), ord('M')):
        cmd = "mute"
      elif c in (ord('f'), ord('F')):
        cmd = "vo_fullscreen"
      elif c in (ord('o'), ord('O')):
        cmd = "osd"
      elif c == curses.KEY_HOME:
        cmd = "seek 0 1"
      elif c == curses.KEY_END:
        cmd = "seek 100 1"
      elif c in (ord('r'), ord('R')):
        cmd = "reload"
      else:
        continue

      if c != ord(':'):
        stdscr.addstr(12, 9, cmd+spaces)
        stdscr.move(12, 9)
    else:
      cmd = options.command

    # Zero-length command
    if len(cmd) == 0:
      if options.command == None:
        continue
      else:
        break

    try:
      client.send( cPickle.dumps(cmd) )
    except socket.error:
      msg = "Connection lost"
      break

    if quit_cmd.match(cmd.lower()) or options.command != None:
      break

  #if get.match(cmd) != None:
  #  stdscr.addstr("Output: '"+client.recv(1024)+"'"+spaces)

  if options.command == None:
    end_ui(stdscr)

  client.close()

  try:
    print >> sys.stderr, msg
  except NameError:
    pass


if __name__ == "__main__":
  main()
