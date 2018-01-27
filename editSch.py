import copy
import datetime
import glob
import os
import pickle
import re
import sys

import logger
import schedFitness
import schedIO


contestDir    = ''
timeDateDir   = ''
schedDir      = ''
binDir        = ''
folderChar    = 'A'

if len(sys.argv) > 1:
   if os.path.exists(sys.argv[1]):
      if os.path.exists(os.path.join(sys.argv[1], 'bin')):
         schedDir   = sys.argv[1]
         contestDir = os.path.join(schedDir, os.path.pardir, os.path.pardir)
         binDir     = schedDir + os.sep + 'bin' + os.sep

   else:
      sys.exit('ERROR: Given folder is not a valid schedule: %s' % sys.argv[1])
else:
   cwd     = os.getcwd()
   now     = datetime.datetime.now()
   curYear = str(now.year) + '_'
   
   dirs = [f for f in os.listdir(cwd) if re.match(curYear, f)]
   dirsSorted = sorted(dirs)
   for x in range(len(dirsSorted)):
      print ('%2d) %s' % (x+1, dirsSorted[x]))
   userIn      = input('Select a contest: ')
   contestDir  = cwd + os.sep + dirsSorted[int(userIn)-1]


   print ('')
   dirs = [f for f in os.listdir(contestDir) if re.match('[\d_-]+', f)]
   dirsSorted = sorted(dirs)
   for x in range(len(dirsSorted)):
      print ('%2d) %s' % (x+1, dirsSorted[x]))
   userIn       = input('Select a run: ')
   timeDateDir  = contestDir + os.sep + dirsSorted[int(userIn)-1]

   print ('')
   dirs = [f for f in os.listdir(timeDateDir) if re.match('\d+', f)]
   dirsSorted = sorted(dirs)
   for x in range(len(dirsSorted)):
      print ('%2d) %s' % (x+1, dirsSorted[x]))
   userIn    = input('Select a schedule: ')
   schedDir  = timeDateDir + os.sep + dirsSorted[int(userIn)-1]
   binDir    = schedDir + os.sep + 'bin' + os.sep
#endif

f = open(binDir + 'entryList.bin','rb')
entryList  = pickle.load(f)
f.close()

f = open(binDir + 'schedule.bin','rb')
schedule   = pickle.load(f)
f.close()

f = open(binDir + 'schoolInfo.bin','rb')
schoolInfo = pickle.load(f)
f.close()

config = {}
exec(open(os.path.join(contestDir,"settings.py")).read(), config)

editsDir = os.path.join(schedDir, 'edits')
if not os.path.isdir(editsDir):
   os.makedirs(editsDir)
#Make these files happy
logger      = logger.Logger(editsDir)
schedIO.setLogger(logger)
if 'G' in config['CONTEST_TYPE'].upper():
   schedIO.setCats('group')
else:
   schedIO.setCats('indiv')

schedFitness.setLogger(logger)
schedFitness.fitnessInitialize(schoolInfo, entryList, config)

#schedFitness.fitnessTest (schedl     = schedule,    \
#                          saveReport = False)
#print ('Score %d' % schedule['score'])

catList = []
for x in schedule['lst']:
   if 'entry' in x and x['entry']['catShort'] not in catList:
      catList.append(x['entry']['catShort'])

userContinue = True

