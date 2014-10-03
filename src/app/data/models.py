import datetime
import logging

from google.appengine.ext import ndb

import s2

from app.data import AutoUuidProperty
from app.data import GuidModel
from app.data import GuidProperty
from app.data import GuidSuffix
from app.data import enums
from app.util import users
from app.util.helpers import json_encode
from app.util.helpers import to_ms
from app.util.timing import Stopwatch


MAPS_KEY = 'AIzaSyAxWfqskGbf7ozRLh-fIzs-B5b0pmpI-a8'


class User(GuidModel):
  """Datastore representation of a user."""
  guid = GuidProperty(suffix=GuidSuffix.USER, indexed=True)
  user_id = ndb.StringProperty(indexed=True)
  email = ndb.StringProperty(indexed=True)
  created = ndb.DateTimeProperty(indexed=False, auto_now_add=True)
  gplus_id = ndb.StringProperty(indexed=True, default=None)
  gplus_name = ndb.StringProperty(indexed=False, default=None)
  nickname = ndb.StringProperty(indexed=False)
  nickname_lower = ndb.StringProperty(indexed=True)
  faction = ndb.StringProperty(indexed=True,
    choices=enums.Faction._values, default=enums.Faction.UNKNOWN)
  avatar = ndb.BlobKeyProperty(indexed=False)
  avatar_url = ndb.StringProperty(indexed=False)
  timezone = ndb.StringProperty(indexed=True, default=None)
  is_superadmin = ndb.BooleanProperty(indexed=False, default=False)
  is_mission_creator = ndb.BooleanProperty(indexed=False, default=False)
  is_banned = ndb.BooleanProperty(indexed=False, default=False)
  xsrf_key = AutoUuidProperty(indexed=False)
  accepted_guidelines = ndb.DateTimeProperty(indexed=False)
  accepted_creator_guidelines = ndb.DateTimeProperty(indexed=False)

  def _prepare_for_put(self):
    """Prepare model for putting to the datastore.

    Overridden to set nickname_lower."""
    super(User, self)._prepare_for_put()
    if self.nickname_lower != self.nickname.lower():
      self.nickname_lower = self.nickname.lower()

  @classmethod
  def current_from_gae_user(cls, gae_user, allow_creation=False):
    """Return a User object for an App Engine user, optionally creating one.

    Args:
      gae_user: An App Engine user object representing the User we want.
      allow_creation: Boolean. If False and there is no matching User in the
        datastore, the function returns None. If True, a new User will be
        created if necessary but NOT saved to the datastore.

    Returns:
      A User model object, or None.
    """
    if not gae_user:
      return None
    user = cls.fetch_by_user_id(gae_user.user_id())
    if allow_creation and user is None:
      user = cls(
        id=gae_user.user_id(),
        user_id=gae_user.user_id(),
        email=gae_user.email().lower(),
        created=datetime.datetime.utcnow(),
      )
    return user

  @classmethod
  def get_current(cls, allow_creation=False):
    """Return a User object for the currently logged-in App Engine user,
    optionally creating one.

    Args:
      allow_creation: Boolean. If False and there is no matching User in the
        datastore, the function returns None. If True, a new User will be
        created if necessary but NOT saved to the datastore.

    Returns:
      A User model object, or None if there is no user logged in.
    """
    return cls.current_from_gae_user(users.get_current_user(), allow_creation)

  @classmethod
  def fetch_by_guid(cls, guid):
    """Return a user model with the given GUID.

    Args:
      guid: String. GUID of the user to fetch.

    Returns:
      A User object if one with the given GUID exists, otherwise None.
    """
    # Overridden because the primary key is more useful as the user ID
    return cls.query(cls.guid == guid).get()

  @classmethod
  def fetch_by_nickname(cls, nickname):
    """Return a user model with the given (case-insensitive) nickname.

    Args:
      nickname: String. Nickname of the user to fetch.

    Returns:
      A User object if one with the given nickname exists, otherwise None.
    """
    return cls.query(cls.nickname_lower == nickname.lower()).get()

  @classmethod
  def fetch_by_user_id(cls, user_id):
    """Return a user model with the given App Engine user ID.

    Args:
      user_id: String. ID of the user to fetch.

    Returns:
      A User object if one with the given user ID exists, otherwise None.
    """
    return cls.get_by_id(user_id)

  @classmethod
  def fetch_by_email(cls, email):
    """Return a user model with the given email address.

    Args:
      email: String. Email address of the user to fetch.

    Returns:
      A User object if one with the given email address exists, otherwise None.
    """
    return cls.query(cls.email == email.lower()).get()


