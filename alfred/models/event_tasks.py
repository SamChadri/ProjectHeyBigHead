from alfred.models.task import Task 
from alfred.mongodb.intent_data import IntentData
from alfred.models.api_models.search_api import SearchAPI
from alfred.models.api_models.sports_api import SportsAPI 
from alfred.models.api_models.wiki_api import WikiAPI 
from alfred.models.api_models.maps_api import MapsAPI 
from alfred.models.api_models.weather_api import WeatherAPI 
from alfred.models.api_models.movie_api import MovieAPI
from alfred.models.api_models.spotify_api import SpotifyAPI, BearerToken
from alfred.models.api_models.calendar_api import GoogleCalendarAPI


from azure.cognitiveservices.search.websearch import WebSearchClient
from azure.cognitiveservices.search.websearch.models import SafeSearch
from msrest.authentication import CognitiveServicesCredentials

import logging 
import asyncio
from alfred.mongodb.intent_data import IntentData
TAG = 'EventTasks: '
#TODO: Filter out for N/A in response message
#TODO: Implement device authentication/checker. Something like that
#TODO: Write Factory function here maybe later
class QueryTask(Task):

    GOOGLE_ENGINE = 0
    BING_ENGINE = 1

    def __init__(self, message):
        super().__init__(message)
        self.api = SearchAPI()
        self.intent_data = IntentData()
    

    #TODO: Add in functionality for 
    def action(self):
        if self.intent_data.web_query_entity in self.message.entities:
            entity = self.message.entities[self.intent_data.web_query_entity]
            """
            Implement later when differentiating between slots
            if self.message.check_entity_slot(entity):
                pass
            else:
                pass
            """
            self.result = self.api.search_request(entity)
        else:
            self.result = self.api.search_request(self.message.msg)   
        

    def response(self):
        return {'message' : self.response_message, 'result' : self.result, 'intent': self.message.intent, 'id': self.id}


class SportsTask(Task):

    #TODO Put the responses in mongodb?
    def __init__(self,message):
        super().__init__(message)
        self.response_message = 'The {} defeated the {}. '
        self.score = 'The final score was {} to {}.'
        self.api = SportsAPI()
        self.intent_data = IntentData()


    def action(self):
        if self.intent_data.team_entity in self.message.entities and self.intent_data.event_entity in self.message.entities:
            team_entity = self.message.entities[self.intent_data.team_entity]
            if "'" in team_entity:
                logging.debug("Stripping {}....".format(self.message.entities["team"]))
                team_entity = team_entity.replace("'", '')
                logging.debug("Stripped entites: {}".format(self.message.entities))
            
            
            self.api.set_league(team_entity)
            #TODO: Add functionality for Dates on games later
            self.result = self.api.last_game(team_entity)

        else:
            self.result = {'error': 'Query type could not be found'}



    def response(self):

        if 'error' not in self.result and self.result != None:                
            sports_response = ''
            home_team = self.result['home_team']
            away_team = self.result['away_team']

            if self.result['home_score'] != None and self.result['away_score'] != None:
                home_score = int(self.result['home_score'].strip())
                away_score = int(self.result['away_score'].strip())


                if home_score > away_score:
                    winner = home_team
                    loser = away_team
                    self.response_message = self.response_message.format(home_team, away_team)
                    self.score = self.score.format(home_score, away_score)
                else:
                    winner = away_team
                    loser = home_team
                    self.response_message = self.response_message.format(away_team, home_team)
                    self.score = self.score.format(away_score, home_score)

                self.response_message = self.response_message + self.score
                return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id} 
            else:
                self.response_message = 'This is what I got'
                return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}

            

        
        else:
            self.response_message = 'Looks like something went wrong. Please try again'
            return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
            

    

