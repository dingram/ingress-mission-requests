import logging

from google.appengine.api import mail

from app.data import models
from app.util.request import RequestHandler


class Root(RequestHandler):

  def get(self, *args, **kwargs):
    if not self.user:
      self.redirect('/')
      return
    if not self.user.is_superadmin:
      self.abort_not_found()
      return
    self.render_page('manage-root.html')


class Users(RequestHandler):

  def get(self, *args, **kwargs):
    if not self.user:
      self.redirect('/')
      return
    if not self.user.is_superadmin:
      self.abort_not_found()
      return
    self.render_page('manage-users.html', {'msg': self.request.get('msg')})

  def post(self, *args, **kwargs):
    if not self.user:
      self.redirect('/')
      return
    if not self.user.is_superadmin:
      self.abort_not_found()
      return

    nickname = self.request.POST.get('nickname')
    if nickname:
      user = models.User.fetch_by_nickname(nickname)
      if not user:
        self.redirect('/manage/users/?msg=%s+does+not+exist%%2e' % nickname)
        return
      if 'promote' in self.request.POST:
        if user.is_mission_creator:
          self.redirect('/manage/users/?msg=%s+is+already+a+creator%%2e' % nickname)
          return
        user.is_mission_creator = True
        user.put()
        mail.send_mail(
            sender='Ingress Mission Requests <admin@ingress-mission-requests.appspotmail.com>',
            to='Agent %s <%s>' % (user.nickname, user.email),
            subject='Access upgraded',
            body='Congratulations, agent. You are now able to start processing the request queue.',
        )
        self.redirect('/manage/users/?msg=%s+is+now+a+creator%%2e' % nickname)
        return
      if 'demote' in self.request.POST:
        if not user.is_mission_creator:
          self.redirect('/manage/users/?msg=%s+never+was+a+creator%%2e' % nickname)
          return
        user.is_mission_creator = False
        user.put()
        self.redirect('/manage/users/?msg=%s+is+no+longer+a+creator%%2e' % nickname)
        return
    else:
      self.redirect('/manage/users/?msg=Error%%2e')
      return
    self.redirect('/manage/users/')


# vim: et sw=2 ts=2 sts=2 cc=80
