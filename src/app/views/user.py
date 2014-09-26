import logging

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


# vim: et sw=2 ts=2 sts=2 cc=80
