# MRT Status Page Configuration

# Sets which datastore to use for storing statuses retrieved from the services.
# Two options are available:
# - "sqlite" - SQLite 3 database file.
# - "redis" - Redis in-memory datastore. You must set up your own Redis instance to connect to.
DATA_STORE = "sqlite"

# The following options only apply if SQLite is the datastore:

SQLITE_DB_FILE = "sqlite.db"      # Name of the sqlite database file stored in the webroot.
SQLITE_SCHEMA_FILE = "schema.sql" # Name of the SQL file specifying commands to run when the webserver is started.

# The following options only apply if Redis is the datastore:

REDIS_HOST = "localhost"    # The address of the Redis instance
REDIS_PORT = 6379           # The port number of the Redis instance
REDIS_DB = 0                # The database number of the Redis instance
REDIS_PASSWORD = "password" # The password required to access the Redis instance. If no password is required, set this to null.

# Other configuration options

# The title of the status page
PAGE_TITLE = "My Status Page"

# How often new statuses should be retrieved from the services
GET_STATUS_EVERY_X_MINUTES = 1