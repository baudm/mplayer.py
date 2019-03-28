### mplayer.py at a glance
```
>>> p = mplayer.Player()
>>> p.loadfile('/path/to/file.mkv')
>>> p.time_pos = 40
>>> print p.length
```

# News
## Version 0.7.2 Released! _(March 28, 2019)_
I will no longer update the PyPi releases. Just install it via pip like so:
```
$ pip install git+https://github.com/baudm/mplayer.py.git@0.7.2
```

  * Don't pause upon initially loading file (Fixes #32)

## Version 0.7.1 Released! _(May 8, 2017)_
You can download it here: http://pypi.python.org/pypi/mplayer.py/0.7.1

  * Various MPlayer2 fixes
  * Fix subprocess.mswindows error in python3.5+
  * Add a gevent-friendly Player subclass.

## Version 0.7.0 Released! _(September 8, 2011)_
You can download it here: http://pypi.python.org/pypi/mplayer.py/0.7.0

  * Expose ALL commands except `get_*` and `*_property` commands and those which have the same name as their corresponding property.
  * Better `QPlayerView` and `GtkPlayerView` widgets; the `Player` objects are now directly accessible via the `player` property.
  * Getting output from MPlayer is now thread-safe (a `Queue` is now used)
  * Data can now be obtained asynchronously from `Player` objects (via subscribers/callbacks)
  * Improved generation of properties (using `functools.partial` objects)
  * Added type checking to generated methods and properties
  * Added value checking to generated properties
  * Abstracted MPlayer type handling away from the core (see `mtypes` module)
  * Python 2.x unicode and str fixes

**Don't forget to read the CHANGES file.**

## Switched to git _(September 7, 2011)_
The **code** of mplayer.py (formerly PyMPlayer/python-mplayer) is now hosted at [GitHub](https://github.com/baudm/mplayer.py).

**NOTE:** Issues and wiki are still hosted here at Google Code.

_Since python-mplayer is a very verbose and long name, let's just call it mplayer.py :)_

## Version 0.6.0 Released! _(March 3, 2011)_
You can download it here: http://pypi.python.org/pypi/PyMPlayer/

  * Support for MPlayer property access (`get_property`, `set_property`, `step_property`) with automatic type conversion via standard Python properties (new-style classes)
  * Drop methods which have the same functionality as their corresponding properties (for cleaner API)
  * No more exposed `command()` and `query()` methods; use the higher-level methods and properties instead
  * Improved code generation; generated methods execute faster than in 0.5.0
  * [Introspection](Introspection.md) now happens on module load, not on instantiation
  * MPlayer is now spawned automatically (See `autospawn` parameter)
  * Setting of command prefix globally (i.e. per class) and per method execution is supported
  * Full support for Windows (for `get_` commands)

**Don't forget to read the CHANGES file.**

# What is mplayer.py?

Initially known as **PyMPlayer** (http://pypi.python.org/pypi/PyMPlayer/ renamed to avoid confusion with other projects), **mplayer.py** provides several Pythonic interfaces to MPlayer. These are implemented as the following classes (see [Introspection](https://github.com/baudm/mplayer.py/wiki/Introspection) for more info):

  1. **[Player](https://github.com/baudm/mplayer.py/wiki/Player)** provides a clean, Pythonic interface to MPlayer.
  2. **[AsyncPlayer](https://github.com/baudm/mplayer.py/wiki/AsyncPlayer)** is a _Player_ subclass with asyncore integration (POSIX only).
  3. **[GPlayer](https://github.com/baudm/mplayer.py/wiki/GPlayer)** is a _Player_ subclass with GTK/GObject integration.
  4. **[QtPlayer](https://github.com/baudm/mplayer.py/wiki/QtPlayer)** is a _Player_ subclass with Qt integration (same usage as AsyncPlayer)
  5. **[GtkPlayerView](https://github.com/baudm/mplayer.py/wiki/GtkPlayerView)** provides a basic (as of now) PyGTK widget that embeds MPlayer.
  6. **[QPlayerView](https://github.com/baudm/mplayer.py/wiki/QPlayerView)** provides a PyQt4 widget similar to _GtkPlayerView_ in functionality.

Show your appreciation by saying thanks or by donating a small amount.

[![](http://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=Q929MN4LWEUPS&lc=PH&item_name=python%2dmplayer&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted)
