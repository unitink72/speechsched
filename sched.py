import os
import copy
import datetime
import distManager
import logger
import math
from multiprocessing import TimeoutError
import multiprocessing
import random
import time
import schedIO
import schedFitness
import signal
import sys
from queue import Empty
import gc


MAX_MUTATIONS_PER_SCHEDULE       = 1
MAX_SWAPS_PER_RHOMP              = 1

#Number of times the random schedule generator will attempt to place a single
#entry into a session of the same category.
MAX_FAILED_TRYS_COUNT        = 500


#Keep a dict of catagories (GM, CR etc) and their starting/ending indexes in the
#sessions list. ie:
# 'EA' :
#       {'startIdx' : 93,
#        'endIdx'   : 121}
# 'GM' :
#       {'startIdx' : 244,
#        'endIdx'   : 276}


def timeStamp():
  dateNow = datetime.datetime.now();
  return dateNow.strftime('%y-%m-%d_%H-%M');
#end timeStamp

def createRandomSchedules(scheduleList, sessions, entries, randGen, maxCount=None):
  #Schedule looks like this:
  #{'score'    : 25402,
  # 'lst'      :
  #   {'category' : 'Group Mime',
  #    'catShort' : 'GM',
  #    'start'    : 800,
  #    'end'      : 805,
  #    'room'     : '132',
  #    'duration' : 10,
  #    'entry'    :
  #                {'school'    : 'Kim Jong Il The Reformer North High',
  #                 'code'      : 'X4',
  #                 'driveTime' : 50,
  #                 'deps'      : 'cy',
  #                 'catShort'  : 'GM'},
  #    'isBreak'  : False}

  randFailCount       = 0
  generatedSchedCount = 0
  sessionsOk          = 1

  for x in range(len(scheduleList)):

    if maxCount != None and generatedSchedCount == maxCount:
      break

    if scheduleList[x]['lst'] != None:      #Only fill in the blank array slots
      continue                             # with new random schedules

    randSched = copy.deepcopy(sessions)

    #Keep a seperate array whose elements are indexes into the sessions array.  As
    #sessions are filled, remove that session from the list.  This way the random
    #generator doesn't pick more and more already-filled sessions as the list of
    #available slots gets smaller.
    scratchList = list(range(len(sessions)))  #Looks like [0,1,2,3,4, ... ]

    for item in entries:
      failedTrys = 0
      placedItem = 0
      #Find the starting and ending session index for this entry's catagory.  This
      #way the random picker can select from a limited set instead of the whole
      #schedule.  Can't just use the categoryIndexes dict because we are working
      #from the scratchlist here.
      foundStart = 0
      startIdx   = 0
      endIdx     = len(scratchList)-1
      for scratchIdx in range(len(scratchList)):
        if not foundStart and randSched[scratchList[scratchIdx]]['catShort'] == item['catShort']:
          startIdx   = scratchIdx
          foundStart = True
        elif foundStart and randSched[scratchList[scratchIdx]]['catShort'] != item['catShort']:
          endIdx     = scratchIdx-1
          break

      #print ('%s Start %d End %d' % (item['catShort'], startIdx, endIdx))
      #end loop
      while 1:
        #Pick a random spot in the scratchlist
        randomIdx        = randGen.randint(startIdx, endIdx)
        randomSessionIdx = scratchList[randomIdx]
        #print('Length %d Rand %d Cat %s' % (len(scratchList), scratchList[randomIdx], randSched[randomSessionIdx]['catShort']))

        #See if that session is eligable for this entry.
        if randSched[randomSessionIdx]['catShort'] == item['catShort'] and \
        randSched[randomSessionIdx]['isBreak'] == False:

          randSched[randomSessionIdx]['entry'] = item  #Found a good match.  Schedule it.
          del scratchList[randomIdx]                   #Remove this session from the available list
          placedItem = 1
          break
        else:
          failedTrys += 1
        #end if
        if failedTrys >= MAX_FAILED_TRYS_COUNT:
          randFailCount += 1
          break
      #end loop

      if not placedItem:
        #Iterate thru all the list at this point to ensure the
        #random picker didn't miss 1 available slot.
        for y, idx in enumerate(scratchList):
          if randSched[idx]['catShort'] == item['catShort'] and \
             randSched[idx]['isBreak'] == False:

            randSched[idx]['entry'] = item            #Found a good match.  Schedule it.
            del scratchList[y]                        #Remove this session from the available list
            placedItem = 1
            break
          #end if
        #end loop
      #end if
      if not placedItem:
        print (item)
        print ('Not enough sessions for cateagory %s\n' % item['catShort'])
        sessionsOk = 0
      #end entry loop

      #entryCount = 0
      #for sched in randSched:
      #  if 'entry' in sched:
      #    entryCount += 1
      #if entryCount != len(entriesList):
      #  sys.exit('Entry count fail after 5rdm')

    #end entry loop

    scheduleList[x]['lst'] = randSched
    schedFitness.fitnessTest(scheduleList[x], False)
    generatedSchedCount += 1
  #end schedule loop
  
  if sessionsOk != 1:
    sys.exit('Sessions file needs work. Exiting.')
  return randFailCount
