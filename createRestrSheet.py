import csv
import os, sys
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
schoolInfo       = schedIO.readSchoolsExport(schoolExportFile)

siteCount        = len(config['CONTEST_SITENAME'])

for site in config['CONTEST_SITENAME']:
  
  entriesList = schedIO.readSchoolWebCsv(schoolCsvFile, schoolInfo, site)
  
  if siteCount > 1:
    restrOutFile = os.path.join(jobFolder, 'restrSheet_' + site[:8] + '.csv')
  else:
    restrOutFile = os.path.join(jobFolder, 'restrSheet.csv')
    
  outFile      = open (restrOutFile, 'w', newline='')
  writer       = csv.writer (outFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
  
  writer.writerow(['regId', 'schoolId', 'SchoolName', 'catShort', 'catIdx',  'entryTitle', 'inContest', 'earliestStart', 'latestEnd'])
  for entry in entriesList:          
    writer.writerow([entry['regId'],                             \
                     entry['schoolId'],                          \
                     schoolInfo[entry['schoolId']]['name'],      \
                     entry['catShort'],                          \
                     entry['catSchoolIdx'],                      \
                     entry['entryTitle'],                        \
                     'X' ])
  
  outFile.close()                  

