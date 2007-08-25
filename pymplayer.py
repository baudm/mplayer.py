"""pymplayer - MPlayer wrapper for Python.

By Darwin Bautista <djclue917@gmail.com>
"""

__version__ = "$Revision: 49 $"
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

try:
    import socket
    import cPickle
    import sys
    from subprocess import Popen, PIPE
    from threading import Thread
    from re import compile
except ImportError, msg:
    exit(msg)


__all__ = ['MPlayer', 'MPlayerServer']


class MPlayer:
    """
    MPlayer wrapper for Python
    Provides the basic interface for sending commands and receiving responses
    to and from MPlayer.
    Responsible for starting up MPlayer in slave mode
    """
    def __init__(self, args=()):
        self.set_args(args)

    def __del__(self):
        self.stop()

    def start(self):
        if not self.isrunning():
            self._subprocess = Popen(self._command, stdin=PIPE)

    def stop(self):
        if self.isrunning():
            self.execute("quit")
            self._subprocess.wait()

    def execute(self, cmd):
        if not isinstance(cmd, basestring):
            raise TypeError("command must be a string")
        if not cmd:
            raise ValueError("zero-length command")
        if self.isrunning():
            self._subprocess.stdin.write("".join([cmd, '\n']))

    def isrunning(self):
        try:
            return True if self._subprocess.poll() is None else False
        except AttributeError:
            return False

    def set_args(self, args):
        # args must either be a tuple or a list
        if not isinstance(args, (list, tuple)):
            raise TypeError("args should either be a tuple or list of strings")
        if args:
            for arg in args:
                if not isinstance(arg, basestring):
                    raise TypeError("args should either be a tuple or list of\
                                     strings")
        self._command = ["mplayer", "-slave", "-idle", "-quiet"]
        self._command.extend(args)

    def get_args(self):
        return self._command[4:]

    def get_playlists(self):
        """
        Returns the list of playlists based on MPlayer cmdline
        """
        playlists = []
        idx = 0
        for match in range(self._command.count("-playlist")):
            try:
                idx = self._command.index("-playlist", idx) + 1
            except ValueError:
                break
            try:
                playlists.append(self._command[idx])
            except IndexError:
                break
        return playlists


class _ClientThread(Thread):
    """
    Thread for handling a client connection
    usage: ClientThread(mplayer, channel, details).start()
    The thread finishes after the connection is closed by the client
    """
    def __init__(self, mplayer_server, channel, details, timeout=None):
        if not isinstance(mplayer_server, MPlayerServer):
            raise TypeError("mplayer_server must be an instance of MPlayerServer")

        self._mplayer_server = mplayer_server
        self.channel = channel
        self.details = details
        self.channel.settimeout(timeout)
        Thread.__init__(self)

    def run(self):
        print "Remote host %s connected at port %d" % self.details
        # RegExp for "quit" command in MPlayer
        quit_cmd = compile('^(qu?|qui?|quit?)( ?| .*)$')
        while self._mplayer_server.isrunning():
            try:
                # Receive command from the client
                data = self.channel.recv(1024)
            except socket.error, msg:
                print >> sys.stderr, msg
                break
            except EOFError, msg:
                print >> sys.stderr, msg
                break
            except socket.timeout:
                print "Connection timed out."
                break
            # Unpickle data
            cmd = cPickle.loads(data)
            # Remote client closed the connection
            if quit_cmd.match(cmd.lower()):
                break
            elif cmd.lower() == "reload":
                # (Re)Loading a playlist makes MPlayer "jump out" of its XEmbed container
                self._mplayer_server.restart_mp()
            else:
                # Send the command to MPlayer
                self._mplayer_server.execute(cmd)
        # Close the connection
        try:
            self.channel.shutdown(socket.SHUT_RDWR)
            self.channel.close()
        except socket.error, msg:
            print >> sys.stderr, msg[1]

        self._mplayer_server.connections.remove(self)
        print "Connection closed: %s at port %d" % self.details


class MPlayerServer(MPlayer, Thread):
    """
    MPlayer wrapper with commands implemented as functions
    This is useful for easily controlling MPlayer in Python
    """
    def __init__(self, mplayer_args=(), host='', port=50001, max_connections=2):
        if not isinstance(port, int):
            raise TypeError("port must be an integer")
        MPlayer.__init__(self, mplayer_args)
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.connections = []
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            print >> sys.stderr, msg[1]
        # Set option to re-use the address to prevent "Address already in use" errors
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.settimeout(5.0)

    def __del__(self):
        MPlayer.__del__(self)
        self.stop()

    def start(self):
        Thread.start(self)

    def run(self):
        MPlayer.start(self)
        try:
            self._socket.bind((self.host, self.port))
            self._socket.listen(1)
        except socket.error, msg:
            self._socket.close()
            sys.exit(msg[1])

        while self.isrunning():
            # Wait for connection from client
            try:
                (conn, addr) = self._socket.accept()
            except socket.timeout:
                continue
            except socket.error:
                break

            if len(self.connections) < self.max_connections:
                # Start separate client thread to handle connection (timeout: 30 seconds)
                client = _ClientThread(self, conn, addr, 30.0)
                self.connections.append(client)
                client.start()
            else:
                conn.close()
                print "Connection rejected: max number of connections reached"

    def stop(self):
        MPlayer.stop(self)
        self._socket.close()
        # Wait for _ClientThreads to terminate.
        for connection in self.connections:
            connection.join()

    def restart_mp(self):
        MPlayer.stop(self)
        MPlayer.start(self)

