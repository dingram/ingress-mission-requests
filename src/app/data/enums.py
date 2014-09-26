import collections


def enum(*sequential, **named):
  """Create an enum-like type."""
  enums = collections.OrderedDict(zip(sequential, sequential), **named)
  _keys = enums.keys()
  _values = enums.values()
  enums.update({'_keys':_keys, '_values':_values})
  return type(r'Enum', (), enums)


Faction = enum('UNKNOWN', 'ENLIGHTENED', 'RESISTANCE')

MissionState = enum(
    'DRAFT',            # Incomplete or not submitted for review
    'AWAITING_REVIEW',  # Submitted for review
    'UNDER_REVIEW',     # Being reviewed
    'ACCEPTED',         # Accepted for creation
    'NEEDS_REVISION',   # Needs changing
    'REJECTED',         # Rejected
    'CREATING',         # Being created
    'CREATED',          # Created!
    'PUBLISHED',        # Published and playable
    'DEPUBLISHED',      # Was published, now unpublished
)

MissionType = enum('ANY_ORDER', 'SEQUENTIAL', 'SEQUENTIAL_HIDDEN')

WaypointType = enum(
    'HACK_PORTAL',
    'INSTALL_ANY_MOD',
    'CAPTURE_PORTAL',
    'LINK_FROM_PORTAL',
    'FIELD_FROM_PORTAL',
    'ENTER_PASSPHRASE',
    'FIELD_TRIP_CARD',
)

# vim: et sw=2 ts=2 sts=2 cc=80
