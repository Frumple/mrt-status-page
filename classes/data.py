from .services.mcserver import MCServer
from .services.mumbleserver import MumbleServer
from .services.webservice import WebService
from .services.thirdpartyservice import ThirdPartyService

import datetime
import json
import os
import time

class Data(): 
  class ServiceGroup():
    def __init__(self, type, json_path):
      self.services = []
      self.last_loaded = 0
      
      self.type = type
      self.json_path = json_path
      
    def load(self):
      if os.path.getmtime(self.json_path) > self.last_loaded:
        print("Loading {} group from {}...".format(self.type.__name__, self.json_path))
      
        with open(self.json_path) as json_file:
          self.services = json.load(json_file, object_hook = self.type.from_json) 

        self.last_loaded = int(time.time())
    
  def __init__(self):
    self.last_updated = None
    
    self.service_groups = {}
    
    self.service_groups[MCServer] = Data.ServiceGroup(MCServer, 'services/mc_servers.json')
    self.service_groups[MumbleServer] = Data.ServiceGroup(MumbleServer, 'services/mumble_servers.json')
    self.service_groups[WebService] = Data.ServiceGroup(WebService, 'services/web_services.json')
    self.service_groups[ThirdPartyService] = Data.ServiceGroup(ThirdPartyService, 'services/third_party_services.json')

  def load_services(self):
    for key in self.service_groups:
      self.service_groups[key].load()
     
  def get_all_statuses(self):
    for key in self.service_groups:
      for service in self.service_groups[key].services:
        service.get_status()
     
    last_updated_datetime = datetime.datetime.now(datetime.timezone.utc)
    self.last_updated = last_updated_datetime.strftime("%Y-%m-%d %H:%M:%S %Z")