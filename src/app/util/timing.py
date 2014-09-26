import logging

import webapp2

from app.util.helpers import to_us


DETAILED_TIMINGS = False


def format_us(time):
  if time < 1000:
    return '%dus' % time
  elif time < 1000000:
    return '%dms' % long(time/1000)
  else:
    return '%.02fs' % float(time/1000000)


class _StopwatchTimer(object):

  def __init__(self, stopwatch, name, nest=False):
    self.stopwatch = stopwatch
    self.name = name
    self.nest = nest

  def __enter__(self):
    self.stopwatch._start(self.name, log=self.nest)

  def __exit__(self, exc_type, exc_value, traceback):
    self.stopwatch._end(self.name, arrow=self.nest)


class Stopwatch(object):
  REQ_KEY = 'stopwatch'

  def __init__(self):
    self.clocks = {}
    self.order = []

  @classmethod
  def exists(cls):
    request = webapp2.get_request()
    return cls.REQ_KEY in request.registry and request.registry[cls.REQ_KEY]

  @classmethod
  def _get(cls):
    request = webapp2.get_request()
    if cls.REQ_KEY not in request.registry:
      request.registry[cls.REQ_KEY] = cls()
    return request.registry[cls.REQ_KEY]

  def _timer(self, name, nest=False):
    return _StopwatchTimer(self, name, nest)

  @classmethod
  def timer(cls, name, nest=False):
    return cls._get()._timer(name, nest)

  def _start(self, name, log=False):
    if name in self.clocks:
      logging.error('Clock "%s" has already been started!' % name)
      return
    if log and DETAILED_TIMINGS:
      logging.debug('[%s]: ->', name)
    self.order.append(name)
    # Very last thing...
    self.clocks[name] = to_us()

  @classmethod
  def start(cls, name, log=False):
    cls._get()._start(name, log)

  def _end(self, name, arrow=False):
    # Very first thing...
    ended_at = to_us()

    if name not in self.clocks:
      logging.error('Clock "%s" was never started!' % name)
      return

    # Find any unstopped timers
    names = []
    while True:
      if not self.order:
        break
      n = self.order.pop()
      names.append(n)
      if n == name:
        break

    # Clear all unstopped timers
    for n in names:
      if DETAILED_TIMINGS:
        duration = format_us(ended_at - self.clocks[n])
        logging.debug('[%s]: %s%s', n, '<- ' if arrow else '', duration)
      del self.clocks[n]

  @classmethod
  def end(cls, name, arrow=False):
    cls._get()._end(name)

  def _cancel(self, name):
    if name not in self.clocks:
      logging.error('Clock "%s" was never started!' % name)
      return

    # Find any unstopped timers
    names = []
    while True:
      if not self.order:
        break
      n = self.order.pop()
      names.append(n)
      if n == name:
        break

    # Clear all unstopped timers
    for n in names:
      del self.clocks[n]

  @classmethod
  def cancel(cls, name):
    cls._get()._cancel(name)

  def _flush(self):
    # Very first thing...
    ended_at = to_us()

    # Clear all unstopped timers
    for n in self.order[::-1]:
      if DETAILED_TIMINGS:
        logging.debug('[%s]: %s', n, format_us(ended_at - self.clocks[n]))
      del self.clocks[n]
    if self.clocks:
      logging.error('Some clocks left! %s', sorted(self.clocks.keys()))
    self.order = []
    self.clocks = {}

  @classmethod
  def flush(cls):
    cls._get()._flush()


# vim: et sw=2 ts=2 sts=2 cc=80
