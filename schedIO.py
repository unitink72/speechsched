import csv, re, sys
import math
import os
import pickle
import random
import string
from operator import itemgetter

catLongList = ['One Act Play','Reader\'s Theatre','Choral Reading','TV News',  \
               'Radio Broadcasting','Short Film','Musical Theatre',            \
               'Group Improv','Ensemble Acting','Group Mime','Solo Mime']

catList = ["OneActPlay","ReadersTheatre", "ChoralReading", "TVNewscasting", \
           "RadioBroadcasting", "ShortFilm", "MusicalTheatre",              \
           "GroupImprovisation", "EnsembleActing", "GroupMime", "SoloMime"]
  
catShortList = ['OA','RT','CR','TV', 'RB','SF','MT','GI', 'EA', 'GM', 'SM']

catToShortMap     = dict(zip(catList,catShortList))
shortToCatMap     = dict(zip(catShortList, catList))
shortToLongCatMap = dict(zip(catShortList, catLongList))

ioLog = None

#Globals used for creating school codes
rnd       = random.SystemRandom()
usedCodes = []

def setLogger(logger):
  global ioLog
  ioLog = logger
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
  sessionsFile = open (fileName, 'r')

  sessionList     = []
  catagoryIndexes = {}

  curCategory      = ''   #cur is short for "current'
  curCategoryAbrv  = ''   # Two-character category abbreviation
  curRoom          = ''
  curDuration      = 0
  nonBreakCount    = 0
  breakCount       = 0

  newCategoryPattern = re.compile("^([\w\s]+)\s+(\w{2})\s+(\d+)",  re.IGNORECASE)
  newRoomPattern     = re.compile("^ROOM (.+)",        re.IGNORECASE)
  newSessionPattern  = re.compile("^(\d+)\s*(BREAK)?", re.IGNORECASE)
  skipLinePattern    = re.compile("(^$)|(^##)")
  multEntryPattern   = re.compile("(^\d{3,4})\s?\*\s?(\d+)")

  catBreakCounts = dict(zip(catShortList,[0] * len(catShortList)))
  catEntryCounts = dict(zip(catShortList,[0] * len(catShortList)))

  while 1:
    line = sessionsFile.readline()
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

      if not curCategoryAbrv in catShortList:
      # Validate the catShort.  Long cat name unused, it could be removed from sessions file
        sys.exit ('Sessions file unknown category %s', curCategoryAbrv)

      #Grab the next line in the file, should specify a Room
      line = sessionsFile.readline()
      p3 = newRoomPattern.match(line)

      if p3:
        curRoom = p3.group(1).strip()
        #print ('Reading %s %s %d' % (curCategory, curRoom, curDuration))
      else:
        sys.exit ("No room specified after %s in Sessions file" % curCategory)
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
      sys.exit ('Error parsing Sessions file line "%s"' % line.strip())
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