class EntertainmentTask(Task):

    def __init__(self,message):
        super().__init__(message)
        self.api = MovieAPI()
        self.more_det = False
        self.response_message = "Here's what I found"
        self.intent_data = IntentData()

    def set_movie(self, movie_id, movie):
        self.movie = movie
        self.movie_id = movie_id

    def set_tv(self, tv_id, tv):
        self.tv = tv
        self.tv_id = tv_id

    def action(self):
        if self.intent_data.title_entity in self.message.entities:
            title_entity = self.message.entities[self.intent_data.title_entity]
            self.result = self.api.get_title(title_entity)

            #TODO Implement the full more details function 
            #self.result = self.api.get_query_results(self.message.entities['title_query'])
            #self.more_det = True

        elif 'movie_query' in self.message.entities and self.more_det == False:
            self.result = self.api.get_movie(self.movie_id, self.movie)
        
        elif 'tv_query' in self.message.entities and self.more_det == False:
            self.result = self.api.get_movie(self.tv_id, self.tv)
        
        else:
            self.result = {'error': 'Query type could not be found'}
    
    def parse_ent_type(self, values):
        retval = ''
        val_len = len(values)
        if val_len == 1:
            retval = values[0].strip()
        elif val_len == 2:
            retval = f'{values[0].strip()} and {values[1].strip()}'
        elif val_len > 2:
            for val in values:
                if values.index(val) == 0:
                    retval += val.strip()
                elif values.index(val) == (val_len - 1):
                    retval += ', and ' + val.strip() + '.'
                else:
                    retval += ', ' + val.strip()
        
        else:
            retval = 'NA'
        
        return retval

    def response(self):
        if self.more_det:
            return {'message' : self.response_message,  'result': self.result, 'intent': self.message.intent, 'id': self.id}

        elif 'error' not in self.result and self.result != None:
            if self.message.entities['ent_type'] == 'cast':
                #TODO create seperate function that can clean the entries of extra spaces. Or maybe do it in the api itself.
                if self.result['source'] == 'omdb':
                    cast = self.parse_ent_type(self.result['title_cast'])
                    if cast != 'NA':
                        self.response_message = "{} stars {}".format(self.result['title_name'], cast)
                    else:
                        self.response_message = "Sorry I couldn't find the cast. However, this is what I found."
                
                    return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}

                else:
                    return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
                    #TODO implement backup

            elif self.message.entities['ent_type'] == 'director':

                if self.result['source'] == 'omdb':
                    directors = self.parse_ent_type(self.result['title_directors'])
                    if directors != 'NA':
                        self.response_message = "{} is directed by {}".format(self.result['title_name'], directors)
                    else:
                        self.response_message = "Sorry I coudln't find the director. However, this is what I found"
                        
                    return {'message': self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}

                else:
                    return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}


            elif self.message.entities['ent_type'] == 'rating':

                if self.result['source'] == 'omdb':
                    rating = self.result['title_rating']

                    self.response_message = "{} is rated {}".format(self.result['title_name'], rating)

                    return {'message': self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}

                else:
                    return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}


            elif self.message.entities['ent_type'] == 'genre':
                
                
                if self.result['source'] == 'omdb':
                    genres = self.parse_ent_type(self.result['title_genres'])
                    genres_len = len(self.result['title_genres'])
                    if genres != 'NA':
                        self.response_message = "{} has {} genres. {}".format(self.result['title_name'], genres_len, genres)
                    else:
                        self.response_message = "Sorry I couldn't find the director. However, here is what I found."

                    return {'message': self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
                else:
                    return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}

            else:
                return {'message' : self.response_message, 'result':self.result, 'intent': self.message.intent, 'id': self.id}

        else:
            self.response_message = 'Looks like something went wrong. Please try again'
            return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}



class WikiTask(Task):

    def __init__(self, message):
        super().__init__(message)
        self.api = WikiAPI()
        self.intent_data = IntentData()


    def action(self):
        #TODO Find a way to diferentiate information from celebs and regular wiki posts
        if self.intent_data.celeb_entity in self.message.entities:
            celeb_entity = self.message.entities[self.intent_data.celeb_entity]
            self.result = self.api.get_celeberty(celeb_entity)
        
        elif self.intent_data.wiki_entity in self.message.entities:
            wiki_entity = self.message.entities[self.intent_data.wiki_entity]
            self.result = self.api.search_wiki(wiki_entity)
        
        else:
            self.result = {'error': 'Query type could not be found'}


    def response(self):
        if 'error' not in self.result and self.result != None:
            #TODO Handle edge case for Jr. and Sr. in the first sentence
            description = self.result['extract'].split('.')[0]
            self.response_message = description
            return {'message': self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
        else:
            self.response_message = 'Looks like something went wrong. Please try again'
            return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id} 




class MapTask(Task):

    def __init__(self, message):
        super().__init__(message)
        self.api = MapsAPI()
        self.intent_data = IntentData()

    def action(self):
        if self.intent_data.location_entity in self.message.entities:
            location_entity = self.message.entities[self.intent_data.location_entity]
            self.result = self.api.search_location(location_entity)

        elif 'direction_query' in self.message.entities:
            
            self.result = self.api.search_location(self.message.entities['direction_query'])

        elif 'origin_query' in self.message.entities and 'destination_query' in self.message.entities:
            """TODO: Deal with merging the queries later"""

            self.result = self.api.get_directions(self.message.entities['origin_query'], self.message.entities['destination_query'])

        else:
           self.result = {'error': 'Query type could not be found'}

    
    def response(self):
        if 'error' not in self.result and self.result != None:
            return {'message': self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}

        else:
            self.response_message = 'Looks like something went wrong. Please try again'
            return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}


