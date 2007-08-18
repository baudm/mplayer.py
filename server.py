#!/usr/bin/env python

#
# pymplayer-server.py: MPlayer remote control server
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

host = ''
port = 50001
max_connections = 2


try:
  import sys
  import socket
  import cPickle
  import re
  from threading import Thread
  from pymplayer.base import MPlayer
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
    print "Remote host %s connected at port %d" % self.details
    # Count this connection
    globals()['curr_conns'] += 1
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
            self._mplayer.command("loadlist "+playlist)
          else:
            # 2nd to nth playlist, append it (take note of the '+' sign!)
            self._mplayer.command("loadlist "+playlist+" +1")
      else:
        # Send the command to MPlayer
        self._mplayer.command(cmd)

    # Close the connection
    try:
      self.channel.shutdown(socket.SHUT_RDWR)
      self.channel.close()
    except socket.error, msg:
      print >> sys.stderr, msg[1]

    globals()['curr_conns'] -= 1
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
  # MPlayer instance
  try:
    mplayer = MPlayer(sys.argv[1:])
  except OSError, msg:
    sys.exit(msg)

  # The server
  server = start_server()

  print "server.py "+version

  while mplayer.isrunning():
    try:
      print "Waiting for connection..."
      # Wait for connection from client
      (conn, addr) = server.accept()

      if globals()['curr_conns'] < max_connections:
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