class MissionAuditLogEntry(ndb.Model):
  """Datastore representation of an action log entry."""
  created_at = ndb.DateTimeProperty(indexed=False, auto_now_add=True)
  action = ndb.StringProperty(indexed=False)
  action_detail = ndb.StringProperty(indexed=False)

  actor_guid = ndb.StringProperty(indexed=False)
  actor_nickname = ndb.StringProperty(indexed=False)
  actor_faction = ndb.StringProperty(indexed=False)

  @classmethod
  def make_entry(cls, actor, action, action_detail=None):
    return cls(
        created_at=datetime.datetime.utcnow(),
        action=action,
        action_detail=action_detail,
        actor_guid=actor.guid,
        actor_nickname=actor.nickname,
        actor_faction=actor.faction,
    )

  @classmethod
  def drafted(cls, user):
    return cls.make_entry(actor=user, action='DRAFTED')

  @classmethod
  def sent_for_review(cls, user):
    return cls.make_entry(actor=user, action='SENT_FOR_REVIEW')

  @classmethod
  def being_reviewed(cls, user):
    return cls.make_entry(actor=user, action='BEING_REVIEWED')

  @classmethod
  def accepted(cls, user):
    return cls.make_entry(actor=user, action='ACCEPTED')

  @classmethod
  def needs_revision(cls, user, details):
    return cls.make_entry(actor=user, action='NEEDS_REVISION',
        action_detail=details)

  @classmethod
  def rejected(cls, user, details):
    return cls.make_entry(actor=user, action='REJECTED', action_detail=details)

  @classmethod
  def being_created(cls, user):
    return cls.make_entry(actor=user, action='BEING_CREATED')

  @classmethod
  def created(cls, user):
    return cls.make_entry(actor=user, action='CREATED')

  @classmethod
  def published(cls, user):
    return cls.make_entry(actor=user, action='PUBLISHED')

  @classmethod
  def re_sent_for_review(cls, user):
    return cls.make_entry(actor=user, action='RE_SENT_FOR_REVIEW')


class MissionWaypoint(GuidModel):
  """Datastore representation of a mission waypoint."""
  guid = GuidProperty(suffix=GuidSuffix.MISSION_WAYPOINT, indexed=False)
  created = ndb.DateTimeProperty(indexed=False, auto_now_add=True)

  type = ndb.StringProperty(indexed=False, choices=enums.WaypointType._values)
  portal_title = ndb.StringProperty(indexed=False)
  latE6 = ndb.IntegerProperty(indexed=False)
  lngE6 = ndb.IntegerProperty(indexed=False)
  location_clue = ndb.StringProperty(indexed=False)
  description = ndb.StringProperty(indexed=False)
  question = ndb.StringProperty(indexed=False)
  passphrase = ndb.StringProperty(indexed=False)
  s2_cells = ndb.StringProperty(indexed=False, repeated=True)

  def _prepare_for_put(self):
    """Prepare model for putting to the datastore.

    Overridden to set s2_cells."""
    super(MissionWaypoint, self)._prepare_for_put()
    cells = set()
    base_cellid = s2.S2CellId.fromLatLng(s2.S2LatLng.fromE6(self.latE6,
      self.lngE6))
    for lvl in range(14, 0, -2):
      cells.add('%x' % base_cellid.parent(lvl).id)
    if set(self.s2_cells) != cells:
      self.s2_cells = sorted(cells)

  def lat(self):
    return float(self.latE6) / 1e6

  def lng(self):
    return float(self.lngE6) / 1e6

  def map_url(self):
    import motionless
    m = motionless.DecoratedMap(350, 150, 'satellite')
    m.key = MAPS_KEY
    m.add_marker(motionless.LatLonMarker(
      float(self.latE6) / 1e6,
      float(self.lngE6) / 1e6,
      size='mid',
      color='red',
    ))
    return m.generate_url()


