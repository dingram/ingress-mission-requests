import datetime
import logging

from google.appengine.ext import ndb

from app.data import AutoUuidProperty
from app.data import GuidModel
from app.data import GuidProperty
from app.data import GuidSuffix
from app.data import enums
from app.util import users
from app.util.helpers import json_encode
from app.util.helpers import to_ms
from app.util.timing import Stopwatch


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
  is_banned = ndb.BooleanProperty(indexed=False, default=False)
  xsrf_key = AutoUuidProperty(indexed=False)

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


# vim: et sw=2 ts=2 sts=2 cc=80
