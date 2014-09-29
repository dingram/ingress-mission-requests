import datetime
import logging
import re

from google.appengine.ext import ndb

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
        mission.waypoints.append(models.MissionWaypoint())

    self.render_page(template, {
      'mission': mission,
      'error': self.request.GET.get('error'),
    })

  def post(self, *args, **kwargs):
    if not self.user or not (self.user.is_mission_creator or self.user.is_superadmin):
      self.redirect('/')
      return

    mission = models.Mission.fetch_by_guid(self.request.route_kwargs['guid'])
    if not mission:
      self.abort_not_found()
      return

    if mission.state == 'AWAITING_REVIEW' or mission.state == 'NEEDS_REVISION':
      if 'state_start_review' in self.request.POST:
        mission.state = 'UNDER_REVIEW'
        mission.started_review = datetime.datetime.utcnow()
        mission.reviewer_guid = self.user.guid
        mission.reviewer_nickname = self.user.nickname
        mission.reviewer_faction = self.user.faction
        mission.audit_log.append(models.MissionAuditLogEntry.being_reviewed(self.user))
        mission.put()

    if mission.state == 'UNDER_REVIEW':
      if 'state_accept' in self.request.POST:
        mission.state = 'ACCEPTED'
        mission.finished_review = datetime.datetime.utcnow()
        mission.audit_log.append(models.MissionAuditLogEntry.accepted(self.user))
        mission.put()
      elif 'state_revision' in self.request.POST and self.request.POST.get('revision_reason', '').strip():
        reason = self.request.POST.get('revision_reason', '').strip()
        mission.state = 'NEEDS_REVISION'
        mission.finished_review = datetime.datetime.utcnow()
        mission.rejection_reason = reason
        mission.audit_log.append(models.MissionAuditLogEntry.needs_revision(self.user, reason))
        mission.put()
      elif 'state_reject' in self.request.POST and self.request.POST.get('rejection_reason', '').strip():
        reason = self.request.POST.get('rejection_reason', '').strip()
        mission.state = 'REJECTED'
        mission.finished_review = datetime.datetime.utcnow()
        mission.rejection_reason = reason
        mission.audit_log.append(models.MissionAuditLogEntry.rejected(self.user, reason))
        mission.put()
      elif 'state_reset_review' in self.request.POST:
        mission.state = 'UNDER_REVIEW'
        mission.started_review = None
        mission.audit_log.append(models.MissionAuditLogEntry.re_sent_for_review(self.user))
        mission.put()

    if mission.state == 'REJECTED':
      if 'state_revision' in self.request.POST and self.request.POST.get('revision_reason', '').strip():
        pass
      elif 'state_reset_review' in self.request.POST:
        mission.state = 'UNDER_REVIEW'
        mission.started_review = None
        mission.audit_log.append(models.MissionAuditLogEntry.re_sent_for_review(self.user))
        mission.put()

    if mission.state == 'ACCEPTED':
      if 'state_start_creation' in self.request.POST:
        mission.state = 'CREATING'
        mission.mission_creation_began = datetime.datetime.utcnow()
        mission.audit_log.append(models.MissionAuditLogEntry.being_created(self.user))
        mission.put()

    if mission.state == 'CREATING':
      if 'state_finish_creation' in self.request.POST:
        mission.state = 'CREATED'
        mission.mission_creation_complete = datetime.datetime.utcnow()
        mission.audit_log.append(models.MissionAuditLogEntry.created(self.user))
        mission.put()

    if mission.state == 'CREATED':
      if 'state_publish' in self.request.POST:
        mission.state = 'PUBLISHED'
        mission.mission_published = datetime.datetime.utcnow()
        mission.publisher_guid = self.user.guid
        mission.publisher_nickname = self.user.nickname
        mission.publisher_faction = self.user.faction
        mission.audit_log.append(models.MissionAuditLogEntry.published(self.user))
        mission.put()

    self.redirect('/missions/%s' % mission.guid, abort=True, code=303)


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

    # helper function
    def err(msg):
      logging.warning('Form error: %s' % msg)
      import urllib
      data = {'error': msg}
      self.redirect(
          '/missions/%s?%s' % (mission.guid, urllib.urlencode(data)),
          code=303,
          abort=True,
      )

    # update model
    mission.title = self.request.POST.get('title', '').strip()
    mission_type = self.request.POST.get('type').strip()
    mission.icon_url = self.request.POST.get('icon_url', '').strip()
    mission.description = self.request.POST.get('description', '').strip()

    logging.debug('title: %s' % mission.title)
    logging.debug('type: %s' % mission_type)
    logging.debug('icon_url: %s' % mission.icon_url)
    logging.debug('description: %s' % mission.description)

    # deal with waypoints
    waypoints = []
    idx = 0
    while True:
      idx += 1
      prefix = 'waypoint_%d_' % idx
      if (prefix + 'portal_title') not in self.request.POST:
        # No more waypoints left
        break

      logging.debug('Processing waypoint %d' % idx)

      title = self.request.POST.get(prefix + 'portal_title', '').strip()
      intel_url = self.request.POST.get(prefix + 'intel_url', '').strip()
      waypoint_type = self.request.POST.get(prefix + 'type')
      location_clue = self.request.POST.get(prefix + 'location_clue', '').strip()
      description = self.request.POST.get(prefix + 'description', '').strip()
      question = self.request.POST.get(prefix + 'question', '').strip()
      passphrase = self.request.POST.get(prefix + 'passphrase', '').strip()

      logging.debug('... title: %s' % title)
      logging.debug('... intel: %s' % intel_url)
      logging.debug('... type: %s' % waypoint_type)
      logging.debug('... location_clue: %s' % location_clue)
      logging.debug('... description: %s' % description)
      logging.debug('... question: %s' % question)
      logging.debug('... passphrase: %s' % passphrase)

      # Decide whether to process this entry
      if not title or not intel_url or not waypoint_type:
        logging.info('Skipping empty waypoint %d' % idx)
        continue

      # Basic validation
      if len(title) > 50:
        err('The portal title for Waypoint %d cannot be longer than 50 characters' % idx)
        return
      if not re.match(r'^https?://(?:[^.]+\.)ingress\.com/intel/?\?.*pll=', intel_url):
        err('The Intel map URL for Waypoint %d must be a link to a specific portal' % idx)
        return
      if waypoint_type not in enums.WaypointType._values:
        err('You must select a valid type for Waypoint %d' % idx)
        return

      # Type-specific validation
      if mission.type == 'SEQUENTIAL_HIDDEN':
        if idx == 1 and location_clue:
          err('You must NOT enter a location clue for Waypoint %d' % idx)
          return
        if idx > 1 and not location_clue:
          err('You must enter a location clue for Waypoint %d' % idx)
          return
        if len(location_clue) > 200:
          err('The location clue for Waypoint %d cannot be longer than 200 characters' % idx)
          return
      elif location_clue:
        err('You must NOT enter a location clue for Waypoint %d' % idx)
        return

      if waypoint_type == 'ENTER_PASSPHRASE':
        if not question:
          err('You must enter a question for Waypoint %d' % idx)
          return
        if len(question) > 200:
          err('The question for Waypoint %d cannot be longer than 200 characters' % idx)
          return
        if not passphrase:
          err('You must enter a passphrase for Waypoint %d' % idx)
          return
        if len(passphrase) > 50:
          err('The passphrase for Waypoint %d cannot be longer than 50 characters' % idx)
          return
      else:
        if question:
          err('You must NOT enter a question for Waypoint %d' % idx)
          return
        if passphrase:
          err('You must NOT enter a passphrase for Waypoint %d' % idx)
          return

      result = re.match(r'^https?://(?:[^.]+\.)ingress\.com/intel/?\?.*pll=(-?\d*\.\d*),(-?\d*\.\d*)', intel_url)
      latE6 = 0
      lngE6 = 0
      try:
        latE6 = int(float(result.group(1)) * 1e6)
        lngE6 = int(float(result.group(2)) * 1e6)
      except:
        pass

      if not latE6 and not lngE6:
        err('Could not extract co-ordinates from Intel map URL for Waypoint %d' % idx)
        return

      logging.debug('... {lat,lng}E6: %d, %d' % (latE6, lngE6))

      waypoints.append(models.MissionWaypoint(
        portal_title = title,
        type = waypoint_type,
        latE6 = latE6,
        lngE6 = lngE6,
        location_clue = location_clue,
        description = description,
        question = question,
        passphrase = passphrase,
      ))
      logging.debug('Added waypoint %d' % idx)

    logging.debug('Done with waypoints; %d total' % len(waypoints))

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
    mission.waypoints = waypoints

    if 'review' in self.request.POST:
      if mission.is_incomplete():
        err('The mission is not ready to submit for review; please ensure you have at least 4 waypoints')
        return
      mission.state = 'AWAITING_REVIEW'
      mission.sent_for_review = datetime.datetime.utcnow()
      mission.audit_log.append(models.MissionAuditLogEntry.sent_for_review(self.user))

    # save
    mission.put()
    logging.debug('Mission saved.')

    # redirect
    self.redirect('/missions/%s' % mission.guid, abort=True, code=303)


class Queue(RequestHandler):

  def get(self, *args, **kwargs):
    if not self.user or not (self.user.is_mission_creator or self.user.is_superadmin):
      self.abort_not_found()
      return

    cursor = ndb.Cursor(urlsafe=self.request.get('start'))
    unfiltered = 'unfiltered' in self.request.GET

    if unfiltered:
      q = models.Mission.query()
    else:
      q = models.Mission.query(
          models.Mission.state == 'AWAITING_REVIEW',
      )

    q = q.order(-models.Mission.last_modified)
    missions, next_cursor, more = (q.fetch_page(50, start_cursor=cursor))

    q = models.Mission.query(ndb.OR(
      models.Mission.reviewer_guid == self.user.guid,
      models.Mission.publisher_guid == self.user.guid,
    )).order(-models.Mission.last_modified)
    my_missions = q.fetch(50)

    self.render_page('queue-view.html', {
      'unfiltered': unfiltered,
      'my_missions': my_missions,
      'missions': missions,
      'cursor_token': next_cursor.urlsafe() if next_cursor and more else None,
    })


# vim: et sw=2 ts=2 sts=2 cc=80
