import collections


def enum(*sequential, **named):
  """Create an enum-like type."""
  enums = collections.OrderedDict(zip(sequential, sequential), **named)
  _keys = enums.keys()
  _values = enums.values()
  enums.update({'_keys':_keys, '_values':_values})
  return type(r'Enum', (), enums)


Faction = enum('UNKNOWN', 'ENLIGHTENED', 'RESISTANCE')

# vim: et sw=2 ts=2 sts=2 cc=80