#end createRandomSchedule

def computeTopScore(schedl):

  bestScore      = 0
  bestScoreIdx   = 0
  sortedScoreList = []

  #First sort the list
  for x in schedl:
    sortedScoreList.append(x['score'])
  sortedScoreList.sort()

  bestScore      = sortedScoreList[0]

  for idx,item in enumerate(schedl):
    if bestScore == item['score']:
      bestScoreIdx = idx
      break

  return (bestScore, bestScoreIdx)
#end computeTopScore

def findParentSchedules(schedList, count, randGen):
  #Find two random schedules from the list.  Can't just pick from
  #list members because most of them will be null.  Instead pick
  #2 randomly, an keep increasing by 1 until a non-null one is
  #reached.  If we "walk" over the end of the list, start over
  #at the begining.

  schedPairList = []

  for x in list(range(count)):
    index1 = randGen.randint(0, len(schedList)-1)
    index2 = randGen.randint(0, len(schedList)-1)

    while schedList[index1] == None:
      if index1 == len(schedList)-1:
        index1 = 0
      else:
        index1 += 1

    while schedList[index2] == None or index1 == index2:  #Dont pick duplicates
      if index2 == len(schedList)-1:
        index2 = 0
      else:
        index2 += 1

    schedPairList.append( [index1, index2] )
  #end loop

  return schedPairList

#end findParentSchedules

def mutate (schedl, randGen):

  newSched               = copy.deepcopy(schedl)
  searchingForTwoEntries = 1
  mutationCount          = randGen.randint(1,MAX_MUTATIONS_PER_SCHEDULE)
  index1                 = 0
  index2                 = 0
  tempEntry              = {}

  #start = time.time()

  for x in list(range(mutationCount)):

    searchingForTwoEntries = 1

    while searchingForTwoEntries:
      index1 = randGen.randint(0, len(newSched['lst'])-1)
      index2 = randGen.randint(0, len(newSched['lst'])-1)
      #TODO add swapping when one of the random slots doesnt have an entry yet
      if index1 != index2                       and \
         'entry' in newSched['lst'][index1]     and \
         'entry' in newSched['lst'][index2]     and \
         newSched['lst'][index1]['catShort'] == newSched['lst'][index2]['catShort']:
        searchingForTwoEntries = 0
    #end loop

    tempEntry = newSched['lst'][index1]['entry']
    newSched['lst'][index1]['entry'] = newSched['lst'][index2]['entry']
    newSched['lst'][index2]['entry'] = tempEntry
  #end loop

  schedFitness.fitnessTest(newSched, False)
  #entryCount = 0
  #for sched in newSched:
  #  if 'entry' in sched:
  #    entryCount += 1
  #if entryCount != len(entriesList):
  #  sys.exit('Entry count fail after 3mut')

  #end = time.time()
  #print ('Mut %d %f' % (mutationCount,(end - start)))

  #if checkSchedForDupes(newSched):
  #  schedIO.printSched(newSched, 'newSched.txt')
  #  sys.exit('Got mutated dupes printed newSched')
  return newSched
#end mutate


def checkSchedForDupes(sched):

  scratchList = [0] * len(entriesList)

  for session in sched:
    if 'entry' in session:

      for x in list(range(len(entriesList))):
        if entriesList[x]['school']     == session['entry']['school']     and \
           entriesList[x]['entryTitle'] == session['entry']['entryTitle'] and \
           entriesList[x]['performers'] == session['entry']['performers']:
          if scratchList[x] == 1:
            print ('Got dupe %s %s' % (session['entry']['school'], session['entry']['entryTitle']))
            return True
          else:
            scratchList[x] = 1
      #end x loop
  #end session loop
  return False
