#
# base.py 0.1.6
#

try:
  from subprocess import Popen, PIPE
  from time import sleep
  #from os import getcwd
  from threading import Thread
  import re
except ImportError, msg:
  exit(msg)

#from os import O_NONBLOCK
#from fcntl import fcntl, F_SETFL

"""
import threading

class MPlayerChecker(threading.Thread):

  Thread to continuously poll MPlayer subprocess every <interval> seconds


  def __init__(self, poll, interval=1.0):
    self.interval = interval
    self._poll = poll
    threading.Thread.__init__ (self)

  def run(self):
    while True:
      sleep(self.interval)
      if self._poll() != None:
        raise OSError, "MPlayer died unexpectedly"
"""

class BenchmarkThread(Thread):
  def __init__(self, mplayer):
    self._mplayer = mplayer
    Thread.__init__(self)

  # TODO: add some checks here
  # while block will loop forever... find a way to stop it
  def run(self):
    benchmark = re.compile("Playing |BENCHMARK(s|%):")
    output = ""
    #result = ""
    #counter = 0

    while True:
      try:
        output = self._mplayer._subprocess.stdout.readline()
      except sys.excepthook:
        break

      if benchmark.match(output):
        file = open(self._mplayer.benchmark_log, "a")
        file.writelines(output)
        file.close()
        #result += output
        #counter += 1
        #if counter == 3:
          #file = open(self.logfile, "a")
          #file.writelines(result+"\n")
          #file.close()
          #result = ""
          #counter = 0


class MPlayer:
  """
  MPlayer wrapper for Python
  Provides the basic interface for sending commands and receiving responses to and from MPlayer
  Responsible for starting up MPlayer in slave mode
  """

  def __init__(self, args=(), benchmark_log="benchmark.log"):
    # args must either be a tuple or a list
    if type(args) not in ( type([]), type(()) ):
      raise TypeError, "args should either be a tuple or list of strings"

    if len(args) > 0:
      for arg in args:
        if type(arg) != type(""):
          raise TypeError, "args should either be a tuple or list of strings"

    if type(benchmark_log) != type(""):
      raise TypeError, "benchmark log should be a string"

    self.benchmark_log = benchmark_log

    self.cmdline = ["mplayer", "-slave", "-idle", "-quiet"]
    self.cmdline.extend(args)

    #self._subprocess = Popen(self.cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=getcwd(), universal_newlines=True)
    self._subprocess = Popen(self.cmdline, stdin=PIPE)

    # Wait for MPlayer to start
    sleep(0.25)

    # If MPlayer died unexpectedly (maybe the args are invalid/incorrect), raise an exception
    if self._subprocess.poll() != None:
      raise OSError, "MPlayer died unexpectedly (possibly invalid/incorrect args)"

    #if self.cmdline.count("-benchmark") != 0:
      # Start benchmark thread
      #BenchmarkThread(self).start()


  def __del__(self):
    if self._subprocess.poll() == None:
      self.command("quit")
      self._subprocess.wait()


  def isrunning(self):
    return True if self._subprocess.poll() == None else False


  def playlists(self):
    """
    Returns the list of playlists based on MPlayer cmdline
    """
    playlists = []
    idx = 0

    for match in range(self.cmdline.count("-playlist")):
      try:
        idx = self.cmdline.index("-playlist", idx)+1
      except ValueError:
	break
      try:
        playlists.append(self.cmdline[idx])
      except IndexError:
        break

    return playlists


  def command(self, cmd):
    if type(cmd) != type(""):
      raise TypeError, "command must be a string"

    #if len(cmd) == 0:
    #  raise ValueError, "zero-length command"

    self._subprocess.stdin.write(cmd+"\n")

    """
    cmd_error = re.compile("Command "+cmd+" requires.")
    error = ""

    while True:
      try:
        error = self._subprocess.stderr.readline()
        if cmd_error.match(error):
          break
      except IOError:
        error = ""
        break

    if error != "":
      return error
    """

    """
    get_cmd = re.compile("get_.")

    if get_cmd.match(cmd.lower()):
      ans = re.compile("ANS_.*='.*'")
      output = ""

      sleep(0.1)

      while ans.match(output) == None:
        try:
          output = self._subprocess.stdout.readline()
        except IOError:
          output = ""
          break

      try:
        return output.split("=", 1)[1].strip("'\n")
      except IndexError:
        return None
    """
