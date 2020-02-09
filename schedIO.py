import csv, re, sys
import math
import os
import pickle
import random
import string
from categories import Categories
from operator import itemgetter

ioLog = None
cats  = None

#Globals used for creating school codes
rnd       = random.SystemRandom()
usedCodes = []

def setLogger(logger):
  global ioLog
  ioLog = logger
###############################################################################
  
def setCats(groupOrIndiv):
  global cats
  cats = Categories(groupOrIndiv)
###############################################################################

def addTime(time1, time2):
  #Adds two clock times
  time1Hours     = math.floor(time1 / 100)
  time1Minutes   = time1 % 100
  time2Hours     = math.floor(time2 / 100)
  time2Minutes   = time2 % 100

  mins  = time1Minutes + time2Minutes
  hours = time1Hours + time2Hours
  if mins >= 60:
    mins -= 60
    hours +=1

  return (hours * 100) + mins
#end addTime ##################################################################
###############################################################################

def to12hr(time):
  hrs  = math.floor(time / 100)
  mins = time % 100
  if hrs > 12:
    hrs -= 12
  return ('%2d:%02d' % (hrs, mins))
#end to12hr   #################################################################
###############################################################################

def readSessionsFile(fileName):
  sessionsFile = open (fileName, 'r', encoding='utf-8-sig')

  sessionList     = []
  catagoryIndexes = {}

  curCategory      = ''   #cur is short for "current'
  curCategoryAbrv  = ''   # Two-character category abbreviation
  curRoom          = ''
  curDuration      = 0
  nonBreakCount    = 0
  breakCount       = 0
  lineNum          = 0

  newCategoryPattern = re.compile("^([\w\s]+)\s+(\w{2,3})\s+(\d+)",  re.IGNORECASE)
  newRoomPattern     = re.compile("^ROOM (.+)",        re.IGNORECASE)
  newSessionPattern  = re.compile("^(\d+)\s*(BREAK)?", re.IGNORECASE)
  skipLinePattern    = re.compile("(^$)|(^##)")
  multEntryPattern   = re.compile("(^\d{3,4})\s?\*\s?(\d+)")

  catBreakCounts = cats.countDict()
  catEntryCounts = cats.countDict()

  while 1:
    line = sessionsFile.readline()
    lineNum += 1
    if not line: break

    #Skip empty or comment lines
    p1 = skipLinePattern.match(line);
    if p1: continue

    p2 = newCategoryPattern.match(line);

    #Check if a new category is being read
    #Ignore lines with the 'Room' keyword
    if p2 and line.find ('Room') == -1:

      curCategory     = p2.group(1).strip()
      curCategoryAbrv = p2.group(2).strip()
      curDuration     = int(p2.group(3))

      if not curCategoryAbrv in cats.shortList():
      # Validate the catShort.  Long cat name unused, it could be removed from sessions file
        sys.exit ('Sessions file line %d unknown category %s' % (lineNum,curCategoryAbrv))

      #Grab the next line in the file, should specify a Room
      line = sessionsFile.readline()
      lineNum += 1
      p3 = newRoomPattern.match(line)

      if p3:
        curRoom = p3.group(1).strip()
        #print ('Reading %s %s %d' % (curCategory, curRoom, curDuration))
      else:
        sys.exit ("No room specified after %s in Sessions file line %d" % (curCategory,lineNum))
      #end if
      continue
    #end if

    #Check for a room line not directly after a catagory line.  Happens when
    #a catagory takes up multiple rooms.
    p3 = newRoomPattern.match(line)
    if p3:
      curRoom = p3.group(1).strip()
      continue
    #end if

    #One session. Specifies a start time and possibly the keyword BREAK
    p4 = newSessionPattern.match(line)
    if p4:
      startTime = int(p4.group(1))
      isBreak   = p4.group(2)!= None
      if isBreak:
        endTime = startTime;
      else:
        endTime   = addTime(startTime, curDuration)
      #print ('appending %s' % line)
      #used to have this also: 'category' : curCategory,      \
      sessionList.append({'catShort' : curCategoryAbrv,  \
                          'room'     : curRoom,          \
                          'duration' : curDuration,      \
                          'start'    : startTime,        \
                          'end'      : endTime,          \
                          'isBreak'  : isBreak })

      if isBreak:
        breakCount += 1
        catBreakCounts[curCategoryAbrv] += 1
      else:
        nonBreakCount += 1
        catEntryCounts[curCategoryAbrv] += 1
      continue
    
    #A multiple entry line.
    p5 = multEntryPattern.match(line)
    if p5:
      startTime   = int(p5.group(1))
      repeatCount = int(p5.group(2))
      for repeatNum in range(repeatCount):
        sessionList.append({'catShort' : curCategoryAbrv,                  \
                            'room'     : curRoom,                          \
                            'duration' : curDuration,                      \
                            'start'    : startTime,                        \
                            'end'      : addTime(startTime, curDuration),  \
                            'isBreak'  : isBreak })
        startTime = addTime(startTime, curDuration)

    else:
      sys.exit ('Error parsing Sessions file line %d "%s"' % (lineNum,line.strip()))
    #end if

  #end loop
  ioLog.msg ('-- Begin Sessions File Report --')
  ioLog.msg ('Loaded %d sessions %d breaks' % (nonBreakCount, breakCount))

  #Reorder the sessionsList so that if a category is split between multiple
  # rooms, the code can handle them not being placed adjacent in the sessions file.
  catList = []
  for x in range (len(sessionList)):
    if sessionList[x]['catShort'] not in catList:
      catList.append(sessionList[x]['catShort'])

  sessionListSorted = []
  for x in range (len(catList)):
    for y in range (len(sessionList)):
      if sessionList[y]['catShort'] == catList[x]:
        sessionListSorted.append(sessionList[y])

  #Create the sessionIndexes list
  #categoryIndexes =
  #  { 'GI': {'startIdx':0,  'endIdx':34},
  #    'SM': {'startIdx':35, 'endIdx':62},
  #    'CR': {'startIdx':63, 'endIdx':107}, ...
  curCategoryAbrv                  = sessionListSorted[0]['catShort']
  catagoryIndexes[curCategoryAbrv] = {'startIdx' : 0}  #Start the first entry

  for x in range (len(sessionList)):
    if sessionListSorted[x]['catShort'] != curCategoryAbrv:
      catagoryIndexes[curCategoryAbrv]['endIdx'] = x-1
      curCategoryAbrv                            = sessionListSorted[x]['catShort']
      catagoryIndexes[curCategoryAbrv]           = {'startIdx' : x}
  #endIdx of the last catagory was not set, close that one out
  catagoryIndexes[curCategoryAbrv]['endIdx'] = len(sessionListSorted) - 1

  #Print some reports and do a check that sorting didn't mess up
  for k, v in catEntryCounts.items():
    if v > 0:
      ioLog.msg('%s  %3i Sessions %2i Breaks' % (k, v, catBreakCounts[k]))

  for k, v in catagoryIndexes.items():
    if v['endIdx']-v['startIdx']+1 != catEntryCounts[k] + catBreakCounts[k]:
      ioLog.msg('ERROR After sorting sessions, counts for %s do not match' % k)
      ioLog.msg('%s Start Idx %i End Idx %i' % (k, v['startIdx'], v['endIdx']))
  ioLog.msg ('-- End Sessions File Report --')

  return (sessionListSorted, catagoryIndexes)
