import calendar
import datetime
import itertools
import json
import random
import re

from google.appengine.ext import db

import bitstring
import s2


def to_us(when=None):
  """Convert a datetime instance to microseconds since epoch.

  Args:
    when: The datetime instance to convert, or current UTC datetime if None.

  Returns:
    Integral number of microseconds since epoch.
  """
  if when is None:
    when = datetime.datetime.utcnow()
  return long((calendar.timegm(when.timetuple()) * 1000000) + when.microsecond)


def to_ms(when=None):
  """Convert a datetime instance to milliseconds since epoch.

  Args:
    when: The datetime instance to convert, or current UTC datetime if None.

  Returns:
    Integral number of milliseconds since epoch.
  """
  return long(to_us(when) / 1000)


def from_ms(when):
  """Convert a number of milliseconds since epoch to a UTC datetime instance.

  Args:
    when: The number of milliseconds since epoch.

  Returns:
    A datetime instance in UTC.
  """
  # TODO: test this around timezone changes etc?
  return datetime.datetime.utcfromtimestamp(when / 1000)


def grouper(n, iterable):
  """Allow iteration over an iterable in chunks of a defined size.

  Args:
    n: Chunk size.
    iterable: The base iterable to grou pinto chunks.

  Yields:
    A tuple containing at most n items from the iterable.
  """
  it = iter(iterable)
  while True:
    chunk = tuple(itertools.islice(it, n))
    if not chunk:
      return
    yield chunk


def slugify(words):
  """Convert an input string into a URL-safe form, suitable for use as a "slug".

  A slug can only contain the basic alphanumeric characters (no accents) and a
  dash. Disallowed characters are converted to dashes, runs of dashes are
  reduced to a single element, and dashes at the start or end are removed.

  Args:
    words: The input to convert

  Returns:
    The slugified string.
  """
  words = words.lower()
  words = re.sub(r'[^0-9a-zA-Z-]+', '-', words)
  words = re.sub(r'^-+', '', words)
  words = re.sub(r'-+$', '', words)
  return words


class JSONEncoder(json.JSONEncoder):
  """Special subclass of json.JSONEncoder to handle serialization of additional
  types."""

  def default(self, o):
    if hasattr(o, 'to_dict'):
      return o.to_dict()
    if hasattr(o, 'to_hash'):
      return o.to_hash()
    if isinstance(o, set):
      return list(o)
    if hasattr(o, 'timetuple') and hasattr(o, 'microsecond'):
      # datetime-like
      return to_ms(o)

    return super(JSONEncoder, self).default(o)


def json_encode(data, stream=None, **kwargs):
  if stream:
    json.dump(data, stream, separators=(',', ':'), cls=JSONEncoder, **kwargs)
  else:
    return json.dumps(data, separators=(',', ':'), cls=JSONEncoder, **kwargs)


