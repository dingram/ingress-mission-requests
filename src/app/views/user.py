import logging
import re

from google.appengine.api import users

from app.data import models
from app.util.request import RequestHandler


class Landing(RequestHandler):

  def get(self, *args, **kwargs):
    self.render_page('index.html', {
      'logged_in': self.gae_user is not None,
    })


class Signup(RequestHandler):

  def get(self, *args, **kwargs):
    self.user = models.User.get_current(allow_creation=True)
    self.render_page('signup.html')

  def post(self, *args, **kwargs):
    nickname = self.request.POST.get('nickname')
    faction = self.request.POST.get('faction')
    error = None

    self.user = models.User.get_current(allow_creation=True)
    try:
      self.check_xsrf_token(required=False)
    except:
      error = 'Invalid XSRF token'

    self.user.nickname = nickname
    self.user.faction = faction

    if not error and not nickname:
      error = 'No nickname'
    if not error and not re.match(r'[0-9a-zA-Z]{3,15}', nickname):
      error = 'Invalid nickname'
    if not error and not faction:
      error = 'No faction'
    if not error and faction not in ('ENLIGHTENED', 'RESISTANCE'):
      error = 'Invalid faction'
    if not error:
      u = models.User.fetch_by_nickname(nickname)
      if u and u.guid != self.user.guid:
        error = 'Nickname is already registered'

    if not error:
      self.user.put()
      self.redirect('/', abort=303)
      return
    else:
      self.render_page('signup.html', {'error': error})


# vim: et sw=2 ts=2 sts=2 cc=80
