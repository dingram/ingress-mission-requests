from google.appengine.api import oauth
from google.appengine.api import users


SCOPE_BASE = 'https://www.googleapis.com/auth/'

SCOPE_PROFILE = 'profile'
SCOPE_EMAIL = 'email'
SCOPE_OLD_PROFILE = SCOPE_BASE + 'userinfo.profile'
SCOPE_OLD_EMAIL = SCOPE_BASE + 'userinfo.email'

SCOPE_PLUS_LOGIN = SCOPE_BASE + 'plus.login'
SCOPE_PLUS_EMAIL = SCOPE_BASE + 'plus.profile.emails.read'

SCOPES = [SCOPE_OLD_PROFILE, SCOPE_OLD_EMAIL]


def get_current_user():
  try:
    return oauth.get_current_user(SCOPES)
  except oauth.Error as e:
    return users.get_current_user()


def is_current_user_admin():
  try:
    return oauth.is_current_user_admin(SCOPES)
  except oauth.Error as e:
    return users.is_current_user_admin()


def get_client_id():
  try:
    return oauth.get_client_id(SCOPES)
  except oauth.Error as e:
    return None


def is_oauth():
  return get_client_id() is not None


# vim: et sw=2 ts=2 sts=2 cc=80
