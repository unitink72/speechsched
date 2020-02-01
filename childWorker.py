import copy
import logger
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


