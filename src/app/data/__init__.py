import uuid

from google.appengine.ext import ndb

from app.data import enums


GuidSuffix = enums.enum(
  USER = '1',
)


class AutoUuidProperty(ndb.TextProperty):

  def _prepare_for_put(self, entity):
    if not self._retrieve_value(entity):
      value = uuid.uuid4().hex
      self._store_value(entity, value)


class GuidProperty(ndb.TextProperty):

  _suffix = False

  _attributes = ndb.TextProperty._attributes + ['_suffix']

  def __init__(self, name=None, suffix=None, **kwds):
    super(GuidProperty, self).__init__(name=name, **kwds)
    self._suffix = suffix
    if not suffix:
      raise ValueError('GuidProperty %s must have a suffix.' % self._name)
    if not isinstance(suffix, basestring):
      raise ValueError('GuidProperty %s suffix must be a string.' %
          self._name)

  def _prepare_for_put(self, entity):
    if not self._has_value(entity):
      value = '%s.%s' % (uuid.uuid4().hex, self._suffix)
      self._store_value(entity, value)


class BaseModel(ndb.Model):
  pass


class GuidModel(BaseModel):

  def __init__(*args, **kwds):
    # self is passed implicitly through args so users can define a property
    # named 'self'.
    (self,) = args
    args = args[1:]
    super(GuidModel, self).__init__(*args, **kwds)
    if not self._properties or 'guid' not in self._properties:
      raise TypeError('A "guid" property must be defined for the %s model' %
        self.__class__.__name__)
    # force GUID generation to happen on model instance creation
    self._properties['guid']._prepare_for_put(self)

  @classmethod
  def fetch_by_guid(cls, guid):
    return cls.get_by_id(guid)

  def _prepare_for_put(self):
    # prepare properties, which will definitely populate the GUID
    super(GuidModel, self)._prepare_for_put()
    # use the GUID as the key
    if self._key is None:
      self._key = ndb.Key(self._get_kind(), self.guid)

# vim: et sw=2 ts=2 sts=2 cc=80
