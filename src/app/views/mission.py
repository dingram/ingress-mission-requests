import logging
import re

from app.data import models
from app.util.request import RequestHandler


class Create(RequestHandler):

  def get(self, *args, **kwargs):
    if not self.user:
      self.redirect('/')
      return
    mission = models.Mission.new_draft(self.user)
    mission.put()
    self.redirect('/missions/%s' % mission.guid)


class View(RequestHandler):

  def get(self, *args, **kwargs):
    if not self.user:
      self.redirect('/')
      return
    mission = models.Mission.fetch_by_guid(self.request.route_kwargs['guid'])
    if mission and mission.owner_guid != self.user.guid:
      mission = None

    template = 'mission-%s.html' % ('edit' if mission.state == 'DRAFT' else 'view')

    self.render_page(template, {
      'mission': mission,
    })


class Update(RequestHandler):

  def post(self, *args, **kwargs):
    if not self.user:
      self.redirect('/')
      return
    self.check_xsrf_token()
    mission = mission.fetch_by_guid(self.request.route_kwargs['guid'])
    if mission and mission.owner_guid != self.user.guid:
      mission = None
    if not mission:
      self.abort_not_found()
      return
    if mission.state != 'DRAFT':
      # Cannot edit an existing mission; just redirect back
      self.redirect('/missions/%s' % mission.guid, abort=303)
      return
    self.redirect('/missions/%s' % mission.guid, abort=303)


# vim: et sw=2 ts=2 sts=2 cc=80
