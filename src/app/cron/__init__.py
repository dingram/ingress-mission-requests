import logging

from google.appengine.api import taskqueue

from app.util.request import RequestHandler


class NotFound(RequestHandler):
  """Simple "not found" handler. Used as a catchall."""

  def get(self, *args, **kwargs):
    self.abort_not_found()

  def post(self, *args, **kwargs):
    self.abort_not_found()


class ReapEmptyMissions(RequestHandler):

  def get(self, *args, **kwargs):
    taskqueue.Task(
        url='/_tasks/reap-empty-missions',
    ).add()

# vim: et sw=2 ts=2 sts=2 cc=80
