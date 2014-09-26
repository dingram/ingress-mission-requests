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

    is_owner = mission and mission.owner_guid == self.user.guid
    is_creator = self.user.is_superadmin or self.user.is_mission_creator
    if not is_owner and not is_creator:
      mission = None
    if not mission:
      self.abort_not_found()
      return

    template = 'mission-view.html'
    if (mission.state == 'DRAFT' and is_owner) or self.user.is_superadmin:
      template = 'mission-edit.html'

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

    is_owner = mission and mission.owner_guid == self.user.guid
    is_creator = self.user.is_superadmin or self.user.is_mission_creator
    if not is_owner and not is_creator:
      mission = None
    if not mission:
      self.abort_not_found()
      return

    if not is_owner and self.user.is_creator:
      # Cannot edit this mission; just redirect back
      self.redirect('/missions/%s' % mission.guid, abort=303)
      return

    if mission.state != 'DRAFT' and not self.user.is_superadmin:
      # Cannot edit a submitted mission; just redirect back
      self.redirect('/missions/%s' % mission.guid, abort=303)
      return

    # save

    # redirect
    self.redirect('/missions/%s' % mission.guid, abort=303)


# vim: et sw=2 ts=2 sts=2 cc=80
