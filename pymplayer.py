#!/usr/bin/env python
# -*- coding: utf-8 -*-
# $Id$
#
# Copyright (C) 2007-2008  UP EEEI Computer Networks Laboratory
# Copyright (C) 2007-2009  Darwin M. Bautista <djclue917@gmail.com>
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

"""

import socket
import asyncore
import asynchat
from time import sleep
from subprocess import Popen, PIPE


__all__ = [
    'MPlayer',
    'Server',
    'Client'
    ]

__version__ = '0.4.0'
__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'


class MPlayer(object):
    """MPlayer(args=())

    An out-of-process wrapper for MPlayer. It provides the basic interface
    for sending commands and receiving responses to and from MPlayer. Take
    note that MPlayer is always started in 'slave', 'idle', and 'quiet' modes.

    @class attribute executable: path to or filename of the MPlayer executable
    @property args: MPlayer arguments
    @property stdout: process' stdout (read-only)
    @property stderr: process' stderr (read-only)

    """

    executable = 'mplayer'

    def __init__(self, args=()):
        self.args = args
        self._process = None
        self._stdout = _file()
        self._stderr = _file()

    def __del__(self):
        # Be sure to stop the MPlayer process.
        self.stop()

    def _get_stdout(self):
        return self._stdout

    stdout = property(fget=_get_stdout)

    def _get_stderr(self):
        return self._stderr

    stderr = property(fget=_get_stderr)

    def _get_args(self):
        return self._args[3:]

    def _set_args(self, args):
        _args = ['-slave', '-idle', '-quiet']
        try:
            _args.extend(args)
        except TypeError:
            raise TypeError('args should be an iterable')
        for i in range(3, len(_args)):
            if not isinstance(_args[i], basestring):
                _args[i] = str(_args[i])
        self._args = _args

    args = property(_get_args, _set_args, doc='MPlayer arguments')

    def start(self, stdout=None, stderr=None):
        """Start the MPlayer process.

        @param stdout: subprocess.PIPE | None
        @param stderr: subprocess.PIPE | subprocess.STDOUT | None

        Returns True on success, False on failure, and None if MPlayer is
        already running. stdout/stderr will be PIPEd regardless of the
        passed parameters if handlers were added to them.

        """
        if not self.isalive():
            args = [self.__class__.executable]
            args.extend(self._args)
            # Force PIPE if callbacks were added
            stdout_ = (PIPE if len(self._stdout._callbacks) > 0 else stdout)
            stderr_ = (PIPE if len(self._stderr._callbacks) > 0 else stderr)
            try:
                # Start the MPlayer process (line-buffered)
                self._process = Popen(args=args, stdin=PIPE, stdout=stdout_, stderr=stderr_, bufsize=1)
            except OSError:
                return False
            else:
                if self._process.stdout is not None:
                    self._stdout._set_file(self._process.stdout)
                if self._process.stderr is not None:
                    self._stderr._set_file(self._process.stderr)
                return True

    def stop(self):
        """Stop the MPlayer process.

        Returns the exit status of MPlayer or None if not running.

        """
        if self.isalive():
            self._stdout._unset_file()
            self._stderr._unset_file()
            self.command('quit')
            process = self._process
            self._process = None
            return process.wait()

    def restart(self):
        """Convenience method for restarting the MPlayer process.

        Returns the return values of the stop and start methods as a 2-tuple.

        """
        return self.stop(), self.start()

    def isalive(self):
        """Check if MPlayer process is alive.

        Returns True if alive, else, returns False.

        """
        try:
            return (self._process.poll() is None)
        except AttributeError:
            return False

    def command(self, cmd):
        """Send a command to MPlayer.

        @param cmd: command string

        Valid MPlayer commands are documented in:
        http://www.mplayerhq.hu/DOCS/tech/slave.txt

        """
        if not isinstance(cmd, basestring):
            raise TypeError('command must be a string')
        if self.isalive() and cmd:
            self._process.stdin.write(''.join([cmd, '\n']))

    def query(self, cmd, timeout=0.1):
        if cmd.lower().startswith('get_'):
            self._stdout._query_in_progress = True
            self.command(cmd)
            sleep(timeout)
            try:
                response = self._process.stdout.readline().rstrip()
            except IOError:
                return None
            if response.startswith('ANS_'):
                response = response.split('=')[1].strip("'").strip('"')
            else:
                response = None
            self._stdout._query_in_progress = False
            return response


class Server(asyncore.dispatcher):
    """Server(mplayer, port, host='', max_conn=1)

    The log method can be overridden to provide more sophisticated
    logging and warning methods.

    """

    def __init__(self, mplayer, port, host='', max_conn=1):
        asyncore.dispatcher.__init__(self)
        self._mplayer = mplayer
        self._max_conn = max_conn
        self._channels = {}
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(self._max_conn)
        self.log('Server started.')

    def __del__(self):
        self.stop()

    def writable(self):
        return False

    def handle_close(self):
        self.close()
        self.log('Server closed.')

    def handle_accept(self):
        conn, addr = self.accept()
        if len(self._channels) < self._max_conn:
            self.log('Connection accepted: %s' % (addr, ))
            # Dispatch connection to a _ClientHandler
            _ClientHandler(self._channels, self._mplayer, conn, self.log)
        else:
            self.log('Max number of connections reached, rejected: %s' % (addr, ))
            conn.close()

    def stop(self):
        """Stop the server.

        Closes all the channels (_ClientHandler) spawned by the Server

        """
        for channel in self._channels.values():
            channel.handle_close()
        self.handle_close()


class Client(asynchat.async_chat):
    """Client()

    The PyMPlayer Client

    """

    ac_in_buffer_size = 512
    ac_out_buffer_size = 512

    def __init__(self):
        asynchat.async_chat.__init__(self)
        self.buffer = []
        self.set_terminator('\r\n')

    def handle_connect(self):
        return

    def handle_error(self):
        self.close()
        raise socket.error('Connection lost.')

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        data = ''.join(self.buffer)
        self.buffer = []
        self.handle_data(data)

    def handle_data(self, data):
        self.log(data)

    def connect(self, (host, port)):
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
        self.push(''.join([cmd, '\r\n\r\n']))
        if 'quit'.startswith(cmd.split()[0].lower()):
            self.close()
            return False
        else:
            return True


class _ClientHandler(asynchat.async_chat):
    """Handler for Client connections"""

    ac_in_buffer_size = 512
    ac_out_buffer_size = 512

    def __init__(self, connections, mplayer, conn, log):
        asynchat.async_chat.__init__(self, conn)
        self.add_channel(connections)
        self.set_terminator('\r\n\r\n')
        self.connections = connections
        self.mplayer = mplayer
        # hook handle_mplayer_data method to mplayer's stdout
        self.handler_id = self.mplayer.stdout.add_handler(self.handle_mplayer_data)
        self.log = log
        self.buffer = []

    def handle_close(self):
        self.mplayer.stdout.remove_handler(self.handler_id)
        del self.connections[self._fileno]
        self.close()
        self.log('Connection closed: %s' % (self.addr, ))

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        data = ''.join(self.buffer)
        self.buffer = []
        self.handle_data(data)

    def handle_data(self, data):
        if not data or 'quit'.startswith(data.split()[0].lower()):
            self.handle_close()
        elif data.lower() == 'reload':
            # then restart the MPlayer process;
            self.mplayer.restart()
        else:
            self.mplayer.command(data)

    def handle_mplayer_data(self, data):
        if data.startswith('ANS_'):
            self.push(''.join([data, '\r\n']))


class _file(object):
    """Wrapper for stdout and stderr

    Exposes the fileno() and readline() methods
    Provides methods for management of data handlers
    """

    def __init__(self):
        self._callbacks = {}
        self._file = None
        self._query_in_progress = False

    def _set_file(self, file):
        self._unset_file()
        self._file = file
        # create file_dispatcher instance and override handle_read method
        asyncore.file_dispatcher(file.fileno()).handle_read = self.readline

    def _unset_file(self):
        if self._file is not None and asyncore.socket_map.has_key(self._file.fileno()):
            del asyncore.socket_map[self._file.fileno()]
        self._file = None

    def fileno(self):
        if self._file is not None:
            return self._file.fileno()

    def readline(self):
        if self._file is not None and not self._query_in_progress:
            try:
                data = self._file.readline().rstrip()
            except IOError:
                return None
            for handler in self._callbacks.values():
                if callable(handler):
                    handler(data)
                else:
                    del self._callbacks[id(handler)]
            return data

    def add_handler(self, callback):
        cid = id(callback)
        self._callbacks[cid] = callback
        return cid

    def remove_handler(self, cid):
        del self._callbacks[cid]


if __name__ == '__main__':
    import sys
    import signal

    def handle_data(data):
        print 'mplayer: ', data

    player = MPlayer()
    player.args = sys.argv[1:]
    player.stdout.add_handler(handle_data)
    player.start()

    signal.signal(signal.SIGTERM, lambda s, f: player.stop())
    signal.signal(signal.SIGINT, lambda s, f: player.stop())
    asyncore.loop()
