class Service():
  def __init__(self, name, address, status = None, message = None):
    self.name = name
    self.address = address
    self.status = status
    self.message = message
    
    self.status_override = status is not None