class WeatherTask(Task):
    #TODO: Update message to include the current temp.
    def __init__(self,message):
        super().__init__(message)
        self.api = WeatherAPI()
        self.response_message = "Here's the weather"
        self.intent_data = IntentData()
        if self.intent_data.weather_entity in self.message.entities:
            self.location = message.entities[self.intent_data.weather_entity]
            self.is_city = (not message.entities['weather_location'].isdigit())

        else:
            self.location = '60304'
            self.is_city = False



    def action(self):
        if self.location != None and self.is_city != None:
            self.result = self.api.get_forecast(self.location, self.is_city)

        else:
            self.result = {'error': 'Query type could not be found'}

    
    def response(self):
        if 'error' not in self.result and self.result != None:
            return {'message': self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}

        else:
            self.response_message = 'Looks like something went wrong. Please try again'
            return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}


class ConversationTask(Task):

    def __init__(self, message):
        super().__init__(message)
        self.message = message
        self.intent_data = IntentData()
        self.result = None

    def response(self):
        if self.message.intent == self.intent_data.hello_intent:
            self.response_message = "Hey, how's it going?"
        elif self.message.intent == self.intent_data.hay_intent:
            self.response_message = "I'm alright, thanks for asking"
        else:
            self.response_message = "See you later"
        return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}



class SpotifyTask(Task):

    def __init__(self, message):
        super().__init__(message)
        if not SpotifyAPI.is_init():
            SpotifyAPI.factory()

        #TODO Add case for when a device instance is being used.
        self.api = SpotifyAPI.acquire(self.message.device_id)
        logging.debug(TAG + 'SpotifyTask Created')
        print(TAG + 'SpotifyTask Created')
        self.response_message = 'Opening Spotfiy'
    

    def action(self):
        if 'player_query' in self.message.entities:
            logging.info(TAG + 'SpotifyTask - Player Query...')
            print(TAG + 'SpotifyTask - Player Query...')
            if 'track_query' in self.message.entities and 'artist_query' in self.message.entities:
                track_query = self.message.entities['track_query']
                artist_query = self.message.entities['artist_query']
                query_string = f'{track_query} artist:{artist_query}' 
                type_query = 'track,album'

                track_uri = self.api.spotify_search(query_string, type_query)
                if type(track_uri) == dict:
                    self.result = track_uri 
                    return 

                self.result = self.api.spotify_request(self.message.intent, self.message.entities['player_query'], track_uri=track_uri)

            elif 'artist_query' in self.message.entities and 'type_query' in self.message.entities:
                artist_query = self.message.entities['artist_query']
                type_query = self.message.entities['type_query']
                query_string = f'artist:{artist_query}'

                track_uri = self.api.spotify_search(query_string, type_query)
                if type(track_uri) == dict:
                    self.result = track_uri 
                    return 

                self.result = self.api.spotify_request(self.message.intent, self.message.entities['player_query'], track_uri=track_uri)

            elif 'track_query' in self.message.entities:
                track_query = self.message.entities['track_query']
                query_string = f'{track_query}' 
                type_query = 'track,album'

                track_uri = self.api.spotify_search(query_string, type_query)
                if type(track_uri) == dict:
                    self.result = track_uri 
                    return 

                self.result = self.api.spotify_request(self.message.intent, self.message.entities['player_query'], track_uri=track_uri)

            elif 'artist_query' in self.message.entities:
                artist_query = self.message.entities['artist_query']
                query_string = f'artist:{artist_query}'
                query_type = 'track,album'

                track_uri = self.api.spotify_search(query_string, query_type)
                if type(track_uri) == dict:
                    self.result = track_uri 
                    return 

                self.result = self.api.spotify_request(self.message.intent, self.message.entities['player_query'], track_uri=track_uri)

            elif 'playlist_query' in self.message.entities:

                playlist_query = self.message.entities['playlist_query']
                playlist_uri = self.api.spotify_playlists(playlist_query)

                if type(playlist_uri) == dict:
                    self.result = playlist_uri
                    return

                self.result = self.api.spotify_request(self.message.intent, self.message.entities['player_query'], track_uri=playlist_uri)

            else:
                self.result = self.api.spotify_request(self.message.intent, self.message.entities['player_query'])

        elif 'volume_query' in self.message.entities:
            self.result = self.api.spotify_request(self.message.intent, volume_level=self.message.entities['volume_query'])

        elif 'skip_query' in self.message.entities:
            self.result = self.api.spotify_request(self.message.intent, self.message.entities['skip_query'])

        else:
            self.result = {'error' : 'Not yet implemented'}
        
        SpotifyAPI.release(self.message.device_id, self.api)


    def response(self):
        if 'error' in self.result or self.result == None:
            self.response_message = 'Looks like something went wrong. Please try again'
            return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
        else:
            #TODO make it nothing for now. But eventually add  in support maybe for telling user what action is being proccessed. However, 
            self.response_message = f'Playing {self.api.result_name}'
            return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
             


