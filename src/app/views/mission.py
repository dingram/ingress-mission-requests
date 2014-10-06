import collections
import datetime
import logging
import re

from google.appengine.api import mail
from google.appengine.ext import ndb

from app.data import enums
from app.data import models
from app.util.request import RequestHandler


COUNTRIES = collections.OrderedDict([('AX', u"\u00c5land Islands"),('AF', u"Afghanistan"),('AL', u"Albania"),('DZ', u"Algeria"),('AS', u"American Samoa"),('AD', u"Andorra"),('AO', u"Angola"),('AI', u"Anguilla"),('AQ', u"Antarctica"),('AG', u"Antigua and Barbuda"),('AR', u"Argentina"),('AM', u"Armenia"),('AW', u"Aruba"),('AU', u"Australia"),('AT', u"Austria"),('AZ', u"Azerbaijan"),('BS', u"Bahamas"),('BH', u"Bahrain"),('BD', u"Bangladesh"),('BB', u"Barbados"),('BY', u"Belarus"),('BE', u"Belgium"),('BZ', u"Belize"),('BJ', u"Benin"),('BM', u"Bermuda"),('BT', u"Bhutan"),('BO', u"Bolivia"),('BA', u"Bosnia and Herzegovina"),('BW', u"Botswana"),('BV', u"Bouvet Island"),('BR', u"Brazil"),('BQ', u"British Antarctic Territory"),('IO', u"British Indian Ocean Territory"),('VG', u"British Virgin Islands"),('BN', u"Brunei"),('BG', u"Bulgaria"),('BF', u"Burkina Faso"),('BI', u"Burundi"),('KH', u"Cambodia"),('CM', u"Cameroon"),('CA', u"Canada"),('CT', u"Canton and Enderbury Islands"),('CV', u"Cape Verde"),('KY', u"Cayman Islands"),('CF', u"Central African Republic"),('TD', u"Chad"),('CL', u"Chile"),('CN', u"China"),('CX', u"Christmas Island"),('CC', u"Cocos [Keeling] Islands"),('CO', u"Colombia"),('KM', u"Comoros"),('CG', u"Congo - Brazzaville"),('CD', u"Congo - Kinshasa"),('CK', u"Cook Islands"),('CR', u"Costa Rica"),('HR', u"Croatia"),('CU', u"Cuba"),('CY', u"Cyprus"),('CZ', u"Czech Republic"),('CI', u"C\u00f4te d\u2019Ivoire"),('DK', u"Denmark"),('DJ', u"Djibouti"),('DM', u"Dominica"),('DO', u"Dominican Republic"),('NQ', u"Dronning Maud Land"),('DD', u"East Germany"),('EC', u"Ecuador"),('EG', u"Egypt"),('SV', u"El Salvador"),('GQ', u"Equatorial Guinea"),('ER', u"Eritrea"),('EE', u"Estonia"),('ET', u"Ethiopia"),('FK', u"Falkland Islands"),('FO', u"Faroe Islands"),('FJ', u"Fiji"),('FI', u"Finland"),('FR', u"France"),('GF', u"French Guiana"),('PF', u"French Polynesia"),('TF', u"French Southern Territories"),('FQ', u"French Southern and Antarctic Territories"),('GA', u"Gabon"),('GM', u"Gambia"),('GE', u"Georgia"),('DE', u"Germany"),('GH', u"Ghana"),('GI', u"Gibraltar"),('GR', u"Greece"),('GL', u"Greenland"),('GD', u"Grenada"),('GP', u"Guadeloupe"),('GU', u"Guam"),('GT', u"Guatemala"),('GG', u"Guernsey"),('GN', u"Guinea"),('GW', u"Guinea-Bissau"),('GY', u"Guyana"),('HT', u"Haiti"),('HM', u"Heard Island and McDonald Islands"),('HN', u"Honduras"),('HK', u"Hong Kong SAR China"),('HU', u"Hungary"),('IS', u"Iceland"),('IN', u"India"),('ID', u"Indonesia"),('IR', u"Iran"),('IQ', u"Iraq"),('IE', u"Ireland"),('IM', u"Isle of Man"),('IL', u"Israel"),('IT', u"Italy"),('JM', u"Jamaica"),('JP', u"Japan"),('JE', u"Jersey"),('JT', u"Johnston Island"),('JO', u"Jordan"),('KZ', u"Kazakhstan"),('KE', u"Kenya"),('KI', u"Kiribati"),('KW', u"Kuwait"),('KG', u"Kyrgyzstan"),('LA', u"Laos"),('LV', u"Latvia"),('LB', u"Lebanon"),('LS', u"Lesotho"),('LR', u"Liberia"),('LY', u"Libya"),('LI', u"Liechtenstein"),('LT', u"Lithuania"),('LU', u"Luxembourg"),('MO', u"Macau SAR China"),('MK', u"Macedonia"),('MG', u"Madagascar"),('MW', u"Malawi"),('MY', u"Malaysia"),('MV', u"Maldives"),('ML', u"Mali"),('MT', u"Malta"),('MH', u"Marshall Islands"),('MQ', u"Martinique"),('MR', u"Mauritania"),('MU', u"Mauritius"),('YT', u"Mayotte"),('FX', u"Metropolitan France"),('MX', u"Mexico"),('FM', u"Micronesia"),('MI', u"Midway Islands"),('MD', u"Moldova"),('MC', u"Monaco"),('MN', u"Mongolia"),('ME', u"Montenegro"),('MS', u"Montserrat"),('MA', u"Morocco"),('MZ', u"Mozambique"),('MM', u"Myanmar [Burma]"),('NA', u"Namibia"),('NR', u"Nauru"),('NP', u"Nepal"),('NL', u"Netherlands"),('AN', u"Netherlands Antilles"),('NT', u"Neutral Zone"),('NC', u"New Caledonia"),('NZ', u"New Zealand"),('NI', u"Nicaragua"),('NE', u"Niger"),('NG', u"Nigeria"),('NU', u"Niue"),('NF', u"Norfolk Island"),('KP', u"North Korea"),('VD', u"North Vietnam"),('MP', u"Northern Mariana Islands"),('NO', u"Norway"),('OM', u"Oman"),('PC', u"Pacific Islands Trust Territory"),('PK', u"Pakistan"),('PW', u"Palau"),('PS', u"Palestinian Territories"),('PA', u"Panama"),('PZ', u"Panama Canal Zone"),('PG', u"Papua New Guinea"),('PY', u"Paraguay"),('YD', u"People's Democratic Republic of Yemen"),('PE', u"Peru"),('PH', u"Philippines"),('PN', u"Pitcairn Islands"),('PL', u"Poland"),('PT', u"Portugal"),('PR', u"Puerto Rico"),('QA', u"Qatar"),('RO', u"Romania"),('RU', u"Russia"),('RW', u"Rwanda"),('RE', u"R\u00e9union"),('BL', u"Saint Barth\u00e9lemy"),('SH', u"Saint Helena"),('KN', u"Saint Kitts and Nevis"),('LC', u"Saint Lucia"),('MF', u"Saint Martin"),('PM', u"Saint Pierre and Miquelon"),('VC', u"Saint Vincent and the Grenadines"),('WS', u"Samoa"),('SM', u"San Marino"),('SA', u"Saudi Arabia"),('SN', u"Senegal"),('RS', u"Serbia"),('CS', u"Serbia and Montenegro"),('SC', u"Seychelles"),('SL', u"Sierra Leone"),('SG', u"Singapore"),('SK', u"Slovakia"),('SI', u"Slovenia"),('SB', u"Solomon Islands"),('SO', u"Somalia"),('ZA', u"South Africa"),('GS', u"South Georgia and the South Sandwich Islands"),('KR', u"South Korea"),('ES', u"Spain"),('LK', u"Sri Lanka"),('SD', u"Sudan"),('SR', u"Suriname"),('SJ', u"Svalbard and Jan Mayen"),('SZ', u"Swaziland"),('SE', u"Sweden"),('CH', u"Switzerland"),('SY', u"Syria"),('ST', u"S\u00e3o Tom\u00e9 and Pr\u00edncipe"),('TW', u"Taiwan"),('TJ', u"Tajikistan"),('TZ', u"Tanzania"),('TH', u"Thailand"),('TL', u"Timor-Leste"),('TG', u"Togo"),('TK', u"Tokelau"),('TO', u"Tonga"),('TT', u"Trinidad and Tobago"),('TN', u"Tunisia"),('TR', u"Turkey"),('TM', u"Turkmenistan"),('TC', u"Turks and Caicos Islands"),('TV', u"Tuvalu"),('UM', u"U.S. Minor Outlying Islands"),('PU', u"U.S. Miscellaneous Pacific Islands"),('VI', u"U.S. Virgin Islands"),('UG', u"Uganda"),('UA', u"Ukraine"),('SU', u"Union of Soviet Socialist Republics"),('AE', u"United Arab Emirates"),('GB', u"United Kingdom"),('US', u"United States"),('UY', u"Uruguay"),('UZ', u"Uzbekistan"),('VU', u"Vanuatu"),('VA', u"Vatican City"),('VE', u"Venezuela"),('VN', u"Vietnam"),('WK', u"Wake Island"),('WF', u"Wallis and Futuna"),('EH', u"Western Sahara"),('YE', u"Yemen"),('ZM', u"Zambia"),('ZW', u"Zimbabwe")])