#end readSessionsFile #########################################################
###############################################################################


###############################################################################
def printSched(schedule, schoolInf, entriesLst, outFolder):
  bySchoolFolder      = os.path.join(outFolder, 'BySchool')
  byRoomFolder        = os.path.join(outFolder, 'ByRoom')
  byRoomCodedFolder   = os.path.join(outFolder, 'ByRoomCoded')
  binFolder           = os.path.join(outFolder, 'bin')

  if os.path.exists(outFolder):
    ioLog.msg('Score %d already printed, skipping' % schedule['score'])
    return  #We've already printed this score
  else:
    ioLog.msg('+++ Printing current best of %d' % schedule['score'])
  os.mkdir(outFolder)
  os.mkdir(bySchoolFolder)
  os.mkdir(byRoomFolder)
  os.mkdir(byRoomCodedFolder)
  os.mkdir(binFolder)

  #Pickled schedule
  f = open(os.path.join(binFolder, 'schedule.bin'),'wb')
  pickle.dump(schedule, f)
  f.close()
  f = open(os.path.join(binFolder, 'schoolInfo.bin'),'wb')
  pickle.dump(schoolInf, f)
  f.close()
  f = open(os.path.join(binFolder, 'entryList.bin'),'wb')
  pickle.dump(entriesLst, f)
  f.close()


  f = open(os.path.join(outFolder, 'masterSched.csv'), 'w', newline='\r\n')
  #f.write ('Score %d\n' % schedule['score'])
  if cats.isGroupContest():
    f.write ('Category,Room/Center,Start,End,School,Code,Entry#,EntryTitle,Performers\n')
  else:
    f.write ('Category,Room/Center,Start,End,School,Code,Entry#,Performer\n')

  for session in schedule['lst']:
    if session['isBreak'] == True:
      if 'entry' in session:
        ioLog.msg ('BREAK FILLED %s %d' % (session['room'], session['start']))

      f.write('%s,\"%s\",%4d,,BREAK,BREAK' % (session['catShort'],      \
                                              session['room'],          \
                                              session['start']))
    else:
      f.write('%s,%s,%4d,%4d' % (session['catShort'],      \
                                 session['room'],          \
                                 session['start'],         \
                                 session['end']))
    if 'entry' in session:
      #Quotes screw up csv
      if cats.isGroupContest():
        sessionStr = '\"' + session['entry']['entryTitle'].replace('\"','').replace('\'','') + '\"'
        f.write(',%s,%s,%d,%s,\"' %                                      \
               (schoolInf[session['entry']['schoolId']]['name'],       \
                schoolInf[session['entry']['schoolId']]['code'],       \
                session['entry']['catSchoolIdx'],                      \
                sessionStr))
      else:
        f.write(',%s,%s,%d,\"' %                                      \
               (schoolInf[session['entry']['schoolId']]['name'],      \
                schoolInf[session['entry']['schoolId']]['code'],      \
                session['entry']['catSchoolIdx']))

      #Print student names
      firstStudentName = True
      for studentName in session['entry']['performers']:
         if not firstStudentName:
            f.write(',')
         f.write('%s' % studentName)
         firstStudentName = False
      f.write('\"\n')
    else:
      f.write(',,\n')   #Time slot is blank
  f.close()

  #############################################################################
  ########################### BySchool ########################################
  #############################################################################
  schoolList = []         # Assemble the list of schools scheduled
  for session in schedule['lst']:
    if 'entry' in session and session['entry']['schoolId'] not in schoolList:
      schoolList.append(session['entry']['schoolId'])
  #end loop

  for school in schoolList:
    schoolName = schoolInf[school]['name']
    schoolFileString = schoolName.replace('\\','_').replace('/','_')  #Get rid of slashes
    f = open(os.path.join(bySchoolFolder, schoolFileString + '.txt'), 'w', newline='\r\n')
                                                  
    sessionList  = []
    longestTitle = 0
    longestRoom  = 0
    for session in schedule['lst']:
      if 'entry' in session and session['entry']['schoolId'] == school:
        #All entries should have a title at this point, even individual
        if 'entryTitle' not in session['entry']:
          errMsg = 'Missing entryTitle in schoolId %i cat %s index %s' % (session['entry']['schoolId'],session['entry']['catShort'],session['entry']['catSchoolIdx'])
          errMsg += '\nVerify this entry exists in students.csv'
          ioLog.msg(errMsg)
          sys.exit(errMsg)
        sessionList.append(session)
        longestTitle = max(longestTitle, len(session['entry']['entryTitle']))
        longestRoom  = max(longestRoom, len(session['room']))
    longestTitle += 1
    longestRoom  += 1

    if cats.isGroupContest():
      f.write('Room                         Start  End   Cat  # EntryTitle' + \
              ' ' * (longestTitle-10) + 'Performers\n')
    else:
      f.write('Room                         Start  End   Cat  # Performer\n')

    sessionsSorted = sorted(sessionList,  key=itemgetter('start'))
    for session in sessionsSorted:
      if cats.isGroupContest():
        grpTitleIndivPerformer = (session['entry']['entryTitle'] + ' '*longestTitle) [:longestTitle]
      else:
        grpTitleIndivPerformer = session['entry']['performers'][0]

      f.write('%17s  %s  %s %3s  %d %s' % \
              (str(session['room'] + ' '*27) [:27],   \
               to12hr(session['start']),              \
               to12hr(session['end']),                \
               session['catShort'],                   \
               session['entry']['catSchoolIdx'],      \
               grpTitleIndivPerformer))

      if cats.isGroupContest():        #Print student names
        firstStudentName = True
        for studentName in session['entry']['performers']:
           if not firstStudentName:
              f.write(',')
           f.write('%s' % studentName)
           firstStudentName = False
      f.write('\n')
    #end session loop
    f.close()
  #end school loop

  #############################################################################
  ########################### ByRoom ##########################################
  #############################################################################
  roomList = []    # Assemble the list of rooms scheduled
  for session in schedule['lst']:
    if 'entry' in session and session['room'] not in roomList:
      roomList.append(session['room'])
  #end loop

  for room in roomList:
    roomFileString = str(room).replace('\\','_').replace('/','_')  #Get rid of slashes
    f = open(os.path.join(byRoomFolder, roomFileString + '.txt'), 'w', newline='\r\n')
    if cats.isGroupContest():
      f.write('Cat  School                     Start  End    Contestant EntryTitle\n')
    else:
      f.write('Cat  School                     Start  End    Contestant Performer\n')

    sessionList  = []
    for session in schedule['lst']:
      if session['room'] == room:
        sessionList.append(session)        
    sessionsSorted = sorted(sessionList,  key=itemgetter('start'))
    
    #Compute performance/contestant numbers
    prevCatShort = ''
    perfMajorNum = 1
    perfMinorNum = 1
    removeList   = []
    for session in sessionsSorted:
      #Breaks and empties still in the list
      if session['isBreak'] == True:
        perfMajorNum += 1
        perfMinorNum = 1
        #sessionsSorted.remove(session)
      elif 'entry' in session:
        if session['entry']['catShort'] != prevCatShort:
          #Check MinorNum != 1 because if a center switches categories it will get
          #both a break and a category switch at that time
          if perfMinorNum != 1:
            perfMajorNum += 1
            perfMinorNum = 1
          prevCatShort = session['entry']['catShort']

        session['contestantNum'] = (str(perfMajorNum) + '-' + str(perfMinorNum)).replace(' ','').ljust(10)
        perfMinorNum += 1

    for session in sessionsSorted:
      if session['isBreak'] or 'entry' not in session:
        continue

      if cats.isGroupContest():
        grpTitleIndivPerformer = session['entry']['entryTitle']
      else:
        grpTitleIndivPerformer = session['entry']['performers'][0]

      schoolName = schoolInf[session['entry']['schoolId']]['name']
      f.write('%s  %25s  %s  %s  %s %s\n' %                  \
               (session['catShort'].ljust(3),                \
                (schoolName + ' '*25) [:25],                 \
                to12hr(session['start']),                    \
                to12hr(session['end']),                      \
                session['contestantNum'],                    \
                grpTitleIndivPerformer))

    f.close()

    f = open(os.path.join(byRoomCodedFolder, roomFileString + '.txt'), 'w', newline='\r\n')
    if cats.isGroupContest():
      f.write('Cat  School    Start  End    Contestant EntryTitle\n')
    else:
      f.write('Cat  School    Start  End    Contestant Performer\n')

    for session in sessionsSorted:
      if session['isBreak'] or 'entry' not in session:
        continue

      if cats.isGroupContest():
        grpTitleIndivPerformer = session['entry']['entryTitle']
      else:
        grpTitleIndivPerformer = session['entry']['performers'][0]

      f.write('%3s  %s       %s  %s  %s %s\n' %                   \
               (session['catShort'].ljust(3),                     \
                schoolInf[session['entry']['schoolId']]['code'],  \
                #(session['entry']['schoolCode'] + ' '*5) [:5],   \
                to12hr(session['start']),                         \
                to12hr(session['end']),                           \
                session['contestantNum'],                         \
                grpTitleIndivPerformer))
    f.close()
  #end room loop

  #Map from school codes to school names
  schoolNameDict = {}
  for schoolId in schoolList:
    schoolNameDict[schoolInf[schoolId]['name']] = schoolInf[schoolId]['code']

  f = open(os.path.join(outFolder, 'schoolCodes.csv'), 'w', newline='\r\n')
  for schoolName in sorted(schoolNameDict.keys()):
    f.write('%s, %s\n' % (schoolNameDict[schoolName], schoolName))
  f.close()