class CalendarTask(Task):

    CREATE_QUERY = "CREATE"
    WHERE_QUERY = "WHERE"
    WHEN_QUERY = "WHEN"
    UPDATE_QUERY = "UDPATE"
    CANCEL_QUERY = "CANCEL"
    GET_QUERY = "GET"
    

    def __init__(self, message):
        super().__init__(message)
        #TODO Add case for when a device instance is being used.
        if not GoogleCalendarAPI.is_init():
            GoogleCalendarAPI.factory()

        self.api = GoogleCalendarAPI.acquire(self.message.device_id)




    
    def action(self):
        if 'calendar_query' in self.message.entities:
            query = self.message.entities['calendar_query']
            print(f'Calendar query in entities {query}')
            if query.lower() == 'Add'.lower() or query.lower() == 'Schedule'.lower():
                print('Add command found')
                self.result = self.api.create_event(**self.message.entities)
                self.query = self.CREATE_QUERY
            elif query.lower() == 'where is' or query.lower() == "where's":
                self.result = self.api.get_events(**self.message.entities)
                self.query = self.WHERE_QUERY
                #TODO  add instance variable to determine the type of calendar_query
                #TODO (handle in response) get location out of the result from api

            elif query.lower() == 'when is' or query.lower() == "when's":
                self.result = self.api.get_events(**self.message.entities)
                self.query = self.WHEN_QUERY
                #TODO  add instance variable to determine the type of calendar_query
                #TODO (handle in response) get the time out of the result from api call
                pass

            elif query.lower() == 'what is' or query.lower() == "what's":
                self.result = self.api.get_events(**self.message.entities)
                self.query = self.GET_QUERY
                pass

            elif query.lower() == 'update' or query.lower() == 'reschedule':
                self.result = self.api.update_event(**self.message.entities)
                self.query = self.UPDATE_QUERY

            elif query.lower() == 'cancel':
                self.result = self.api.delete_event(**self.message.entities)
                self.query = self.CANCEL_QUERY
            else:
                pass
        else:
            self.result = {'error' : 'Not yet implemented'}

        GoogleCalendarAPI.release(self.message.device_id, self.api)

    def response(self):

        if self.result == None or 'error' in self.result:
            self.response_message = "Looks like something went wrong please try again"
            return {'message': self.message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}

        else:
            #TODO update keys for batch results to use init_query for response messages
            if self.query == self.CREATE_QUERY:
                self.response_message = "A google calendar {} has been created on {} at {}"
                event_type = self.result['event_type']
                event_date = self.result['start_date'].strftime("%B %d, %Y")
                event_time = self.result['start_date'].strftime("%I:%M")

                self.result['start_date'] = str(self.result['start_date'])
                self.result['end_date'] = str(self.result['end_date'])

                self.response_message = self.response_message.format(event_type,event_date, event_time)
                return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}

            elif self.query == self.WHEN_QUERY:
                self.response_message= "Your next google calendar {} is on {} at {}"
                event_type = self.result['event_type']
                event_date = self.result['init_query_time'].strftime("%B %d, %Y")
                event_time = self.result['init_query_time'].strftime("%I:%M")
                self.response_message = self.response_message.format(event_type,event_date, event_time)
                return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
            elif self.query == self.UPDATE_QUERY:
                self.response_message = "Your google calendar event {} has been updated to {}".format(self.result['calendar_param'], self.result['calendar_update'])
                return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
            elif self.query == self.GET_QUERY:
                self.response_message = "Your next google calendar {} is on {}"
                event_type = self.result['event_type']
                event_date = self.result['init_query_time'].strftime("%B %d, %Y")
                self.response_message = self.response_message.format(event_type, event_date)
                return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
            elif self.query == self.WHERE_QUERY:
                self.response_message = "Your next google calendar {} is at {}"
                event_location = self.result['init_query_location']
                event_type = self.result['event_type']
                self.response_message = self.response_message.format(event_type, event_location)
                return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
            elif self.query == self.CANCEL_QUERY:
                self.response_message = "Your google calendar {} on {} has been canceled"
                event_type = self.result['init_query_event_type']
                event_date = self.result['init_query_start_date'].strftime("%B %d, %Y")
                self.response_message = self.response_message.format(event_type,event_date)
                return {'message' : self.response_message, 'result': self.result, 'intent': self.message.intent, 'id': self.id}
            else:
                #TODO Implement later
                pass


