# -*- coding: utf-8 -*-
# $Id$
#
# Copyright (C) 2007-2008  UP EEEI Computer Networks Laboratory
# Copyright (C) 2007-2010  Darwin M. Bautista <djclue917@gmail.com>
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

import shlex
import subprocess
from threading import Lock
if not subprocess.mswindows:
    import select


__all__ = ['MPlayer']


class MPlayer(object):
    """MPlayer(args=())

    An out-of-process wrapper for MPlayer. It provides the basic
    interface for sending commands and receiving responses to and from
    MPlayer. Take note that MPlayer is always started in 'slave',
    'idle', and 'quiet' modes.

    @class attribute path: full/relative path to or filename of MPlayer
    @property args: MPlayer arguments
    @property stdout: process' stdout (read-only)
    @property stderr: process' stderr (read-only)
    """

    path = 'mplayer'

    def __init__(self, args=()):
        self.args = args
        self._process = None
        self._stdout = _FileWrapper()
        self._stderr = _FileWrapper()

    def __del__(self):
        # Be sure to stop the MPlayer process.
        self.quit()

    def __repr__(self):
        if self.is_alive():
            status = 'with pid = %d' % (self._process.pid)
        else:
            status = 'not running'
        return '<%s.%s %s>' % (__name__, self.__class__.__name__, status)

    @staticmethod
    def _check_command_args(name, min_argc, max_argc, args):
        argc = len(args) + 1
        if not min_argc and argc:
            raise TypeError('%s() takes no arguments (%d given)' %
                (name, argc))
        if argc < min_argc:
            s = ('s' if min_argc > 1 else '')
            raise TypeError('%s() takes at least %d argument%s (%d given)' %
                (name, min_argc, s, argc))
        if min_argc == max_argc and argc != max_argc:
            s = ('s' if max_argc > 1 else '')
            raise TypeError('%s() takes exactly %d argument%s (%d given)' %
                (name, max_argc, s, argc))
        if argc > max_argc:
            s = ('s' if max_argc > 1 else '')
            raise TypeError('%s() takes at most %d argument%s (%d given)' %
                (name, max_argc, s, argc))

    def _get_args(self):
        return self._args[7:]

    def _set_args(self, args):
        _args = ['-slave', '-idle', '-quiet', '-input', 'nodefault-bindings',
            '-noconfig', 'all']
        # Assume that args is a string.
        try:
            args = shlex.split(args)
        except AttributeError: # args is not a string
            # Force all args to string
            args = map(str, args)
        _args.extend(args)
        self._args = _args

    args = property(_get_args, _set_args, doc='list of MPlayer arguments')

    @property
    def stdout(self):
        """stdout of the MPlayer process"""
        return self._stdout

    @property
    def stderr(self):
        """stderr of the MPlayer process"""
        return self._stderr

    @classmethod
    def introspect(cls):
        """Introspect the MPlayer executable

        Generate methods based on the available commands. The generated
        methods check the number and type of the passed parameters.

        Returns True if successful, False otherwise.
        """
        args = [cls.path, '-input', 'cmdlist', '-really-quiet']
        try:
            mplayer = subprocess.Popen(args, bufsize=1, stdout=subprocess.PIPE,
                universal_newlines=True)
        except OSError:
            return False
        for line in mplayer.communicate()[0].split('\n'):
            if not line or line.startswith('quit') or \
               line.startswith('get_property'):
                continue
            args = line.lower().split()
            name = args.pop(0)
            if not name.startswith('get_'):
                required = len(args) - str(args).count("'[")
                code = '''
                def %(name)s(self, *args):
                    """%(name)s(%(args)s)"""
                    try:
                        self._check_command_args('%(name)s', %(min_argc)d,
                            %(max_argc)d, args)
                    except TypeError as msg:
                        raise TypeError(msg)
                    return self.command('%(name)s', *args)
                ''' % dict(
                    name=name, args=', '.join(args),
                    min_argc=(required + 1), max_argc=(len(args) + 1)
                )
            else:
                code = '''
                def %(name)s(self, timeout=0.25):
                    """%(name)s(timeout=0.25)"""
                    return self.query('%(name)s', timeout)
                ''' % dict(name=name)
            local = {}
            exec(code.strip(), globals(), local)
            setattr(cls, name, local[name])
        return True

    def start(self, stdout=None, stderr=None):
        """Start the MPlayer process.

        @param stdout: subprocess.PIPE | None
        @param stderr: subprocess.PIPE | subprocess.STDOUT | None

        Returns True on success, False on failure, or None if MPlayer
        is already running. stdout/stderr will be PIPEd regardless of
        the passed parameters if subscribers were added to them.
        """
        assert stdout in (subprocess.PIPE, None), \
            'stdout should either be PIPE or None'
        assert stderr in (subprocess.PIPE, subprocess.STDOUT, None), \
            'stderr should be one of PIPE, STDOUT, or None'
        if not self.is_alive():
            args = [self.__class__.path]
            args.extend(self._args)
            # Force PIPE if subscribers were added
            if self._stdout._subscribers:
                stdout = subprocess.PIPE
            if self._stderr._subscribers:
                stderr = subprocess.PIPE
            try:
                # Start the MPlayer process (unbuffered)
                self._process = subprocess.Popen(args, stdin=subprocess.PIPE,
                    stdout=stdout, stderr=stderr, universal_newlines=True)
            except OSError:
                return False
            else:
                self._stdout._file = self._process.stdout
                self._stderr._file = self._process.stderr
                return True

    def quit(self, retcode=0):
        """Stop the MPlayer process.

        Returns the exit status of MPlayer or None if not running.
        """
        if self.is_alive():
            self._stdout._file = None
            self._stderr._file = None
            self._process.stdin.write('quit %d\n' % (retcode, ))
            self._process.stdin.flush()
            return self._process.wait()

    def is_alive(self):
        """Check if MPlayer process is alive.

        Returns True if alive, else, returns False.
        """
        if self._process is not None:
            return (self._process.poll() is None)
        else:
            return False

    def command(self, name, *args):
        """Send a command to MPlayer.

        @param name: command string

        Valid MPlayer commands are documented in:
        http://www.mplayerhq.hu/DOCS/tech/slave.txt
        """
        assert self.is_alive(), 'MPlayer not yet started'
        assert not 'quit'.startswith(name.split()[0].lower()), \
            'use the quit() method instead'
        if self.is_alive() and name:
            command = ['pausing_keep', name]
            command.extend(map(str, args))
            command.append('\n')
            self._process.stdin.write(' '.join(command))
            self._process.stdin.flush()

    def query(self, name, timeout=0.25):
        """Send a query to MPlayer. The result is returned, if there is any.

        query() will first consume all data in stdout before proceeding.
        This is to ensure that it'll get the response from the command
        given and not just some random data.
        """
        assert not subprocess.mswindows, "query() doesn't work in MS Windows"
        assert (self._stdout._file is not None), 'MPlayer stdout not PIPEd'
        if self._stdout._file is not None and name.lower().startswith('get_'):
            self._stdout._lock.acquire()
            # Consume all data in stdout before proceeding
            while self._stdout.readline() is not None:
                pass
            self.command(name)
            response = self._stdout.readline(timeout) or ''
            self._stdout._lock.release()
            if not response.startswith('ANS_'):
                return None
            ans = response.partition('=')[2].strip('\'"')
            if ans.isdigit():
                ans = int(ans)
            elif ans.count('.') == 1:
                try:
                    ans = float(ans)
                except ValueError:
                    pass
            elif ans == '(null)':
                ans = None
            return ans

    def get_property(self, name, timeout=0.25):
        """get_property(name, timeout=0.25)"""
        return self.query(' '.join(['get_property', name]), timeout)


