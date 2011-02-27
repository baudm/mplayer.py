# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011  Darwin M. Bautista <djclue917@gmail.com>
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


__all__ = [
    'PAUSING',
    'PAUSING_TOGGLE',
    'PAUSING_KEEP',
    'PAUSING_KEEP_FORCE',
    'Player',
    'Step'
    ]

# Command prefixes
PAUSING = 'pausing'
PAUSING_TOGGLE = 'pausing_toggle'
PAUSING_KEEP = 'pausing_keep'
PAUSING_KEEP_FORCE = 'pausing_keep_force'


class Step(object):
    """Step(value=0, direction=0)

    A vector which contains information about the step magnitude and direction.
    This is meant to be used with property access to implement
    the 'step_property' command like so:

        p.fullscreen = Step()
        p.time_pos = Step(50, -1)
    """

    def __init__(self, value=0, direction=0):
        self._val = value
        self._dir = direction


class Player(object):
    """Player(args=(), stdout=PIPE, stderr=None)

    @param stdout: subprocess.PIPE | None
    @param stderr: subprocess.PIPE | subprocess.STDOUT | None

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
    command_prefix = PAUSING_KEEP_FORCE
    query_timeout = 0.5

    def __init__(self, args=(), stdout=subprocess.PIPE, stderr=None):
        self.args = args
        self._proc = None
        assert stdout in (subprocess.PIPE, None), \
            'stdout should either be PIPE or None'
        assert stderr in (subprocess.PIPE, subprocess.STDOUT, None), \
            'stderr should be one of PIPE, STDOUT, or None'
        self._stdout = _FileWrapper(stdout)
        self._stderr = _FileWrapper(stderr)

    def __del__(self):
        # Be sure to stop the MPlayer process.
        self.quit()

    def __repr__(self):
        if self.is_alive():
            status = 'with pid = %d' % (self._proc.pid)
        else:
            status = 'not running'
        return '<%s.%s %s>' % (__name__, self.__class__.__name__, status)

    @staticmethod
    def _gen_sig(args):
        sig = []
        for i, arg in enumerate(args):
            if arg.startswith('['):
                arg = arg.strip('[]')
                arg = '%s%d=""' % (arg, i)
            else:
                arg = '%s%d' % (arg, i)
            sig.append(arg)
        sig = ', '.join(sig)
        # Append an extra comma
        if sig:
            sig += ','
        params = sig.replace('=""', '')
        return sig, params

    @staticmethod
    def _gen_propget(pname, ptype):
        if ptype != bool:
            def propget(self):
                res = self._query('get_property ' + pname)
                if res is not None:
                    return ptype(res)
        else:
            def propget(self):
                res = self._query('get_property ' + pname)
                if res is not None:
                    return (res == 'yes')
        return propget

    @staticmethod
    def _gen_propset(pname, ptype):
        if ptype != bool:
            def propset(self, value):
                if not isinstance(value, Step):
                    return self._command('set_property', pname, value)
                else:
                    return self._command('step_property', pname, value._val, value._dir)
        else:
            def propset(self, value):
                if not isinstance(value, Step):
                    return self._command('set_property', pname, int(value))
                else:
                    return self._command('step_property', pname)
        return propset

    @staticmethod
    def _gen_propdoc(ptype, pmin, pmax, propset):
        doc = ['Type: ' + str(ptype).split("'")[1]]
        if propset is not None and ptype != bool:
            if pmin != 'No':
                doc.append('Min: %s' % (pmin, ))
            if pmax != 'No':
                doc.append('Max: %s' % (pmax, ))
        if propset is None:
            doc.append('* Read-only')
        return '\n'.join(doc)

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

        Generate available methods and properties.
        """
        # Generate properties
        type_map = {
            'Flag': bool, 'Float': float, 'Integer': int,
            'Position': int, 'String': str, 'Time': float
        }
        get_include = ['length', 'pause', 'stream_end', 'stream_length',
            'stream_start']
        get_exclude = ['sub_delay']
        rename = {'pause': 'paused', 'path': 'filepath'}
        args = [cls.path, '-list-properties']
        mplayer = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE,
            universal_newlines=True)
        for line in mplayer.communicate()[0].split('\n'):
            line = line.split()
            if len(line) != 4 or line[0] == 'Name':
                continue
            pname, ptype, pmin, pmax = line
            ptype = type_map[ptype]
            propget = cls._gen_propget(pname, ptype)
            if (pmin == pmax == 'No' and pname not in get_exclude) or pname in get_include:
                propset = None
            else:
                propset = cls._gen_propset(pname, ptype)
            docstring = cls._gen_propdoc(ptype, pmin, pmax, propset)
            prop = property(propget, propset, doc=docstring)
            # Rename some properties to avoid conflict
            if pname in rename:
                pname = rename[pname]
            setattr(cls, pname, prop)
        # Generate methods
        exclude = ['tv_set_brightness', 'tv_set_contrast', 'tv_set_saturation',
            'tv_set_hue', 'vo_fullscreen', 'vo_ontop', 'vo_rootwin', 'vo_border',
            'osd', 'frame_drop']
        args = [cls.path, '-input', 'cmdlist']
        mplayer = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE,
            universal_newlines=True)
        for line in mplayer.communicate()[0].split('\n'):
            args = line.lower().split()
            if not args or (args[0].startswith('get_') and \
                    not args[0].startswith('get_meta')) or \
                    args[0].endswith('_property') or args[0] == 'quit':
                continue
            name = args.pop(0)
            # Skip conflicts with properties
            if hasattr(cls, name) or name in exclude:
                continue
            if not name.startswith('get_'):
                # Fix truncated command name
                if name.startswith('osd_show_property_'):
                    name = 'osd_show_property_text'
                sig, params = cls._gen_sig(args)
                code = '''
                def %(name)s(self, %(sig)s prefix=None):
                    """%(name)s(%(args)s)"""
                    return self._command('%(name)s', %(params)s prefix=prefix)
                ''' % dict(
                    name=name, args=', '.join(args),
                    sig=sig, params=params
                )
            else:
                code = '''
                def %(name)s(self, timeout=None, prefix=None):
                    """%(name)s()"""
                    return self._query('%(name)s', timeout, prefix)
                ''' % dict(name=name)
            local = {}
            exec(code.strip(), globals(), local)
            setattr(cls, name, local[name])

    def start(self):
        """Start the MPlayer process.

        Returns None if MPlayer is already running.
        """
        if not self.is_alive():
            args = [self.__class__.path]
            args.extend(self._args)
            # Start the MPlayer process (unbuffered)
            self._proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                stdout=self._stdout._handle, stderr=self._stderr._handle,
                universal_newlines=True)
            self._stdout._file = self._proc.stdout
            self._stderr._file = self._proc.stderr

    def quit(self, retcode=0):
        """Stop the MPlayer process.

        Returns the exit status of MPlayer or None if not running.
        """
        if self.is_alive():
            self._stdout._file = None
            self._stderr._file = None
            self._proc.stdin.write('quit %d\n' % (retcode, ))
            self._proc.stdin.flush()
            return self._proc.wait()

    def is_alive(self):
        """Check if MPlayer process is alive.

        Returns True if alive, else, returns False.
        """
        if self._proc is not None:
            return (self._proc.poll() is None)
        else:
            return False

    def _command(self, name, *args, **kwargs):
        """Send a command to MPlayer.

        @param name: command string

        Valid MPlayer commands are documented in:
        http://www.mplayerhq.hu/DOCS/tech/slave.txt
        """
        assert self.is_alive(), 'MPlayer not yet started'
        assert not 'quit'.startswith(name.split()[0].lower()), \
            'use the quit() method instead'
        if self.is_alive() and name:
            prefix = kwargs.get('prefix', self.command_prefix)
            if prefix is None:
                prefix = self.command_prefix
            command = [prefix, name]
            command.extend(map(str, args))
            command.append('\n')
            if name in ['pause', 'stop']:
                command.pop(0)
            self._proc.stdin.write(' '.join(command))
            self._proc.stdin.flush()

    def _query(self, name, timeout=None, prefix=None):
        """Send a query to MPlayer. The result is returned, if there is any.

        query() will first consume all data in stdout before proceeding.
        This is to ensure that it'll get the response from the command
        given and not just some random data.
        """
        assert not subprocess.mswindows, "query() doesn't work in MS Windows"
        assert (self._stdout._file is not None), 'MPlayer stdout not PIPEd'
        if self._stdout._file is not None and name.lower().startswith('get_'):
            if timeout is None:
                timeout = self.query_timeout
            self._stdout._lock.acquire()
            # Consume all data in stdout before proceeding
            while self._stdout._readline() is not None:
                pass
            self._command(name, prefix=prefix)
            response = self._stdout._readline(timeout) or ''
            self._stdout._lock.release()
            if not response.startswith('ANS_'):
                return None
            ans = response.partition('=')[2].strip('\'"')
            if ans in ['(null)', 'PROPERTY_UNAVAILABLE']:
                ans = None
            return ans


