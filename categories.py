class Categories:

   def __init__(self, groupOrSingle):
      if groupOrSingle == 'group':
         print("GROUP")
         self.catLong =                                                         \
              ["OneActPlay","ReadersTheatre", "ChoralReading", "TVNewscasting", \
               "RadioBroadcasting", "ShortFilm", "MusicalTheatre",              \
               "GroupImprovisation", "EnsembleActing", "GroupMime", "SoloMime"]

         self.catShort =                                                        \
              ['OA','RT','CR','TV', 'RB','SF','MT','GI', 'EA', 'GM', 'SM']

         self.schoolRegLists =                                       \
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

         self.studentCsvFields =                         \
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

      else:
         print("INDIVIDUAL")
         self.catLong =                                                              \
              ['PublicAddress', 'SoloMusicalTheatre', 'Acting', 'ReadingPoetry',     \
               'ReadingProse', 'LiteraryProgram', 'OriginalOratory',                 \
               'SpontaneousSpeaking', 'RadioNews', 'ExpositoryAddress',              \
               'Storytelling', 'AfterDinner', 'Improvisation', 'Reviewing'] 
                    
         self.catShort =                                                             \
              ['PA','SMT','ACT','PO','PR','LP','OO','SS','RN','EA','ST','AD','IMP','RV']
         '''
         self.schoolRegLists =                                       \ #Not used in indiv
         [                                                           \
           ['PA1','PA2','PA3'                                        \
           ['SMT1','SMT2','SMT3'],                                   \
           ['ACT1','ACT2','ACT3','ACT4','ACT5','ACT6],               \
           ['PO1','PO2','PO2'],                                      \
           ['PR1','PR2','PR3'],                                      \
           ['LP1','LP2','LP3'],                                      \
           ['OO1','OO2','OO3'],                                      \
           [
         '''
         self.studentCsvFields =                         \
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
      #endif

      self.shortToLongMap = dict(zip(self.catShort, self.catLong))
      self.longToShortMap = dict(zip(self.catLong, self.catShort))
   #end __init__

   def longList (self):
      return self.catLong;

   def shortList (self):
      return self.catShort;

   def schoolRegMap (self):
      return dict( zip(self.catLong, self.schoolRegLists) )

   def studentRegFields (self):
      return self.studentCsvFields;

   def longToShort (self, longName):
      return self.longToShortMap[longName]

   def shortToLong (self, shortName):
      return self.shortToLongMap[shortName]

   def count (self):
      return len(self.catShort)

   def countDict (self):
      return dict( zip(self.catShort, [0] * len(self.catShort) ) )


