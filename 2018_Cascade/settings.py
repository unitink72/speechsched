#Notes
# Check #3 isn't as important as #1.  However for #1, the big schools pretty
# much expect to be there all day.  Its important for the small schools not to
# get stuck there all day.  For large group sm=5 entries, med=6-8, lg=8+
#Possible idea is use percentage.  50%sm 25%med 25%lg


###############################################################################
##    Conetest Settings
############################################################### ################
#Master student.csv and school.csv files dumped from IHSSA website
MASTER_FILE_PATH = '2018Master'

#Used for drive time lookup. Use Column A from SchoolsExport.csv
HOST_SCHOOL_ID = 473 #Cascade

#List of sitenames for this contest.  Will only be 1 for district contests,
# four for state contests.  Must match case EXACTLY from registration data.
CONTEST_SITENAME = ['Cascade']

#Is this a Large Group or Individual Speech contest. 'Group' or 'Indiv'
CONTEST_TYPE = 'Group'

#School codes can either be 3-digit numbers or 2 letters. 0=Numbers, 1=Letters
SCHOOL_CODE_CHARS = 0

###############################################################################
##    Fitness Function Settings
###############################################################################
#These constants define how many points are docked when the fitness function
#finds less than ideal or impossible schedules.
PTS_PER_MINUTE_SCHOOL_LEAVES_BEFORE_7AM = 10

#Schools over this length of drive in minutes are checked for shorter span
#from first to last performance
MIN_DRIVING_TIME_PERF_SPAN_CHECK = 90

#Average amount of time a remote school should have its performances scheduled at.
#Exceeding this(on average) will trigger the remote school penalty.
LONG_PERFORMANCE_SPAN_AVG = 50

#Points docked when span is over entry count * LONG_PERFORMANCE_SPAN_AVG
LONG_PERFORMANCE_SPAN_PENALTY = 250

#3
#If a school has more than this many entries, do not check for 2 performances
#scheduled at the same time
MAX_ENTRIES_FOR_CONFLICT_CHECKING = 12
CONFLICT_PENALTY = 1000

#4
TWO_SCHOOL_ENTRIES_HAVE_SAME_JUDGES_PENALTY = 2000

#5
BROKEN_RESTRICTION_PENALTY     = 6000
RESTRICTION_PER_MINUTE_PENALTY = 10

#6
#Dock big time when a kid is scheduled for two performances at once
STUDENT_SCHEDULE_TIME_CONFLICT = 5000
#A little less hit if they are between 10 and 30 minutes apart
STUDENT_SCHEDULE_CONFLICT_PER_MIN = 100


###############################################################################
##   Execution Settings
###############################################################################
DISPLAY_BEST_SCORE_SECS   = 120
BEST_SCORE_PRINT_MINS     = 5

STAGE_1_ARRAY_SIZE        = 20    #10
STAGE_1_MINUTES_PER_FLUSH = 10
STAGE_1_HOURS             = 10   #7
STAGE_2_HOURS             = 0.5  #1

###############################################################################
##   Internet Settings
###############################################################################
#http_proxy = {'http': 'http://usproxy.rockwellcollins.com:9090/'}
http_proxy = None
