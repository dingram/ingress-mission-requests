from collections import defaultdict
import logging

from google.appengine.api import apiproxy_stub_map
from google.appengine.datastore import datastore_index


logging.debug('Initializing datastore stats module')


def model_name_from_key(key):
  return key.path().element_list()[0].type()


class DSStatsHolder(object):
  stats = None

  @classmethod
  def get(cls):
    return cls.stats

  @classmethod
  def clear(cls):
    cls.stats = defaultdict(lambda: defaultdict(int))


def get_stats():
  return DSStatsHolder.get()


def end_stats():
  ds_stats = DSStatsHolder.get()
  if ds_stats is None:
    return
  for model in sorted(ds_stats.keys()):
    if model == '?':
      msg = 'DB stats:'
    else:
      msg = 'DB stats for %s:' % model
    for op in sorted(ds_stats[model].keys()):
      msg += ' %s=%d' % (op, ds_stats[model][op])
    logging.debug(msg)
  DSStatsHolder.clear()


def hook(service, call, request, response):
  try:
    assert service == 'datastore_v3'
    ds_stats = DSStatsHolder.get()
    if ds_stats is None:
      return
    if call == 'Put':
      for entity in request.entity_list():
        ds_stats[model_name_from_key(entity.key())][call] += 1
      if len(request.entity_list()) == 1:
        model_type = model_name_from_key(request.entity_list()[0].key())
        ds_stats[model_type]['entity_writes'] += response.cost().entity_writes()
        ds_stats[model_type]['index_writes'] += response.cost().index_writes()
    elif call in ('Get', 'Delete'):
      for key in request.key_list():
        ds_stats[model_name_from_key(key)][call] += 1
      if call == 'Get':
        ds_stats['_cost']['reads'] += len(request.key_list())
      elif len(request.key_list()) == 1:
        model_type = model_name_from_key(request.key_list()[0])
        ds_stats[model_type]['entity_writes'] += response.cost().entity_writes()
        ds_stats[model_type]['index_writes'] += response.cost().index_writes()
    elif call in ('RunQuery',): # 'Next'):
      kind = datastore_index.CompositeIndexForQuery(request)[1]
      ds_stats[kind][call] += 1
      if call == 'RunQuery':
        ds_stats[kind]['reads'] += 1
        ds_stats['_cost']['reads'] += 1
      cost_type = 'small_reads' if response.keys_only() else 'reads'
      num_results = len(response.result_list()) + response.skipped_results()
      ds_stats[kind][cost_type] += num_results
      ds_stats['_cost'][cost_type] += num_results
    else:
      ds_stats['?'][call] += 1
    if hasattr(response, 'cost'):
      ds_stats['_cost']['entity_writes'] += response.cost().entity_writes()
      ds_stats['_cost']['index_writes'] += response.cost().index_writes()
  except:
    logging.exception('Exception occurred during datastore stats')


def datastore_stats_wsgi_middleware(app):

  def datastore_stats_wsgi_wrapper(environ, start_response):
    DSStatsHolder.clear()
    try:
      result = app(environ, start_response)
    except Exception:
      end_stats()
      raise
    if result is not None:
      for value in result:
        yield value
    end_stats()

  return datastore_stats_wsgi_wrapper


apiproxy_stub_map.apiproxy.GetPostCallHooks().Append(
    'ds_stats', hook, 'datastore_v3')


# vim: et sw=2 ts=2 sts=2 cc=80
