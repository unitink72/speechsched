import math
import time


#Dict of schools' data
    #{'Stalin Communist Prep School': {'driveTime': 45,
    #                                  'address': '12234 blah street',
    #                                  'entryCount': 6,
    #                                  'latestSession': 1030,
    #                                  'earliestSession':820},
    #'Wallaby West':                  {'driveTime': 115,
    #                                  'address': '973 whoey street',
    #                                  'entryCount': 6,
    #                                  'latestSession': 1540,
    #                                  'earliestSession': 920,
    #                                  'earliestStartRstr': 1030},
    #'Dubuque Hempstead':             {'driveTime': 70,
    #                                  'address': '402 neener street',
    #                                  'entryCount': 9,
    #                                  'latestSession': 1660,
    #                                  'earliestSession': 830,
    #                                  'latestEndRstr': 1500}
    #}
localSchoolInfo = {}
schConfig       = {}

fitLog          = None

#Keep a hash of how many centers each category has.  Can compute at startup, used
#by check #5
#{'EA': 2, 'GM': 1, 'OA':2}
centerCount = {}

#Compute the longest school name. Used to format reports in nice columns
longSchoolNameLength = 0

def setLogger(logger):
  global fitLog
  fitLog = logger

def fitnessInitialize(schoolInfo, entryList, configFromFile):
  global longSchoolNameLength

  #Configuration settings read from file.  For some reason have to brute-force copy this.
  for key,value in configFromFile.items():
  	schConfig[key] = value

  for k,v in schoolInfo.items():
    if v['inContest']:
      localSchoolInfo[k] = {'driveTime'       : v['driveTime'], \
                            'earliestSession' : 2400,              \
                            'latestSession'   : 0,                 \
                            'entryCount'      : 0,                 \
                            'name'            : v['name']}
      longSchoolNameLength = max(longSchoolNameLength, len(v['name']))

      if 'earliestStartRstr' in v:
        localSchoolInfo[k]['earliestStartRstr'] = v['earliestStartRstr']
      if 'latestEndRstr' in v:
        localSchoolInfo[k]['latestEndRstr'] = v['latestEndRstr']
  #end loop
  
  #Count how many entries each school has
  for entry in entryList:
    localSchoolInfo[entry['schoolId']]['entryCount'] += 1
  #end loop
#end fitnessInitialize

def centerCountInitialize (sched):
  #Need to get a count of centers per category for check #5.  Could do this in
  # fitnessInitialize() but would have to send in more data to the child workers.
  # Instead do this just once the first time fitnessTest is called.

  catCenters = {}
  #{'SM': ['Choir 104'],
  # 'GA': ['Band 202', 'Lit 404'],
  # 'MT': ['Lit 339', 'Little Theatre'], ...
  curCategory = ''
  curRoom     = ''

  for x in sched:
    if (x['catShort'] != curCategory or \
        x['room']     != curRoom):

      curCategory         = x['catShort']
      curRoom             = x['room']
      if curCategory in catCenters:
        catCenters [curCategory].append(curRoom)
      else:
        catCenters [curCategory] = [curRoom]
  #end loop

  #Dont need to know each center for a category, just the count.
  global centerCount
  for cat,rooms in catCenters.items():
    centerCount[cat] = len(rooms)
    print('CAT COUNT %s %d' % (cat, len(rooms)))

#end centerCountInitialize

def subtractTime(startTime, endTime):
  #Returns answer in minutes
  startHours   = math.floor(startTime / 100)
  startMinutes = startTime % 100
  endHours     = math.floor(endTime / 100)
  endMinutes   = endTime % 100
  answer = 0

  if endMinutes > startMinutes:
    answer += endMinutes - startMinutes;
    answer += (endHours - startHours) * 60
  else:
    answer += abs(startMinutes - (endMinutes+60))
    answer += (endHours - startHours - 1) * 60
  #end if;
  return answer
#end subtractTime

def fitnessTestForList (scheduleList):
  scoreList = []

  for sched in scheduleList:
    if sched == None:
      fitLog.msg ("Got none sched")
    scoreList.append(fitnessTest(sched, False))
  #end loop
  return scoreList
#end fitnessTestForList

fitnessTimes = []  #Used for measuring computation time spent in the fitness function

def fitnessTestNoReport(scheduleList):
  fitnessTest(scheduleList, False)
