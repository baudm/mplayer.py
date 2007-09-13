#!/usr/bin/env python

"""MPlayer remote control server
"""

__version__ = "$Revision$"
# $Source$

__date__ = "$Date$"

__copyright__ = """
Copyright (C) 2007  The MA3X Project (http://bbs.eee.upd.edu.ph)

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

    from pymplayer import MPlayerServer
except ImportError, msg:
    exit(msg)


def main():
    host = ''
    port = 50001
    max_connections = 2

    server = MPlayerServer(sys.argv[1:], host, port, max_connections)

    try:
        # start server
        server.start()
        # wait for server to terminate
        # (actually, this is to stop the server from terminating prematurely)
        server.wait()
    except KeyboardInterrupt:
        pass

    sys.exit()


if __name__ == "__main__":
    main()