while userContinue:
    print ('')
    for x in range(len(catList)):
       print ('%2d) %s' % (x+1, catList[x]))
    userIn = input('Select cateogry to swap: ')
    swapCat = catList[int(userIn)-1]
    print(swapCat)

    schoolList = []
    for x in schedule['lst']:
       if 'entry' in x and                           \
          x['entry']['catShort'] == swapCat and      \
          x['entry']['schoolId'] not in schoolList:
          schoolList.append(x['entry']['schoolId'])

    print ('')
    for x in range(len(schoolList)):
       print ('%2d) %s' % (x+1, schoolInfo[schoolList[x]]['name']))
    userIn = input('\nSelect first school: ')
    swapSchool1 = schoolList[int(userIn)-1]

    userIn = input('Select second school: ')
    swapSchool2 = schoolList[int(userIn)-1]

    #Now we know the category and schools to be swapped.  Last check 
    # needed is to see if those two schools are entered twice in
    # that category and ask the user which of those entries to swap.
    entryChoice1 = []
    for x in schedule['lst']:
       if 'entry' in x and                           \
          x['entry']['catShort'] == swapCat and      \
          x['entry']['schoolId'] == swapSchool1:

          entryChoice1.append(x)

    if len(entryChoice1) > 1:
       print('')
       for x in range(len(entryChoice1)):
          choiceTitle = ''
          if 'entryTitle' in entryChoice1[x]['entry']:
             choiceTitle = entryChoice1[x]['entry']['entryTitle']
          choiceStudents = entryChoice1[x]['entry']['performers']

          print('%2d) %d %s %s' % (x+1,                        \
                                   entryChoice1[x]['start'],   \
                                   choiceTitle,                \
                                   choiceStudents[0]))
       userIn = input('\nChoose the entry for %s: ' % schoolInfo[swapSchool1]['name'])
       userChoice1Idx = entryChoice1[int(userIn)-1]['entry']['index']
    else:
       userChoice1Idx = entryChoice1[0]['entry']['index']

    entryChoice2 = []
    for x in schedule['lst']:
       if 'entry' in x and                           \
          x['entry']['catShort'] == swapCat and      \
          x['entry']['schoolId'] == swapSchool2:

          entryChoice2.append(x)

    if len(entryChoice2) > 1:
       print('')
       for x in range(len(entryChoice2)):
          choiceTitle = ''
          if 'entryTitle' in entryChoice2[x]['entry']:
             choiceTitle = entryChoice2[x]['entry']['entryTitle']
          choiceStudents = entryChoice2[x]['entry']['performers']

          print('%2d) %d %s %s' % (x+1,                        \
                                   entryChoice2[x]['start'],   \
                                   choiceTitle,                \
                                   choiceStudents[0]))
       userIn = input('\nChoose the entry for %s: ' % schoolInfo[swapSchool2]['name'])
       userChoice2Idx = entryChoice2[int(userIn)-1]['entry']['index']
    else:
       userChoice2Idx = entryChoice2[0]['entry']['index']


    #Convert entry index to list array index
    for x in range(len(schedule['lst'])):
       if 'entry' in schedule['lst'][x]:
          if schedule['lst'][x]['entry']['index'] == userChoice1Idx:
             choice1ListIdx = x 
          elif schedule['lst'][x]['entry']['index'] == userChoice2Idx:
             choice2ListIdx = x

    #print ('\nSwap entry index %d %d' % (userChoice1Idx, userChoice2Idx))
    #print ('Swap array Index %d %d' % (choice1ListIdx, choice2ListIdx))
    print ('Old Score %d' % schedule['score'])

    temp1Copy = schedule['lst'][choice1ListIdx]['entry']
    schedule['lst'][choice1ListIdx]['entry'] = schedule['lst'][choice2ListIdx]['entry']
    schedule['lst'][choice2ListIdx]['entry'] = temp1Copy

    schedFitness.fitnessTest (schedl     = schedule,   \
                              saveReport = False)

    newSchedFolder = os.path.join(schedDir, 'edits', str(int(schedule['score'])))
    tempDir = newSchedFolder
    while os.path.isdir(tempDir):
       tempDir    = newSchedFolder + folderChar
       folderChar = chr(ord(folderChar) + 1)
    newSchedFolder = tempDir

    schedIO.printSched       (schedule   = schedule,               \
                              schoolInf  = schoolInfo,             \
                              entriesLst = entryList,              \
                              outFolder  = newSchedFolder)

    schedFitness.fitnessTest (schedl     = schedule,        \
                              saveReport = True,            \
                              fileName   = os.path.join(newSchedFolder,'fitnessReport.txt'))
    print ('New Score %d' % schedule['score'])

    userIn = input('Press [x] to exit, [ENTER] to continue editing schedule: ')
    userContinue = userIn.find('x') == -1