#end printSched ###############################################################
###############################################################################


###############################################################################
def getSitenameList(schoolRegFile):

  try:
     inFile = open (schoolRegFile, 'r', newline='', encoding='utf-8-sig')
     schoolReg = inFile.read()
     inFile.close()
  except Exception as ex:
     print (ex)
     #print (ex.args)
     print (type(ex))
     sys.exit('Error opening schoolReg.csv')

  reader = csv.DictReader(schoolReg.splitlines(), delimiter=',', quotechar='"')

  sites = set()
  currentLine = 1
  try:
    for row in reader:
      siteNameCsv = row['sitename'].rstrip()
      sites.add(siteNameCsv)
      currentLine += 1
  except:
     sys.exit('Unexpected error in schoolReg.csv line %d' % currentLine)
  return sites
#end getSitenameList()  #######################################################
###############################################################################


###############################################################################
def readSchoolWebCsv(fileName, schoolInfo, siteName, codeChar):

  ###############################################################################
  def getRandomSchoolCode(codeChar):
    global usedCodes
    blackList = ['FU', '666', '420']  #Numeric codes start at 101
          
    firstLoopIteration = True
    if codeChar == 0:
      while firstLoopIteration   or         \
            newCode in usedCodes or         \
            newCode in blackList or         \
            int(newCode) <= 100:
        newCode = rnd.choice(string.digits) + rnd.choice(string.digits) + rnd.choice(string.digits)
        firstLoopIteration = False
    else:
      while firstLoopIteration or         \
            newCode in usedCodes or       \
            newCode in blackList or       \
            newCodeMirror in usedCodes:
        newCode = rnd.choice(string.ascii_uppercase) + rnd.choice(string.ascii_uppercase)
        newCodeMirror = newCode[1] + newCode[0]
        firstLoopIteration = False

    usedCodes.append(newCode)
    return newCode
  #end getRandomSchoolCode()  
  ###############################################################################

  try:
     inFile    = open (fileName, 'r', newline='', encoding='utf-8-sig')
     schoolCsv = inFile.read()
     inFile.close()
  except Exception as ex:
     print (ex)
     #print (ex.args)
     print (type(ex))
     sys.exit('Error opening schoolReg.csv')

  reader    = csv.DictReader(schoolCsv.splitlines(), delimiter=',', quotechar='"')

  entriesList = []
  entryIndex  = 0
  schoolCount = 0
  
  #List of fields to retrieve for each entry. Max 3 of any type