class _FileWrapper(object):
    """Wrapper for stdout and stderr

    Exposes the fileno() and readline() methods
    Provides methods for management of subscribers (data handlers)
    """

    def __init__(self):
        self._file = None
        self._lock = Lock()
        self._subscribers = []

    def __call__(self, *args):
        """Publish data to subscribers"""
        if self._lock.locked() or self._file is None:
            return True
        data = self._file.readline().rstrip()
        if not data:
            return True
        for subscriber in self._subscribers:
            subscriber(data)
        return True

    def fileno(self):
        if self._file is not None:
            return self._file.fileno()

    if subprocess.mswindows:
        def readline(self, timeout=0):
            """This method will block in MS Windows"""
            if self._file is not None:
                return self._file.readline().rstrip()
    else:
        def readline(self, timeout=0):
            if self._file is not None and \
               select.select([self._file], [], [], timeout)[0]:
                return self._file.readline().rstrip()

    def hook(self, subscriber):
        if not hasattr(subscriber, '__call__'):
            raise TypeError("'%s' object is not callable" %
                (str(type(subscriber)).split("'")[1], ))
        try:
            self._subscribers.index(subscriber)
        except ValueError:
            self._subscribers.append(subscriber)
            return True
        else:
            return False

    def unhook(self, subscriber):
        try:
            self._subscribers.remove(subscriber)
        except ValueError:
            return False
        else:
            return True


if __name__ == '__main__':
    import sys

    player = MPlayer()
    player.args = sys.argv[1:]
    player.start()
    # block execution
    try:
        raw_input()
    except NameError: # raw_input() was renamed to input() in Python 3
        input()
