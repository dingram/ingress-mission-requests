import base64
import hashlib
import hmac
import json
import logging
import os
import uuid

from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.runtime import apiproxy_errors
from google.appengine.runtime import DeadlineExceededError
import webapp2

import datastore_stats

from app.data.models import User
from app.util import users
from app.util.helpers import json_encode
from app.util.helpers import to_ms
from app.util.timing import Stopwatch


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(
  os.path.dirname(__file__))), 'tpl')

_OAUTH_WHITELIST = frozenset([
  '292824132082.apps.googleusercontent.com', # API explorer
  '407408718192.apps.googleusercontent.com', # OAuth2 playground
])


class RequestHandler(webapp2.RequestHandler):
  """Base class to be used for all request handlers.

  This class provides a number of useful utility functions for rendering.

  Attributes:
    _log (bool): Whether to log request information. In this class, it just
      controls logging of rendered JSON output. Subclasses may use it to control
      other request-related logging, such as request parameters.
  """
  _log = True
  XSRF_NAME = '__xsrf__'

  def dispatch(self, *args, **kwargs):
    self.gae_user = users.get_current_user()
    if users.is_oauth():
      if users.get_client_id() not in _OAUTH_WHITELIST:
        logging.warning('OAuth consumer %s forbidden' % users.get_client_id())
        self.abort(403)
    with Stopwatch.timer('userfetch'):
      self.user = User.get_current()
    try:
      super(RequestHandler, self).dispatch(*args, **kwargs)
      self.flush_stopwatch()
    except Exception:
      self.flush_stopwatch()
      raise

  def flush_stopwatch(self):
    # flush any pending stopwatch timings
    if Stopwatch.exists():
      Stopwatch.flush()

  def render_page(self, template_file, vars=None):
    """Render a template to the response output stream.

    Some variables are automatically provided to the template:

      CURRENT_PAGE: contains the name of the template file (excluding path and
        extension).
      USER: provides access to the current user object

    Args:
      template_file: path to the template to render, relative to TEMPLATE_DIR.
      vars: additional template variables to set, if any. Note that the
        automatic variables will override any with the same name.
    """
    params = vars or {}
    params['CURRENT_PAGE'] = os.path.splitext(os.path.split(
      template_file)[1])[0]
    if not 'USER' in params:
      params['USER'] = self.user
    params['XSRF_NAME'] = self.XSRF_NAME
    params['XSRF_TOKEN'] = self.get_xsrf_token()
    path = os.path.join(TEMPLATE_DIR, template_file)
    self.response.out.write(template.render(path, params))

  def xsrf_key(self):
    # check xsrf_key to see if it's been saved to the datastore
    if self.user and self.user.xsrf_key:
      key = self.user.xsrf_key
    elif self.gae_user:
      key = self.gae_user.user_id()
    else:
      key = os.environ.get('REMOTE_ADDR')
    return str(key) + str(os.environ.get('CURRENT_VERSION_ID'))

  def xsrf_signature(self, timestamp, nonce):
    logging.info(type(self.xsrf_key()))
    return base64.urlsafe_b64encode(hmac.HMAC(
        self.xsrf_key(),
        timestamp + nonce,
        hashlib.sha1
    ).digest()).strip('=')

  def get_xsrf_token(self, key=None):
    timestamp = str(to_ms())
    nonce = base64.urlsafe_b64encode(uuid.uuid4().bytes).strip('=')
    if key:
      nonce += str(key)
    signature = self.xsrf_signature(timestamp, nonce)
    return ':'.join([timestamp, nonce, signature])

  def check_xsrf_token(self, required=True, key=None):
    token = self.request.POST.get(self.XSRF_NAME)
    if not token:
      if required:
        logging.warning('XSRF violation: not present')
        self.abort(403)
      else:
        return False
    try:
      timestamp, nonce, signature = token.split(':')
      if not timestamp or not nonce or not signature:
        logging.warning('XSRF violation: improper token format')
        self.abort(403)
      if key:
        nonce += str(key)
      expected_sig = self.xsrf_signature(timestamp, nonce)
      if signature != expected_sig:
        logging.warning('XSRF violation: signature mismatch')
        self.abort(403)
      # 12hr limit
      if to_ms() > int(timestamp) + (3600000 * 12):
        logging.warning('XSRF violation: timestamp too old')
    except webapp2.HTTPException:
      # Let aborts through
      pass
    except:
      logging.exception('XSRF violation: exception')
      self.abort(403)
    return True

  def render_json(self, *args, **kwargs):
    """Render standard-format JSON to the response output stream, including
    correct headers.

    Standard-format JSON is an object with exactly one of the following keys:

      result: Indicates a successful response. May be of any type, even None.
      error: Indicates a known error, either client or server side. Usually a
        string, but is not required to be.
      exception: Indicates an unexpected exception was raised in the server
        code. Must be a string.

    Other keys for the response may be provided as keyword arguments.

    Note also that if _log is set on the instance, this method will log the
    rendered object.

    Args:
      *args[0]: Value for the "result" key in the output.
      **kwargs[result]: Value for the "result" key in the output. Overrides
        *args[0], if present.
      **kwargs[error]: Value for the "error" key in the output.
      **kwargs[exception]: Value for the "exception" key in the output.
      **kwargs: Any other keyword arguments are added verbatim to the output
        object.
    """
    output = {}
    if len(args) > 0:
      output['result'] = args[0]
    if 'result' in kwargs:
      output['result'] = kwargs['result']
      del kwargs['result']
    if 'error' in kwargs:
      output['error'] = kwargs['error']
      del kwargs['error']
    if 'exception' in kwargs:
      if not isinstance(kwargs['exception'], basestring):
        raise ValueError('exception must be a string')
      output['exception'] = kwargs['exception']
      del kwargs['exception']

    if kwargs:
      output.update(kwargs)

    # sanitize
    with Stopwatch.timer('json/sanitize'):
      output = self.sanitize_json_for_output(output)

    self.response.content_type = 'application/json'
    self.response.charset = 'utf8'

    with Stopwatch.timer('json/write'):
      json_encode(output, stream=self.response.out)
    if self._log:
      with Stopwatch.timer('json/log'):
        logging.debug('Result: %s', json_encode(output))

  def sanitize_json_for_output(self, obj):
    """Sanitize JSON for output, removing internal-only fields that may appear
    from caches."""
    if hasattr(obj, 'iteritems'):
      return {
          k: self.sanitize_json_for_output(v)
          for k, v in obj.iteritems()
          if k == '_ds_stats' or not k.startswith('_')
      }
    elif isinstance(obj, (list, set, tuple)):
      return [self.sanitize_json_for_output(v) for v in obj]
    else:
      return obj

  def abort_not_found(self):
    """Render a standard "not found" page to the response output stream, and
    abort further processing with the 404 status code.

    Note that the default template is "404.html".
    """
    self.render_page('404.html')
    self.abort(404)


class BlobstoreUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  """Blobstore upload handler subclass, which clones the render_page method from
  RequestHandler.
  """

  # clone method from RequestHandler
  render_page = RequestHandler.__dict__['render_page']


class RpcError(StandardError):
  """Representation of an RPC error."""
  pass


def rpc_precondition(test, error):
  """Immediately abort processing with an error if a precondition is not met.

  Args:
    test: The precondition to test.
    error: The error message to raise.
  """
  if not test:
    raise RpcError(error)


class RpcRequestHandler(RequestHandler):
  """Base class to be used for all RPC request handlers.

  This class set up a number of elements for the request, such as the current
  user object. It handles parameter deserialization, authorization and
  authentication checks, and response serialization.

  All requests must use POST (or OPTIONS for CORS checking). GET requests are
  rejected immediately. Subclasses must implement the rpc() method, which
  accepts a single argument containing the deserialized parameters sent in the
  request.

  Attributes:
    rpc_params: A dict of the RPC parameters passed to this request.
    raw_rpc_params: A dict of all RPC parameters passed to this request,
      including side-channel data.
    user: The User model associated with the currently logged-in user.
  """
  DEPRECATED = False

  def __init__(self, *args, **kwargs):
    super(RpcRequestHandler, self).__init__(*args, **kwargs)
    self.rpc_params = None
    self.raw_rpc_params = None

  def abort_not_found(self):
    """Render a standard "not found" page to the response output stream, and
    abort further processing with the 404 status code.

    The superclass method is overridden to always render JSON."""
    self.render_json(exception='Not found')
    self.abort(404)

  def rpc_precondition(self, test, error):
    """Immediately abort processing with an error if a precondition is not met.

    Args:
      test: The precondition to test.
      error: The error message to raise.
    """
    rpc_precondition(test, error)

  def rpc_optional_param(self, name, param_type, type_error=None):
    """Declare an optional parameter for this RPC request, and ensure it matches
    a specific type if present.

    Args:
      name: The parameter name.
      param_type: The parameter type. Either a single type, or a tuple of
        types. If None, then no type checking is performed.
      type_error: A custom error message to return if the parameter has the
        wrong type.

    Returns:
      The argument value if present, otherwise None.
    """
    if param_type is not None and type_error is None:
      type_desc = ''
      if isinstance(param_type, tuple):
        type_desc = '/'.join(t.__name__ for t in param_type)
      else:
        type_desc = param_type.__name__
      type_desc = type_desc.replace('basestring', 'string')
      type_error = 'Parameter "%s" must be of type %s, not type %%s' % (name, type_desc)
    if not self.rpc_params or name not in self.rpc_params:
      return None
    if param_type is not None and not isinstance(self.rpc_params[name], param_type) and self.rpc_params[name] is not None:
      raise TypeError(type_error % (type(self.rpc_params[name]).__name__,))
    return self.rpc_params[name]

  def rpc_require_param(self, name, param_type, error=None, type_error=None):
    """Declare a required parameter for this RPC request, and ensure it matches
    a specific type.

    Args:
      name: The parameter name.
      param_type: The parameter type. Either a single type, or a tuple of
        types. If None, then no type checking is performed.
      error: A custom error message to return if the parameter is not present.
      type_error: A custom error message to return if the parameter has the
        wrong type.

    Returns:
      The argument value if present, otherwise None.
    """
    if param_type is not None:
      if isinstance(param_type, tuple):
        type_desc = '/'.join(t.__name__ for t in param_type)
      else:
        type_desc = param_type.__name__
      type_desc = type_desc.replace('basestring', 'string')
    if error is None:
      if param_type is None:
        error = 'Parameter "%s" is required' % (name,)
      else:
        error = '%s parameter "%s" is required' % (type_desc, name)
    if param_type is not None and type_error is None:
      type_error = 'Parameter "%s" must be of type %s, not type %%s' % (name, type_desc)
    if not self.rpc_params or name not in self.rpc_params:
      raise KeyError(error)
    if param_type is not None and not isinstance(self.rpc_params[name], param_type):
      raise TypeError(type_error % (type(self.rpc_params[name]).__name__,))
    return self.rpc_params[name]

  def client_error(self, error):
    """Immediately abort the request and return an error response.

    Args:
      error: The error message to raise.

    Raises:
      RpcError: Used to abort processing.
    """
    raise RpcError(error)

  def preprocess_params(self, params):
    """Preprocess the deserialized parameters, performing any necessary
    side-channel actions.

    Args:
      params: The deserialized parameters for the request.

    Returns:
      The parameters that requests can act upon, with side-channel data removed.
    """
    if 'params' not in params:
      logging.warning('JSON missing "params" key')
      self.render_json(exception='Invalid request body')
      self.abort(400)
    self.knob_timestamp = params.get('knob_timestamp', None)
    return params['params']

  def get(self, *args, **kwargs):
    """Handle a GET request.

    Returns a 405 Method Not Allowed response and aborts request processing.
    """
    self.render_json(exception='Method not allowed')
    self.abort(405, headers=[('Allow', 'POST')])

  def cors_check(self, force=False):
    """Check whether CORS is permitted for this RPC endpoint.

    If CORS is not permitted, aborts processing immediately with a 403 error.

    Args:
      force: If True, forces the check to happen in the absence of an "Origin"
        header in the request.
    """
    if ('origin' in self.request.headers) or force:
      if getattr(self.rpc, 'rpc_allow_cors', False):
        self.response.headers.add_header('Access-Control-Allow-Origin',
            self.request.headers.get('origin', '*'))
        self.response.headers.add_header('Access-Control-Allow-Headers',
            'Content-Type,Cookie,X-Token')
        self.response.headers.add_header('Access-Control-Allow-Methods',
            'POST,OPTIONS')
        self.response.headers.add_header('Access-Control-Allow-Credentials',
            'true')
      else:
        logging.warning('CORS request from %s forbidden' %
            self.request.headers.get('origin', '*'))
        self.render_json(exception='CORS request forbidden')
        self.abort(403)

  def options(self, *args, **kwargs):
    """Handle an OPTIONS request.

    Used for CORS preflight requests.
    """
    logging.debug('OPTIONS request')
    self.cors_check(force=True)

  def check_authorization(self):
    """Ensure that the current user is allowed to access this RPC call, or raise
    an appropriate error if not.
    """
    if self.gae_user:
      if self.user:
        logging.info('User: %s' % self.user.nickname)
      else:
        logging.info('No user for: %s' % self.gae_user.email())
    else:
      logging.info('No GAE user')

    #if self.user and self.user.is_banned:
    #  logging.info('USER BANNED; request forbidden')
    #  self.abort(403)

  def post(self, *args, **kwargs):
    """Handle a POST request."""
    if self.request.route_kwargs.get('deprecated', False):
      logging.warning('Deprecated endpoint')

    self.cors_check()

    try:
      self.raw_rpc_params = json.loads(self.request.body)
      if self._log:
        logging.debug(self.request.body)
    except:
      self.raw_rpc_params = None
      logging.warning("Invalid JSON body to POST: " + self.request.body)
      self.render_json(exception='Invalid request body')
      self.abort(400)
      return

    try:
      self.rpc_params = self.preprocess_params(self.raw_rpc_params)

      self.check_authorization()

      resp = self.rpc(self.rpc_params)
      extras = {}
      if self.user and self.user.is_superadmin:
        extras['_ds_stats'] = datastore_stats.get_stats()
      if self.request.route_kwargs.get('deprecated', False):
        extras['deprecated'] = True
      self.render_json(resp, **extras)
    except webapp2.HTTPException as e:
      # Let HTTP exceptions through
      if not self.response._app_iter:
        # Render our own last-ditch exception if there is no response body
        self.render_json(exception=e.title)
      self.response.set_status(e.code)
      return
    except RpcError as e:
      if len(e.args) == 1:
        self.render_json(error=e.args[0])
        # NOTE: this is not ideal, but the client needs to be able to cope
        # better with non-200 responses.
        self.response.status = 200
        return
      elif len(e.args) > 1:
        self.render_json(error=e.args[1])
        self.response.status = int(e.args[0])
        return
      else:
        logging.exception('Should not happen')
        self.render_json(exception='Internal server error')
        self.response.status = 500
        return
    except apiproxy_errors.OverQuotaError:
      logging.exception('Over quota')
      self.render_json(error='OVER_QUOTA')
      self.response.status = 503
    except DeadlineExceededError, apiproxy_errors.DeadlineExceededError:
      logging.exception('Internal timeout')
      self.render_json(error='TIMEOUT')
      self.response.status = 503
    except BaseException as e:
      logging.exception('Unexpected exception')
      self.render_json(exception=str(e))
      self.response.status = 500
      return

# vim: et sw=2 ts=2 sts=2 cc=80
