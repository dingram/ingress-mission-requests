import logging
import re

from app.data import models
from app.util.request import RequestHandler


class Landing(RequestHandler):

  def get(self, *args, **kwargs):
    draft_missions = []
    review_queue = []

    if self.user:
      for m in models.Mission.query(models.Mission.owner_guid == self.user.guid):
        if m.state == 'DRAFT':
          draft_missions.append(m)
        else:
          review_queue.append(m)
        draft_missions.sort(key=lambda x: x.title.lower() if x.title else '')
        review_queue.sort(key=lambda x: x.title.lower() if x.title else '')

    self.render_page('index.html', {
      'logged_in': self.gae_user is not None,
      'drafts': draft_missions,
      'review_queue': review_queue,
    })


class Signup(RequestHandler):

  def get(self, *args, **kwargs):
    if not self.gae_user:
      self.redirect('/login')
      return
    self.user = models.User.get_current(allow_creation=True)
    self.render_page('signup.html')

  def post(self, *args, **kwargs):
    if not self.gae_user:
      self.redirect('/login')
      return
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
      self.redirect('/', abort=True, code=303)
      return
    else:
      self.render_page('signup.html', {'error': error})


# vim: et sw=2 ts=2 sts=2 cc=80