class Mission(GuidModel):
  """Datastore representation of a mission."""
  guid = GuidProperty(suffix=GuidSuffix.MISSION, indexed=True)
  owner_guid = ndb.StringProperty(indexed=True)
  owner_email = ndb.StringProperty(indexed=False)
  owner_nickname = ndb.StringProperty(indexed=True)
  owner_faction = ndb.StringProperty(indexed=True)
  last_modified = ndb.DateTimeProperty(indexed=True, auto_now=True)
  drafted = ndb.DateTimeProperty(indexed=True, auto_now_add=True)
  sent_for_review = ndb.DateTimeProperty(indexed=True)
  started_review = ndb.DateTimeProperty(indexed=True)
  finished_review = ndb.DateTimeProperty(indexed=True)
  rejection_reason = ndb.StringProperty(indexed=False, default='')
  mission_creation_began = ndb.DateTimeProperty(indexed=True)
  mission_creation_complete = ndb.DateTimeProperty(indexed=True)
  mission_published = ndb.DateTimeProperty(indexed=True)
  reviewer_guid = ndb.StringProperty(indexed=True)
  reviewer_nickname = ndb.StringProperty(indexed=True)
  reviewer_faction = ndb.StringProperty(indexed=True)
  publisher_guid = ndb.StringProperty(indexed=True)
  publisher_nickname = ndb.StringProperty(indexed=True)
  publisher_faction = ndb.StringProperty(indexed=True)
  state = ndb.StringProperty(indexed=True, choices=enums.MissionState._values,
      default=enums.MissionState.DRAFT)

  s2_cells = ndb.StringProperty(indexed=True, repeated=True)
  geo_city = ndb.StringProperty(indexed=True, repeated=True)
  geo_country = ndb.StringProperty(indexed=True, repeated=True)
  geo_description = ndb.StringProperty(indexed=True)

  title = ndb.StringProperty(indexed=True)
  description = ndb.StringProperty(indexed=False)
  type = ndb.StringProperty(indexed=True, choices=enums.MissionType._values)
  icon_url = ndb.StringProperty(indexed=False)
  waypoints = ndb.LocalStructuredProperty(MissionWaypoint, repeated=True)
  city = ndb.StringProperty(indexed=True)
  country_code = ndb.StringProperty(indexed=True)
  attn = ndb.StringProperty(indexed=True)

  audit_log = ndb.LocalStructuredProperty(MissionAuditLogEntry, repeated=True)

  def _prepare_for_put(self):
    """Prepare model for putting to the datastore.

    Overridden to set s2_cells from waypoints."""
    super(Mission, self)._prepare_for_put()
    cells = set()
    for w in self.waypoints:
      cells.update(w.s2_cells)
    if set(self.s2_cells) != cells:
      self.s2_cells = sorted(cells)

  @classmethod
  def new_draft(cls, owner):
    m = cls(
        owner_guid=owner.guid,
        owner_email=owner.email,
        owner_nickname=owner.nickname,
        owner_faction=owner.faction,
    )
    m.audit_log.append(MissionAuditLogEntry.drafted(owner))
    return m

  def status_icon(self):
    if self.state == 'DRAFT':
      return 'create'
    elif self.state == 'AWAITING_REVIEW':
      return 'cloud-queue'
    elif self.state == 'UNDER_REVIEW':
      return 'assignment'
    elif self.state == 'ACCEPTED':
      return 'thumb-up'
    elif self.state == 'NEEDS_REVISION':
      return 'assignment-return'
    elif self.state == 'REJECTED':
      return 'thumb-down'
    elif self.state == 'CREATING':
      return 'cached'
    elif self.state == 'CREATED':
      return 'check-circle'
    elif self.state == 'PUBLISHED':
      return 'visibility'
    elif self.state == 'DEPUBLISHED':
      return 'visibility-off'
    else:
      return 'error'

  def status_color(self):
    if self.state == 'DRAFT':
      return '#616161' # grey 700
    elif self.state == 'AWAITING_REVIEW':
      return '#212121' # grey 900
    elif self.state == 'UNDER_REVIEW':
      return '#ffb74d' # orange 300
    elif self.state == 'ACCEPTED':
      return '#259b24' # green 500
    elif self.state == 'NEEDS_REVISION':
      return '#ff9800' # orange 500
    elif self.state == 'REJECTED':
      return '#e51c23' # red 500
    elif self.state == 'CREATING':
      return '#7986cb' # indigo 300
    elif self.state == 'CREATED':
      return '#3f51b5' # indigo 500
    elif self.state == 'PUBLISHED':
      return '#009688' # teal 500
    elif self.state == 'DEPUBLISHED':
      return '#f36c60' # red 300
    else:
      return '#b0120a' # red 900

  def is_incomplete(self):
    """Return whether this mission is definitely incomplete (i.e. not eligible
    to be published).
    """
    if not self.title or not self.description or not self.type:
      return True
    if len(self.waypoints) < 4:
      return True
    return False

  def map_url_overview(self):
    import motionless
    m = motionless.DecoratedMap(600, 450, 'satellite', pathcolor='red')
    m.key = MAPS_KEY
    num = 0
    try:
      for w in self.waypoints:
        num += 1
        m.add_marker(motionless.LatLonMarker(
          float(w.latE6) / 1e6,
          float(w.lngE6) / 1e6,
          size='mid',
          color='yellow' if num == 1 else 'red',
          label=str(num % 10),
        ))
        m.add_path_latlon(
          '%.06f' % (float(w.latE6) / 1e6),
          '%.06f' % (float(w.lngE6) / 1e6),
        )
      return m.generate_url()
    except:
      logging.exception('Map failed to generate')
      return ''

  def map_url_mini(self):
    import motionless
    m = motionless.DecoratedMap(96, 96, 'roadmap', zoom=6)
    m.key = MAPS_KEY
    try:
      if self.waypoints:
        m.add_marker(motionless.LatLonMarker(
          float(self.waypoints[0].latE6) / 1e6,
          float(self.waypoints[0].lngE6) / 1e6,
          size='tiny',
          color='red',
        ))
      return m.generate_url()
    except:
      logging.exception('Map failed to generate')
      return ''

# vim: et sw=2 ts=2 sts=2 cc=80
