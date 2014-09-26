import logging

appstats_CALC_RPC_COSTS = True
appstats_TZOFFSET = 0
appstats_MAX_LOCALS = 0
appstats_MAX_REPR = 0
appstats_MAX_DEPTH = 0

def webapp_add_wsgi_middleware(wsgi_app):
  from google.appengine.ext.appstats import recording
  wsgi_app = recording.appstats_wsgi_middleware(wsgi_app)
  try:
    import datastore_stats
    wsgi_app = datastore_stats.datastore_stats_wsgi_middleware(wsgi_app)
  except:
    logging.exception('No DS Stats module')
    pass
  return wsgi_app

# vim: et sw=2 ts=2 sts=2 cc=80
