import logging
import os, re, time

#log = logging.getLogger(__name__)
#log.setLevel( logging.DEBUG )
#sh  = logging.StreamHandler()
#sh.setFormatter( logging.Formatter( '%(asctime)s [%(levelname)-4.4s] %(message)s' ) )
#sh.setLevel(logging.DEBUG)
#log.addHandler( sh )

SEASONEP = re.compile('[sS](\d{2,})[eE](\d{2,})')
isID     = lambda dbID: dbID[:4] == 'tvdb' or dbID[:4] == 'tmdb'        # If tvdb or tmdb in the first four (4) characters

freeform = lambda x: '----:com.apple.iTunes:{}'.format( x )                             # Functio

def encoder( val ):
  if isinstance(val, (tuple, list,)):
    return [i.encode() for i in val]
  elif isinstance( val, str ):
    return val.encode()
  else:
    return val

# A dictionary where keys are the starndard internal tags and values are MP4 tags
# If a value is a tuple, then the first element is the tag and the seoncd is the
# encoder function required to get the value to the correct format
COMMON2MP4 = {
  'year'       :  '\xa9day',
  'title'      :  '\xa9nam',
  'seriesName' :  'tvsh',
  'seasonNum'  : ('tvsn', lambda x: [x]),
  'episodeNum' : ('tves', lambda x: [x]),
  'genre'      :  '\xa9gen',
  'kind'       : ('stik', lambda x: [9] if x == 'movie' else [10]),
  'sPlot'      :  'desc',
  'lPlot'      : (freeform('LongDescription'),   encoder,),
  'rating'     : (freeform('ContentRating'),     encoder,),
  'prod'       : (freeform('Production Studio'), encoder,),
  'cast'       : (freeform('Actor'),             encoder,),
  'dir'        : (freeform('Director'),          encoder,),
  'wri'        : (freeform('Writer'),            encoder,),
  'comment'    : '\xa9cmt',
  'cover'      : 'covr'
}

MP42COMMON = {}
for key, val in COMMON2MP4.items():
  if isinstance(val, tuple):
    val = val[0]
  MP42COMMON[val] = key

# A dictionary where keys are the standard internal tags and values are MKV tags
# THe first value of each tuple is the level of the tag and the second is the tag name
# See: https://matroska.org/technical/specs/tagging/index.html
COMMON2MKV = {
  'year'       : (50, 'DATE_RELEASED'),
  'title'      : (50, 'TITLE'),
  'seriesName' : (70, 'TITLE'),
  'seasonNum'  : (60, 'PART_NUMBER'),
  'episodeNum' : (50, 'PART_NUMBER'),
  'genre'      : (50, 'GENRE'),
  'kind'       : (50, 'CONTENT_TYPE'),
  'sPlot'      : (50, 'SUMMARY'),
  'lPlot'      : (50, 'SYNOPSIS'),
  'rating'     : (50, 'LAW_RATING'),
  'prod'       : (50, 'PRODUCION_STUDIO'),
  'cast'       : (50, 'ACTOR'),
  'dir'        : (50, 'DIRECTOR'),
  'wri'        : (50, 'WRITTEN_BY'),
  'comment'    : (50, 'COMMENT'),
  'cover'      : 'covr'
}

MKV2COMMON = {}
for key, val in COMMON2MKV.items():
  MKV2COMMON[val] = key

from .API import BaseAPI, KEYS
from .Person import Person
from . import Movie
from . import Series
from . import Episode

###################################################################
class TMDb( BaseAPI ):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.__log = logging.getLogger(__name__)

  def search( self, title = None, episode = None, seasonEp = None, year = None, page = None ):
    params = {'query' : title}
    if page: params['page'] = page

    json = self._getJSON( self.TMDb_URLSearch, **params )
    if json:
      items = json['results']
      for i in range( len(items) ): 
        item = items.pop(0)
        if (item['media_type'] == 'movie'):
          item = Movie.TMDbMovie( data = item )
          self.__log.info( 'Found movie: {}'.format(item) )
        elif (item['media_type'] == 'tv'):
          item = Series( data = item )
          self.__log.info( 'Found series: {}'.format(item) )
        elif (item['media_type'] == 'person'):
          item = Person( data = item )
          self.__log.info( 'Found person: {}'.format(item) )
        else:
          continue
        items.append( item ) 
      return items
    return []
  
  #################################
  def byIMDb( self, IMDbID ):
    if (IMDbID[:2] != 'tt'): IMDbID = 'tt{}'.format(IMDbID)
    params = {'external_source' : 'imdb_id'}
    url  = self.TMDb_URLFind.format( IMDbID )
    json = self._getJSON( url, **params )
    if json:
      for key, val in json.items():
        for i in range( len(val) ): 
          item = val.pop(0)
          if (key == 'movie_results'):
            val.append( Movie.TMDbMovie( item['id'] ) ) 
          elif (key == 'person_resutls'):
            val.append( Person( item['id'] ) ) 
          elif (key == 'tv_results'):
            val.append( Series.TMDbSeries( item['id'] ) ) 
          elif (key == 'tv_episode_results'):
            val.append( Episode.TMDbEpisode( item['id'] ) ) 
          #elif (key == 'tv_season_results'):
          #  val.append( Season( item ) )
          else:
            pass
            #print(key) 
      return json
    return None 

