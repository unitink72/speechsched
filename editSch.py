import datetime
import glob
import os
import pickle
import re
import sys

import schedFitness


contestDir    = ''
timeDateDir   = ''
schedDir      = ''
binDir        = ''

if len(sys.argv) > 1:
   if os.path.exists(sys.argv[1]):
      if os.path.exists(os.path.join(sys.argv[1], 'bin')):
         schedDir = sys.argv[1]
         binDir   = os.path.join(sys.argv[1], 'bin')

   else:
      sys.exit('ERROR: Given folder is not a valid schedule: %s' % sys.argv[1])
else:
   cwd     = os.getcwd()
   now     = datetime.datetime.now()
   curYear = str(now.year) + '_'
   
   dirs = [f for f in os.listdir(cwd) if re.match(curYear, f)]
   for x in range(len(dirs)):
      print ('%2d) %s' % (x+1, dirs[x]))
   userIn      = input('Select a contest: ')
   contestDir  = cwd + os.sep + dirs[int(userIn)-1]


   dirs = [f for f in os.listdir(contestDir) if re.match('[\d_-]+', f)]
   for x in range(len(dirs)):
      print ('%2d) %s' % (x+1, dirs[x]))
   userIn       = input('Select a run: ')
   timeDateDir  = contestDir + os.sep + dirs[int(userIn)-1]

   dirs = [f for f in os.listdir(timeDateDir) if re.match('\d+', f)]
   for x in range(len(dirs)):
      print ('%2d) %s' % (x+1, dirs[x]))
   userIn    = input('Select a schedule: ')
   schedDir  = timeDateDir + os.sep + dirs[int(userIn)-1]
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

schedFitness.fitnessInitialize(schoolInfo, entryList, config)

schedFitness.fitnessTest (schedl     = schedule,    \
                          saveReport = False)

print ('Score %d' % schedule['score'])