# $Id$
#
# Copyright (C) 2007-2008  UP EEE Computer Networks Laboratory
# Copyright (C) 2007-2008  Darwin M. Bautista <djclue917@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Thin, out-of-source wrapper and client/server for MPlayer

Classes:

MPlayer -- thin, out-of-process wrapper for MPlayer
Server -- asynchronous server that manages an MPlayer instance
Client -- client for sending MPlayer commands

Function:

loop() -- the asyncore.loop function, for use in conjunction with Client

Constants:

PORT -- default port used by Client and Server
MAX_CMD_LEN -- maximum length of a command
"""

__version__ = "0.2.0"
__author__ = "Darwin M. Bautista <djclue917@gmail.com>"


import re
import socket
import asyncore
import asynchat
from asyncore import loop
from subprocess import Popen, PIPE


__all__ = ['MPlayer', 'Server', 'Client', 'loop', 'PORT', 'MAX_CMD_LEN']


PORT = 50001
MAX_CMD_LEN = 256


class _ReadableFile(object):
    """Imitates a readable asyncore.dispatcher class.

    This class serves as a wrapper for stdout and stderr
    so that the polling function of asyncore can check them
    for any pending I/O events. The polling function will
    call the handle_read_event method as soon as there is data
    to read.
    """
    def __init__(self, map, file, handler):
        # Add self to map
        map[file.fileno()] = self
        self.handle_read_event = handler

    def __getattr__(self, attr):
        # Always return a callable for non-existent attributes and
        # methods in order to 'fool' asyncore's polling function.
        # (IMO, this is a better approach than defining all
        #  the other asyncore.dispatcher methods)
        return lambda: None

    @staticmethod
    def readable():
        return True

    @staticmethod
    def writable():
        return False


class MPlayer(object):
    """MPlayer(path='mplayer', args=())

    An out-of-process wrapper for MPlayer. It provides the basic interface
    for sending commands and receiving responses to and from MPlayer. Take
    note that MPlayer is always started in 'slave', 'idle', and 'quiet' modes.

    The MPlayer process would eventually "freeze" if the poll_output method
    is not called because the stdout/stderr PIPE buffers would get full.
    Also, the handle_data and handle_error methods would only get called,
    given an I/O event, after the poll_output method is called.

    A different 'I/O watcher' can be used by overriding the create_handler
    and remove_handler methods.

    @property path: path to MPlayer or name of executable as found in PATH
    @property args: MPlayer arguments
    """
    def __init__(self, path='mplayer', args=()):
        self.path = path
        self.args = args
        self._map = {}
        self.__process = None

    def __del__(self):
        # Be sure to stop the MPlayer process.
        self.stop()

    def _get_path(self):
        return self.__path

    def _set_path(self, path):
        if not isinstance(path, basestring):
            raise TypeError("path should be a string")
        self.__path = path

    path = property(_get_path, _set_path, doc="path to MPlayer or name of executable as found in PATH")

    def _get_args(self):
        return self.__args[3:]

    def _set_args(self, args):
        if not isinstance(args, (list, tuple)):
            raise TypeError("args should either be a tuple or list of strings")
        elif args:
            for arg in args:
                if not isinstance(arg, basestring):
                    raise TypeError("args should either be a tuple or list of strings")
        self.__args = ['-slave', '-idle', '-quiet']
        self.__args.extend(args)

    args = property(_get_args, _set_args, doc="MPlayer arguments")

    def _handle_data(self, *args):
        data = self.__process.stdout.readline().rstrip()
        if data:
            self.handle_data(data)
        # gobject.io_add_watch compatibility
        return True

    def _handle_error(self, *args):
        error = self.__process.stderr.readline().rstrip()
        if error:
            self.handle_error(error)
        # gobject.io_add_watch compatibility
        return True

    def create_handler(self, file, callback):
        """Create a handler for file.

        @param file: file-like object
        @param callback: function to be called when data can be read from file

        This method may be overridden like so:

        PyGTK/PyGObject:
        self.handles[file] = gobject.io_add_watch(file, gobject.IO_IN|gobject.IO_PRI, callback)

        Tkinter:
        tkinter.createfilehandler(file, tkinter.READABLE, callback)
        """
        _ReadableFile(self._map, file, callback)

    def remove_handler(self, file):
        """Remove a handler for file.

        @param file: file-like object

        This method may be overridden like so:

        PyGTK/PyGObject:
        gobject.source_remove(self.handles.pop(file))

        Tkinter:
        tkinter.deletefilehandler(file)
        """
        # Clear the map so that asyncore.loop will terminate.
        # This will be called twice, one of stdout and one for
        # stderr, but that doesn't actually matter.
        self._map.clear()

    def poll_output(self, timeout=30.0, use_poll=False):
        """Start polling MPlayer's stdout and stderr.

        @param timeout=30.0: timeout parameter for select() or poll()
        @param use_poll=False: use poll() instead of select()

        This method will block unless it is called before MPlayer is
        started or if the MPlayer process is currently not running.

        This method need not be called when the create_handler and/or
        remove_handler methods are overridden for use with a certain
        GUI toolkit (e.g. PyGTK, Tkinter).

        In a multithreaded app, you may want to spawn a new Thread
        for running this method after calling the start method:

        mplayer = MPlayer()
        mplayer.start()
        thread = threading.Thread(target=mplayer.poll_output)
        thread.setDaemon(True)
        thread.start()
        """
        # Don't call asyncore.loop if MPlayer isn't running
        # or if the create_handler method was overridden.
        if self.isalive() and self._map:
            loop(timeout=timeout, use_poll=use_poll, map=self._map)

    def start(self):
        """Start the MPlayer process.

        Returns True on success, False on failure,
        and None if MPlayer is already running.
        """
        if not self.isalive():
            args = [self.path]
            args.extend(self.__args)
            try:
                # Start the MPlayer process (line-buffered)
                self.__process = Popen(args=args, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=1)
            except OSError:
                retcode = False
            else:
                self.create_handler(self.__process.stdout, self._handle_data)
                self.create_handler(self.__process.stderr, self._handle_error)
                retcode = True
            return retcode

    def stop(self):
        """Stop the MPlayer process.

        Returns the exit status of MPlayer or None if not running.
        """
        if self.isalive():
            self.command("quit")
            self.remove_handler(self.__process.stdout)
            self.remove_handler(self.__process.stderr)
            return self.__process.wait()

    def restart(self):
        """Convenience method for restarting the MPlayer process.

        Restarting MPlayer means stopping the current process and
        starting a new one which means that the poll_output method
        will finish and return and will need to be called again.

        Returns the return values of the stop and start methods as a 2-tuple.
        """
        return self.stop(), self.start()

    def command(self, cmd):
        """Send a command to MPlayer.

        @param cmd: valid MPlayer command

        Valid MPlayer commands are documented in:
        http://www.mplayerhq.hu/DOCS/tech/slave.txt
        """
        if not isinstance(cmd, basestring):
            raise TypeError("command must be a string")
        if self.isalive() and cmd:
            self.__process.stdin.write("".join([cmd, '\n']))

    def isalive(self):
        """Check if MPlayer process is alive.

        Returns True if alive, else, returns False.
        """
        try:
            return (self.__process.poll() is None)
        except AttributeError:
            return False

    @staticmethod
    def handle_data(data):
        """Handle the data read from stdout.

        This method is meant to be overridden.
        It will be called for each readline() from stdout.

        @param data: the line read from stdout
        """
        return

    @staticmethod
    def handle_error(data):
        """Handle the data read from stderr.

        This method is meant to be overridden.
        It will be called for each readline() from stderr.

        @param data: the line read from stderr
        """
        return


class _ClientHandler(asynchat.async_chat):
    """Handler for Client connections"""

    ac_in_buffer_size = MAX_CMD_LEN
    ac_out_buffer_size = 512

    def __init__(self, mplayer, conn, map, log):
        asynchat.async_chat.__init__(self, conn)
        # We're using a custom map so remove self from asyncore.socket_map.
        asyncore.socket_map.pop(self._fileno)
        self._map = map
        self.add_channel()
        self.mplayer = mplayer
        self.mplayer_handle_data = mplayer.handle_data
        def handle_data(data):
            self.handle_data(data)
            self.mplayer_handle_data(data)
        self.mplayer.handle_data = handle_data
        self.log = log
        self.buffer = []
        self.set_terminator("\r\n\r\n")

    def handle_data(self, data):
        if data.startswith('ANS_'):
            self.push("".join([data, "\r\n"]))

    def handle_close(self):
        self.close()
        self.mplayer.handle_data = self.mplayer_handle_data
        self.log("Connection closed: %s" % (self.addr, ))

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        cmd = "".join(self.buffer)
        self.buffer = []
        if not cmd or "quit".startswith(cmd.split()[0].lower()):
            self.handle_close()
        elif cmd.lower() == "reload":
            # (Re)loading a file or a playlist would make MPlayer "jump out"
            # of its XEmbed container, restart the MPlayer process instead:
            # First, remove stdout and stderr from the map;
            map(self._map.pop, self.mplayer._map)
            # then restart the MPlayer process;
            self.mplayer.restart()
            # and finally, add stdout and stderr back to the map.
            self._map.update(self.mplayer._map)
        else:
            self.mplayer.command(cmd)


class Server(asyncore.dispatcher):
    """Server(host='', port=pymplayer.PORT, max_conn=1)

    Although this class isn't a subclass of MPlayer, all of MPlayer's
    methods (except poll_output) and properties are exposed via
    the __getattr__ method. The MPlayer properties function and
    behave properly via some __getattr__ and __setattr__ magic.

    The log method can be overridden to provide more sophisticated
    logging and warning methods.
    """
    def __init__(self, host='', port=PORT, max_conn=1):
        # Use own socket map
        self._map = {}
        asyncore.dispatcher.__init__(self, map=self._map)
        self.__mplayer = MPlayer()
        self.max_conn = max_conn
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(self.max_conn)

    def __del__(self):
        self.stop()

    def __getattr__(self, attr):
        # Expose the MPlayer methods (except poll_output) and properties
        if hasattr(self.__mplayer, attr) and attr != 'poll_output':
            return getattr(self.__mplayer, attr)
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, attr))

    def __setattr__(self, attr, value):
        # Make the MPlayer properties behave properly
        if attr not in ('args', 'path'):
            self.__dict__[attr] = value
        else:
            setattr(self.__mplayer, attr, value)

    @staticmethod
    def writable():
        return False

    def handle_close(self):
        self.log("Server closed.")
        self.close()

    def handle_accept(self):
        conn, addr = self.accept()
        if len(self._map) - len(self.__mplayer._map) - 1 < self.max_conn:
            self.log("Connection accepted: %s" % (addr, ))
            # Dispatch connection to a _ClientHandler
            _ClientHandler(self.__mplayer, conn, self._map, self.log)
        else:
            self.log("Max number of connections reached, rejected: %s" % (addr, ))
            conn.close()

    def stop(self):
        """Stop the server.

        Closes all the channels found in self._map (including itself)
        """
        for channel in self._map.values():
            channel.handle_close()
        # The _ReadableFile instances would still remain in self._map,
        # clear map so that asyncore.loop will terminate.
        self._map.clear()
        return self.__mplayer.stop()

    def start(self, timeout=30.0, use_poll=False):
        """Start the server.

        @param timeout=30.0: timeout parameter for select() or poll()
        @param use_poll=False: use poll() instead of select()

        Starts the MPlayer process, then calls asyncore.loop (blocking)
        """
        if self.__mplayer.isalive():
            return
        self.__mplayer.start()
        # Include the _ReadableFile instances from self.__mplayer._map
        self._map.update(self.__mplayer._map)
        self.log("Server started.")
        loop(timeout=timeout, use_poll=use_poll, map=self._map)


class Client(asynchat.async_chat):
    """Client()

    The PyMPlayer Client
    """
    ac_in_buffer_size = 512
    ac_out_buffer_size = MAX_CMD_LEN

    def __init__(self):
        asynchat.async_chat.__init__(self)
        self.buffer = []
        self.set_terminator("\r\n")

    @staticmethod
    def handle_connect():
        return

    def handle_error(self):
        self.close()
        raise socket.error("Connection lost.")

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        data = "".join(self.buffer)
        self.buffer = []
        self.handle_data(data)

    def handle_data(self, data):
        self.log(data)

    def connect(self, host, port=PORT):
        """Connect to a pymplayer.Server

        @param host: host to connect to
        @param port: port to use

        pymplayer.loop should be called (if not called previously)
        after calling this method.
        """
        if self.connected:
            return
        if self.socket:
            self.close()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        asynchat.async_chat.connect(self, (host, port))

    def send_command(self, cmd):
        """Send an MPlayer command to the server

        @param cmd: valid MPlayer command

        Valid MPlayer commands are documented in:
        http://www.mplayerhq.hu/DOCS/tech/slave.txt
        """
        self.push("".join([cmd, "\r\n\r\n"]))
        if "quit".startswith(cmd.split()[0].lower()):
            self.close()
            return False
        else:
            return True
