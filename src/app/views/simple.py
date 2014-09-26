import logging

from google.appengine.api import users

from app.util.request import RequestHandler


class Login(RequestHandler):
  def get(self, *args, **kwargs):
    self.redirect(users.create_login_url(
      self.request.route_kwargs.get('_uri', '/')))


class Logout(RequestHandler):
  def get(self, *args, **kwargs):
    self.redirect(users.create_logout_url(
      self.request.route_kwargs.get('_uri', '/')))


class NotFound(RequestHandler):
  def get(self, *args, **kwargs):
    self.abort_not_found()


class SimplePage(RequestHandler):
  def get(self, *args, **kwargs):
    if hasattr(self, 'TEMPLATE'):
      self.render_page(self.TEMPLATE, self.request.route_kwargs.get('_vars',
        None))
    elif '_template' in self.request.route_kwargs:
      self.render_page(self.request.route_kwargs['_template'],
          self.request.route_kwargs.get('_vars', None))
    else:
      logging.error('No template to render as a simple page')
      self.abort(500)

# vim: et sw=2 ts=2 sts=2 cc=80
