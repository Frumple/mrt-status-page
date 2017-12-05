from .datastore import DataStore
from flask import g

import os
import pickle
import sqlite3

SQLITE_SCHEMA_FILE = "schema.sql"

class SqliteDataStore(DataStore):
  def __init__(self, app):
    DataStore.__init__(self, app)

    db = self.get_db()
    with db:
      with app.open_resource(SQLITE_SCHEMA_FILE, mode = 'r') as file:
        db.cursor().executescript(file.read())
  
  def open_connection(self):
    db_path = os.path.join(self.app.instance_path, self.app.config["SQLITE_DB_FILE"])
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db

  def close_connection(self):
    if hasattr(g, 'db'):
      g.db.close()

  def get_data(self):
    db = self.get_db()

    cursor = db.execute("select data from data_store")
    row = cursor.fetchone()

    if row is not None:
      pickled_data = row['data']
      return pickle.loads(pickled_data)
    else:
      return None

  def set_data(self, data):
    db = self.get_db()
    
    with db:
      pickled_data = pickle.dumps(data)
      binary_data = sqlite3.Binary(pickled_data)
      
      if self.get_data() is not None:
        cursor = db.execute("update data_store set data = ?", [binary_data])
      else:     
        cursor = db.execute("insert into data_store (data) values (?)", [binary_data])