###################################################################
class TVDb( BaseAPI ):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.__log = logging.getLogger(__name__)

  def search( self, title=None, episode=None, seasonEp=None, year=None, page=None, nresults=10 ):
    params = {'name' : title}
    if page: params['page'] = page

    json = self._getJSON( self.TVDb_URLSearch, **params )                               # Get JSON data from API
    if isinstance(json, dict) and 'data' in json:                                       # If json is dict and has data key
      items = json['data'][:nresults]                                                   # Take first nresults
      for i in range( len(items) ):                                                     # Iterate over all results
        item = items.pop(0)                                                             # Pope off item from items
        if ('seriesName' in item):                                                      # If key is in item
          item = Series.TVDbSeries( item['id'] )                                        # Create TVDbSeries instance
          if year is not None and item.air_date is not None:                            # If year input and air_date in series
            try:
              test = (item.air_date.year != year)
            except:
              test = False
            if test: continue
          if seasonEp:                                                                  # If seasonEp set
            item = Episode.TVDbEpisode( item, *seasonEp )                               # Create TVDbEpisode
          time.sleep(0.5)                                                               # Sleep for request limit
        if item.title is not None:                                                      # If item title is set
          items.append( item )                                                          # Append item to items list
      return items                                                                      # Return items
    return []                                                                           # Return empty list
  
  #################################
  def byIMDb( self, IMDbID, season=None, episode=None ):
    if (IMDbID[:2] != 'tt'): IMDbID = 'tt{}'.format(IMDbID)
    params = {'imdbId' : IMDbID}
    json = self._getJSON( self.TVDb_URLSearch, **params )
    if json:
      data = []
      for item in json.get('data', []):
        if season and episode:
          tmp = Episode.TVDbEpisode( item['id'], season, episode )
        else:
          tmp = Series.TVDbSeries( item['id'] )
        if tmp:
          data.append( tmp  )
      return data
    return None 

###################################################################
def getMetaData( file=None, dbID=None, seasonEp=(), version='', **kwargs ):
  '''
  Purpose:
    Function to get Movie or Episode object based on
    information from file name or dbID
  Inputs:
    None
  Keywords:
    file    : Full path, or base name of file to get
               information for. MUST match naming conventions
    dbID    : TVDb or TMDb to use for file; overrides any
                information parsed from file name
    seasonEP : Tuple or list containing season and episode number
    version : Version for movie; e.g., Extended Edition
  Returns:
    A TMDbMovie, TMDbEpisode, TVDbMovie, or TVDbEpisode object
  '''
  if file:
    fileDir, fileBase = os.path.split( file )
    seasonEp = SEASONEP.findall(fileBase)
  
    if not isinstance(dbID, str):                             # If dbID is NOT a string
      tmp = os.path.splitext(fileBase)[0].split('.')
      if isID(tmp[0]):                                        # If tvdb or tmdb in the first four (4) characters
        dbID    = tmp[0]                                      # Use first value as DB id
      elif len(seasonEp) == 1:                                # Else, if seasonEp was parsed from file name
        try:
          dbID = tmp[1]                                         # Assume second value is dbID
        except:
          dbID = ''
      else:                                                   # Else, assume is movie
        try:
          dbID = tmp[2]                                      # Assume third value is dbID
        except:
          dbID = ''
      if not version:
        try:
          version = tmp[1]                                      # Assume second value is version (Extended Edition, Director's Cut, etc.)
        except:
          version = ''
  elif dbID:
    if len(seasonEp) == 2:
      seasonEp = (seasonEp,)
    else:
      seasonEp = ()
  else:
    raise Exception('Must input file or dbID')

  if not isID( dbID ):
    return None

  if (dbID[:4] == 'tvdb'):
    if len(seasonEp) == 1:
      return Episode.TVDbEpisode( dbID, *seasonEp[0], **kwargs )
    else:
      return Movie.TVDbMovie( dbID, version=version, **kwargs )
  elif (dbID[:4] == 'tmdb'):
    if len(seasonEp) == 1:
      return Episode.TMDbEpisode( dbID, *seasonEp[0], **kwargs )
    else:
      return Movie.TMDbMovie( dbID, version=version, **kwargs )
  return None
