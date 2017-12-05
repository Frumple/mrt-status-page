from abc import ABCMeta, abstractmethod
from flask import g

class DataStore():
  __metaclass__ = ABCMeta

  def __init__(self, app):
    self.app = app

  @abstractmethod  
  def open_connection(self):
    pass
    
  @abstractmethod
  def close_connection(self):
    pass
    
  @abstractmethod
  def get_data(self):
    pass

  @abstractmethod
  def set_data(self, data):
    pass  
    
  def get_db(self):
    if not hasattr(g, 'db'):
      g.db = self.open_connection()
    return g.db