#  csvFields =                                                 \
#  [                                                           \
#    ['OneActName'],                                           \
#    ['ReadersName'],                                          \
#    ['ChoralName'],                                           \
#    ['TVNewscastingCallLetters','TVNewscastingCallLetters2'], \
#    ['RadioBroadcastingName1','RadioBroadcastingName2'],      \
#    ['ShortFilmName1', 'ShortFilmName2'],                     \
#    ['MusicalName1','MusicalName2','MusicalName3'],           \
#    ['GroupName1','GroupName2','GroupName3'],                 \
#    ['EnsembleName1','EnsembleName2','EnsembleName3'],        \
#    ['GroupMimeName1','GroupMimeName2','GroupMimeName3'],     \
#    ['SoloMimeName1','SoloMimeName2','SoloMimeName3']         \
#  ]
  currentLine = 1
  try:
    for row in reader:
      schoolNameCsv  = row['SchoolName'].rstrip()
      siteNameCsv    = row['sitename'].rstrip()
      schoolIdCsvRaw = row['SchoolID'].rstrip()
      if not str.isdigit(schoolIdCsvRaw):
        #If we have a multi-year schoolReg dump, the early years don't have schoolIDs. Skip them.
        continue
      #TODO don't process previous year's entries
      schoolIdCsv   = int(schoolIdCsvRaw)
      regIdCsv      = int(row['RegistrationID'])
      #print(schoolCsv + ' RegId:%i' % regIdCsv)

      #Check that this school is registered for the contest we are running, or ALL has been specified
      if siteNameCsv not in siteName:
        #print ('Skipping %s',  schoolNameCsv)
        continue      

      schoolCount += 1
      
      #Validate that this school is in the schoolInfo dict
      if schoolIdCsv not in schoolInfo:
        print('Schools Export/School Registration missing on School ID %i %s' % (schoolIdCsv,schoolNameCsv))
        ioLog.msg('Schools Export/School Registration missing on School ID %i %s' % (schoolIdCsv,schoolNameCsv))
      elif schoolNameCsv != schoolInfo[schoolIdCsv]['name']:
        print('Schools Export/School Registration name mismatch on ID %i "%s" "%s"' % (schoolIdCsv,schoolNameCsv,schoolInfo[schoolIdCsv]['name']))
        ioLog.msg('Schools Export/School Registration name mismatch on ID %i "%s" "%s"' % (schoolIdCsv,schoolNameCsv,schoolInfo[schoolIdCsv]['name']))
      else:
        if not schoolInfo[schoolIdCsv]['inContest']:
          schoolInfo[schoolIdCsv]['inContest'] = True
          schoolInfo[schoolIdCsv]['code']      = getRandomSchoolCode(codeChar)

      #Writing a number over the yes/no values seems to wipe out the whole
      # row object.  So keep a seperate copy to act on here
      catCount = {}
      for performanceCat in cats.longList():
        if row[performanceCat].isdigit():
          countFromCsv = row[performanceCat]
        else:
          countFromCsv = 0
          print('Warning: Not a number in schoolReg.csv RegID:%d %s %s' % (regIdCsv, schoolNameCsv, performanceCat))
        catCount[performanceCat] = int(countFromCsv)

      if cats.isGroupContest():
        #####################################################
        ############        GROUP CONTEST          ##########
        #####################################################
        #INDV fields = cats.schoolRegMap()
        for perfCat,csvNameList in cats.schoolRegMap().items():
          #print('  ' + perfCat + ' ' + str(catCount[perfCat]))
          for entryNum in range(catCount[perfCat]):
            csvColName = csvNameList[entryNum]
            #print('    ' + csvColName + ' ' + row[csvColName])
            newE = {'schoolId'      : schoolIdCsv,                     \
                    'regId'         : regIdCsv,                        \
                    'catShort'      : cats.longToShort(perfCat),       \
                    'category'      : perfCat,                         \
                    'catSchoolIdx'  : entryNum+1,                      \
                    'index'         : entryIndex,                      \
                    'inContest'     : False,                           \
                    'entryTitle'    : row[csvColName],                 \
                    'performers'    : [],                              \
                    'earliestStart' : 100,                             \
                    'latestEnd'     : 2300}

            #print('E SchoolId %d RegId %d' % (schoolIdCsv, regIdCsv))
            entriesList.append(newE)
            #Adding a unique index makes it easy to compare entries for equality,
            #instead of doing a bunch of string and list comparisons.
            entryIndex += 1
      else:
        #####################################################
        ############        INDIVIDUAL CONTEST     ##########
        #####################################################
        for perfCat in cats.longList():
          for entryNum in range(catCount[perfCat]):
            #print('    ' + csvColName) ;
            newE = {'schoolId'      : schoolIdCsv,                     \
                    'regId'         : regIdCsv,                        \
                    'catShort'      : cats.longToShort(perfCat),       \
                    'catSchoolIdx'  : entryNum+1,                      \
                    'index'         : entryIndex,                      \
                    'inContest'     : False,                           \
                    'performers'    : [],                              \
                    'earliestStart' : 100,                             \
                    'latestEnd'     : 2300,                            \
                    'studentDataFilled' : False}

            #StudentDataFilled is used by the student data reader to show that
            # entry's student and entry name have been filled in.  Only used
            # for individual contest logic
            entriesList.append(newE)
            entryIndex += 1

      currentLine += 1
  except Exception as ex:
     print (ex)
     print (ex.args)
     print (type(ex))
     sys.exit('Unexpected error in schoolReg.csv line %d' % currentLine)

  if not ioLog is None:
    ioLog.msg ('Loaded %d schools, %d entries' % (schoolCount,entryIndex))
  print ('Loaded %d schools, %d entries' % (schoolCount,entryIndex))
  return entriesList
