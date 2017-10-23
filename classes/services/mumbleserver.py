from .service import Service
from ..enums import Version, Status

import Ice
import sys

class MumbleServer(Service):
  class Players:
    def __init__(self):
      self.reset()
    
    def reset(self):
      self.online = 0
      self.max = 0
      self.names = []

  def __init__(self, name, address, port, ice_address, ice_port, ice_secret, ice_timeout_in_millis = 1000, status = None, message = None):
    Service.__init__(self, name, address, status, message)
    self.port = port
    self.ice_address = ice_address
    self.ice_port = ice_port
    self.ice_secret = ice_secret
    self.ice_timeout_in_millis = ice_timeout_in_millis
    
    self.version = Version.UNKNOWN.value
    self.players = MumbleServer.Players()
  
  @staticmethod
  def from_json(dict):
    status = dict["status"]
  
    return MumbleServer( \
      dict["name"], \
      dict["address"], \
      dict["port"], \
      dict["ice_address"], \
      dict["ice_port"], \
      dict["ice_secret"] if "ice_secret" in dict else None, \
      dict["ice_timeout_in_millis"] if "ice_timeout_in_millis" in dict else None, \
      Status[status] if status is not None else None, \
      dict["message"])
      
  def reset_status(self):
    self.version = Version.UNKNOWN.value
    self.players.reset()
  
  def get_status(self):
    print("Mumble Server: {} at {}:{}, ICE at {}:{}".format(self.name, self.address, self.port, self.ice_address, self.ice_port))
    
    self.reset_status()
    
    ice = self.init_ice()
    
    try:
      if self.ice_secret is not None:
        ice.getImplicitContext().put("secret", self.ice_secret)
      
      proxy_str = str.format("Meta:tcp -h {} -p {}", self.ice_address, self.ice_port)
      proxy = ice.stringToProxy(proxy_str)
      
      import Murmur
      murmur = Murmur.MetaPrx.checkedCast(proxy)

      version_major, version_minor, version_path, version_text = murmur.getVersion()
      self.version = version_text
      
      servers = murmur.getBootedServers()
      server = servers[0]

      if server.isRunning():
        users = server.getUsers().values()
        user_names = list(map(lambda user: user.name, users))
        
        all_conf = murmur.getDefaultConf()
        max_users = all_conf["users"]
        
        self.players.online = len(users)
        self.players.max = max_users
        self.players.names = user_names
        
        if not self.status_override:
          self.status = Status.ONLINE
      else:
        if not self.status_override:
          self.status = Status.OFFLINE
        
    except Exception as e:
      print(e)
      if not self.status_override:
        self.status = Status.OFFLINE
      
    print("> Version: {}, Players: {}/{}, Status: {}, Message: {}".format( \
      self.version, \
      self.players.online, \
      self.players.max, \
      self.status.name, \
      self.message))  
      
    ice.destroy()
    
  def init_ice(self):
    initdata_properties = Ice.createProperties(sys.argv)
    initdata_properties.setProperty("Ice.ImplicitContext", "Shared")
    initdata_properties.setProperty("Ice.Default.EncodingVersion", "1.0")
    initdata_properties.setProperty("Ice.Default.Timeout", str(self.ice_timeout_in_millis))
    
    initdata = Ice.InitializationData()
    initdata.properties = initdata_properties
    
    return Ice.initialize(initdata)

  @staticmethod
  def init_slice():
    slice_dir = '-I' + Ice.getSliceDir()   
    slice_file = 'Murmur.ice'  
    Ice.loadSlice('', [slice_dir] + [slice_file])