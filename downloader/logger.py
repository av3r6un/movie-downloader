from colorama import Fore

class Logger:
  __messages = []

  def __init__(self, error_color: str, info_color: str, not_colorize=False):
    self.info_c = getattr(Fore, f'{info_color.upper()}') if not not_colorize else ''
    self.error_c = getattr(Fore, f'{error_color.upper()}') if not not_colorize else ''
    self.reset = Fore.RESET if not not_colorize else ''
    self.main = Fore.YELLOW if not not_colorize else ''

  @property
  def messages(self):
    return self.__messages
  
  @messages.setter
  def messages(self, value):
    self.__messages.append(value)

  def info(self, message):
    self.messages = message
    print(self.info_c + '[INFO]:\t', self.main + message + self.reset)
  
  def error(self, message):
    self.messages = message
    print(self.error_c + '[INFO]:\t', self.main + message + self.reset)
  
  def last(self):
    return self.__messages[-1]
