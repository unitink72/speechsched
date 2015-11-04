import time
import urllib.request
import xml.etree.ElementTree as etree

class DrivingTime:

  def __init__ (self, configFromFile):
    proxies                = configFromFile['http_proxy']
    self.opener            = urllib.request.FancyURLopener(proxies)
    self.lastLookupTime    = 0
    self.MIN_REQUEST_DELAY = 1                 #Minimum 1 second between api calls
  #end __init__

  def getDist(self,orig, dest):
    SEC_PER_MIN = 60
    urlTrys = 0
    origStr = orig.replace(' ', '+')
    destStr = dest.replace(' ', '+')

    url = 'http://maps.googleapis.com/maps/api/directions/xml?origin=%s&destination=%s&sensor=false' %(origStr,destStr)

    while urlTrys <= 3:
      try:
        if time.clock() - self.lastLookupTime < self.MIN_REQUEST_DELAY:
          #A negative delay time is possible here, protect using max()
          delayTime = max(0, self.MIN_REQUEST_DELAY - (time.clock() - self.lastLookupTime))
          time.sleep(delayTime)

        self.lastLookupTime = time.clock()
        result              = self.opener.open(url)
        break
      except:
        print ('ERROR. Trying again in a few seconds...')
        time.sleep(3)

      urlTrys += 1
    #end loop

    tree = etree.fromstring(result.read())   #Parse xml

    distxml = tree.find('route/leg/duration/value')
    try:
      distSecStr = distxml.text
    except:
      print ('Google API result not parseable: \n%s' % result.read())
      distSecStr = 'abc'

    if distSecStr.isnumeric():
      distMins = int(distSecStr) / SEC_PER_MIN
      #print ('Got distance %d minutes' % distMins)
      return distMins
    else:
      return None
    #end if

  #end getDist