#end readSchoolWebCsv() #######################################################
###############################################################################


###############################################################################
def readStudentWebCsv(entriesList, fileName):

  try:
    inFile = open (fileName, 'r', newline='', encoding='utf-8-sig')
    studentCsv = inFile.read()
    inFile.close()
  except Exception as ex:
     print (ex)
     #print (ex.args)
     print (type(ex))
     sys.exit('Error opening students.csv')

  reader = csv.DictReader(studentCsv.splitlines(), delimiter=',', quotechar='"')
 
  #Reverse lookup dict from the "Category" column of the student 
  # data to the entry category and index(1,2,3)
#  csvFields =                                     \
#  {                                               \
#    'oneact'               : ("OA",1),            \
#    'readerstheatre'       : ("RT",1),            \
#    'choral reading'       : ("CR",1),            \
#    'tvnewscasting1'       : ("TV",1),            \
#    'tvnewscasting2'       : ("TV",2),            \
#    'radiobroadcasting1'   : ("RB",1),            \
#    'radiobroadcasting2'   : ("RB",2),            \
#    'shortfilm1'           : ("SF",1),            \
#    'shortfilm2'           : ("SF",2),            \
#    ...
#  }
  csvFields = cats.studentRegFields()

  currentLine = 1
  try:
    for row in reader:
      if row['RegistrationID'] == '':
        continue
        
      csvRegId    = int(row['RegistrationID'])
      csvCategory = row['Category']

      if cats.isGroupContest():
        #####################################################
        ############        GROUP CONTEST          ##########
        #####################################################
        for entry in entriesList:
          if entry['regId'] == csvRegId and                     \
             csvFields[csvCategory][0] == entry['catShort'] and \
             csvFields[csvCategory][1] == entry['catSchoolIdx']:

            #This student row matches by regId (school), category and index(1-3)
            entry['performers'].append(row['Name'])
            #print('Placed ', row['Name'])
            break
        #else:
          #print('No entry match for student ' + row['Name'] + ' ' +row['Category'])

      else:
        #####################################################
        ############        INDIVIDUAL CONTEST     ##########
        #####################################################
         for entry in entriesList:
           if entry['regId'] == csvRegId and                     \
              not entry['studentDataFilled'] and                 \
              csvCategory.lower() == cats.shortToLong(entry['catShort']).lower():

              #This student row matches by regId (school)
               entry['performers'].append(row['Name'])
               entry['entryTitle'] = row['Title']
               #Mark this one as filled.  Useful for INDV only
               entry['studentDataFilled'] = True
               #print('Placed ', row['Name'])
               break
       #else:
        #print('No entry match for student ' + row['Name'] + ' ' +row['Category'])
    currentLine += 1
  except Exception as e:
    print (e)
    #print (e.args)
    print (type(e))
    sys.exit('Unexpected error in students.csv line %d' % currentLine)
