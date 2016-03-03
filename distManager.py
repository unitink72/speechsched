from collections import defaultdict
import drivingTime
import os
import pickle

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


  def __init__ (self,logger,config):

    if os.path.exists(self._cacheFile):
      f = open(self._cacheFile, 'rb')
      self.nestedDict = pickle.load(f)
      self.schoolAddr = pickle.load(f)
      f.close
    else:
      self.nestedDict = defaultdict(dict)
      self.schoolAddr = {}
    #end if
    self.timeFetcher = drivingTime.DrivingTime(config)
    self.logger      = logger
    self.hostSchool  = 0
  #end __init__


  def __del__ (self):
    #self.writeCache() Not working for some reason?????  #############
    pass
  #end __del__

  def writeCache(self):
    f = open(self._cacheFile, 'wb')
    pickle.dump(self.nestedDict, f)
    pickle.dump(self.schoolAddr, f)
    f.close()
  #end writeCache

  #def getCache(self)
  #  return (self.nestedDict, self.schoolAddr)
  #def setCache(self, cacheA, cacheB)
  #  self.nestedDict = cacheA
  #  self.schoolAddr = cacheB

  def addSchool(self,school,address):
    if school not in self.nestedDict:
      #Adding a new school to the list (new row).  Add a column for each existing school.
      self.nestedDict[school] = dict.fromkeys(list(self.nestedDict.keys()))
      self.schoolAddr[school] = address
  #end addSchools

  def driveTimeLookup(self, school1, school2):
    if school1 == school2:
      return 0
    elif school1 in self.nestedDict           \
      and school2 in self.nestedDict[school1] \
      and self.nestedDict[school1][school2] != None:

      return self.nestedDict[school1][school2]

    elif school2 in self.nestedDict \
      and school1 in self.nestedDict[school2] \
      and self.nestedDict[school2][school1] != None:

      return self.nestedDict[school2][school1]

    else:
      self.logger.msg('Driving Time not found! %s %s' % (school1,school2))
      return 0
    #end if
   #end driveTimeLookup

  def setHostSchool(self, hostSchool):
    #Call this last after adding all the schools.
    #Will compute distances from all schools to the Host.  There
    #are two cells for every school pair, so just fill in one of them.
    self.hostSchool = hostSchool
    for school1 in self.schoolAddr.keys():

      #Get the list of column-wise schools in the row.
      otherSchools = list(self.nestedDict[school1].keys())

      for school2 in otherSchools:

        #If this dict's value is None and the table's compliment doesn't exist or
        #is None, perform the lookup.
        if (school1 == hostSchool or school2 == hostSchool) and \
           self.nestedDict[school1][school2] is None and        \
        (  school1 not in self.nestedDict[school2] or           \
           self.nestedDict[school2][school1] is None ):

          self.logger.msg('getDist %s:%s %s %s' % (school1, school2, formatSch(self.schoolAddr[school1]), formatSch(self.schoolAddr[school2])))
          self.nestedDict[school1][school2] = self.timeFetcher.getDist                \
                                                       (self.schoolAddr[school1],     \
                                                        self.schoolAddr[school2])
#    for school1 in self.nestedDict.keys():
#      if school1 != hostSchool and                           \
#         self.nestedDict[hostSchool][school1] == None and    \
#         self.nestedDict[school1][hostSchool] == None:

#        self.logger.msg('getDist %s %s' %                             \
#                            (formatSch(self.schoolAddr[hostSchool]),  \
#                             formatSch(self.schoolAddr[school1])))

#        self.nestedDict[hostSchool][school1] = self.timeFetcher.getDist        \
#                                                (self.schoolAddr[hostSchool],  \
#                                                 self.schoolAddr[school1])

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

          self.logger.msg('getDist %s %s' % (formatSch(self.schoolAddr[school1]), formatSch(self.schoolAddr[school2])))
          self.nestedDict[school1][school2] = self.timeFetcher.getDist                \
                                                       (self.schoolAddr[school1],     \
                                                        self.schoolAddr[school2])

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

  #end printTimes