class Create(RequestHandler):

  def get(self, *args, **kwargs):
    if not self.user:
      self.redirect('/')
      return
    if not self.user.accepted_guidelines:
      self.redirect('/guidelines', abort=True, code=303)
      return
    mission = models.Mission.new_draft(self.user)
    mission.put()
    self.redirect('/missions/%s' % mission.guid)


class View(RequestHandler):

  def get(self, *args, **kwargs):
    if not self.user:
      self.redirect('/')
      return
    if not self.user.accepted_guidelines:
      self.redirect('/guidelines', abort=True, code=303)
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
    if (mission.state in ('DRAFT', 'NEEDS_REVISION') and is_owner) or (self.user.is_superadmin and 'edit' in self.request.GET):
      template = 'mission-edit.html'

      # Add some empty waypoints to keep things interesting
      for i in range(4):
        mission.waypoints.append(models.MissionWaypoint())

    self.render_page(template, {
      'COUNTRIES': COUNTRIES,
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

    if self.user.guid == mission.owner_guid:
      # Cannot process your own missions
      self.redirect('/missions/%s' % mission.guid, abort=True, code=303)
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
        mail.send_mail(
            sender='Ingress Mission Requests <updates+%s@ingress-mission-requests.appspotmail.com>' % mission.guid,
            to='Agent %s <%s>' % (mission.owner_nickname, mission.owner_email),
            subject='Mission accepted: %s' % mission.title,
            body='Your mission "%s" has been accepted by our reviewers. You will be emailed again when it has been published.' % mission.title,
        )
      elif 'state_revision' in self.request.POST and self.request.POST.get('revision_reason', '').strip():
        reason = self.request.POST.get('revision_reason', '').strip()
        mission.state = 'NEEDS_REVISION'
        mission.finished_review = datetime.datetime.utcnow()
        mission.rejection_reason = reason
        mission.audit_log.append(models.MissionAuditLogEntry.needs_revision(self.user, reason))
        mission.put()
        mail.send_mail(
            sender='Ingress Mission Requests <updates+%s@ingress-mission-requests.appspotmail.com>' % mission.guid,
            to='Agent %s <%s>' % (mission.owner_nickname, mission.owner_email),
            subject='Mission needs revision: %s' % mission.title,
            body='Your mission "%s" has been reviewed and needs some changes:\n\n%s\n\nPlease update your mission and submit for review again.' % (mission.title, mission.rejection_reason),
        )
      elif 'state_reject' in self.request.POST and self.request.POST.get('rejection_reason', '').strip():
        reason = self.request.POST.get('rejection_reason', '').strip()
        mission.state = 'REJECTED'
        mission.finished_review = datetime.datetime.utcnow()
        mission.rejection_reason = reason
        mission.audit_log.append(models.MissionAuditLogEntry.rejected(self.user, reason))
        mission.put()
        mail.send_mail(
            sender='Ingress Mission Requests <updates+%s@ingress-mission-requests.appspotmail.com>' % mission.guid,
            to='Agent %s <%s>' % (mission.owner_nickname, mission.owner_email),
            subject='Mission rejected: %s' % mission.title,
            body='Your mission "%s" has been rejected by our reviewers:\n\n%s\n\nThanks for your enthusiasm, and we look forward to whatever new missions you request in future.' % (mission.title, mission.rejection_reason),
        )
      elif 'state_reset_review' in self.request.POST:
        mission.state = 'AWAITING_REVIEW'
        mission.started_review = None
        mission.audit_log.append(models.MissionAuditLogEntry.re_sent_for_review(self.user))
        mission.put()

    if mission.state == 'REJECTED':
      if 'state_revision' in self.request.POST and self.request.POST.get('revision_reason', '').strip():
        reason = self.request.POST.get('revision_reason', '').strip()
        mission.state = 'NEEDS_REVISION'
        mission.finished_review = datetime.datetime.utcnow()
        mission.rejection_reason = reason
        mission.audit_log.append(models.MissionAuditLogEntry.needs_revision(self.user, reason))
        mission.put()
        mail.send_mail(
            sender='Ingress Mission Requests <updates+%s@ingress-mission-requests.appspotmail.com>' % mission.guid,
            to='Agent %s <%s>' % (mission.owner_nickname, mission.owner_email),
            subject='Mission needs revision: %s' % mission.title,
            body='Your mission "%s" has been reviewed and needs some changes:\n\n%s\n\nPlease update your mission and submit for review again.' % (mission.title, mission.rejection_reason),
        )
      elif 'state_reset_review' in self.request.POST:
        mission.state = 'AWAITING_REVIEW'
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
        mail.send_mail(
            sender='Ingress Mission Requests <updates+%s@ingress-mission-requests.appspotmail.com>' % mission.guid,
            to='Agent %s <%s>' % (mission.owner_nickname, mission.owner_email),
            subject='Mission published: %s' % mission.title,
            body='Your mission "%s" has been created, and should now be playable. Thanks for submitting it!' % mission.title,
        )

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

    if mission.state not in ('DRAFT', 'NEEDS_REVISION') and not self.user.is_superadmin:
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
    mission.country_code = self.request.POST.get('country', '').strip()
    mission.city = self.request.POST.get('city', '').strip()
    mission.attn = self.request.POST.get('attn', '').strip()

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
    if not mission.description:
      err('You must provide a mission description')
      return
    if len(mission.description) > 200:
      err('The mission description cannot be longer than 200 characters')
      return
    if not mission.country_code:
      err('You must provide a country')
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
      q = q.order(models.Mission.last_modified)
    else:
      q = models.Mission.query(
          models.Mission.state == 'AWAITING_REVIEW',
      )
      q = q.order(models.Mission.sent_for_review)

    missions, next_cursor, more = (q.fetch_page(20, start_cursor=cursor))

    my_mission_states = [
      'UNDER_REVIEW',
      'ACCEPTED',
      'NEEDS_REVISION',
      'CREATING',
      'CREATED',
    ]
    if 'all_my_missions' in self.request.GET:
      my_mission_states.extend(['PUBLISHED', 'REJECTED'])

    q = models.Mission.query(
        ndb.OR(
          models.Mission.reviewer_guid == self.user.guid,
          models.Mission.publisher_guid == self.user.guid,
        ),
        models.Mission.state.IN(my_mission_states)
    ).order(-models.Mission.last_modified)
    my_missions = q.fetch(50)

    self.render_page('queue-view.html', {
      'unfiltered': unfiltered,
      'my_missions': my_missions,
      'missions': missions,
      'cursor_token': next_cursor.urlsafe() if next_cursor and more else None,
    })


# vim: et sw=2 ts=2 sts=2 cc=80
