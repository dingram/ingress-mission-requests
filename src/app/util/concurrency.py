import time

from google.appengine.api import memcache

from app.util.helpers import to_ms


class LockTimeout(Exception):
  """Exception raised if lock acquisition times out."""
  pass


class MemcacheLock(object):
  """A global lock, handled with Memcache.

  This class provides a context manager that can ensure atomicity and mutual
  exclusion in regions of App Engine code.

  Examples:

    >>> with MemcacheLock('some lock-specific key'):
    >>>   doSomeCriticalThing()

    >>> try:
    >>>   with MemcacheLock('other lock-specific key'):
    >>>     doSomethingThreadUnsafe()
    >>>     doAnotherCriticalThing('foo', 'bar')
    >>> except LockTimeout:
    >>>   print 'Sorry, could not acquire lock'
  """

  def __init__(self, key, timeout_ms=750, namespace=None):
    """Set up the lock.

    Args:
      key: The key to use that uniquely identifies this lock.
      timeout_ms: The maximum number of milliseconds to wait while trying to
        acquire the lock. This is a lower bound, and the wait time may in fact
        be longer.
      namespace: The App Engine namespace to use for Memcache, if any.
    """
    self.key = '<lock>:' + key
    self.timeout = timeout_ms
    self.namespace = namespace

  def __enter__(self):
    """Enter the monitor, attempting to acquire the lock."""
    start = to_ms()
    self.waited = False
    while not memcache.add(self.key, 'LOCK', time=2, namespace=self.namespace):
      self.waited = True
      time.sleep(0.1) # 100ms
      if to_ms() - start > self.timeout:
        raise LockTimeout('Failed to acquire lock within %dms' % self.timeout)
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    """Exit the monitor and release the lock."""
    memcache.delete(self.key, namespace=self.namespace)

# vim: et sw=2 ts=2 sts=2 cc=80