def printSched(schedule, schoolInf, outFolder):
  bySchoolFolder      = os.path.join(outFolder, 'BySchool')
  byRoomFolder        = os.path.join(outFolder, 'ByRoom')
  byRoomCodedFolder   = os.path.join(outFolder, 'ByRoomCoded')
  
  if os.path.exists(outFolder):
    ioLog.msg('Score %d already printed, skipping' % schedule['score'])
    return  #We've already printed this score
  else:
    ioLog.msg('+++ Printing current best of %d' % schedule['score'])
  os.mkdir(outFolder)
  os.mkdir(bySchoolFolder)
  os.mkdir(byRoomFolder)
  os.mkdir(byRoomCodedFolder)

  #Pickled schedule
  f = open(os.path.join(outFolder, 'schedule.bin'),'wb')
  pickle.dump(schedule, f)

  f = open(os.path.join(outFolder, 'masterSched.csv'), 'w', newline='\r\n')
  #f.write ('Score %d\n' % schedule['score'])
  f.write ('Category,Room/Center,Start,End,School,Code,Entry#,EntryTitle\n')
  for session in schedule['lst']:
    if session['isBreak'] == True:
      if 'entry' in session:
        ioLog.msg ('BREAK FILLED %s %d' % (session['room'], session['start']))

      f.write('%s,\"%s\",%4d,,BREAK' % (session['catShort'],      \
                                        session['room'],          \
                                        session['start']))
    else:
      f.write('%s,%s,%4d,%4d' % (session['catShort'],      \
                                 session['room'],          \
                                 session['start'],         \
                                 session['end']))
    if 'entry' in session:
      #Quotes screw up csv
      sessionStr = session['entry']['entryTitle'].replace('\"','').replace('\'','')
      f.write(',%s,%s,%d,%s\n' %                                        \
             (schoolInf[session['entry']['schoolId']]['name'],       \
              schoolInf[session['entry']['schoolId']]['code'],       \
              session['entry']['catSchoolIdx'],                      \
              sessionStr))
    else:
      f.write(',,\n')   #Time slot is blank
  f.close()

  # Assemble the list of schools scheduled to create the BySchool reports
  schoolList = []
  for session in schedule['lst']:
    if 'entry' in session and session['entry']['schoolId'] not in schoolList:
      schoolList.append(session['entry']['schoolId'])
  #end loop

  for school in schoolList:
    schoolName = schoolInf[school]['name']
    schoolFileString = schoolName.replace('\\','_').replace('/','_')  #Get rid of slashes
    f = open(os.path.join(bySchoolFolder, schoolFileString + '.txt'), 'w', newline='\r\n')
    f.write('Room                         Start  End   Cat # EntryTitle\n')
    sessionList = []
    for session in schedule['lst']:
      if 'entry' in session and session['entry']['schoolId'] == school:
        sessionList.append(session)
        
    sessionsSorted = sorted(sessionList,  key=itemgetter('start'))
    for session in sessionsSorted:
      f.write('%17s  %s  %s %s  %d %s\n' % \
              (str(session['room'] + ' '*27) [:27],   \
               to12hr(session['start']),              \
               to12hr(session['end']),                \
               session['catShort'],                   \
               session['entry']['catSchoolIdx'],      \
               session['entry']['entryTitle']))
    #end session loop
    f.close()
  #end school loop

  # Assemble the list of rooms scheduled to create the ByRoom reports
  roomList = []
  for session in schedule['lst']:
    if 'entry' in session and session['room'] not in roomList:
      roomList.append(session['room'])
  #end loop

  for room in roomList:
    roomFileString = str(room).replace('\\','_').replace('/','_')  #Get rid of slashes
    f = open(os.path.join(byRoomFolder, roomFileString + '.txt'), 'w', newline='\r\n')
    f.write('Cat  School                     Start  End    EntryTitle\n')
    sessionList = []
    for session in schedule['lst']:
      if 'entry' in session and session['room'] == room:
        sessionList.append(session)        
    sessionsSorted = sorted(sessionList,  key=itemgetter('start'))
    
    for session in sessionsSorted:
      schoolName = schoolInf[session['entry']['schoolId']]['name']
      f.write('%s   %25s  %s  %s  %s\n' %                    \
               (session['catShort'],                         \
                (schoolName + ' '*25) [:25],                 \
                to12hr(session['start']),                    \
                to12hr(session['end']),                      \
                session['entry']['entryTitle']))
    f.close()
    f = open(os.path.join(byRoomCodedFolder, roomFileString + '.txt'), 'w', newline='\r\n')
    f.write('Cat  School   Start  End   EntryTitle\n')
    for session in sessionsSorted:
      f.write('%s   %s       %s  %s %s\n' % 
               (session['catShort'],                              \
                schoolInf[session['entry']['schoolId']]['code'],  \
                #(session['entry']['schoolCode'] + ' '*5) [:5],   \
                to12hr(session['start']),                         \
                to12hr(session['end']),                           \
                session['entry']['entryTitle']))
    f.close()
  #end room loop
  
  #Map from school codes to school names
  f = open(os.path.join(outFolder, 'schoolCodes.txt'), 'w', newline='\r\n')
  for school in schoolList:
    f.write('%s  %s\n' % (schoolInf[school]['code'], schoolInf[school]['name']))
  f.close()
#end printSched ###############################################################
###############################################################################

def readSchoolWebCsv(fileName, schoolInfo, siteName):
  inFile = open (fileName, 'r', newline='')

  entriesList = []
  entryIndex  = 0
  schoolCount = 0

  reader = csv.DictReader(inFile, delimiter=',', quotechar='"')

  #List of fields to retrieve for each entry. Max 3 of any type
