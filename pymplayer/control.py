#
# control.py SVN r10
#

try:
  from pymplayer.base import MPlayer
except ImportError, msg:
  exit(msg)


class MPlayerControl(MPlayer):
  """
  MPlayer wrapper with commands implemented as functions
  This is useful for easily controlling MPlayer in Python
  """

  def alt_src_step(self, value):
    """
    (ASX playlist only)
    When more than one source is available it selects the next/previous one.
    """
    pass

  def audio_delay(self, value, abs=0):
    """
    audio_delay(value, abs=0)

    Set/adjust the audio delay.
    If [abs] is not given or is zero, adjust the delay by <value> seconds.
    If [abs] is nonzero, set the delay to <value> seconds.
    """
    self.command("audio_delay %f %d" % (value, abs))

  def set_video_param(self, param, value, abs=0):
    """
    set_video_param(param, value, abs=0)

    param = [brightness|contrast|gamma|hue|saturation]
    Set/adjust video parameters.
    If [abs] is not given or is zero, modifies parameter by <value>.
    If [abs] is non-zero, parameter is set to <value>.
    <value> is in the range [-100, 100].
    """
    if type(param) != type(""):
      raise TypeError, "param must be a string"

    if type(value) != type(0):
      raise TypeError, "value must be an integer"

    if type(value) != type(0):
      raise TypeError, "abs must be an integer"

    if param.lower() not in ('brightness', 'contrast', 'gamma', 'hue', 'saturation'):
      raise ValueError, "param = [brightness|contrast|gamma|hue|saturation]"

    if not -100 <= value <= 100:
      raise ValueError, "value is in the range [-100, 100]"

    self.command("set_video_param %s %f %d" % (param, value, abs))


  def change_rectangle(self, val1, val2):
    """
    Change the position of the rectangle filter rectangle.
        <val1>
            Must be one of the following:
                0 = width
                1 = height
                2 = x position
                3 = y position
        <val2>
            If <val1> is 0 or 1:
                Integer amount to add/subtract from the width/height.
                Positive values add to width/height and negative values
                subtract from it.
            If <val1> is 2 or 3:
                Relative integer amount by which to move the upper left
                rectangle corner. Positive values move the rectangle
                right/down and negative values move the rectangle left/up.
    """
    if type(val1) != type(0):
      raise TypeError, "val1 must be an integer"

    if type(val2) != type(0):
      raise TypeError, "val2 must be an integer"

    if val1 not in (0, 1, 2, 3):
      raise ValueError, "val1 must be one of the ff: 0, 1, 2, 3"

    self.command("change_rectangle %d %d" % (val1, val2))


  def dvb_set_channel(self, channel_number, card_number):
    """
    Set DVB channel.
    """
    pass

  def dvdnav(self, button):
    """
    Press the given dvdnav button.
        1 up
        2 down
        3 left
        4 right
        5 menu
        6 select
    """
    if type(button) != type(0):
      raise TypeError, "button must be an integer"

    if button not in (1, 2, 3, 4, 5, 6):
      raise ValueError, "button must be on of the ff: 1, 2, 3, 4, 5, 6"

    self.command("dvdnav %d" % button)


  def edl_mark(self):
    """
    Write the current position into the EDL file.
    """
    self.command("edl_mark")


  def frame_drop(self, value):
    """
    Toggle/set frame dropping mode.
    """
    pass

  def get_audio_bitrate(self):
    """
    Print out the audio bitrate of the current file.
    """
    return self.command("get_audio_bitrate")

  def get_audio_codec(self):
    """
    Print out the audio codec name of the current file.
    """
    return self.command("get_audio_codec")

  def get_audio_samples(self):
    """
    Print out the audio frequency and number of channels of the current file.
    """
    return self.command("get_audio_samples")

  def get_file_name(self):
    """
    Print out the name of the current file.
    """
    return self.command("get_file_name")

  def get_meta_album(self):
    """
    Print out the 'Album' metadata of the current file.
    """
    return self.command("get_meta_album")

  def get_meta_artist(self):
    """
    Print out the 'Artist' metadata of the current file.
    """
    return self.command("get_meta_artist")

  def get_meta_comment(self):
    """
    Print out the 'Comment' metadata of the current file.
    """
    return self.command("get_meta_comment")

  def get_meta_genre(self):
    """
    Print out the 'Genre' metadata of the current file.
    """
    return self.command("get_meta_genre")

  def get_meta_title(self):
    """
    Print out the 'Title' metadata of the current file.
    """
    return self.command("get_meta_title")

  def get_meta_track(self):
    """
    Print out the 'Track Number' metadata of the current file.
    """
    return self.command("get_meta_track")

  def get_meta_year(self):
    """
    Print out the 'Year' metadata of the current file.
    """
    return self.command("get_meta_year")

  def get_percent_pos(self):
    """
    Print out the current position in the file, as integer percentage [0-100).
    """
    return self.command("get_percent_pos")

  def get_property(self, property):
    """
    Print out the current value of a property.
    """
    return self.command("get_property "+property)

  def get_sub_visibility(self):
    """
    Print out subtitle visibility (1 == on, 0 == off).
    """
    return self.command("get_sub_visibility")

  def get_time_length(self):
    """
    Print out the length of the current file in seconds.
    """
    return self.command("get_time_length")

  def get_time_pos(self):
    """
    Print out the current position in the file in seconds, as float.
    """
    return self.command("get_time_pos")

  def get_vo_fullscreen(self):
    """
    Print out fullscreen status (1 == fullscreened, 0 == windowed).
    """
    return self.command("get_vo_fullscreen")

  def get_video_bitrate(self):
    """
    Print out the video bitrate of the current file.
    """
    return self.command("get_video_bitrate")

  def get_video_codec(self):
    """
    Print out the video codec name of the current file.
    """
    return self.command("get_video_codec")

  def get_video_resolution(self):
    """
    Print out the video resolution of the current file.
    """
    return self.command("get_video_resolution")

  def screenshot(self, value):
    """
    Take a screenshot. Requires the screenshot filter to be loaded.
        0 Take a single screenshot.
        1 Start/stop taking screenshot of each frame.
    """
    if type(value) != type(0):
      raise TypeError, "value must be an integer"

    if value not in (0, 1):
      raise ValueError, "value must be either 0 or 1"

    self.command("screenshot %d" % value)


  #GUI actions
  def gui_about(self):
    self.command("gui_about")

  def gui_loadfile(self):
    self.command("gui_loadfile")

  def gui_loadsubtitle(self):
    self.command("gui_loadsubtitle")

  def gui_play(self):
    self.command("gui_play")

  def gui_playlist(self):
    self.command("gui_playlist")

  def gui_preferences(self):
    self.command("gui_preferences")

  def gui_skinbrowser(self):
    self.command("gui_skinbrowser")

  def gui_stop(self):
    self.command("gui_stop")


  def key_down_event(self, value):
    """
    Inject <value> key code event into MPlayer.
    """
    pass

  def loadfile(self, filename, append=0):
    """
    Load the given file/URL, stopping playback of the current file/URL.
    If <append> is nonzero playback continues and the file/URL is
    appended to the current playlist instead.
    """
    try:
      file = open(filename, "rb")
      file.close()
    except IOError:
      raise IOError, "file not found or isn't readable"
    except TypeError:
      raise TypeError, "filename should be a string"

    self.command("loadfile %s %d" % (filename, append))

  def loadlist(self, playlist, append=0):
    """
    Load the given playlist file, stopping playback of the current file.
    If <append> is nonzero playback continues and the playlist file is
    appended to the current playlist instead.
    """
    try:
      file = open(playlist, "rb")
      file.close()
    except IOError:
      raise IOError, "playlist not found or isn't readable"
    except TypeError:
      raise TypeError, "filename should be a string"

    self.command("loadlist %s %d" % (playlist, append))

  def menu(self, command):
    """
    Execute an OSD menu command.
        up     Move cursor up.
        down   Move cursor down.
        ok     Accept selection.
        cancel Cancel selection.
        hide   Hide the OSD menu.
    """
    if type(command) != type(""):
      raise TypeError, "command should be a string"

    if command not in ("up", "down", "ok", "cancel", "hide")
      raise ValueError, "command should be one of the ff: up, down, ok, cancel, hide"

    self.command("menu "+command)

  def set_menu(self, menu_name):
    """
    Display the menu named <menu_name>.
    """
    pass

  def mute(self, value=None):
    """
    Toggle sound output muting or set it to [value] when [value] >= 0
    (1 == on, 0 == off).
    """
    if value != None:
      self.command("mute")
    else:
      self.command("mute %d" % value)

  def osd(self, level=None):
    """
    Toggle OSD mode or set it to [level] when [level] >= 0.
    """
    pass

  def osd_show_property_text(self, string, duration=None, level=0):
    """
    Show an expanded property string on the OSD, see -playing-msg for a
    description of the available expansions. If [duration] is >= 0 the text
    is shown for [duration] ms. [level] sets the minimum OSD level needed
    for the message to be visible (default: 0 - always show).
    """
    pass

  def osd_show_text(self, string, duration=0, level=0):
    """
    Show <string> on the OSD.
    """
    pass

  #def panscan <-1.0 - 1.0> | <0.0 - 1.0> <abs>
    """
    Increase or decrease the pan-and-scan range by <value>, 1.0 is the maximum.
    Negative values decrease the pan-and-scan range.
    If <abs> is != 0, then the pan-and scan range is interpreted as an
    absolute range.
    """
    #pass

  def pause(self):
    """
    Pause/unpause the playback.
    """
    self.command("pause")

  def frame_step(self):
    """
    Play one frame, then pause again.
    """
    self.command("frame_step")

  def pt_step(self, value, force=0):
    """
    Go to the next/previous entry in the playtree. The sign of <value> tells
    the direction.  If no entry is available in the given direction it will do
    nothing unless [force] is non-zero.
    """
    self.command("pt_step %s %d" % (value, force))

  def pt_up_step(self, value, force=0):
    """
    Similar to pt_step but jumps to the next/previous entry in the parent list.
    Useful to break out of the inner loop in the playtree.
    """
    self.command("pt_up_step %s %d" % (value, force))

  #def quit(self, value=0):
    """
    Quit MPlayer. The optional integer [value] is used as the return code
    for the mplayer process (default: 0).
    """
    #self.__del__(value)

  def radio_set_channel(self, channel):
    """
    Switch to <channel>. The 'channels' radio parameter needs to be set.
    """
    pass

  def radio_set_freq(self, frequency):
    """
    Set the radio tuner frequency (in MHz).
    """
    pass

  #def radio_step_channel <-1|1>
    """
    Step forwards (1) or backwards (-1) in channel list. Works only when the
    'channels' radio parameter was set.
    """
    #pass

  def radio_step_freq(self, value):
    """
    Tune frequency by the <value> (positive - up, negative - down).
    """
    pass

  def seek(self, value, type=0):
    """
    Seek to some place in the movie.
        0 is a relative seek of +/- <value> seconds (default).
        1 is a seek to <value> % in the movie.
        2 is a seek to an absolute position of <value> seconds.
    """
    self.command("seek %s %d" % (value, type))

  def seek_chapter(self, value, type=0):
    """
    Seek to the start of a chapter.
        0 is a relative seek of +/- <value> chapters (default).
        1 is a seek to chapter <value>.
    """
    pass

  def set_mouse_pos(self, x, y):
    """
    Tells MPlayer the coordinates of the mouse in the window.
    This command doesn't move the mouse!
    """
    pass

  def set_property(self, property, value):
    """
    Set a property.
    """
    return self.command("set_property "+property+" "+value)

  def speed_incr(self, value):
    """
    Add <value> to the current playback speed.
    """
    pass

  def speed_mult(self, value):
    """
    Multiply the current speed by <value>.
    """
    pass

  def speed_set(self, value):
    """
    Set the speed to <value>.
    """
    pass

  def step_property(self, property, value=None, direction=None):
    """
    Change a property by value, or increase by a default if value is
    not given or zero. The direction is reversed if direction is less
    than zero.
    """
    pass
    #return self.command("step_property "+property)

  def sub_alignment(self, value=0):
    """
    Toggle/set subtitle alignment.
        0 top alignment
        1 center alignment
        2 bottom alignment
    """
    pass

  def sub_delay(self, value, abs=False):
    """
    Adjust the subtitle delay by +/- <value> seconds or set it to <value>
    seconds when [abs] is nonzero.
    """
    pass

  def sub_load(self, subtitle_file):
    """
    Loads subtitles from <subtitle_file>.
    """
    pass

  def sub_log(self):
    """
    Logs the current or last displayed subtitle together with filename
    and time information to ~/.mplayer/subtitle_log. Intended purpose
    is to allow convenient marking of bogus subtitles which need to be
    fixed while watching the movie.
    """
    pass

  def sub_pos(self, value, abs=False):
    """
    Adjust/set subtitle position.
    """
    pass

  def sub_remove(self, value=None):
    """
    If the [value] argument is present and non-negative, removes the subtitle
    file with index [value]. If the argument is omitted or negative, removes
    all subtitle files.
    """
    pass

  def sub_select(self, value=None):
    """
    Display subtitle with index [value]. Turn subtitle display off if
    [value] is -1 or greater than the highest available subtitle index.
    Cycle through the available subtitles if [value] is omitted or less
    than -1. Supported subtitle sources are -sub options on the command
    line, VOBsubs, DVD subtitles, and Ogg and Matroska text streams.
    """
    pass

  def vobsub_lang(self):
    """
    This is a stub linked to sub_select for backwards compatibility.
    """
    pass

  def sub_step(self, value):
    """
    Step forward in the subtitle list by <value> steps or backwards if <value>
    is negative.
    """
    pass

  def sub_visibility(self, value=False):
    """
    Toggle/set subtitle visibility.
    """
    pass

  def forced_subs_only(self, value=False):
    """
    Toggle/set forced subtitles only.
    """
    pass

  def switch_audio(self, value=None):
    """
    (MPEG and Matroska only)
    Switch to the audio track with the id [value]. Cycle through the
    available tracks if [value] is omitted or negative.
    """
    pass

  def switch_ratio(self, value=None):
    """
    Change aspect ratio at runtime. [value] is the new aspect ratio expressed
    as a float (e.g. 1.77778 for 16/9).
    There might be problems with some video filters.
    """
    pass

  def switch_vsync(self, value=None):
    """
    Toggle vsync (1 == on, 0 == off). If [value] is not provided,
    vsync status is inverted.
    """
    pass

  def tv_step_channel(self, channel):
    """
    Select next/previous TV channel.
    """
    pass

  def tv_step_norm(self):
    """
    Change TV norm.
    """
    pass

  def tv_step_chanlist(self):
    """
    Change channel list.
    """
    pass

  def tv_set_channel(self, channel):
    """
    Set the current TV channel.
    """
    pass

  def tv_last_channel(self):
    """
    Set the current TV channel to the last one.
    """
    pass

  def tv_set_freq(self, frequency):
    """
    <frequency> in MHz
    Set the TV tuner frequency.
    """
    pass

  def tv_step_freq(self, frequency):
    """
    frequency offset in MHz>
    Set the TV tuner frequency relative to current value.
    """
    pass

  def tv_set_norm(self, norm):
    """
    Set the TV tuner norm (PAL, SECAM, NTSC, ...).
    """
    pass

  """def tv_set_brightness <-100 - 100> [abs]
    #Set TV tuner brightness or adjust it if [abs] is set to 0.

tv_set_contrast <-100 -100> [abs]
    Set TV tuner contrast or adjust it if [abs] is set to 0.

tv_set_hue <-100 - 100> [abs]
    Set TV tuner hue or adjust it if [abs] is set to 0.

tv_set_saturation <-100 - 100> [abs]
    Set TV tuner saturation or adjust it if [abs] is set to 0.
    """

  def use_master(self):
    """
    Switch volume control between master and PCM.
    """
    self.command("use_master")

  def vo_border(self, value=0):
    """
    Toggle/set borderless display.
    """
    pass

  def vo_fullscreen(self, value=0):
    """
    Toggle/set fullscreen mode.
    """
    self.command("vo_fullscreen")

  def vo_ontop(self, value=0):
    """
    Toggle/set stay-on-top.
    """
    pass

  def vo_rootwin(self, value=0):
    """
    Toggle/set playback on the root window.
    """
    pass

  def volume(self, value, abs=0):
    """
    Increase/decrease volume or set it to <value> if [abs] is nonzero.
    """
    pass


#The following commands are really only useful for OSD menu console mode:

  def help(self):
    """
    Displays help text, currently empty.
    """
    pass

  def exit(self):
    """
    Exits from OSD menu console. Unlike 'quit', does not quit MPlayer.
    """
    pass

  def hide(self):
    """
    Hides the OSD menu console. Clicking a menu command unhides it. Other
    keybindings act as usual.
    """
    pass

  def run(self, value):
    """
    Run <value> as shell command. In OSD menu console mode stdout and stdin
    are through the video output driver.
    """
    pass
