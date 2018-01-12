#from collections import defaultdict
import drivingTime
import os
#import pickle
import random

def formatSch (schoolStr):
  strWidth = 20
  if len(schoolStr) < strWidth:
    trailingSpaces = strWidth - len(schoolStr)
    return schoolStr + (' ' * trailingSpaces)
  else:
    return schoolStr
#end formatSch

class DistManager:

  _cacheFile = 'schoolDist.cache'


  def __init__ (self,logger,config,dryRunMode):

    #if os.path.exists(self._cacheFile):
    #  f = open(self._cacheFile, 'rb')
    #  self.nestedDict = pickle.load(f)
    #  self.schoolAddr = pickle.load(f)
    #  f.close
    #else:
    #self.nestedDict = defaultdict(dict)
    self.sList   = {}
    self.schoolAddr = {}
    #end if
    self.timeFetcher  = drivingTime.DrivingTime(config)
    self.logger       = logger
    self.hostSchool   = 0
    self.hostAddr     = ''
    self.allAddrValid = 1
    self.dryRunMode   = dryRunMode
    if dryRunMode:
       self.logger.msg('getDist using RANDOM values from 1-100 for dryrun mode')
  #end __init__


  def __del__ (self):
    #self.writeCache() Not working for some reason?????  #############
    pass
  #end __del__

  #def writeCache(self):
  #  f = open(self._cacheFile, 'wb')
  #  pickle.dump(self.nestedDict, f)
  #  pickle.dump(self.schoolAddr, f)
  #  f.close()
  #end writeCache

  #def getCache(self)
  #  return (self.nestedDict, self.schoolAddr)
  #def setCache(self, cacheA, cacheB)
  #  self.nestedDict = cacheA
  #  self.schoolAddr = cacheB

  def addSchool(self,school,address):
    if school not in self.sList:
      self.sList[school] = [1, address] #Default drivetime to 1
      if not address:
         self.logger.msg('School %s has blank City in schoolsExport.csv' % school)
         self.allAddrValid = 0
  #end addSchools

  def driveTimeLookup(self, school):
    if school == self.hostSchool:
      return 0

    elif school in self.sList:
      return self.sList[school][0]

    else:
      self.logger.msg('Driving Time not found! %s %s' % (school1,school2))
      return 0
    #end if
   #end driveTimeLookup

  def setHostSchool(self, hostSchool, hostAddr):
    #Call this last after adding all the schools.
    #Will compute distances from all schools to the Host.  There
    #are two cells for every school pair, so just fill in one of them.
    self.hostSchool = hostSchool
    self.hostAddr   = hostAddr

    for schoolID in self.sList.keys():

      if not self.sList[schoolID][1]:
        #School doesn't have an address
        dist = 0
        self.logger.msg('No Addr')
      else:
        if self.dryRunMode:
           dist = random.randrange(100)
        else: 
           dist = self.timeFetcher.getDist (self.sList[schoolID][1], hostAddr)
          
           self.sList[schoolID][0] = dist
           self.logger.msg('getDist %s:%s %s %s (%d)' % (hostSchool,                         \
                                                         schoolID,                           \
                                                         formatSch(hostAddr),                \
                                                         formatSch(self.sList[schoolID][1]), \
                                                         dist))


  def calculateAllTimes(self):
    #Brute force lookup of times between every school.  Probably
    #not usefull since the lookup count grows at N^2

    for school1 in self.schoolAddr.keys():

      #Get the list of column-wise schools in the row.
      otherSchools = list(self.nestedDict[school1].keys())

      for school2 in otherSchools:
        #If this dict's value is None and the table's compliment doesn't exist or
        #is None, perform the lookup.
        if self.nestedDict[school1][school2] is None and  \
        (  school1 not in self.nestedDict[school2] or     \
           self.nestedDict[school2][school1] is None ):

          if self.dryRunMode:
             dist = random.randrange(100)
          else:
             dist = self.timeFetcher.getDist (self.schoolAddr[school1],     \
                                              self.schoolAddr[school2])

          self.nestedDict[school1][school2] = dist
          self.logger.msg('getDist %s:%s %s %s (%d)' % (school1,         \
                                                        school2,         \
                                                        formatSch(self.schoolAddr[school1]), \
                                                        formatSch(self.schoolAddr[school2]), \
                                                        dist))
  #end calculateTimes

  def printTimes(self):
    self.logger.msg ('Driving times')
    for school1 in self.schoolAddr.keys():

      #Get the list of column-wise schools in the row.
      otherSchools = list(self.nestedDict[school1].keys())

      for school2 in otherSchools:
        if self.nestedDict[school1][school2] == None:
          self.logger.msg ('X  %s %s' % (school1, school2))
        else:
          self.logger.msg ('%3d %s %s' % (self.nestedDict[school1][school2], formatSch(school1), formatSch(school2)))

  #end printTimes

  def printAddr(self):
    self.logger.msg ('School addresses')
    for key in self.schoolAddr:
      self.logger.msg ('%s - %s' % (formatSch(key), self.schoolAddr[key]))

  def allAddressesValid(self):
     #Returns true of all school lookups were given a non-blank city/address string
     return self.allAddrValid

  #end printTimes
