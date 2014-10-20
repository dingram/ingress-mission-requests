import datetime as dt
import logging
import time

from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from app.data import models
from app.util.request import RequestHandler


class NotFound(RequestHandler):
  """Simple "not found" handler. Used as a catchall."""

  def get(self, *args, **kwargs):
    self.abort_not_found()

  def post(self, *args, **kwargs):
    self.abort_not_found()


class ReapEmptyMissions(RequestHandler):
  LAST_MOD_DAYS = 3

  def post(self, *args, **kwargs):
    cursor = ndb.Cursor(urlsafe=self.request.POST.get('cursor'))

    try:
      keys_to_delete = []
      end_by = time.time() + 45000
      more = True
      count = 0
      reap_before = dt.datetime.utcnow() - dt.timedelta(days=self.LAST_MOD_DAYS)
      while more and cursor and (time.time() < end_by):
        missions, cursor, more = models.Mission.query().fetch_page(150,
            start_cursor=cursor)
        for m in missions:
          count += 1
          if m.state != 'DRAFT':
            # Not a draft, skip
            continue
          if m.title or m.description:
            # has a title/description, skip
            continue
          if m.last_modified > reap_before:
            # modified since cutoff, skip
            continue
          keys_to_delete.append(m.key)

      logging.info('%d missions processed this batch, %d to reap', count,
          len(keys_to_delete))

      ndb.delete_multi(keys_to_delete)
      logging.info('%d missions cleaned up', len(keys_to_delete))

      if more and cursor:
        # not yet done! reschedule...
        logging.info('Not done; rescheduling reap')
        taskqueue.Task(
            url='/_tasks/reap-empty-missions',
            params={
              cursor: cursor,
            },
        ).add()
    except:
      logging.exception('Failed to reap missions')

# vim: et sw=2 ts=2 sts=2 cc=80