class LocationHelper(object):
  """Collection of useful functions for dealing with locations."""
  REGION_BIT_SHIFT = 26
  LOCAL_BIT_SHIFT = 49

  REGIONS = ["AF", "AS", "NR", "PA", "AM", "ST"]
  CODEWORDS = [
      "ALPHA",
      "BRAVO",
      "CHARLIE",
      "DELTA",
      "ECHO",
      "FOXTROT",
      "GOLF",
      "HOTEL",
      "JULIET",
      "KILO",
      "LIMA",
      "MIKE",
      "NOVEMBER",
      "PAPA",
      "ROMEO",
      "SIERRA",
  ]
  RX_CELL = re.compile(
      '^(?:' + '|'.join(REGIONS) + ')'    # region name
      '(?:0[1-9]|1[0-6])-'                # region number
      '(?:' + '|'.join(CODEWORDS) + ')-'  # codeword
      '(?:0[0-9]|1[0-5])$'                # division number
  )

  @classmethod
  def _make_latlng(cls, *args, **kwargs):
    """Convert the arguments to a standardised lat/lng tuple. Accepted forms:

     - (lat, lng)
     - ([lat, lng])
     - ((lat, lng))
     - ('xxxx')                      [game-format hexE6 location]
     - ({'hex': z})                  [game-format hexE6 location]
     - ({'lat': x, 'lng': y})
     - ({'latE6': x, 'lngE6': y})
     - (hex=z)                       [game-format hexE6 location]
     - (lat=x, lng=y)
     - (latE6=x, lngE6=y)

    Also acceptable are objects with latDegrees/lngDegrees functions, or pairs
    of attributes:

     - lat/lng
     - lat/lon
     - latE6/lngE6
     - latE6/lonE6
    """
    if len(args):
      loc = args[0]
      if isinstance(loc, dict):
        return cls._make_latlng(**loc)
      elif isinstance(loc, list) or isinstance(loc, tuple):
        return cls._make_latlng(*loc)
      elif isinstance(loc, basestring):
        return (bitstring.BitArray(hex=loc[0:8]).int / 1e6,
            bitstring.BitArray(hex=loc[9:17]).int / 1e6)
      elif hasattr(loc, 'latDegrees') and hasattr(loc, 'lngDegrees'):
        return (loc.latDegrees(), loc.lngDegrees())
      elif hasattr(loc, 'lat') and hasattr(loc, 'lng'):
        return (loc.lat, loc.lng)
      elif hasattr(loc, 'lat') and hasattr(loc, 'lon'):
        return (loc.lat, loc.lon)
      elif hasattr(loc, 'latE6') and hasattr(loc, 'lngE6'):
        return (loc.latE6 / 1e6, loc.lngE6 / 1e6)
      elif hasattr(loc, 'latE6') and hasattr(loc, 'lonE6'):
        return (loc.latE6 / 1e6, loc.lonE6 / 1e6)
      elif len(args) == 2:
        return (args[0], args[1])
      else:
        raise ValueError('You must specify a location in a recognised format: '
          '%s' % (repr(args)))
    else:
      if 'lat' in kwargs and 'lng' in kwargs:
        return (kwargs['lat'], kwargs['lng'])
      elif 'latE6' in kwargs and 'lngE6' in kwargs:
        return (kwargs['latE6'] / 1e6, kwargs['lngE6'] / 1e6)
      elif 'hex' in kwargs:
        return (bitstring.BitArray(hex=kwargs['hex'][0:8]).int / 1e6,
            bitstring.BitArray(hex=kwargs['hex'][9:17]).int / 1e6)
      else:
        raise ValueError('You must specify a location in a recognised format: '
          '%s' % (repr(kwargs)))

  @classmethod
  def hex(cls, *args, **kwargs):
    """Convert a location to a game hex location."""
    latE6, lngE6 = cls.latlngE6(*args, **kwargs)
    return '%s,%s' % (bitstring.BitArray(int=latE6, length=32).hex,
        bitstring.BitArray(int=lngE6, length=32).hex)

  @classmethod
  def latlng(cls, *args, **kwargs):
    """Convert a location to a latitude/longitude pair tuple."""
    return cls._make_latlng(*args, **kwargs)

  @classmethod
  def latlngE6(cls, *args, **kwargs):
    """Convert a location to a latitude/longitude E6 pair tuple."""
    lat, lng = cls._make_latlng(*args, **kwargs)
    return (int(lat * 1e6), int(lng * 1e6))

  @classmethod
  def latlngE6_dict(cls, *args, **kwargs):
    """Convert a location to a latitude/longitude E6 dict."""
    lat, lng = cls._make_latlng(*args, **kwargs)
    return {'latE6': int(lat * 1e6), 'lngE6': int(lng * 1e6)}

  @classmethod
  def db_geopt(cls, *args, **kwargs):
    """Convert a location to a db.GeoPt object."""
    latlng = cls._make_latlng(*args, **kwargs)
    return db.GeoPt(*latlng)

  @classmethod
  def s2latlng(cls, *args, **kwargs):
    """Convert a location to a s2.S2LatLng object."""
    latlng = cls._make_latlng(*args, **kwargs)
    return s2.S2LatLng.fromDegrees(*latlng)

  @classmethod
  def s2cellid(cls, *args, **kwargs):
    """Convert a location to an s2.S2CellId object."""
    latlng = cls.s2latlng(*args, **kwargs)
    return s2.S2CellId.fromLatLng(latlng)

  @classmethod
  def scoring_cell(cls, *args, **kwargs):
    """Convert a location to the name of an Ingress scoring cell."""
    latlng = cls._make_latlng(*args, **kwargs)
    s2cell = s2.S2CellId.fromLatLng(s2.S2LatLng.fromDegrees(*latlng))
    i, j, face = s2cell.toFaceIJOrientation(0, 0, None)

    region_name = cls.REGIONS[face]
    i = int(i >> cls.REGION_BIT_SHIFT)
    j = int(j >> cls.REGION_BIT_SHIFT)
    if face % 2:
      region_number = j + 1
      codeword = cls.CODEWORDS[i]
    else:
      region_number = i + 1
      codeword = cls.CODEWORDS[j]
    division = int((s2cell.pos() >> cls.LOCAL_BIT_SHIFT) & 0xF)

    return '%s%02d-%s-%02d' % (
        region_name,
        region_number,
        codeword,
        division,
    )

  @classmethod
  def is_cell_name(cls, cell):
    """Return whether the given string is a valid cell name.
    """
    return bool(cls.RX_CELL.match(cell))


# vim: et sw=2 ts=2 sts=2 cc=80
