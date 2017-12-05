from .service import Service

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