class _FileWrapper(object):
    """Wrapper for stdout and stderr

    Implements the publisher-subscriber design pattern.
    """

    def __init__(self, handle):
        self._handle = handle
        self._file = None
        self._lock = Lock()
        self._subscribers = []

    if subprocess.mswindows:
        def _readline(self, timeout=0):
            """This method will block in MS Windows"""
            if self._file is not None:
                return self._file.readline().rstrip()
    else:
        def _readline(self, timeout=0):
            if self._file is not None and \
               select.select([self._file], [], [], timeout)[0]:
                return self._file.readline().rstrip()

    def fileno(self):
        if self._file is not None:
            return self._file.fileno()

    def publish(self, *args):
        """Publish data to subscribers

        This is a callback for use with event loops of other frameworks.
        It is NOT meant to be called manually. Sample usage:

        m.stdout.hook(callback1)
        m.start()

        fd = m.stdout.fileno()
        cb = m.stdout.publish

        tkinter.createfilehandler(fd, tkinter.READABLE, cb)
        """
        if self._lock.locked() or self._file is None:
            return True
        data = self._file.readline().rstrip()
        if not data:
            return True
        for subscriber in self._subscribers:
            subscriber(data)
        return True

    def hook(self, subscriber):
        if not callable(subscriber):
            # Raise TypeError
            subscriber()
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
            return True
        else:
            return False

    def unhook(self, subscriber):
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
            return True
        else:
            return False


# Introspect on module load
try:
    Player.introspect()
except OSError:
    pass


if __name__ == '__main__':
    import sys

    player = Player()
    player.args = sys.argv[1:]
    player.start()
    # block execution
    try:
        raw_input()
    except NameError: # raw_input() was renamed to input() in Python 3
        input()
