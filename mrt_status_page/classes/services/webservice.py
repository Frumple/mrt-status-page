from .service import Service
from ..enums import Status

import requests

class WebService(Service):
  def __init__(self, name, address, basic_auth_username = None, basic_auth_password = None, status = None, message = None):
    Service.__init__(self, name, address, status, message)
    self.basic_auth_username = basic_auth_username
    self.basic_auth_password = basic_auth_password
    
    self.reset_status()
    
  @staticmethod
  def from_json(dict):
    status = dict["status"]
      
    return WebService( \
      dict["name"], \
      dict["address"], \
      dict["basic_auth_username"] if "basic_auth_username" in dict else None, \
      dict["basic_auth_password"] if "basic_auth_password" in dict else None, \
      Status[status] if status is not None else None, \
      dict["message"])
  
  def reset_status(self):
    self.status_code = ""
    self.response = ""
  
  def get_status(self):
    print("Web Service: {} at {}".format(self.name, self.address))
  
    self.reset_status()
  
    try:
      http_basic_auth = None
    
      if self.basic_auth_username is not None and self.basic_auth_password is not None:
        http_basic_auth = requests.auth.HTTPBasicAuth(self.basic_auth_username, self.basic_auth_password)
   
      http_response = requests.get(self.address, auth = http_basic_auth)
      self.status_code = http_response.status_code
      self.response = http_response.reason
    
      if http_response.status_code < 400:
        if not self.status_override:
          self.status = Status.ONLINE
      else:
        if not self.status_override:
          self.status = Status.OFFLINE
    except Exception as e:
      print(e)
      if not self.status_override:
          self.status = Status.OFFLINE
          
    print("> Code: {}, Response: {}, Status: {}, Message: {}".format( \
      self.status_code, \
      self.response, \
      self.status.name, \
      self.message))