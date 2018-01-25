import time
import urllib.request
import xml.etree.ElementTree as etree

class DrivingTime:

  def __init__ (self, configFromFile):
    proxies                = configFromFile['http_proxy']
    self.opener            = urllib.request.FancyURLopener(proxies)
    self.lastLookupTime    = 0
    self.MIN_REQUEST_DELAY = 0.5  #Minimum .5 second between api calls
  #end __init__

  def getDist(self,orig, dest):
    SEC_PER_MIN = 60
    urlTrys = 0
    origStr = orig.replace(' ', '%20')
    destStr = dest.replace(' ', '%20')
    origStr = origStr.replace(',', '%2C')
    destStr = destStr.replace(',', '%2C')
    distSecStr = ''

    url = 'http://maps.googleapis.com/maps/api/directions/xml?origin=%s&destination=%s&sensor=false' %(origStr,destStr)

    while urlTrys <= 15:
      try:
        if time.clock() - self.lastLookupTime < self.MIN_REQUEST_DELAY:
          #A negative delay time is possible here, protect using max()
          delayTime = max(0, self.MIN_REQUEST_DELAY - (time.clock() - self.lastLookupTime))
          time.sleep(delayTime)

        self.lastLookupTime = time.clock()
        result              = self.opener.open(url)

        tree       = etree.fromstring(result.read())
        distxml    = tree.find('route/leg/duration/value')
        distSecStr = distxml.text
        break
      except:
        print ('Drivetime lookup error %s %s.  Retrying...'% (orig,dest))
        distSecStr = 'abc'
        time.sleep(1)

      urlTrys += 1
    #end loop

    if distSecStr.isnumeric():
      distMins = int(distSecStr) / SEC_PER_MIN
      #print ('Got distance %d minutes' % distMins)
      return distMins
    else:
      print ('Error in distance lookup between\n%s\n%s' % (origStr,destStr))
      print ('URL open result:')
      print (result.read())
      return 1
    #end if

  #end getDist