#end readStudentWebCsv() ######################################################
###############################################################################

def readSchoolsExport(fileName):

  try:
    inFile    = open (fileName, 'r', newline='', encoding='utf-8-sig')
    schoolReg = inFile.read()
    inFile.close()
  except Exception as e:
    print (e)
    #print (e.args)
    print (type(e))
    sys.exit('Unexpected error reading schools export')

  reader    = csv.DictReader(schoolReg.splitlines(), delimiter=',', quotechar='"')

  schoolInfo = {}

  for row in reader:
    csvRegId      = int(row['SchoolID'])

    schoolDict               = {'name' : row['SchoolName'].rstrip()}
    schoolDict['inContest']  = False
    schoolDict['code']       = '$$'
    schoolDict['address1']   = row['Address1']
    schoolDict['city']       = row['City']
    schoolDict['state']      = row['State']
    schoolDict['zipCode']    = row['ZipCode']
    
    schoolInfo[csvRegId] = schoolDict

  return schoolInfo
#end readSchoolsExport ########################################################
###############################################################################

def readRestrSheet(entriesList, fileName):

  inFile = open (fileName, 'r', newline='', encoding='utf-8-sig')
  reader = csv.DictReader(inFile, delimiter=',', quotechar='"')
  catCounts = cats.countDict()
  lineNum   = 1

  try:
    for row in reader:
      regIdCsvRaw        = row['regId']
      schoolIdCsvRaw     = row['schoolId']
      catIdxCsvRaw       = row['catIdx']
      if not str.isdigit(regIdCsvRaw)     or \
         not str.isdigit(schoolIdCsvRaw)  or \
         not str.isdigit(catIdxCsvRaw):
        sys.exit('RestrSheet.csv Error at RegId:%s SchoolId:%s CatIdx:%s' % (regIdCsvRaw, schoolIdCsvRaw, catIdxCsvRaw))

      regIdCsv           = int(regIdCsvRaw)
      schoolIdCsv        = int(schoolIdCsvRaw)
      catIdxCsv          = int(catIdxCsvRaw)
      catShortCsv        = row['catShort'].rstrip().upper()
      earliestStartCsv   = row['earliestStart'].rstrip()
      latestEndCsv       = row['latestEnd'].rstrip()
      inContestCsv       = row['inContest'].rstrip()

      debug = schoolIdCsv == 999999999
      if debug:
        print ('Searching %d %s %d' % (schoolIdCsv, catShortCsv, catIdxCsv))

      for entry in entriesList:
        if debug and entry['regId'] == regIdCsv:
          print ('    Try %d %s %d' % (entry['schoolId'], entry['catShort'], entry['catSchoolIdx']))
        if entry['regId']        == regIdCsv    and          \
           entry['schoolId']     == schoolIdCsv and          \
           entry['catShort']     == catShortCsv and          \
           entry['catSchoolIdx'] == catIdxCsv:
         
          if earliestStartCsv and earliestStartCsv.isdigit():
            entry['earliestStart'] = int(earliestStartCsv)
          if latestEndCsv  and latestEndCsv.isdigit():
            entry['latestEnd'] = int(latestEndCsv)
          if inContestCsv :
            entry['inContest']      = True
            catCounts[catShortCsv] += 1
          if debug:
            print ('Entry: %d %d *%s*' % (entry['regId'],entry['catSchoolIdx'],inContestCsv))
          break
      else:
         if inContestCsv:
           warnMsg = 'WARNING: School %d %s %d in restrSheet marked in contest but no matching entry found' % \
                       (schoolIdCsv, catShortCsv, catIdxCsv)
           print(warnMsg)
           ioLog.msg (warnMsg)
      lineNum += 1
  except BaseException as e:
    inFile.close()
    print (e)
    #print (e.args)
    print (type(e))
    sys.exit('Error parsing RestrSheet.csv at line %d\n' % lineNum + str(e))

  #Now delete the entries not in this contest
  newEntList     = []
  for entry in entriesList:
    if entry['inContest']:
      newEntList.append(entry)
      #if entry['catShort'] == 'SF':
        #print ('Copy %d  %d' % (entry['regId'],entry['catSchoolIdx']))
      #print ('Copy: %d %d' % (entry['regId'],entry['catSchoolIdx']))

  ioLog.msg ('%d in contest after reading RestrSheet' % len(newEntList))
  ioLog.msg ('Contest entries per category:')
  for k,v in catCounts.items():
    ioLog.msg ('%s : %d' % (k,v))
  print ('%d in contest' % len(newEntList))
  inFile.close()
  return newEntList
  
##end readRestrSheet   ########################################################
###############################################################################
