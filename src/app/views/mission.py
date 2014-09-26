import logging
import re

from app.data import enums
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

      # Add some empty waypoints to keep things interesting
      for i in range(4):
        mission.objectives.append(models.MissionObjective())

    self.render_page(template, {
      'mission': mission,
      'error': self.request.GET.get('error'),
    })


class Update(RequestHandler):

  def post(self, *args, **kwargs):
    if not self.user:
      self.redirect('/')
      return
    self.check_xsrf_token()
    mission = models.Mission.fetch_by_guid(self.request.route_kwargs['guid'])

    is_owner = mission and mission.owner_guid == self.user.guid
    is_creator = self.user.is_superadmin or self.user.is_mission_creator
    if not is_owner and not is_creator:
      mission = None
    if not mission:
      self.abort_not_found()
      return

    if not is_owner and self.user.is_creator:
      # Cannot edit this mission; just redirect back
      self.redirect('/missions/%s' % mission.guid, abort=True, code=303)
      return

    if mission.state != 'DRAFT' and not self.user.is_superadmin:
      # Cannot edit a submitted mission; just redirect back
      self.redirect('/missions/%s' % mission.guid, abort=True, code=303)
      return

    # update model
    mission.title = self.request.POST.get('title')
    mission_type = self.request.POST.get('type')
    mission.icon_url = self.request.POST.get('icon_url')
    mission.description = self.request.POST.get('description')

    # deal with waypoints

    def err(msg):
      import urllib
      data = {'error': msg}
      self.redirect(
          '/missions/%s?%s' % (mission.guid, urllib.urlencode(data)),
          code=303,
          abort=True,
      )

    # validate
    if not mission.title:
      err('You must provide a mission title')
      return
    if len(mission.title) > 50:
      err('The mission title cannot be longer than 50 characters')
      return
    if not mission_type:
      err('You must select a mission type')
      return
    if mission_type not in enums.MissionType._values:
      err('You must select a valid mission type')
      return
    if mission.icon_url and not re.match(r'^https?://[^/]+\.[^/]+/.*', mission.icon_url):
      err('You must provide a valid URL for the mission icon')
      return
    if len(mission.description) > 200:
      err('The mission description cannot be longer than 200 characters')
      return

    # update model phase 2
    mission.type = mission_type

    # save
    mission.put()

    # redirect
    self.redirect('/missions/%s' % mission.guid, abort=True, code=303)


# vim: et sw=2 ts=2 sts=2 cc=80
