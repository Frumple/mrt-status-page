import datetime

class DateTimeUtils():
  @staticmethod
  def get_current_datetime_as_string():
    last_updated_datetime = datetime.datetime.now(datetime.timezone.utc)
    return last_updated_datetime.strftime("%Y-%m-%d %H:%M:%S %Z")
