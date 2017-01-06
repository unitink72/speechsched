import csv
import os, sys
import logger
import schedIO

if len(sys.argv) < 2:
  sys.exit('Usage: python3 %s jobFolder' % sys.argv[0])

if not os.path.exists(sys.argv[1]):
  sys.exit('ERROR: Job Folder %s was not found!' % sys.argv[1])

#Setup output folder and Logger for this run
jobFolder   = os.path.join(os.getcwd(), sys.argv[1])


#Load config file
configRaw = {}
config    = {}
exec(open(os.path.join(jobFolder,"settings.py")).read(), config)
for key,value in configRaw:  #For some reason the raw config isnt pickleable
  config[key] = value



#Read input files
schoolCsvFile    = os.path.join(config['MASTER_FILE_PATH'], 'schoolReg.csv')
schoolExportFile = os.path.join(config['MASTER_FILE_PATH'], 'schoolsExport.csv')
studentCsvFile   = os.path.join(config['MASTER_FILE_PATH'], 'students.csv')

if not os.path.isfile(schoolCsvFile):    sys.exit ('SchoolCsv file not found: %s' % schoolCsvFile)
if not os.path.isfile(schoolExportFile): sys.exit ('SchoolExport file not found: %s' % schoolExportFile)
if not os.path.isfile(studentCsvFile):   sys.exit ('StudentCsv file not found: %s' % studentCsvFile)

#Don't need logger setup unless something bad happens in the data
#logger = logger.Logger(jobFolder)
#schedIO.setLogger(logger)

if 'G' in config['CONTEST_TYPE'].upper():
  schedIO.setCats('group')
else:
  schedIO.setCats('indiv')

schoolInfo       = schedIO.readSchoolsExport(schoolExportFile)

siteCount        = len(config['CONTEST_SITENAME'])

for site in config['CONTEST_SITENAME']:
  print ('Processing %s' % site)

  entriesList = schedIO.readSchoolWebCsv(fileName   = schoolCsvFile,   \
                                         schoolInfo = schoolInfo,      \
                                         siteName   = site,            \
                                         codeChar   = 0)
  schedIO.readStudentWebCsv (entriesList, studentCsvFile)
  
  if siteCount > 1:
    restrOutFile = os.path.join(jobFolder, 'restrSheet_' + site[:8] + '.csv')
  else:
    restrOutFile = os.path.join(jobFolder, 'restrSheet.csv')
    
  outFile      = open (restrOutFile, 'w', newline='')
  writer       = csv.writer (outFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
  
  writer.writerow(['regId', 'schoolId', 'SchoolName', 'catShort', 'catIdx',  'entryTitle', 'inContest', 'earliestStart', 'latestEnd','performers'])
  for entry in entriesList:          
    writer.writerow([entry['regId'],                             \
                     entry['schoolId'],                          \
                     schoolInfo[entry['schoolId']]['name'],      \
                     entry['catShort'],                          \
                     entry['catSchoolIdx'],                      \
                     entry['entryTitle'],                        \
                     'X',                                        \
                     '',                                         \
                     '',                                         \
                     ','.join(map(str,entry['performers'])) ])
  
  outFile.close()                  

