from .service import Service
from ..enums import Version, Status

from mcstatus import MinecraftServer

MINECRAFT_DEFAULT_PORT = 25565

class MCServer(Service):
  class Software:
    def __init__(self):
      self.reset()
      
    def reset(self):
      self.version = Version.UNKNOWN.value
      self.brand = ""

  class Players:
    def __init__(self):
      self.reset()
      
    def reset(self):
      self.online = 0
      self.max = 0
      self.names = []
  
  def __init__(self, name, address, port = MINECRAFT_DEFAULT_PORT, query_port = MINECRAFT_DEFAULT_PORT, status = None, message = None):
    Service.__init__(self, name, address, status, message)
    self.port = port 
    self.query_port = query_port

    self.software = MCServer.Software()
    self.players = MCServer.Players()
     
  @staticmethod
  def from_json(dict):
    status = dict["status"]
    port = dict["port"] if "port" in dict else MINECRAFT_DEFAULT_PORT
    query_port = dict["query_port"] if "query_port" in dict else port
  
    return MCServer( \
      dict["name"], \
      dict["address"], \
      port, \
      query_port, \
      Status[status] if status is not None else None, \
      dict["message"])
      
  def reset_status(self):
    self.software.reset()
    self.players.reset()
  
  def get_status(self):
    print("MC Server: {} at {}:{}".format(self.name, self.address, self.query_port))
  
    self.reset_status()
  
    server = MinecraftServer(self.address, self.query_port)
    
    try:    
      response = server.query()
 
      self.software.version = response.software.version
      self.software.brand = response.software.brand.split(" ", 1)[0].strip()
      
      self.players.online = response.players.online
      self.players.max = response.players.max
      self.players.names = response.players.names
      
      if not self.status_override:
        self.status = Status.ONLINE
    except Exception as e:
      print(e)
      if not self.status_override:
        self.status = Status.OFFLINE
      
    print("> Version: {} {}, Players: {}/{}, Status: {}, Message: {}".format( \
      self.software.brand, \
      self.software.version, \
      self.players.online, \
      self.players.max, \
      self.status.name, \
      self.message)) 