# end fitnessTestNoReport

centerCountInitHasRun = 0

def fitnessTest (schedl, saveReport=False, fileName=''):
  #Test each schedule for the following
  #1. Long distance schools minimize the time competing
  #2. Long distance schools don't start in the earliest timeslots
  #3. 1 school not scheduled twice in the same timeslot.  May be acceptable for larger schools.
  #4. 1 school with multiple entries for a category are not scheduled in the same room/
  #     time block.  Need to have different judges.
  #5  Same school cannot be entered twice in the same center.  Used for state contests
  #6. Obey time constraints given by schools and students when their earliest/latest performances are.
  #7. Students should have 1 half hour between performances.
  start = time.time()
  global longSchoolNameLength

  #Reset the schoolInfo array
  for value in localSchoolInfo.values():
    value['earliestSession'] = 2400
    value['latestSession']   = 0
  #schoolInfo = copy.deepcopy(schoolInfoMaster)

  global centerCountInitHasRun
  if not centerCountInitHasRun:
    centerCountInitHasRun = 1
    centerCountInitialize(schedl['lst'])

  reportText = ''
  test1Score = 0
  test2Score = 0
  test3Score = 0
  test4Score = 0
  test5Score = 0
  test6Score = 0
  test7Score = 0

  #Find the earlies and latest entries for each school
  for session in schedl['lst']:
    if 'entry' in session:
      #Only processes sessions that are assigned an entry
      if session['start'] < localSchoolInfo[session['entry']['schoolId']]['earliestSession']:
        localSchoolInfo[session['entry']['schoolId']]['earliestSession'] = session['start']
      #end if
      if session['end'] > localSchoolInfo[session['entry']['schoolId']]['latestSession']:
        localSchoolInfo[session['entry']['schoolId']]['latestSession'] = session['end']
      #end if
    #end if
  #end loop

  #1
  #Check the first and last performance time for long distance schools.  If
  #they are too long, dock the points.  Right now "too long" is if the schedule
  #exceeds a rate of 30 minutes per performance on average.  Could be made smarter
  #by checking the category of each performance and using those times instead.
  for school in localSchoolInfo.keys():
    if localSchoolInfo[school]['driveTime'] > schConfig['MIN_DRIVING_TIME_PERF_SPAN_CHECK']:
      performanceSpan = subtractTime(localSchoolInfo[school]['earliestSession'], \
                                     localSchoolInfo[school]['latestSession'])
      performanceRate = performanceSpan / localSchoolInfo[school]['entryCount']
      if performanceRate > 30:
        test1Score += schConfig['LONG_PERFORMANCE_SPAN_PENALTY']
        if saveReport:
          bufferLen = max(0, 30 - len(localSchoolInfo[school]['name']))
          reportText += '1 Long Duration      %4d %s Avg rate %3.1f mins\n' % (schConfig['LONG_PERFORMANCE_SPAN_PENALTY'],          \
                                                                               localSchoolInfo[school]['name'] + (' ' * bufferLen), \
                                                                               performanceRate)
      #end if
    #end if
  #end loop

  #2
  #For this test, find the earliest performance time for a school.  If that time
  #minus that school's drive time is less than 0700 (ie that school needs to leave
  #before 7), then score points for every minute before 0700.
  #Points configured by PTS_PER_MINUTE_SCHOOL_LEAVES_BEFORE_7AM
  for school in localSchoolInfo.keys():
    penalty2       = 0
    durationAfter7 = subtractTime(700, localSchoolInfo[school]['earliestSession'])
    if durationAfter7 < localSchoolInfo[school]['driveTime']:
      penalty2   = (localSchoolInfo[school]['driveTime'] - durationAfter7) * schConfig['PTS_PER_MINUTE_SCHOOL_LEAVES_BEFORE_7AM']
      test2Score += penalty2
      if saveReport:
        reportText += '2 Leave Before 7     %4d %s Earliest %4d DriveTime %d\n' % \
                      (penalty2,                                                       \
                       localSchoolInfo[school]['name'].ljust(longSchoolNameLength),    \
                       localSchoolInfo[school]['earliestSession'],                     \
                       localSchoolInfo[school]['driveTime'])
    #end if
  #end loop

  #3
  #If a school has less than MAX_ENTRIES_FOR_CONFLICT_CHECKING entries, check
  #that it doesn't have any overlapping performances.
  #Nested loop here to check every schedule against every other one.
  #Keep a separate array which matches up with the schedule array.  Mark its
  #value true if a conflict was found with that session's entry, that way we
  #do not count them twice

  #Assemble a data struct by school that holds all their entry times
  schoolEntries = {k : [] for k in localSchoolInfo.keys()}
  for x in schedl['lst']:
    if 'entry' in x:
      schoolEntries[x['entry']['schoolId']].append([x['start'], x['end']])
  #end loop
  for school in schoolEntries.keys():
    #print(school)
    #Do a nested loop here to check each entry against every other one(except itself)
    skipArray = [False] * len(schoolEntries[school])
    pIndex    = 0
    for p in schoolEntries[school]:
      #print(p[0], p[1])
      qIndex = 0
      for q in schoolEntries[school]:    #0 = Start, 1 = End
        if p != q and                \
           skipArray[qIndex] == False and \
           (p[0] <= q[0] <= p[1] or  \
            p[0] <= q[1] <= p[1]):

          test3Score += schConfig['CONFLICT_PENALTY']
          if saveReport:
            reportText += '3 Time Conflict      %4d %s' %                                  \
                           (schConfig['CONFLICT_PENALTY'],                                 \
                            localSchoolInfo[school]['name'].ljust(longSchoolNameLength))
            reportText += ' ' + str(p[0])
            #if 'entryTitle' in x['entry']:
            #  reportText += ' ' + x['entry']['entryTitle']
            reportText += ' ' + str(q[0])
            #if 'entryTitle' in y['entry']:
            #  reportText += ' ' + y['entry']['entryTitle']
            reportText += '\n'
          skipArray[pIndex] = True  #Otherwise this conflict will show up twice
        qIndex += 1
      #end loop q
      pIndex += 1
    #end loop p
  #end loop school


  #4
  #For each category, make sure the same school isn't scheduled twice in a
  #room between breaks.  This keeps schools entries judged by different judges.
  #5
  #For state contests they don't switch judges at breaks, so do another check
  #of the same school twice in the same center.  Only do the check if the category
  #is ran in more than one center.
  curCategory         = ''
  curRoom             = ''
  schoolList          = {}
  schoolListPerCenter = {}
  check4Penalty       = schConfig['TWO_SCHOOL_ENTRIES_HAVE_SAME_JUDGES_PENALTY']
  check5Penalty       = schConfig['TWO_SCHOOL_ENTRIES_IN_SAME_CENTER_PENALTY']

  for x in schedl['lst']:
    if 'entry' in x and                 \
       (x['catShort'] != curCategory or \
        x['room']     != curRoom):

      curCategory         = x['catShort']
      curRoom             = x['room']
      schoolList          = {x['entry']['schoolId'] : 1}
      schoolListPerCenter = {x['entry']['schoolId'] : 1}

    elif x['isBreak']:
      schoolList = {}

    elif check5Penalty != 0         and \
       centerCount[curCategory] > 1 and \
       'entry' in x                 and \
       x['catShort'] == curCategory and \
       x['room']     == curRoom     and \
       x['entry']['schoolId'] in schoolListPerCenter:
      test5Score += schConfig['TWO_SCHOOL_ENTRIES_IN_SAME_CENTER_PENALTY']
      if saveReport:
        reportText += '5 Center Conflict    %4d %s   %s - %s\n' %                                       \
                          (check5Penalty,                                                                \
                           localSchoolInfo[x['entry']['schoolId']]['name'].ljust(longSchoolNameLength),  \
                           curCategory,                                                                  \
                           curRoom)

    elif check4Penalty != 0         and \
       'entry' in x                 and \
       x['catShort'] == curCategory and \
       x['room']     == curRoom     and \
       x['entry']['schoolId'] in schoolList:
      test4Score += schConfig['TWO_SCHOOL_ENTRIES_HAVE_SAME_JUDGES_PENALTY']
      if saveReport:
        reportText += '4 Judge Conflict     %4d %s   %s - %s\n' %                                         \
                          (check4Penalty,                                                                 \
                           localSchoolInfo[x['entry']['schoolId']]['name'].ljust(longSchoolNameLength),   \
                           curCategory,                                                                   \
                           curRoom)

    elif 'entry' in x:
      schoolList[x['entry']['schoolId']]          = 1
      schoolListPerCenter[x['entry']['schoolId']] = 1
    #end if
  #end for

  #6
  #Obey special requests.  These come in two forms.  Either an entire school
  #has an earliestStart/latestEnd restriction, or individual entries do.
  #To compute a penalty for breaking a special restriction, dock the schedule
  #BROKEN_RESTRICTION_PENALTY points if it is 1 minute before/after the
  #restriction.  Then, for every minute it is early/late, dock it
  #y minutes * RESTRICTION_PER_MINUTE_PENALTY points per minute.  This
  #will minimize the magnitude of the restriction breaking.
  for school, schoolData in localSchoolInfo.items():
    if 'earliestStartRstr' in schoolData:

      if schoolData['earliestSession'] < schoolData['earliestStartRstr']:
        points = (subtractTime(schoolData['earliestSession'], schoolData['earliestStartRstr']) \
                 * schConfig['RESTRICTION_PER_MINUTE_PENALTY']) + schConfig['BROKEN_RESTRICTION_PENALTY']
        test6Score += points
        if saveReport:
          schoolN = schoolData['name'].ljust(longSchoolNameLength)
          reportText += '6 School Early Restr %4d %s Restr %d Schdl %d\n' % \
                         (points, schoolN, schoolData['earliestStartRstr'], schoolData['earliestSession'])

    if 'latestEndRstr' in schoolData:

      if schoolData['latestSession'] > schoolData['latestEndRstr']:
        points = (subtractTime(schoolData['latestEndRstr'], schoolData['latestSession']) \
                 * schConfig['RESTRICTION_PER_MINUTE_PENALTY']) + schConfig['BROKEN_RESTRICTION_PENALTY']
        test6Score += points
        if saveReport:
          schoolN = schoolData['name'].ljust(longSchoolNameLength)
          reportText += '6 School Late Restr  %4d %s Restr %d Schdl %d\n' % \
                         (points, schoolN, schoolData['latestEndRstr'], schoolData['latestSession'])
  #end loop

  #Now check for entry restrictions
  for x in schedl['lst']:
    if 'entry' in x and 'earliestStart' in x['entry']:
      if x['start'] < x['entry']['earliestStart']:
        points = (subtractTime(x['start'], x['entry']['earliestStart']) \
                  * schConfig['RESTRICTION_PER_MINUTE_PENALTY']) + schConfig['BROKEN_RESTRICTION_PENALTY']
        test6Score += points
        if saveReport:
          schoolN = localSchoolInfo[x['entry']['schoolId']]['name'].ljust(longSchoolNameLength)
          #bufferLen = max(0, 27 - len(schoolName))
          reportText += '6 Entry Early Restr  %4d %s %s Restr %d Schdl %d\n' % \
                         (points,                                              \
                          schoolN,                                             \
                          x['catShort'],                                       \
                          x['entry']['earliestStart'],                         \
                          x['start'])

    if 'entry' in x and 'latestEnd' in x['entry']:
      if x['end'] > x['entry']['latestEnd']:
        points = (subtractTime(x['entry']['latestEnd'], x['end']) \
                  * schConfig['RESTRICTION_PER_MINUTE_PENALTY']) + schConfig['BROKEN_RESTRICTION_PENALTY']
        test6Score += points
        if saveReport:
          schoolN = localSchoolInfo[x['entry']['schoolId']]['name'].ljust(longSchoolNameLength)
          #bufferLen = max(0, 27 - len(schoolName))
          reportText += '6 Entry Late Restr   %4d %s %s Restr %d Schdl %d\n' % \
                         (points,                                              \
                          schoolN,                                             \
                          x['catShort'],                                       \
                          x['entry']['latestEnd'],                             \
                          x['end'])
  #end loop

  #7
  #Students should have 1/2 hour between performances.
  #First assemble a hash of students and their performance times.
  #The dictionary key is a tuple of (studentName, schoolID) so that students with the same
  #name at different schools are separately considered.
  #The values of the dict are still dicts themselves.  Unnecessary but left in for growth/bloat
  #OLD:
  # 'Stuart Smally'   : {'School' : 'South Sully', 'times' : ((805,840), (930,945), (1315,1330))}
  # 'Benito Musolini' : {'School' : 'Rifle Acdmy', 'times' : ((1015,1035), (1020,1040), (1440,1500))}
  #NEW:
  # ('Stuart Smally', 422)   : {'times' : ((805,840), (930,945), (1315,1330))}
  # ('Benito Musolini', 195) : {'times' : ((1015,1035), (1020,1040), (1440,1500))}
  performTimeHash = {}

  for x in schedl['lst']:
    if 'entry' in x and 'performers' in x['entry']:
      for performer in x['entry']['performers']:
        performerSchoolID = x['entry']['schoolId']
        if not (performer, performerSchoolID) in performTimeHash:
		      #Add the performer to the hash on the first encounter
          performTimeHash[(performer, performerSchoolID)]           = {}
          performTimeHash[(performer, performerSchoolID)]['times']  = []
        #Start/Stop time is a tuple
        performTimeHash[(performer, performerSchoolID)]['times'].append((x['start'],x['end']))
        #print ('Performer %s %d %d' % (performer, x['start'], x['end']))

  #Check that the performance times don't conflict
  for k,v in performTimeHash.items():
    performer = k[0]
    schoolID  = k[1]
    times     = v['times']
    #print ('Performer %d %s' % (len(times), performer))

    for x in range(0, len(times)-1):
      for y in range(x+1, len(times)):
        points = 0
        #print ('Checking (%d %d)(%d %d)' % (times[x][0],times[x][1],times[y][0],times[y][1]))
        if times[x][0] == times[y][0]:
          #Their start times are the same.  No way Jose.
          timeDelta = 0
        elif times[x][0] < times[y][0]:
          #Time X is before Y.  Compute diff between X's end time and Y's start
          timeDelta = subtractTime(times[x][1], times[y][0])
        else:
          #Time Y is before X.  Compute diff between Y's end time and X's start
          timeDelta = subtractTime(times[y][1], times[x][0])

        #Dock points as conflicts are found
        if timeDelta < 10:
          points = schConfig['STUDENT_SCHEDULE_TIME_CONFLICT']
        elif timeDelta >= 10 and timeDelta <= 45:
          points = schConfig['STUDENT_SCHEDULE_TIME_CONFLICT'] -                \
                   (timeDelta * schConfig['STUDENT_SCHEDULE_CONFLICT_PER_MIN'])

        if saveReport and points > 0:
          txt = '7 Student Time Conflict %4d     Times %4d %4d %s %s\n' %       \
                         (points,                                               \
                          times[x][0],                                          \
                          times[y][0],                                          \
                          performer,
                          localSchoolInfo[schoolID]['name'])
          #print (txt)
          reportText += txt
        test7Score += points
      #end y loop
    #end x loop
  #end performer loop



  end = time.time()
  fitnessTimes.append (end-start)
  
  #print ("Score %d %d %d %d" % (test1Score,test2Score,test3Score,test4Score))
  schedl['score'] = (test1Score + test2Score + test3Score + \
                     test4Score + test5Score + test6Score + test7Score)

  if saveReport:
    f = open(fileName, 'w', newline='\r\n')
    f.write (reportText)
    f.write ('\nScore: %d' % schedl['score'])
    f.close()


  #Schedule looks like this:
  #{'category' : 'Group Mime',
  # 'catShort' : 'GM',
  # 'start'    : 800,
  # 'end'      : 805,
  # 'room'     : '132',
  # 'duration' : 10,
  # 'entry'    :
  #             {'school'        : 'Kim Jong Il The Reformer North High',
  #              'driveTime'     : 50,
  #              'entryTitle'    : 'The incredible edible egg',
  #              'performers'    : ['Cory Mankin', 'Matt Sliter', 'Zach Koehn']
  #              'catShort'      : 'GM',
  #              'earliestStart' : 0930,
  #              'latestEnd'     : 1400},
  # 'isBreak'  : False}
  #end loop

#end fitnessTest

def getFitnessMetrics():
  lowest  = 99999.9
  highest = 0.0
  avg     = 0
  if len(fitnessTimes) > 0:
    for fitTime in fitnessTimes:
      avg += fitTime
      if fitTime < lowest:
        lowest = fitTime
      if fitTime > highest:
        highest = fitTime
    #end loop
    avg = avg / len(fitnessTimes)
    return '%d Fitness Max %f Min %f Avg %f' % (len(fitnessTimes), highest, lowest, avg)
#end printFitnessMetrics
