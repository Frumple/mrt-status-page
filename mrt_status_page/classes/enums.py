from enum import Enum

class Status(Enum):
  ONLINE = "online"
  OFFLINE = "offline"
  PARTIAL = "partial"
  ALERT = "alert"
  MAINTENANCE = "maintenance"
  UNKNOWN = "unknown"

class Version(Enum):
  UNKNOWN = "Unknown"