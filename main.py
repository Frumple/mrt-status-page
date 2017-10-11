from flask import Flask, render_template, g

from mcstatus import MinecraftServer
import requests
import Ice

from abc import ABCMeta, abstractmethod
from enum import Enum
from threading import Thread

import datetime
import json
import os
import pickle
import redis
import schedule
import sqlite3
import sys
import time

MINECRAFT_DEFAULT_PORT = 25565

class Status(Enum):
  ONLINE = "online"
  OFFLINE = "offline"
  PARTIAL = "partial"
  ALERT = "alert"
  MAINTENANCE = "maintenance"
  UNKNOWN = "unknown"
  
class Version(Enum):
  UNKNOWN = "Unknown"
 
class Service():
  def __init__(self, name, address, status = None, message = None):
    self.name = name
    self.address = address
    self.status = status
    self.message = message
    
    self.status_override = status is not None

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
    
class MumbleServer(Service):
  class Players:
    def __init__(self):
      self.reset()    
    
    def reset(self):
      self.online = 0
      self.max = 0
      self.names = []

  def __init__(self, name, address, port, ice_address, ice_port, ice_secret, status = None, message = None):
    Service.__init__(self, name, address, status, message)
    self.port = port
    self.ice_address = ice_address
    self.ice_port = ice_port
    self.ice_secret = ice_secret
    
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
      Status[status] if status is not None else None, \
      dict["message"])
      
  def reset_status(self):
    self.version = Version.UNKNOWN.value
    self.players.reset() 
  
  def get_status(self):     
    print("Mumble Server: {} at {}:{}, ICE at {}:{}".format(self.name, self.address, self.port, self.ice_address, self.ice_port))
    
    self.reset_status()
    
    ice = self.initialize_ice()
    
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
    
  def initialize_ice(self):
    initdata_properties = Ice.createProperties(sys.argv)
    initdata_properties.setProperty("Ice.ImplicitContext", "Shared")
    initdata_properties.setProperty("Ice.Default.EncodingVersion", "1.0")
    initdata_properties.setProperty("Ice.Default.Timeout", str(app.config["ICE_TIMEOUT_IN_MILLIS"]))
    
    initdata = Ice.InitializationData()
    initdata.properties = initdata_properties
    
    return Ice.initialize(initdata)    
    
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
    self.reason = ""
  
  def get_status(self):
    print("Web Service: {} at {}".format(self.name, self.address))
  
    self.reset_status()
  
    try:
      http_basic_auth = None
    
      if self.basic_auth_username is not None and self.basic_auth_password is not None:
        http_basic_auth = requests.auth.HTTPBasicAuth(self.basic_auth_username, self.basic_auth_password)
   
      http_response = requests.get(self.address, auth = http_basic_auth)
      self.status_code = http_response.status_code
      self.reason = http_response.reason
    
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
          
    print("> Code: {}, Reason: {}, Status: {}, Message: {}".format( \
      self.status_code, \
      self.reason, \
      self.status.name, \
      self.message))    
  
class ThirdPartyService(Service):
  def __init__(self, name, address, status_address):
    Service.__init__(self, name, address)
    self.status_address = status_address
    
  def get_status(self):
    pass
      
  @staticmethod
  def from_json(dict):
    return ThirdPartyService( \
      dict["name"], \
      dict["address"], \
      dict["status_address"])

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

class DataStore():
  __metaclass__ = ABCMeta

  @abstractmethod
  def __init__(self):
    pass

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
    
class SqliteDataStore(DataStore):
  def __init__(self):
    db = self.get_db()
    with db:
      with app.open_resource(app.config["SQLITE_SCHEMA_FILE"], mode = 'r') as file:
        db.cursor().executescript(file.read())
  
  def open_connection(self):
    db = sqlite3.connect(app.config["SQLITE_DB_FILE"])
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
  
class RedisDataStore(DataStore):
  def __init__(self):
    db = self.get_db()
    db.flushdb()

  def open_connection(self):
    r = redis.Redis(
      host = app.config["REDIS_HOST"], 
      port = app.config["REDIS_PORT"],
      db = app.config["REDIS_DB"],
      password = app.config["REDIS_PASSWORD"])
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
      
def init_slice():
  slice_dir = '-I' + Ice.getSliceDir()   
  slice_file = 'Murmur.ice'  
  Ice.loadSlice('', [slice_dir] + [slice_file])
  
def init_data_store():
  global data_store
  
  data_store_type = app.config["DATA_STORE"]
  if data_store_type is "sqlite":
    data_store = SqliteDataStore()
  elif data_store_type is "redis":
    data_store = RedisDataStore()
  else:
    raise TypeError("'{}' is not a valid data store type. Must be 'sqlite' or 'redis'.".format(data_store_type)) 
 
def init_schedule():
  get_status_every_x_minutes = int(app.config["GET_STATUS_EVERY_X_MINUTES"])
  schedule.every(get_status_every_x_minutes).minutes.do(refresh_data)
  thread = Thread(target = run_schedule)
  thread.start()   
  
def run_schedule():
  while True:
    schedule.run_pending()
    time.sleep(1)
  
def refresh_data():
  global data_store

  with app.app_context():
    print("--- Data refresh started... ---")
    
    data = data_store.get_data()
    if data is None:
      data = Data()
    
    print("Retrieved data last updated at: {}".format(data.last_updated))    
    
    data.load_services()
    data.get_all_statuses()
    
    data_store.set_data(data)    
     
    print("--- Data refresh finished at: {} ---".format(data.last_updated))    

app = Flask(__name__)
app.config.from_pyfile("config.cfg")
with app.app_context():
  init_slice()
  init_data_store()
  refresh_data()
  init_schedule()
  
@app.route("/")
def index():
  global data_store

  data = data_store.get_data()

  print("Data last updated: " + data.last_updated);
  return render_template('index.html', \
    Status = Status, \
    MCServer = MCServer, \
    MumbleServer = MumbleServer, \
    WebService = WebService, \
    ThirdPartyService = ThirdPartyService, \
    title = app.config["PAGE_TITLE"], \
    refresh_every_x_seconds = int(app.config["GET_STATUS_EVERY_X_MINUTES"]) * 60, \
    data = data)
    
@app.teardown_appcontext  
def teardown(error):
  data_store.close_connection()    