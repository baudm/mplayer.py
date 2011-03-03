# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011  Darwin M. Bautista <djclue917@gmail.com>
#
# This file is part of PyMPlayer.
#
# PyMPlayer is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyMPlayer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with PyMPlayer.  If not, see <http://www.gnu.org/licenses/>.

import shlex
import subprocess
from threading import Lock


__all__ = [
    'Player',
    'CommandPrefix',
    'Step'
    ]


class CommandPrefix(object):
    """MPlayer command prefixes"""

    PAUSING = 'pausing'
    PAUSING_TOGGLE = 'pausing_toggle'
    PAUSING_KEEP = 'pausing_keep'
    PAUSING_KEEP_FORCE = 'pausing_keep_force'


class Step(object):
    """
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
    """
    An out-of-process wrapper for MPlayer. It provides the basic
    interface for sending commands and receiving responses to and from
    MPlayer. Take note that MPlayer is always started in 'slave',
    'idle', and 'quiet' modes.

    @class attr path: path to the MPlayer executable
    @class attr command_prefix: prefix for MPlayer commands (see CommandPrefix)
    @property args: MPlayer arguments
    @property stdout: process' stdout (read-only)
    @property stderr: process' stderr (read-only)
    """

    path = 'mplayer'
    command_prefix = CommandPrefix.PAUSING_KEEP_FORCE

    def __init__(self, args=(), stdout=subprocess.PIPE, stderr=None, autospawn=True):
        self.args = args
        self._stdout = _FileWrapper(stdout)
        self._stderr = _FileWrapper(stderr)
        self._proc = None
        if autospawn:
            self.spawn()

    def __del__(self):
        # Be sure to stop the MPlayer process.
        self.quit()

    def __repr__(self):
        if self.is_alive():
            status = 'with pid = %d' % (self._proc.pid)
        else:
            status = 'not running'
        return '<%s.%s %s>' % (__name__, self.__class__.__name__, status)

    @property
    def args(self):
        """list of MPlayer arguments"""
        return self._args[7:]

    @args.setter
    def args(self, args):
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

    @property
    def stdout(self):
        """stdout of the MPlayer process"""
        return self._stdout

    @property
    def stderr(self):
        """stderr of the MPlayer process"""
        return self._stderr

    @staticmethod
    def _gen_propget(pname, ptype):
        if ptype not in [bool, dict]:
            def propget(self):
                res = self._command('get_property', pname)
                if res is not None:
                    return ptype(res)
        elif ptype == bool:
            def propget(self):
                res = self._command('get_property', pname)
                if res is not None:
                    return (res == 'yes')
        else:
            def propget(self):
                res = self._command('get_property', pname)
                if res is not None:
                    res = res.split(',')
                    # For now, return list as a dict ('metadata' property)
                    return dict(zip(res[::2], res[1::2]))
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

    @staticmethod
    def _gen_func_sig(args):
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

    @classmethod
    def _generate_properties(cls):
        type_map = {
            'Flag': bool, 'Float': float, 'Integer': int, 'Position': int,
            'Time': float, 'String': str, 'String list': dict
        }
        read_only = ['length', 'pause', 'stream_end', 'stream_length',
            'stream_start']
        read_write = ['sub_delay']
        rename = {'pause': 'paused', 'path': 'filepath'}
        args = [cls.path, '-list-properties']
        mplayer = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE)
        for line in mplayer.stdout:
            line = line.decode().split()
            if not line or not line[0].islower():
                continue
            try:
                pname, ptype, pmin, pmax = line
            except ValueError:
                pname, ptype, ptype2, pmin, pmax = line
                ptype = ' '.join([ptype, ptype2])
            ptype = type_map[ptype]
            propget = cls._gen_propget(pname, ptype)
            if (pmin == pmax == 'No' and pname not in read_write) or pname in read_only:
                propset = None
            else:
                propset = cls._gen_propset(pname, ptype)
            propdoc = cls._gen_propdoc(ptype, pmin, pmax, propset)
            prop = property(propget, propset, doc=propdoc)
            # Rename some properties to avoid conflict
            if pname in rename:
                pname = rename[pname]
            setattr(cls, pname, prop)

    @classmethod
    def _generate_methods(cls):
        exclude = ['tv_set_brightness', 'tv_set_contrast', 'tv_set_saturation',
            'tv_set_hue', 'vo_fullscreen', 'vo_ontop', 'vo_rootwin', 'vo_border',
            'osd', 'frame_drop']
        args = [cls.path, '-input', 'cmdlist']
        mplayer = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE)
        for line in mplayer.stdout:
            args = line.decode().lower().split()
            # Skip get_* (except get_meta_*), *_property, and quit commands
            if not args or (args[0].startswith('get_') and \
                    not args[0].startswith('get_meta')) or \
                    args[0].endswith('_property') or args[0] == 'quit':
                continue
            name = args.pop(0)
            # Skip conflicts with properties
            if hasattr(cls, name) or name in exclude:
                continue
            # Fix truncated command name
            if name.startswith('osd_show_property_'):
                name = 'osd_show_property_text'
            sig, params = cls._gen_func_sig(args)
            code = '''
            def %(name)s(self, %(sig)s prefix=None):
                return self._command('%(name)s', %(params)s prefix=prefix)
            ''' % dict(name=name, sig=sig, params=params)
            local = {}
            exec(code.strip(), globals(), local)
            setattr(cls, name, local[name])

    @classmethod
    def introspect(cls):
        """Introspect the MPlayer executable

        Generate available methods and properties.
        See http://www.mplayerhq.hu/DOCS/tech/slave.txt
        """
        cls._generate_properties()
        cls._generate_methods()

    def spawn(self):
        """Spawn the underlying MPlayer process.

        Returns None if MPlayer is already running.
        """
        if self.is_alive():
            return
        args = [self.__class__.path]
        args.extend(self._args)
        # Start the MPlayer process (unbuffered)
        self._proc = subprocess.Popen(args, stdin=subprocess.PIPE,
            stdout=self._stdout._handle, stderr=self._stderr._handle,
            close_fds=(not subprocess.mswindows))
        self._stdout._file = self._proc.stdout
        self._stderr._file = self._proc.stderr

    def quit(self, retcode=0):
        """Terminate the underlying MPlayer process.

        Returns the exit status of MPlayer or None if not running.
        """
        if not self.is_alive():
            return
        self._stdout._file = None
        self._stderr._file = None
        self._command('quit', retcode)
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
        """Send a command to MPlayer. The result, if any, is returned."""
        if not self.is_alive() or not name:
            return
        prefix = kwargs.get('prefix', self.__class__.command_prefix)
        if prefix is None:
            prefix = self.__class__.command_prefix
        command = [prefix, name]
        command.extend(map(str, args))
        command.append('\n')
        if name in ['quit', 'pause', 'stop']:
            command.pop(0)
        command = ' '.join(command).encode()
        # For non-getter commands, simply send the command
        if not name.startswith('get_'):
            self._proc.stdin.write(command)
            self._proc.stdin.flush()
        # For getter commands, expect a result
        elif self._proc.stdout is not None:
            with self._stdout._lock:
                self._proc.stdin.write(command)
                self._proc.stdin.flush()
                while True:
                    response = self._proc.stdout.readline().decode().rstrip()
                    if response.startswith('ANS_'):
                        break
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

    def fileno(self):
        if self._file is not None:
            return self._file.fileno()

    def publish(self, *args):
        """Publish data to subscribers

        This is a callback for use with event loops of other frameworks.
        It is NOT meant to be called manually. Sample usage:

        m.stdout.hook(callback1)

        fd = m.stdout.fileno()
        cb = m.stdout.publish

        tkinter.createfilehandler(fd, tkinter.READABLE, cb)
        """
        if self._lock.locked() or self._file is None:
            return True
        data = self._file.readline().decode().rstrip()
        if not data:
            return True
        for subscriber in self._subscribers:
            subscriber(data)
        return True

    def hook(self, subscriber):
        if not hasattr(subscriber, '__call__'):
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

    player = Player(sys.argv[1:])
    # block execution
    try:
        raw_input()
    except NameError: # raw_input() was renamed to input() in Python 3
        input()
