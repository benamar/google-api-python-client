# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""App Engine memcache based cache for the discovery document."""

import logging
import pickle

# This is only an optional dependency because we only import this
# module when google.appengine.api.memcache is available.
from google.appengine.api import memcache

from . import base
from ..discovery_cache import DISCOVERY_DOC_MAX_AGE


LOGGER = logging.getLogger(__name__)

NAMESPACE = 'google-api-client'


class Cache(base.Cache):
  """A cache with app engine memcache API."""

  def __init__(self, max_age, use_multi=True):
      """Constructor.

      Args:
        max_age: Cache expiration in seconds.
        use_multi: use multi keys cache to overcome MAX size limitation.
        TODO: may be retrieved from a configuration parameter
      """
      self._max_age = max_age
      self._use_multi = use_multi

  def get(self, url):
    if self._use_multi:
      return self.get_multi(url)

    try:
      return memcache.get(url, namespace=NAMESPACE)
    except Exception as e:
      LOGGER.warning(e, exc_info=True)

  def set(self, url, content):
    if self._use_multi:
      return self.set_multi(url,content)

    try:
      memcache.set(url, content, time=int(self._max_age), namespace=NAMESPACE)
    except Exception as e:
      LOGGER.warning(e, exc_info=True)

  def set_multi(self, key, value, chunksize=950000):
    try:
      serialized = pickle.dumps(value, 2)
      values = {}
      for i in xrange(0, len(serialized), chunksize):
        values['%s.%s' % (key, i//chunksize)] = serialized[i : i+chunksize]
      memcache.set_multi(values)
    except Exception as e:
      LOGGER.warning(e, exc_info=True)

  def get_multi(self, key):
    try:
      result = memcache.get_multi(['%s.%s' % (key, i) for i in xrange(32)])
      serialized = ''.join([v for k, v in sorted(result.items()) if v is not None])
      return pickle.loads(serialized)
    except Exception as e:
      LOGGER.warning(e, exc_info=True)

cache = Cache(max_age=DISCOVERY_DOC_MAX_AGE)
