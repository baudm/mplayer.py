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
from functools import partial
from threading import Thread
try:
    import queue
except ImportError:
    import Queue as queue

from mplayer import mtypes


__all__ = [
    'Player',
    'CmdPrefix',
    'Step'
    ]


class CmdPrefix(object):
    """MPlayer command prefixes"""

    NONE = ''
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
        if not isinstance(value, mtypes.FloatType.type):
            raise TypeError('expected float for value')
        if not isinstance(direction, mtypes.IntegerType.type):
            raise TypeError('expected int for direction')
        self._val = mtypes.FloatType.adapt(value)
        self._dir = mtypes.IntegerType.adapt(direction)


class Player(object):
    """
    An out-of-process wrapper for MPlayer. It exposes MPlayer commands and
    properties as Python methods and properties, respectively.

    Take note that MPlayer is always started in 'slave', 'idle', and 'quiet' modes.

    @class attr exec_path: path to the MPlayer executable
    @class attr cmd_prefix: prefix for MPlayer commands (see CmdPrefix class)
    """

    exec_path = 'mplayer'
    cmd_prefix = CmdPrefix.PAUSING_KEEP_FORCE

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
            status = 'with pid = {0}'.format(self._proc.pid)
        else:
            status = 'not running'
        return '<{0} {1}>'.format(self.__class__.__name__, status)

    @property
    def args(self):
        """list of additional MPlayer arguments"""
        return self._args[7:]

    @args.setter
    def args(self, args):
        _args = ['-slave', '-idle', '-quiet', '-input', 'nodefault-bindings',
            '-noconfig', 'all']
        # Assume that args is a string.
        try:
            args = shlex.split(args)
        except AttributeError:
            # Force all args to string
            args = map(str, args)
        _args.extend(args)
        self._args = _args

    def _propget(self, pname, ptype):
        res = self._run_command('get_property', pname)
        if res is not None:
            return ptype.convert(res)

    def _propset(self, value, pname, ptype, pmin, pmax):
        if not isinstance(value, Step):
            if not isinstance(value, ptype.type):
                raise TypeError('expected {0}'.format(ptype.name))
            if pmin is not None and value < pmin:
                raise ValueError('value must be at least {0}'.format(pmin))
            if pmax is not None and value > pmax:
                raise ValueError('value must be at most {0}'.format(pmax))
            value = ptype.adapt(value)
            self._run_command('set_property', pname, value)
        else:
            self._run_command('step_property', pname, value._val, value._dir)

    @staticmethod
    def _gen_propdoc(ptype, pmin, pmax, propset):
        doc = ['type: {0}'.format(ptype.name)]
        if propset is not None:
            if pmin is not None:
                doc.append('min: {0}'.format(pmin))
            if pmax is not None:
                doc.append('max: {0}'.format(pmax))
        else:
            doc.append('(read-only)')
        return '\n'.join(doc)

    @classmethod
    def _generate_properties(cls):
        # Properties which don't have pmin == pmax == None but are read-only
        read_only = ['length', 'pause', 'stream_end', 'stream_length',
            'stream_start', 'stream_time_pos']
        rename = {'pause': 'paused'}
        args = [cls.exec_path, '-list-properties']
        proc = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE)
        for line in proc.stdout:
            line = line.decode().split()
            if not line or not line[0].islower():
                continue
            try:
                pname, ptype, pmin, pmax = line
            except ValueError:
                pname, ptype, ptype2, pmin, pmax = line
                ptype += ' ' + ptype2
            # Get the corresponding Python type and convert pmin and pmax
            ptype = mtypes.type_map[ptype]
            pmin = ptype.convert(pmin) if pmin != 'No' else None
            pmax = ptype.convert(pmax) if pmax != 'No' else None
            # Generate property fget
            propget = partial(cls._propget, pname=pname, ptype=ptype)
            # Generate property fset
            if (pmin is None and pmax is None and pname != 'sub_delay') or \
               pname in read_only:
                propset = None
            else:
                # Min and max values don't make sense for FlagType
                if ptype is mtypes.FlagType:
                    pmin = pmax = None
                propset = partial(cls._propset, pname=pname, ptype=ptype,
                                  pmin=pmin, pmax=pmax)
            # Generate property doc
            propdoc = cls._gen_propdoc(ptype, pmin, pmax, propset)
            prop = property(propget, propset, doc=propdoc)
            # Rename some properties to avoid conflict
            if pname in rename:
                pname = rename[pname]
            assert not hasattr(cls, pname), "name conflict for '{0}'".format(pname)
            setattr(cls, pname, prop)

    @staticmethod
    def _process_args(*args, **kwargs):
        """Discard None args, check types, then adapt for MPlayer"""
        # Get number of required parameters
        req = kwargs['req']
        # Discard None only from optional args
        args = list(args[:req]) + [x for x in args[req:] if x is not None]
        types = kwargs['types']
        for i, arg in enumerate(args):
            if not isinstance(arg, types[i].type):
                msg = 'expected {0} for argument {1}'.format(types[i].name, i + 1)
                raise TypeError(msg)
            args[i] = types[i].adapt(arg)
        return tuple(args)

    @staticmethod
    def _gen_func_sig(args):
        sig = []
        types = []
        required = 0
        for i, arg in enumerate(args):
            if not arg.startswith('['):
                optional = ''
                required += 1
            else:
                arg = arg.strip('[]')
                optional = '=None'
            t = mtypes.type_map[arg]
            sig.append('{0}{1}{2},'.format(t.name, i, optional))
            types.append('mtypes.{0}'.format(t.__name__))
        sig = ''.join(sig)
        params = sig.replace('=None', '')
        types = '({0},)'.format(','.join(types)) if types else '()'
        return sig, params, types, required

    @classmethod
    def _generate_methods(cls):
        # Commands to exclude
        exclude = ['tv_set_brightness', 'tv_set_contrast', 'tv_set_saturation',
            'tv_set_hue', 'vo_fullscreen', 'vo_ontop', 'vo_rootwin', 'vo_border',
            'osd', 'frame_drop']
        # Commands which have truncated names in -input cmdlist
        truncated = {'osd_show_property_te': 'osd_show_property_text'}
        args = [cls.exec_path, '-input', 'cmdlist']
        proc = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE)
        for line in proc.stdout:
            args = line.decode().split()
            # Skip get_* and *_property commands
            if not args or args[0].startswith('get_') or \
                    args[0].endswith('_property'):
                continue
            name = args.pop(0)
            # Skip conflicts with properties or defined methods
            if hasattr(cls, name) or name in exclude:
                continue
            # Fix truncated command names
            if name in truncated:
                name = truncated[name]
            # As of now, there's no way of specifying a function's signature
            # without dynamically generating code
            sig, params, types, req = cls._gen_func_sig(args)
            code = '''
            def {name}(self, {sig}):
                args = self._process_args({params} types={types}, req={req})
                return self._run_command('{name}', *args)
            '''.format(name=name, sig=sig, params=params, types=types, req=req)
            local = {}
            exec(code.strip(), globals(), local)
            setattr(cls, name, local[name])

    @classmethod
    def introspect(cls):
        """Introspect the MPlayer executable

        Generate available methods and properties based on the output of:
        $ mplayer -input cmdlist
        $ mplayer -list-properties

        See also http://www.mplayerhq.hu/DOCS/tech/slave.txt
        """
        cls._generate_properties()
        cls._generate_methods()

    def spawn(self):
        """Spawn the underlying MPlayer process."""
        if self.is_alive():
            return
        args = [self.__class__.exec_path]
        args.extend(self._args)
        # Start the MPlayer process (unbuffered)
        self._proc = subprocess.Popen(args, stdin=subprocess.PIPE,
            stdout=self._stdout._handle, stderr=self._stderr._handle,
            close_fds=(not subprocess.mswindows))
        self._stdout._attach(self._proc.stdout)
        self._stderr._attach(self._proc.stderr)

    def quit(self, retcode=0):
        """Terminate the underlying MPlayer process.
        Returns the exit status of MPlayer or None if not running.
        """
        if not self.is_alive():
            return
        self._stdout._detach()
        self._stderr._detach()
        self._run_command('quit', mtypes.IntegerType.adapt(retcode))
        return self._proc.wait()

    def is_alive(self):
        """Check if MPlayer process is alive.
        Returns True if alive, else, returns False.
        """
        if self._proc is not None:
            return (self._proc.poll() is None)
        else:
            return False

    def _run_command(self, name, *args):
        """Send a command to MPlayer. The result, if any, is returned.
        args is assumed to be a tuple of strings.
        """
        if not self.is_alive() or not name:
            return
        command = [self.__class__.cmd_prefix, name]
        command.extend(args)
        command.append('\n')
        # Don't prefix the following commands
        if name in ['quit', 'pause', 'stop']:
            command.pop(0)
        command = ' '.join(command).encode()
        self._proc.stdin.write(command)
        self._proc.stdin.flush()
        # Expect a response for 'get_property' only
        if name == 'get_property' and self._proc.stdout is not None:
            # The reponses for properties start with 'ANS_<property name>'
            key = 'ANS_{0}'.format(args[0])
            while True:
                try:
                    res = self._stdout._answers.get(timeout=1.0)
                except queue.Empty:
                    return
                if res.startswith(key):
                    break
                if res.startswith('ANS_ERROR'):
                    return
            ans = res.partition('=')[2].strip('\'"')
            if ans == '(null)':
                ans = None
            return ans


class _FileWrapper(object):
    """Wrapper for stdout and stderr"""

    def __init__(self, handle):
        self._handle = handle
        self._file = None
        self._answers = None

    def _attach(self, file):
        if file is None:
            return
        self._file = file
        self._answers = queue.Queue()
        t = Thread(target=self._process_output)
        t.daemon = True
        t.start()

    def _detach(self):
        self._file = None

    def _process_output(self):
        while self._file is not None:
            line = self._file.readline().decode().rstrip()
            if line.startswith('ANS_'):
                self._answers.put_nowait(line)
        # Cleanup
        self._answers = None


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
