from flask import Flask, render_template, g

from threading import Thread
import functools
import schedule
import time

from .classes.datastores.sqlitedatastore import SqliteDataStore
from .classes.datastores.redisdatastore import RedisDataStore

from .classes.services.mcserver import MCServer
from .classes.services.mumbleserver import MumbleServer
from .classes.services.webservice import WebService
from .classes.services.thirdpartyservice import ThirdPartyService

from .classes.utils.datetimeutils import DateTimeUtils

from .classes.data import Data
from .classes.enums import Status

def init_data_store(app):
  global data_store

  data_store_type = app.config["DATA_STORE"]
  if data_store_type == "sqlite":
    data_store = SqliteDataStore(app)
  elif data_store_type == "redis":
    data_store = RedisDataStore(app)
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

def catch_exceptions(cancel_on_failure=False):
  global data_store

  def catch_exceptions_decorator(job_func):
    @functools.wraps(job_func)
    def wrapper(*args, **kwargs):
      try:
        return job_func(*args, **kwargs)
      except:
        import traceback
        print(traceback.format_exc())

        with app.app_context():
          data = Data(app)
          data.error = True
          data_store.set_data(data)

        if cancel_on_failure:
          return schedule.CancelJob
    return wrapper
  return catch_exceptions_decorator

@catch_exceptions()
def refresh_data():
  global data_store

  with app.app_context():
    print("--- Data refresh started... ---")

    data = data_store.get_data()
    if data is None:
      data = Data(app)

    print("Data last updated: {}".format(data.last_updated))

    data.load_services()
    data.get_all_statuses()
    data.error = False

    data_store.set_data(data)

    print("--- Data refresh finished: {} ---".format(data.last_updated))

app = Flask(__name__, instance_relative_config = True)
app.config.from_object('mrt_status_page.default_config')
app.config.from_pyfile("config.py")
with app.app_context():
  MumbleServer.init_slice()
  init_data_store(app)
  refresh_data()
  init_schedule()

@app.route("/")
def index():
  global data_store

  data = data_store.get_data()

  print("Current time:      {}".format(DateTimeUtils.get_current_datetime_as_string()))
  print("Data last updated: {}".format(data.last_updated));

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

if __name__ == "__main__":
  app.run()