#end checkSchedForDupes

def validateSched (sched, sessions, entries, logger):
  returnVal = 0
  #Check that every entry is in the schedule only once
  for entry in entries:
    entryFoundCount = 0

    for session in sched['lst']:
      if 'entry' in session and session['entry']['index'] == entry['index']:
        entryFoundCount += 1

    if entryFoundCount > 1:
      print ('Entry scheduled more than once')
      returnVal += 1
    elif entryFoundCount == 0:
      print ('Entry not scheduled')
      returnVal += 2

  #No breaks get filled with an entry
  for session in sched['lst']:
    if session['isBreak'] == True and 'entry' in session:
      print ('Entry scheduled during a break')
      returnVal += 4

  if returnVal > 0:
  	logger.msg ('Validation Failed, score %d' % returnVal)
  else:
  	logger.msg ('Validation Passed')


def scheduleSex(baseParent, donorParent, randGen):
  #A new child schedule is created by first cloning the baseParent.  The child
  #is then modified via accepting a few "traits" of the donorParent.
  newSched          = copy.deepcopy(baseParent)
  searchingForEntry = 1
  swapsCount        = randGen.randint(1,MAX_SWAPS_PER_RHOMP)
  index1            = 0
  index2            = -1
  tempEntry         = {}

  #start = time.time()

  for x in list(range(swapsCount)):

    searchingForEntry = 1

    while searchingForEntry:
      index1 = randGen.randint(0, (len(newSched['lst']))-1)
      if 'entry' in newSched['lst'][index1]:
        searchingForEntry = 0
    #end loop

    #print('Searching %s %s' % (newSched['lst'][index1]['entry']['school'], newSched['lst'][index1]['entry']['entryTitle']))
    if 'entry' in donorParent['lst'][index1]:
      tempEntry = donorParent['lst'][index1]['entry']

      #Now find where the entry from parent 2 is located in parent 1
      for y in list(range(len(newSched['lst']))):
        if 'entry' in newSched['lst'][y] and \
           newSched['lst'][y]['entry']['index'] == tempEntry['index']:
          index2 = y
          break
      else:
        print ('newSched[\'lst\'][index1] :')
        print (newSched['lst'][index1])
        schedIO.printSched(newSched, 'newSched.txt')       #WILL FAIL
        schedIO.printSched(donorParent, 'donorParent.txt')
        checkSchedForDupes(donorParent)
        sys.exit ("No match in donorParent")
    else:
      #donorParent has an unfilled session in that spot.  Find a corresponding one in newSched
      newSchedIndexList = list(range(len(newSched['lst'])))
      randGen.shuffle (newSchedIndexList)  #Randomize the list
      for z in newSchedIndexList:
        if 'entry' not in newSched['lst'][z]      and \
           newSched['lst'][z]['isBreak'] == False and \
           newSched['lst'][z]['catShort'] == newSched['lst'][index1]['catShort']:
          index2 = z
          break
    #end if

    if index1 == index2:
      #The random entry to swap is already in the same place
      #in both parents, no need to do anything
      #This is possibly not needed since the swap algorithm won't
      #harm anything.
      continue

    if newSched['lst'][index1]['catShort'] != newSched['lst'][index2]['catShort']:
      #This algorithm assumes that for any index (q) in baseParent array,
      #the catagory of baseParent(q) is equal to the catagory of donorParent(q)
      sys.exit ("Woa nelly sumthins mixed up")

    #Its possible that index2 doesn't have an entry.
    if 'entry' in newSched['lst'][index2]:
      tempEntry                        = newSched['lst'][index1]['entry']
      newSched['lst'][index1]['entry'] = newSched['lst'][index2]['entry']
      newSched['lst'][index2]['entry'] = tempEntry

    else:
      newSched['lst'][index2]['entry'] = newSched['lst'][index1]['entry']
      del(newSched['lst'][index1]['entry'])

    #if checkSchedForDupes(newSched):
    #  schedIO.printSched(newSched, 'newSched.txt')
    #  sys.exit('Got dupes printed newSched')
    #entryCount = 0
    #for sched in newSched:
    #  if 'entry' in sched:
    #    entryCount += 1
    #if entryCount != len(entriesList):
    #  sys.exit('Entry count fail after 2')

  #end loop
  schedFitness.fitnessTest(newSched, False)
  #end = time.time()
  #print ('Sex %d %f' % (swapsCount,(end - start)))

  return newSched
