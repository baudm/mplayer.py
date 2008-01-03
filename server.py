#!/usr/bin/env python
# $Id$

"""MPlayer remote control server"""

__copyright__ = """
Copyright (C) 2007-2008  The MA3X Project (http://bbs.eee.upd.edu.ph)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


try:
    import sys
    import socket
except ImportError, msg:
    exit(msg)
from pymplayer import Server


def main():
    try:
        server = Server(args=sys.argv[1:], max_conn=2)
    except socket.error, msg:
        sys.exit(msg)
    server.start()
    try:
        server.wait()
    except KeyboardInterrupt:
        pass

    server.stop()
    sys.exit()


if __name__ == "__main__":
    main()
