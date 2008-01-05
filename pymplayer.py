# $Id$

"""pymplayer - MPlayer wrapper for Python."""

__version__ = '0.1.0'

__author__ = 'Darwin Bautista <djclue917@gmail.com>'

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


_asyncore_loop_started = False
_re_cmd_quit = re.compile(r'^(qu?|qui?|quit?)( ?| .*)$', re.IGNORECASE)


PORT = 50001
MAX_CMD_LENGTH = 150


class MetaData(object):
    """use with -identify
    """
    video_id = None
    audio_id = None
    filename = None
    demuxer = None
    video_format = None
    video_codec = None
    video_bitrate = None
    video_width = None
    video_height = None
    video_fps = None
    video_aspect = None
    audio_format = None
    audio_codec = None
    audio_bitrate = None
    audio_rate = None
    audio_nch = None
    length = None


class MPlayer(object):
    """MPlayer wrapper for Python
    Provides the basic interface for sending commands
    and receiving responses to and from MPlayer.
    Responsible for starting up MPlayer in slave mode

    The handle_data and handle_error methods would
    only be called if gobject.MainLoop is running.
    """
    path = "mplayer"

    def __init__(self, args=()):
        self.args = args
        self.__subprocess = None

    def __del__(self):
        self.stop()

    def _set_args(self, args):
        if not isinstance(args, (list, tuple)):
            raise TypeError("args should either be a tuple or list of strings")
        if args:
            for arg in args:
                if not isinstance(arg, basestring):
                    raise TypeError("args should either be a tuple or list of strings")
        self.__args = [self.path, "-slave", "-idle", "-really-quiet", "-msglevel", "global=4"]
        self.__args.extend(args)

    def _get_args(self):
        return self.__args[6:]

    args = property(_get_args, _set_args, doc="MPlayer arguments")

    def _handle_data(self, source, condition):
        self.handle_data(source.readline().rstrip())
        return True

    def _handle_error(self, source, condition):
        self.handle_error(source.readline().rstrip())
        return True

    def start(self):
        """Starts an MPlayer instance.
        Returns True on success, False on failure, and None if MPlayer is already running
        """
        if not self.isalive():
            try:
                # Start subprocess (line-buffered)
                self.__subprocess = Popen(args=self.__args, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=1)
            except OSError:
                ret = False
            else:
                self._stdout_watch = gobject.io_add_watch(self.__subprocess.stdout,
                    gobject.IO_IN|gobject.IO_PRI, self._handle_data)
                self._stderr_watch = gobject.io_add_watch(self.__subprocess.stderr,
                    gobject.IO_IN|gobject.IO_PRI, self._handle_error)
                ret = True
            return ret

    def stop(self):
        """Stops a running MPlayer instance
        Returns the exit status of MPlayer or None if not running
        """
        if self.isalive():
            self.command("quit")
            gobject.source_remove(self._stdout_watch)
            gobject.source_remove(self._stderr_watch)
            return self.__subprocess.wait()
        else:
            return None

    def command(self, cmd):
        """Send a command to MPlayer

        @param cmd: MPlayer command (see: http://www.mplayerhq.hu/DOCS/tech/slave.txt)
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

        @param data: the line read from stdout
        """
        pass

    def handle_error(self, error):
        """This method is meant to be overridden.
        This method is called when a line is read from stderr.

        @param error: the line read from stderr
        """
        pass


class _Channel(asynchat.async_chat):
    """Client -> Server connection"""
    def __init__(self, mplayer, conn):
        print "session started"
        asynchat.async_chat.__init__(self, conn=conn)
        self.mplayer = mplayer
        self.buffer = []
        self.set_terminator("\r\n\r\n")

    def writable(self):
        """Returning True would cause the CPU usage to jump to ~100%"""
        return False

    def handle_close(self):
        print "session closed"
        self.close()

    def handle_error(self):
        self.handle_close()

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
            self.mplayer.restart()
        else:
            self.mplayer.command(cmd)


class _AsynCoreLoop(Thread):
    """Just a Thread for running asyncore.loop()
    """
    def __init__(self, timeout=30):
        super(_AsynCoreLoop, self).__init__()
        self.timeout = timeout
        self.setDaemon(True)

    def run(self):
        global _asyncore_loop_started
        if _asyncore_loop_started:
            raise RuntimeError("asyncore.loop() already started")
        asyncore.loop(self.timeout)
        _asyncore_loop_started = True


# TODO: fix start/stop
# start is ok upon first time, but after stop(), it will not work because the socket is already closed
#
class Server(MPlayer, asyncore.dispatcher):
    """MPlayer Server
    """
    def __init__(self, args=(), port=PORT, max_conn=1):
        # asyncore.dispatcher is not a new-style class!
        asyncore.dispatcher.__init__(self)
        MPlayer.__init__(self, args=args)
        self.port = port
        self.max_conn = max_conn
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        # FIXME: clean this up!
        try:
            self.bind(('', self.port))
        except socket.error, msg:
            self.handle_close()
            raise socket.error(msg)
        self.listen(self.max_conn)

    def __del__(self):
        """this won't ever get called because there will always be a reference in asyncore.socket_map
        """
        #self.stop()
        pass

    def writable(self):
        return False

    def handle_close(self):
        print "server closed"
        self.close()

    def handle_error(self):
        self.handle_close()

    def handle_accept(self):
        connection, address = self.accept()
        if len(asyncore.socket_map) - 1 < self.max_conn:
            print "accepted connection"
            _Channel(self, connection)
        else:
            print "max number of connections reached"
            connection.close()

    def wait(self, timeout=None):
        self._loop.join(timeout)

    def stop(self):
        if not self.isalive():
            return
        #raise asyncore.ExitNow
        self.handle_close()
        for session in asyncore.socket_map.values():
            session.handle_close()
        retcode = MPlayer.stop(self)
        self.wait()
        return retcode

    def start(self):
        if self.isalive():
            return
        retcode = MPlayer.start(self)
        # AssertionError would only happen in __debug__ mode
        # To be safe when not __debug__
        self._loop = _AsynCoreLoop(timeout=2)
        self._loop.start()
        return retcode

    def restart(self):
        MPlayer.stop(self)
        MPlayer.start(self)


class Client(asynchat.async_chat):
    def __init__(self, host, port=PORT):
        asynchat.async_chat.__init__(self)
        self.host = host
        self.port = port

    def handle_connect(self):
        pass

    def handle_error(self):
        self.close()
        raise socket.error("Connection lost")

    def readable(self):
        return False

    def connect(self):
        if self.connected:
            return
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        asynchat.async_chat.connect(self, (self.host, self.port))
        self._loop = _AsynCoreLoop(timeout=1)
        self._loop.start()

    def disconnect(self):
        self.close()

    def send_command(self, cmd):
        self.push("".join([cmd, "\r\n\r\n"]))
        if _re_cmd_quit.match(cmd):
            self.close()
            return False
        else:
            return True