#end scheduleSex


def childWorker(inQueue,     \
                outQueue,    \
                schoolInfo,  \
                entriesList, \
                config):

  #gc.set_debug(gc.DEBUG_LEAK)
  procName    = multiprocessing.current_process().name
  newSched    = None

  #Load config file
  wrkConfig = config
  #exec(open("settings.py").read(), wrkConfig)
  schedFitness.fitnessInitialize(schoolInfo, entriesList, wrkConfig)
  
  randGenWrk  = random.SystemRandom()
  startTime   = time.time()
  counter     = 0
  mutateCnt   = 0
  xOverCnt    = 0

  while True:
    workPackage = inQueue.get()
    counter    += 1    
#    if procName == 'SchedWorker5' and counter%1000==0 :
#      msgStr = ('Wrkr5 GC Obj %d' % len(gc.get_objects()))
#      outQueue.put({'msg':msgStr})
      
    if workPackage['cmd'] == 'STOP':
      break
      
    elif workPackage['cmd'] == 'Mutate': 
      newSched = mutate(workPackage['sch1'], randGenWrk)
      if newSched['score'] < workPackage['sch1']['score']:
        #print ('Mutate child parent fitness %d %d' % (newSched['score'], workPackage['sch1']['score']))
        outQueue.put ({'idx':workPackage['idx'], 'sch':newSched, 'method':'M'})
        mutateCnt += 1
        
    elif workPackage['cmd'] == 'XOver':
      newSched    = scheduleSex(workPackage['sch1'], workPackage['sch2'], randGenWrk)
      if newSched['score'] < workPackage['sch1']['score']:
        #print ('XOver child parent fitness %d %d' % (newSched['score'], workPackage['sch1']['score']))
        outQueue.put ({'idx':workPackage['idx'], 'sch':newSched, 'method':'X'})
        xOverCnt += 1

    elif workPackage['cmd'] == 'Done':
        outQueue.put({'done':1})

  msgStr = '%s STOP Count %d Rate %1.1f xOver:%d Mutate:%d:' % \
           (procName, counter, counter / (time.time()-startTime), xOverCnt, mutateCnt)
  outQueue.put({'msg':msgStr})
  msgStr = procName + ' ' + schedFitness.getFitnessMetrics()
  outQueue.put({'msg':msgStr})
#end childWorker

################################################################################
#Begin Main

#if __name__ == '__main__':
#  print ('Starting Main process')

#Validate the folder to process from and write logs to
if len(sys.argv) < 2:
  sys.exit('Usage: python3 %s jobFolder' % sys.argv[0])

if not os.path.exists(sys.argv[1]):
  sys.exit('ERROR: Job Folder %s was not found!' % sys.argv[1])

dryRunMode = '-dryrun' in sys.argv

randGenMain = random.SystemRandom()

#Setup output folder and Logger for this run
contestFolder   = sys.argv[1]
timeStampFolder = timeStamp()
jobFolder       = os.path.join(os.getcwd(), contestFolder)
outFolder       = os.path.join(jobFolder, timeStampFolder)
try:
   os.makedirs(outFolder)
except FileExistsError:
   sys.exit('Need to wait 1 minute between runs')
logger      = logger.Logger(outFolder)
schedIO.setLogger(logger)
schedFitness.setLogger(logger)

#Load config file
configRaw = {}
config    = {}
exec(open(os.path.join(jobFolder,"settings.py")).read(), config)
for key,value in configRaw:  #For some reason the raw config isnt pickleable
  config[key] = value

if dryRunMode:
   print ('--++## Dry Run Mode ##++--')

#Tell schedIO and Categories object if we are group or individal.
if 'G' in config['CONTEST_TYPE'].upper():
  schedIO.setCats('group')
else:
  schedIO.setCats('indiv')

#Read input files
sessionsFile     = os.path.join(jobFolder, 'Sessions.txt')
restrSheetFile   = os.path.join(jobFolder, 'restrSheet.csv')
schoolCsvFile    = os.path.join(config['MASTER_FILE_PATH'], 'schoolReg.csv')
schoolExportFile = os.path.join(config['MASTER_FILE_PATH'], 'schoolsExport.csv')
studentCsvFile   = os.path.join(config['MASTER_FILE_PATH'], 'students.csv')

