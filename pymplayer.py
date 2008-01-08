# $Id$

"""pymplayer - MPlayer wrapper for Python."""

__version__ = '0.1.0'

__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'

__copyright__ = """
Copyright (C) 2007-2008  The MA3X Project (http://bbs.eee.upd.edu.ph)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import re
import socket
import asyncore
import asynchat
from subprocess import Popen, PIPE
from threading import Thread

import gobject


__all__ = ['MPlayer', 'Server', 'Client', 'PORT', 'MAX_CMD_LENGTH']


_re_cmd_quit = re.compile(r'^(qu?|qui?|quit?)( ?| .*)$', re.IGNORECASE)


PORT = 50001
MAX_CMD_LENGTH = 256


class MPlayer(object):
    """MPlayer(path='mplayer', args=())

    Provides the basic interface for sending commands and receiving
    responses to and from MPlayer. Take note that MPlayer is always
    started in slave (-slave) and idle (-idle) modes.

    The MPlayer process would eventually "freeze" if gobject.MainLoop
    is not running because the stdout/stderr PIPE buffers would get full.

    The handle_data and handle_error methods would only get executed
    if gobject.MainLoop is running.

    @property path: path to MPlayer
    @property args: MPlayer arguments
    """
    def __init__(self, path='mplayer', args=()):
        self.path = path
        self.args = args
        self.__subprocess = None

    def __del__(self):
        # Be sure to stop the MPlayer process.
        self.stop()

    def _set_path(self, path):
        if not isinstance(path, basestring):
            raise TypeError("path should be a string")
        self.__path = path

    def _get_path(self):
        return self.__path

    path = property(_get_path, _set_path, doc="Path to MPlayer")

    def _get_args(self):
        return self.__args[6:]

    def _set_args(self, args):
        if not isinstance(args, (list, tuple)):
            raise TypeError("args should either be a tuple or list of strings")
        if args:
            for arg in args:
                if not isinstance(arg, basestring):
                    raise TypeError("args should either be a tuple or list of strings")
        self.__args = [self.path, "-slave", "-idle", "-really-quiet", "-msglevel", "global=4"]
        self.__args.extend(args)

    args = property(_get_args, _set_args, doc="MPlayer arguments")

    def _handle_data(self, source, condition):
        # source is stdout
        self.handle_data(source.readline().rstrip())
        return True

    def _handle_error(self, source, condition):
        # source is stderr
        self.handle_error(source.readline().rstrip())
        return True

    def start(self):
        """Start the MPlayer process.

        Returns True on success, False on failure,
        and None if MPlayer is already running.
        """
        if not self.isalive():
            try:
                # Start subprocess (line-buffered)
                self.__subprocess = Popen(args=self.__args, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=1)
            except OSError:
                retcode = False
            else:
                self._stdout_watch = gobject.io_add_watch(self.__subprocess.stdout,
                    gobject.IO_IN|gobject.IO_PRI, self._handle_data)
                self._stderr_watch = gobject.io_add_watch(self.__subprocess.stderr,
                    gobject.IO_IN|gobject.IO_PRI, self._handle_error)
                retcode = True
            return retcode

    def stop(self):
        """Stop the MPlayer process.

        Returns the exit status of MPlayer or None if not running.
        """
        if self.isalive():
            self.command("quit")
            gobject.source_remove(self._stdout_watch)
            gobject.source_remove(self._stderr_watch)
            return self.__subprocess.wait()
        else:
            return None

    def command(self, cmd):
        """Send a command to MPlayer.

        @param cmd: valid MPlayer command

        Valid MPlayer commands are documented in:
        http://www.mplayerhq.hu/DOCS/tech/slave.txt
        """
        if not isinstance(cmd, basestring):
            raise TypeError("command must be a string")
        if not cmd:
            raise ValueError("zero-length command")
        if self.isalive():
            self.__subprocess.stdin.write("".join([cmd, '\n']))

    def isalive(self):
        """Check if MPlayer process is alive.

        Returns True if alive, else, returns False
        """
        try:
            return (self.__subprocess.poll() is None)
        except AttributeError:
            return False

    def handle_data(self, data):
        """This method is meant to be overridden.

        This method is called when a line is read from stdout.

        @param data: the line (str) read from stdout
        """
        pass

    def handle_error(self, error):
        """This method is meant to be overridden.

        This method is called when a line is read from stderr.

        @param error: the line (str) read from stderr
        """
        pass


class _Channel(asynchat.async_chat):

    ac_in_buffer_size = MAX_CMD_LENGTH
    ac_out_buffer_size = 0

    def __init__(self, mplayer, conn, map):
        asynchat.async_chat.__init__(self, conn)
        self.add_channel(map)
        self.map = map
        self.mplayer = mplayer
        self.buffer = []
        self.set_terminator("\r\n\r\n")

    def writable(self):
        return False

    def handle_close(self):
        self.del_channel(self.map)
        self.close()
        self.log("Connection closed: %s" % (self.addr, ))

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        cmd = "".join(self.buffer)
        self.buffer = []
        if not cmd or _re_cmd_quit.match(cmd):
            self.handle_close()
        elif cmd.lower() == "reload":
            # (Re)Loading a playlist makes MPlayer "jump out" of its XEmbed container
            # Restart MPlayer instead
            self.mplayer.stop()
            self.mplayer.start()
        else:
            self.mplayer.command(cmd)


class Server(asyncore.dispatcher):
    """Server(host='', port=pymplayer.PORT, max_conns=1)

    The PyMPlayer Server

    The log method can be overridden to provide more sophisticated
    logging and warning methods.
    """
    def __init__(self, host='', port=PORT, max_conns=1):
        # Custom socket_map
        self.socket_map = {}
        # asyncore.dispatcher is not a new-style class!
        # Use own socket_map
        asyncore.dispatcher.__init__(self, map=self.socket_map)
        self.host = host
        self.port = port
        self.max_conns = max_conns
        # For now, do this since properties can't be used
        self.mplayer = MPlayer()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((self.host, self.port))
        self.listen(self.max_conns)

    def writable(self):
        return False

    def handle_close(self):
        self.log("Server closed.")
        self.close()

    def handle_accept(self):
        conn, addr = self.accept()
        if len(self.socket_map) - 1 < self.max_conns:
            self.log("Connection accepted: %s" % (addr, ))
            # Dispatch connection to _Channel and set channel logger to self.log
            _Channel(self.mplayer, conn=conn, map=self.socket_map).log = self.log
        else:
            self.log("Max number of connections reached.")
            conn.close()

    def stop(self):
        """Stop the server.

        Closes all the channels found in self.socket_map (including itself)
        """
        for channel in self.socket_map.values():
            channel.handle_close()
        return self.mplayer.stop()

    def start(self, timeout=None):
        """Start the server.

        Starts the MPlayer process, then enters asyncore.loop (blocking)
        """
        if self.mplayer.isalive():
            return
        self.mplayer.start()
        self.log("Server started.")
        asyncore.loop(timeout=timeout, map=self.socket_map)


class Client(asynchat.async_chat):
    """Client(host, port=pymplayer.PORT)

    The PyMPlayer Client
    """
    ac_in_buffer_size = 0
    ac_out_buffer_size = MAX_CMD_LENGTH

    def __init__(self, host, port=PORT):
        asynchat.async_chat.__init__(self)
        self.host = host
        self.port = port
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

    def readable(self):
        return False

    def handle_connect(self):
        pass

    def handle_error(self):
        self.close()
        raise socket.error("Connection lost.")

    def connect(self):
        if self.connected:
            return
        asynchat.async_chat.connect(self, (self.host, self.port))
        t = Thread(target=asyncore.loop)
        t.setDaemon(True)
        t.start()

    def send_command(self, cmd):
        """Send an MPlayer command to the server

        @param cmd: valid MPlayer command
        """
        self.push("".join([cmd, "\r\n\r\n"]))
        if _re_cmd_quit.match(cmd):
            self.close()
            return False
        else:
            return True
