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

    encode = staticmethod(str)

    @classmethod
    def has_instance(cls, value):
        """Check if value isinstance of type"""
        return isinstance(value, cls.types)


class FlagType(MPlayerType):

    name = 'bool'
    types = bool

    @staticmethod
    def decode(value):
        return ('yes' == value)

    @staticmethod
    def encode(value):
        return MPlayerType.encode(int(value))


class IntegerType(MPlayerType):

    name = 'int'
    types = int
    decode = staticmethod(int)


class FloatType(MPlayerType):

    name = 'float'
    types = (float, int)
    decode = staticmethod(float)


class StringType(MPlayerType):

    name = 'str'
    types = basestring

    @staticmethod
    def decode(value):
        return value


class StringListType(MPlayerType):

    name = 'dict'

    @staticmethod
    def decode(value):
        value = value.split(',')
        # For now, return list as a dict ('metadata' property)
        return dict(zip(value[::2], value[1::2]))

    @staticmethod
    def encode(value):
        raise NotImplementedError('not supported by MPlayer')


type_map = {
    'Flag': FlagType, 'Integer': IntegerType, 'Position': IntegerType,
    'Float': FloatType, 'Time': FloatType, 'String': StringType,
    'String list': StringListType
}