#  fields = {                                                                    \
#    'OneActPlay'        : ['OneActName'],                                       \
#    'ReadersTheatre'    : ['ReadersName'],                                      \
#    'ChoralReading'     : ['ChoralName'],                                       \
#    'TVNewscasting'     : ['TVNewscastingCallLetters','TVNewscastingCallLetters2'],  \
#    'RadioBroadcasting' : ['RadioBroadcastingName1','RadioBroadcastingName2'],  \
#    'ShortFilm'         : ['ShortFilmName1', 'ShortFilmName2'],                 \
#    'MusicalTheatre'    : ['MusicalName1','MusicalName2','MusicalName3'],       \
#    'GroupImprovisation': ['GroupName1','GroupName2','GroupName3'],             \
#    'EnsembleActing'    : ['EnsembleName1','EnsembleName2','EnsembleName3'],    \
#    'GroupMime'         : ['GroupMimeName1','GroupMimeName2','GroupMimeName3'], \
#    'SoloMime'          : ['SoloMimeName1','SoloMimeName2','SoloMimeName3']     \
#  }
  csvFields =                                                 \
  [                                                           \
    ['OneActName'],                                           \
    ['ReadersName'],                                          \
    ['ChoralName'],                                           \
    ['TVNewscastingCallLetters','TVNewscastingCallLetters2'], \
    ['RadioBroadcastingName1','RadioBroadcastingName2'],      \
    ['ShortFilmName1', 'ShortFilmName2'],                     \
    ['MusicalName1','MusicalName2','MusicalName3'],           \
    ['GroupName1','GroupName2','GroupName3'],                 \
    ['EnsembleName1','EnsembleName2','EnsembleName3'],        \
    ['GroupMimeName1','GroupMimeName2','GroupMimeName3'],     \
    ['SoloMimeName1','SoloMimeName2','SoloMimeName3']         \
  ]

  fields = dict(zip(catList,csvFields))

  for row in reader:
    schoolNameCsv = row['SchoolName'].rstrip()
    siteNameCsv   = row['sitename'].rstrip()
    schoolIdCsv   = int(row['SchoolID'])
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

        firstLoopIteration = True
        while firstLoopIteration or         \
              newCode in usedCodes or       \
              newCodeMirror in usedCodes:
          newCode = rnd.choice(string.ascii_uppercase) + rnd.choice(string.ascii_uppercase)
          newCodeMirror = newCode[1] + newCode[0]
          firstLoopIteration = False
        

        usedCodes.append(newCode)
        schoolInfo[schoolIdCsv]['code'] = newCode

    #Writing a number over the yes/no values seems to wipe out the whole
    # row object.  So keep a seperate copy to act on here
    catCount = {}
    for performanceCat in catList:   #fields.keys():
      if row[performanceCat].isdigit():
        countFromCsv = row[performanceCat]
      else:
        countFromCsv = 0
      catCount[performanceCat] = int(countFromCsv)

    for perfCat,csvNameList in fields.items():
      #print('  ' + perfCat + ' ' + str(catCount[perfCat]))
      for entryNum in range(catCount[perfCat]):
        csvColName = csvNameList[entryNum]
        #print('    ' + csvColName) ;
        newE = {'schoolId'      : schoolIdCsv,                     \
                'regId'         : regIdCsv,                        \
                'catShort'      : catToShortMap[perfCat],          \
                #'category'      : perfCat,                        \
                'catSchoolIdx'  : entryNum+1,                      \
                'index'         : entryIndex,                      \
                'inContest'     : True,                            \
                'entryTitle'    : row[csvColName],                 \
                'performers'    : [],                              \
                'earliestStart' : 100,                             \
                'latestEnd'     : 2300}
        entriesList.append(newE)
        #Adding a unique index makes it easy to compare entries for equality,
        #instead of doing a bunch of string and list comparisons.
        entryIndex += 1

  if not ioLog is None:
    ioLog.msg ('Loaded %d schools, %d entries' % (schoolCount,entryIndex))
  print ('Loaded %d schools, %d entries' % (schoolCount,entryIndex))
  return entriesList
#end readSchoolWebCsv() #######################################################
###############################################################################

def readStudentWebCsv(entriesList, fileName):

  inFile = open (fileName, 'r', newline='')
  reader = csv.DictReader(inFile, delimiter=',', quotechar='"')
 
  #Reverse lookup dict from the "Category" column of the student 
  # data to the entry category and index(1,2,3)
