import logging
import os
import sys
import webapp2

from google.appengine.ext import ndb

import fix_path

import app.views.simple
import app.views.user


DEBUG_MODE = (os.environ.get('SERVER_SOFTWARE', '').startswith('Development')
    or 'test' in os.environ.get('HTTP_HOST', os.environ.get('SERVER_NAME')))


application = ndb.toplevel(webapp2.WSGIApplication([
  webapp2.Route('/', app.views.user.Landing, 'landing'),

  webapp2.Route('/login',  app.views.simple.Login,  'login'),
  webapp2.Route('/logout', app.views.simple.Logout, 'logout'),

  webapp2.Route('/signup', app.views.user.Signup, 'signup'),

  (r'.*', app.views.simple.NotFound),
], debug=DEBUG_MODE))


def main():
  logging.getLogger().setLevel(logging.INFO)
  application.run()

if __name__ == "__main__":
  main()

# vim: et sw=2 ts=2 sts=2 cc=80
