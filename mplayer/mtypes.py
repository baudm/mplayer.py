# -*- coding: utf-8 -*-
#
# Copyright (C) 2011  Darwin M. Bautista <djclue917@gmail.com>
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

# Python 2.x compatibility
try:
    basestring
except NameError:
    basestring = str


class MPlayerType(object):
    """The base MPlayer type.

    This class and its subclasses aren't really types. They simply encapsulate
    all the information regarding a specific MPlayer type. In particular:

    name - human-readable name of the type
    type - valid Python type(s) for this type (for use with isinstance())
    convert - a callable which converts MPlayer responses
              to the corresponding Python object
    adapt - a callable which adapts a Python object into a type (str)
            suitable for MPlayer's stdin
    """

    name = None
    type = None
    convert = None
    adapt = staticmethod(str)


class FlagType(MPlayerType):

    name = 'bool'
    type = bool

    @staticmethod
    def convert(value):
        return ('yes' == value)

    @staticmethod
    def adapt(value):
        return MPlayerType.adapt(int(value))


class IntegerType(MPlayerType):

    name = 'int'
    type = int
    convert = staticmethod(int)


class FloatType(MPlayerType):

    name = 'float'
    type = (float, int)
    convert = staticmethod(float)


class StringType(MPlayerType):

    name = 'str'
    type = basestring

    @staticmethod
    def convert(value):
        """Value is already a string"""
        return value


class StringListType(MPlayerType):

    name = 'dict'

    @staticmethod
    def convert(value):
        value = value.split(',')
        # For now, return list as a dict ('metadata' property)
        return dict(zip(value[::2], value[1::2]))

    @staticmethod
    def adapt(value):
        raise NotImplementedError('not supported by MPlayer')


type_map = {
    'Flag': FlagType, 'Integer': IntegerType, 'Position': IntegerType,
    'Float': FloatType, 'Time': FloatType, 'String': StringType,
    'String list': StringListType
}
