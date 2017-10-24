from .datastore import DataStore

import pickle
import redis

class RedisDataStore(DataStore):
  def __init__(self, app):
    DataStore.__init__(self, app)

    db = self.get_db()
    db.flushdb()

  def open_connection(self):
    r = redis.Redis(
      host = self.app.config["REDIS_HOST"],
      port = self.app.config["REDIS_PORT"],
      db = self.app.config["REDIS_DB"],
      password = self.app.config["REDIS_PASSWORD"])
    return r
    
  def close_connection(self):
    pass
    
  def get_data(self):
    db = self.get_db()
    pickled_data = db.get('data')
    
    if pickled_data is not None:
      return pickle.loads(pickled_data)
    else:
      return None

  def set_data(self, data):
    db = self.get_db()
    pickled_data = pickle.dumps(data)
    db.set('data', pickled_data)