if not os.path.isfile(sessionsFile):     sys.exit ('Sessions file not found: %s' % sessionsFile)
if not os.path.isfile(restrSheetFile):   sys.exit ('RestrSheet file not found: %s' % restrSheetFile)
if not os.path.isfile(schoolCsvFile):    sys.exit ('SchoolCsv file not found: %s' % schoolCsvFile)
if not os.path.isfile(schoolExportFile): sys.exit ('SchoolExport file not found: %s' % schoolExportFile)
if not os.path.isfile(studentCsvFile):   sys.exit ('StudentCsv file not found: %s' % studentCsvFile)

(sessionList, catagoryIndexes) = schedIO.readSessionsFile(sessionsFile)
schoolInfo                     = schedIO.readSchoolsExport(schoolExportFile)
rawEntriesList                 = schedIO.readSchoolWebCsv(fileName   = schoolCsvFile,              \
                                                          schoolInfo = schoolInfo,                 \
                                                          siteName   = config['CONTEST_SITENAME'], \
                                                          codeChar   = config['SCHOOL_CODE_CHARS'])
schedIO.readStudentWebCsv (rawEntriesList, studentCsvFile)
entriesList                    = schedIO.readRestrSheet (rawEntriesList, restrSheetFile)
  
#Remove schools that are removed because of no entries in the restrictions sheet
newSchoolInfo = []
for school in schoolInfo:
  Found = False
  for entry in entriesList:
    if entry['schoolId'] == school:
      Found = True
      break
  if not Found:
    schoolInfo[school]['inContest'] = False


#Fill in school address info, force a write to cache.  Clients
# will read this cache for their distance lookups.
hostSchoolAddr = ''
distMgr = distManager.DistManager(logger,config,dryRunMode)
for school, data in schoolInfo.items():
  if data['inContest']:
    if data['city']:
      distMgr.addSchool(school, data['city'] + ',IA')
      print('Adding %s' % data['city'])
    else:
      #No city is given.  distMgr handles this gracefully
      distMgr.addSchool(school, '')
  if school == config['HOST_SCHOOL_ID']:
    if data['city']:
      hostSchoolAddr = data['city'] + ',IA'
    else:
      sys.exit('schoolsExport.csv missing city data for host school ID %d' % school)

hostSchoolId = config['HOST_SCHOOL_ID']
if not hostSchoolId in schoolInfo:
  print('ERROR: Host school not in contest')

distMgr.setHostSchool(hostSchoolId, hostSchoolAddr)
if not distMgr.allAddressesValid():
   sys.exit('\nschoolsExport.csv missing City data.\n  See %s%s/runLog.txt' %  \
                                               (contestFolder,timeStampFolder))

for school,data in schoolInfo.items():
  if data['inContest']:
    data['driveTime'] = distMgr.driveTimeLookup(hostSchoolId,school)
    #print('Dist %s %d' % (data['city'], data['driveTime']))
    #data['driveTime'] = 10

#Initialize fitness.  Main thread uses it at the last step.
schedFitness.fitnessInitialize(schoolInfo, entriesList, config)

#Test creating a random schedule to make sure there are enough sessions
# for all the entries.  If it fails, quit before spinning off childWorkers
tstRdm    = [{'score':-1, 'lst':None}]
randFails = createRandomSchedules (tstRdm, sessionList, entriesList, randGenMain)

childPID = os.fork()
if childPID:
  sys.exit('PID %d going to background\n' % childPID)

#Creating a worker for each cpu core gives wacko results.  There are queue issues
#and garbage collection gets starved.
cpuCount  = multiprocessing.cpu_count() - 1
processes = []
taskQueue = multiprocessing.Queue()
doneQueue = multiprocessing.Queue()

rdm = []
for x in range(1, config['STAGE_1_ARRAY_SIZE']):
  rdm.append({'score':-1, 'lst':None})

topScores      = []
lowestScore    = 0
lowestScoreIdx = -1

