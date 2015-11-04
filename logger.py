import datetime
import os

def timeStamp():
  dateNow = datetime.datetime.now();
  return dateNow.strftime('%d %H:%M:%S')
#end timeStamp

class Logger:

  def __init__ (self, folder):

    self.f = open(os.path.join(folder, 'runLog.txt'), 'w', 1)  #Small as possible buffer
  #end __init__
  
  
  def __del__ (self):
    self.f.close
  #end __del__

  def msg (self, msg):
    self.f.write (timeStamp() + ' ' + msg + '\n')

#end Logger
