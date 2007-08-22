#!/usr/bin/env python

"""MPlayer remote control server
"""

__version__ = "$Revision: 42 $"
# $Source$

__copyright__ = """
Copyright (C) 2007  The MA3X Project (http://bbs.eee.upd.edu.ph)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


host = ''
port = 50001
max_connections = 2


try:
  import sys
  import socket
  import cPickle
  import re
  from threading import Thread
  from optparse import OptionParser

  from pymplayer import MPlayer
except ImportError, msg:
  exit(msg)


# Current number of client connections (global)
# FIXME: implement this in a more elegant way
curr_conns = 0

# based on: http://www.devshed.com/c/a/Python/Basic-Threading-in-Python/1/
class ClientThread(Thread):
  """
  Thread for handling a client connection
  usage: ClientThread(mplayer, channel, details).start()
  The thread finishes after the connection is closed by the client
  """

  # Override Thread's __init__ method to accept the parameters needed:
  def __init__(self, mplayer, channel, details):
    self._mplayer = mplayer
    self.channel = channel
    self.details = details
    Thread.__init__(self)

  def run(self):
    global curr_conns

    print "Remote host %s connected at port %d" % self.details
    # Count this connection
    curr_conns += 1
    # RegExp for "quit" command in MPlayer
    quit_cmd = re.compile('^(qu?|qui?|quit?)( ?| .*)$')

    while self._mplayer.isrunning():
      # Receive command from the client then unpickle it
      try:
        cmd = cPickle.loads( self.channel.recv(1024) )
      except socket.error, msg:
        print >> sys.stderr, msg[1]
        break
      except EOFError, msg:
        print >> sys.stderr, msg
        break

      # Restrict client from terminating MPlayer
      if quit_cmd.match(cmd.lower()):
        # Remote client closed the connection
        break
      elif cmd.lower() == "reload":
        # Get list of playlists
        playlists = self._mplayer.playlists()

        for playlist in playlists:
          if playlists.index(playlist) == 0:
            # First playlist, just load it! :D
            self._mplayer.command("".join(['loadlist ', playlist]))
          else:
            # 2nd to nth playlist, append it (take note of the '+' sign!)
            self._mplayer.command("".join(['loadlist ', playlist, ' +1']))
      else:
        # Send the command to MPlayer
        self._mplayer.command(cmd)

    # Close the connection
    try:
      self.channel.shutdown(socket.SHUT_RDWR)
      self.channel.close()
    except socket.error, msg:
      print >> sys.stderr, msg[1]

    curr_conns -= 1
    print "Connection closed: %s at port %d" % self.details


def start_server(queue=1):
  """
  Starts the server
  """
  try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  except socket.error, msg:
    sys.exit(msg[1])

  try:
    #Set option to re-use the address to prevent "Address already in use" errors
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((host, port))
    server.listen(queue)
  except socket.error, msg:
    server.close()
    sys.exit(msg[1])

  return server


def main():
  global curr_conns, port, max_connections

  sv_ver = "".join(['%prog ', __version__])

  parser = OptionParser(version=sv_ver)

  parser.add_option("-m", "--max-connections", dest="max_connections", metavar="N", help="Maximum number of simultaneous connections")
  parser.add_option("-p", "--port", dest="port", help="server port to connect to")

  (options, args) = parser.parse_args()

  if options.max_connections is not None:
    max_connections = options.max_connections

  if options.port is not None:
    port = options.port

  # MPlayer instance
  try:
    mplayer = MPlayer(sys.argv[1:])
  except OSError, msg:
    sys.exit(msg)

  # The server
  server = start_server()

  print "".join(['server.py ', __version__])

  while mplayer.isrunning():
    try:
      print "Waiting for connection..."
      # Wait for connection from client
      (conn, addr) = server.accept()

      if curr_conns < max_connections:
        # Start separate client thread to handle connection
        ClientThread(mplayer, conn, addr).start()
      else:
        conn.close()
        print "Connection rejected: max number of connections reached"

    except KeyboardInterrupt:
      break

  del mplayer
  server.close()
  sys.exit("Caught signal. Terminated.")


if __name__ == "__main__":
  main()