for x in range(cpuCount):
  p = multiprocessing.Process(target = childWorker,        \
                              args   = (taskQueue,         \
                                        doneQueue,         \
                                        schoolInfo,        \
                                        entriesList,       \
                                        config),           \
                              name   = 'SchedWorker%d' % x)
  p.start()
  processes.append(p)

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

#############################################################################
## PHASE 1 Fill the list with random schedules
#############################################################################
randFails        = createRandomSchedules (rdm, sessionList, entriesList, randGenMain)
stageNum         = 1
stageStart       = time.time()
flushCycleStart  = time.time()
printCnt         = 1
waitCnt          = 0

prevBestScore         = 999999999999
scoreLastImprovedTime = time.time()
  
jobMaxSize       = 1000
jobMinSize       = 10
jobSizeIncr      = 10

lastScorePrintTime = time.time()

logger.msg('Start Main Loop')
jobCurrentSize = jobMinSize

#DEBUG for getting a quick printout
schedIO.printSched (schedule   = rdm[2],                \
                    schoolInf  = schoolInfo,            \
                    entriesLst = entriesList,           \
                    outFolder  = outFolder + '/xx')
if dryRunMode:
   logger.msg('Finished dry run')
   exit()

while True:
  parentsList = findParentSchedules(rdm, jobCurrentSize, randGenMain)
  for x in parentsList:
    taskQueue.put({'cmd':'XOver', 'idx':x[0], 'sch1':rdm[x[0]], 'sch2':rdm[x[1]]})

  for x in range(jobCurrentSize):
      mutateIdx = randGenMain.randint(0, len(rdm)-1)
      taskQueue.put({'cmd':'Mutate', 'idx':mutateIdx, 'sch1':rdm[mutateIdx]})
  taskQueue.put({'cmd':'Done'})  #End of job marker
  jobCurrentSize = min(jobCurrentSize + jobSizeIncr,  jobMaxSize)
    
  if jobCurrentSize == jobMaxSize - 10:
    logger.msg('*')

  #This is a good time to do work while waiting for the child procs to finish
  #Print out the best score every so often
  if time.time() - lastScorePrintTime > config['BEST_SCORE_PRINT_MINS'] * 60:
    if stageNum == 1 and len(topScores) > 0:
      (lowestScore, lowestScoreIdx) = computeTopScore (topScores)
      scorePrintFolder              = os.path.join(outFolder, str(math.floor(lowestScore)))
      if not os.path.exists(scorePrintFolder):
        schedIO.printSched (schedule   = topScores[lowestScoreIdx],  \
                            schoolInf  = schoolInfo,                 \
                            entriesLst = entriesList,                \
                            outFolder  = scorePrintFolder)
        schedFitness.fitnessTest (schedl     = topScores[lowestScoreIdx],    \
                                  saveReport = True,                         \
                                  fileName   = os.path.join(scorePrintFolder, 'FitnessReport.txt'))
        validateSched(topScores[lowestScoreIdx], sessionList, entriesList, logger)
    elif stageNum == 2 and len(rdm) > 0:
      (lowestScore, lowestScoreIdx) = computeTopScore (rdm)
      scorePrintFolder              = os.path.join(outFolder, str(math.floor(lowestScore)))
      if not os.path.exists(scorePrintFolder):
        schedIO.printSched (schedule   = rdm[lowestScoreIdx],   \
                            schoolInf = schoolInfo,             \
                            entriesLst = entriesList,           \
                            outFolder  = scorePrintFolder)
        schedFitness.fitnessTest (schedl     = rdm[lowestScoreIdx],    \
                                  saveReport = True,                   \
                                  fileName   = os.path.join(scorePrintFolder, 'FitnessReport.txt'))
        validateSched(rdm[lowestScoreIdx], sessionList, entriesList, logger)
    lastScorePrintTime = time.time()

  #Wait for the task queue to empty so we don't get ahead of ourselves
  while not taskQueue.empty():
    time.sleep(0.1)
    waitCnt += 1
    
  while True:
    try:
      response = doneQueue.get(block=True,timeout=60)
      if 'done' in response:
        break
      elif 'msg' in response:
      	logger.msg (response['msg'])
      else:
        #Double check that the score is better. Otherwise a race is possible and will decrease score.
        oldScore = rdm[response['idx']]['score']
        if response['sch']['score'] < oldScore:
          rdm[response['idx']] = response['sch']
          if stageNum == 2:
            logger.msg ('%s %d -> %d' % (response['method'], oldScore, response['sch']['score']))
    except Empty:
      break
    except IndexError:
      print ('rdm[%d] not a valid index' % response['idx'])

  (lowestScore, lowestScoreIdx) = computeTopScore (rdm)
  #Display the best score in the log
  if (time.time() - stageStart) / (config['DISPLAY_BEST_SCORE_SECS'] * printCnt) > 1.0:
    logger.msg ('Best Score %4d' % (lowestScore))
    printCnt += 1

  if lowestScore < prevBestScore:
     prevBestScore         = lowestScore
     scoreLastImprovedTime = time.time()

  #Stage 1 Flush
  # After 5 minutes of no improvement, do a flush
  if stageNum == 1 and time.time() - scoreLastImprovedTime > 5 * 60:
    logger.msg ('Flushing list')
    logger.msg ('Main GC Obj %d' % len(gc.get_objects()))

    prevBestScore = 999999999999
    for idx,z in enumerate(rdm):          #Add the top score to the topScores list
      if z['score'] == lowestScore:
        logger.msg ('Adding %d to top scores' % z['score'])
        topScores.append(z)
    #end loop
      
      #Clean out the results queue so it doesn't overwrite the new randoms with old(better) results.
