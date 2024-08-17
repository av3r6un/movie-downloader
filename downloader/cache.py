import shutil
import os

class CacheTree:
  __folders = []
  __files = []

  def __init__(self, path):
    super().__init__()
    self.path = path

  @property
  def folders(self):
    return self.__folders

  @folders.setter
  def folders(self, value):
    self.__folders.append(value)

  @property
  def files(self):
    return self.__files
  
  @files.setter
  def files(self, value):
    self.__files.append(value)

  def clear_folders(self):
    for folder in self.__folders:
      if os.path.exists(f'{self.path}/{folder}'):
        shutil.rmtree(f'{self.path}/{folder}')
      self.__folders.remove(folder)

  def clear_files(self):
    for file in self.__files:
      if os.path.exists(f'{self.path}/{file}'):
        os.remove(f'{self.path}/{file}')
      self.__files.remove(file)

  def clear(self):
    self.clear_files()
    self.clear_folders()