#  csvFields =                                                 \
#  {                                                           \
#    'oneact'               : ("OneActPlay",1),                \
#    'readerstheatre'       : ("ReadersTheatre",1),            \
#    'choral reading'       : ("ChoralReading",1),             \
#    'tvnewscasting1'       : ("TVNewscasting",1),             \
#    'tvnewscasting2'       : ("TVNewscasting",2),             \
#    'radiobroadcasting1'   : ("RadioBroadcasting",1),         \
#    'radiobroadcasting2'   : ("RadioBroadcasting",2),         \
#    'shortfilm1'           : ("ShortFilm",1),                 \
#    'shortfilm2'           : ("ShortFilm",2),                 \
#    'musicaltheatre1'      : ("MusicalTheatre",1),            \
#    'musicaltheatre2'      : ("MusicalTheatre",2),            \
#    'musicaltheatre3'      : ("MusicalTheatre",3),            \
#    'group1'               : ("GroupImprovisation",1),        \
#    'group2'               : ("GroupImprovisation",2),        \
#    'group3'               : ("GroupImprovisation",3),        \
#    'ensemble1'            : ("EnsembleActing",1),            \
#    'ensemble2'            : ("EnsembleActing",2),            \
#    'ensemble3'            : ("EnsembleActing",3),            \
#    'groupmime1'           : ("GroupMime",1),                 \
#    'groupmime2'           : ("GroupMime",2),                 \
#    'groupmime3'           : ("GroupMime",3),                 \
#    'solomime1'            : ("SoloMime",1),                  \
#    'solomime2'            : ("SoloMime",2),                  \
#    'solomime3'            : ("SoloMime",3),                  \
#  }
  csvFields =                                     \
  {                                               \
    'oneact'               : ("OA",1),            \
    'readerstheatre'       : ("RT",1),            \
    'choral reading'       : ("CR",1),            \
    'tvnewscasting1'       : ("TV",1),            \
    'tvnewscasting2'       : ("TV",2),            \
    'radiobroadcasting1'   : ("RB",1),            \
    'radiobroadcasting2'   : ("RB",2),            \
    'shortfilm1'           : ("SF",1),            \
    'shortfilm2'           : ("SF",2),            \
    'musicaltheatre1'      : ("MT",1),            \
    'musicaltheatre2'      : ("MT",2),            \
    'musicaltheatre3'      : ("MT",3),            \
    'group1'               : ("GI",1),            \
    'group2'               : ("GI",2),            \
    'group3'               : ("GI",3),            \
    'ensemble1'            : ("EA",1),            \
    'ensemble2'            : ("EA",2),            \
    'ensemble3'            : ("EA",3),            \
    'groupmime1'           : ("GM",1),            \
    'groupmime2'           : ("GM",2),            \
    'groupmime3'           : ("GM",3),            \
    'solomime1'            : ("SM",1),            \
    'solomime2'            : ("SM",2),            \
    'solomime3'            : ("SM",3),            \
  }

  for row in reader:
    if row['RegistrationID'] == '':
      continue
      
    csvRegId    = int(row['RegistrationID'])
    csvCategory = row['Category']

    for entry in entriesList:
      if entry['regId'] == csvRegId and                     \
         csvFields[csvCategory][0] == entry['catShort'] and \
         csvFields[csvCategory][1] == entry['catSchoolIdx']:
         
         #This student row matches by regId (school),
         # category and index(1-3)
         entry['performers'].append(row['Name'])
         #print('Placed ', row['Name'])
         break
     #else:
      #print('No entry match for student ' + row['Name'] + ' ' +row['Category'])
#end readStudentWebCsv() ######################################################
###############################################################################

def readSchoolsExport(fileName):

  inFile    = open (fileName, 'r', newline='')
  reader    = csv.DictReader(inFile, delimiter=',', quotechar='"')

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

  inFile = open (fileName, 'r', newline='')
  reader = csv.DictReader(inFile, delimiter=',', quotechar='"')
  catCounts = dict(zip(catShortList, [0]*len(catShortList)))
  
  for row in reader:
    regIdCsv           = int(row['regId'])
    schoolIdCsv        = int(row['schoolId'])
    catIdxCsv          = int(row['catIdx'])
    catShortCsv        = row['catShort'].rstrip()
    earliestStartCsv   = row['earliestStart'].rstrip()
    latestEndCsv       = row['latestEnd'].rstrip()
    inContestCsv       = row['inContest'].rstrip()

    for entry in entriesList:
      if entry['regId']        == regIdCsv    and          \
         entry['schoolId']     == schoolIdCsv and          \
         entry['catShort']     == catShortCsv and          \
         entry['catSchoolIdx'] == catIdxCsv:
         
        if earliestStartCsv and earliestStartCsv.isdigit():
          entry['earliestStart'] = int(earliestStartCsv)
        if latestEndCsv  and latestEndCsv.isdigit():
          entry['latestEnd'] = int(latestEndCsv)
        if not inContestCsv :
          entry['inContest'] = False
        else:
          catCounts[catShortCsv] += 1
          #print ('Entry: %d %d *%s*' % (entry['regId'],entry['catSchoolIdx'],inContestCsv))


  #Now delete the entries not in this contest
  newEntList     = []
  for entry in entriesList:
    if entry['inContest']:
      newEntList.append(entry)
      #print ('Copy: %d %d' % (entry['regId'],entry['catSchoolIdx']))

  ioLog.msg ('%d in contest after reading RestrSheet' % len(newEntList))
  ioLog.msg ('Contest entries per category:')
  for k,v in catCounts.items():
    ioLog.msg ('%s : %d' % (k,v))
  print ('%d in contest' % len(newEntList))
  return newEntList
  
##end readRestrSheet   ########################################################
###############################################################################