#      while True:
#        try:
#          response = doneQueue.get(block=True,timeout=60)
#          if 'msg' in response:
#            logger.msg (response['msg'])
#        except Empty:
#          break

    if time.time() - stageStart > config['STAGE_1_HOURS'] * 60 * 60 and len(topScores) > 1:
      #This "if" only gets checked when flushing.  So its timing is not very accurate
      #Stage 1 Finished.  Now start improving just the topScores array
      logger.msg ('Starting Stage 2')

      rdm       = topScores
      topScores = []
      logger.msg ('Stage 2 Scores:')
      for scoreX in rdm:
        logger.msg ('   %d ' % scoreX['score'])

      stageNum   = 2
      printCnt   = 1
      stageStart = time.time()
    else:
      #Wipe the schedule array, fill it back up with randoms and start over
      rdm = []
      for x in range(config['STAGE_1_ARRAY_SIZE']-1):
        rdm.append({'score':-1, 'lst':None})
      randFails = createRandomSchedules (rdm, sessionList, entriesList, randGenMain)
      flushCycleStart = time.time()  #Reset the flush timer
      jobCurrentSize = jobMinSize
        
  elif stageNum == 2 and time.time() - stageStart > config['STAGE_2_HOURS'] * 60 * 60:
    logger.msg ('End Stage 2')
    for x in range(cpuCount):
      logger.msg ('Stopping task %d' % x)
      taskQueue.put({'cmd':'STOP'})
    break



  waitCnt = 0
#end loop

logger.msg ('Compute loop finished')


#############################################################################
## PHASE 2 Empty the output queue and close up shop
#############################################################################

#Empty the output queue
respCount = 0;
while True:
  try:
    response = doneQueue.get(block=True,timeout=20)
    if 'msg' in response:
      logger.msg (response['msg'])
    respCount += 1;
  except Empty:
    break
logger.msg ('Cleaned out %d from output queue' % respCount)

for p in processes:
  try:
    p.join(timeout=60)
  except TimeoutError:
    logger.msg ('Timeout joining process')

(lowestScore, lowestScoreIdx) = computeTopScore (rdm)
logger.msg ('Best Score %4d' % lowestScore)
logger.msg(schedFitness.getFitnessMetrics())

logger.msg ('Scores:')
for scoreX in rdm:
  logger.msg ('   %d ' % scoreX['score'])

logger.msg ('Printing best score of %d' % lowestScore)

scorePrintFolder = os.path.join(outFolder, str(math.floor(lowestScore)))
if not os.path.exists(scorePrintFolder):
  fitnessFile      = os.path.join(scorePrintFolder, 'fitnessReport.txt')

  schedIO.printSched       (schedule   = rdm[lowestScoreIdx],   \
                            schoolInf = schoolInfo,             \
                            entriesLst = entriesList,           \
                            outFolder  = scorePrintFolder)
  validateSched(rdm[lowestScoreIdx], sessionList, entriesList, logger)

  schedFitness.fitnessTest (schedl     = rdm[lowestScoreIdx],    \
                            saveReport = True,                   \
                            fileName   = fitnessFile)

