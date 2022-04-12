import pymongo
from .intent_data import IntentData
import os 
import logging
from datetime import datetime
from alfred.mongodb.api_store import APIStore

curr_dir = os.path.curdir
TAG = 'IntentStore:: '
class IntentStore:



    def __init__(self):
        logging.debug(TAG + 'Initializing IntentStore()...')
        self.class_init()
        self.init_db()


    @classmethod
    def class_init(cls):
        logging.basicConfig(filename='alfred.log', level=logging.INFO)
        now = datetime.now().time()
        current_time = now.strftime("%m/%d/%Y, %H:%M:%S")

        logging.info('Run DateTime: ' + current_time)
        cls.intent_constants = IntentData()
        mongo_client = pymongo.MongoClient(os.environ['MONGO_IP'])
        cls.intent_db = mongo_client["intent_database"]
        cls.intent_config = mongo_client["config"]["intent_db"]
        cls.salutation_intents = cls.intent_db["salutation_intents"]
        cls.search_intents = cls.intent_db["search_intents"]
        cls.sports_intents = cls.intent_db["sports_intents"]
        cls.wiki_intents = cls.intent_db["wiki_intents"]
        cls.map_intents = cls.intent_db["map_intents"]
        cls.ent_intents = cls.intent_db["entertainment_intents"]
        cls.weather_intents = cls.intent_db["weather_intents"]
        cls.time_intents = cls.intent_db["time_intents"]
        cls.spotify_intents = cls.intent_db['spotify_intents']
        cls.calendar_intents = cls.intent_db['calendar_intents']
        cls.api_store = APIStore()
       
        #TODO Add calendar intents


    @classmethod
    def insert_intent(cls, intent, intent_values, cached=False):

        entry = {
            "intent" : intent,
            "intent_values" : intent_values,
            "cached" : cached
        }
        #print(salutation)
        db_name = cls.intent_constants.get_intent_db(intent)
        retval  = cls.intent_db[db_name].insert_one(entry)
        return retval
        
    
    @classmethod
    def add_intent_value(cls, intent_value, intent):
        param = {}
        
        param["intent"] = intent
        new_val = {"$push" :{"intent_values": intent_value}}

        db_name = cls.intent_constants.get_intent_db(intent)
        retval = cls.intent_db[db_name].update_one(param, new_val)
        return retval.modified_count


    @classmethod
    def get_intent_values(cls, intent):
        param = {}

        
        param["intent"] = intent
        db_name = cls.intent_constants.get_intent_db(intent)
        #print("db_name: " + db_name)
        #print("intent: "+ intent)
        return cls.intent_db[db_name].find_one(param)


    @classmethod
    def insert_entity(cls, entity, entity_values, cached=False):
        entry= {
            "entity": entity,
            "entity_values" : entity_values,
            "cached": cached
        }

        db_name = cls.intent_constants.get_entity_db(entity)
        return  cls.intent_db[db_name].insert_one(entry)

    @classmethod
    def add_entity_value(cls, entity, entity_value):
        param = {}

        param["entity"] = entity
        new_val = {"$push" :{"entity_values": entity_value}}
        db_name = cls.intent_constants.get_entity_db(entity)

        retval = cls.intent_db[db_name].update_one(param, new_val)
        return retval.modified_count

    @classmethod
    def set_intent_cached(cls, intent, cached):
        param = {}
        param["intent"] = intent

        new_val = {"$set" :{"cached": cached}}
        db_name = cls.intent_constants.get_intent_db(intent)

        retval = cls.intent_db[db_name].update_one(param, new_val)
        return retval.modified_count

    @classmethod
    def set_entity_cached(cls, entity, cached):
        param = {}
        param["entity"] = entity


        db_name = cls.intent_constants.get_entity_db(entity)
        new_val = {"$set" :{"cached": cached}}
        
        retval = cls.intent_db[db_name].update_one(param, new_val)
        return retval.modified_count

    @classmethod
    def get_entity_values(cls, entity):
        param = {}
        param["entity"] = entity 

        db_name = cls.intent_constants.get_entity_db(entity)
        #print('db_name: ' + db_name)
        #print('entity: ' + entity)
        return cls.intent_db[db_name].find_one(param)

    @classmethod
    def check_db(cls):
        param = {"initialized": True}

        result =  cls.intent_config.find_one(param) 
        return (result != None)

    @classmethod
    def init_db(cls):
        if not cls.check_db():
            logging.info(TAG + "Intent database not initialized")
            cls.populate_db()
            cls.api_store.init_database()
        else:
            logging.info(TAG + "Intent database already intitialized")

    @classmethod
    def load_teams(cls, file=os.path.abspath('alfred/data/team_list.txt')):
        team_list = []
        with open(file, 'r') as f:
            teams = f.readlines()
            for team in teams:
                team = team.strip('\n')
                team_list.append(team)

        return team_list

    #TODO Implement for flexibility for location_query entity.
    #TODO Update intents for addresses for origin and destination query.
    #TODO UPdate Direction flexibility for street names.
    @classmethod
    def populate_db(cls):
        logging.info(TAG + "Populating Database...")
        greeting_intents =  [
            {
                "intent": cls.intent_constants.hello_intent,
                "intent_values": ["Hello", "Hi there", "Hey", "Howdy", "Hey, what's up"],
                "cached" : False
            },
            {
                "intent": cls.intent_constants.bye_intent,
                "intent_values": ["See You", "Bye", "Goodbye", "bye-bye", "See you later" ],
                "cached": False
            },
            {
                "intent" : cls.intent_constants.hay_intent,
                "intent_values": ["how are you", "how's it going", "what's up", "what's happening", "what's going on"],
                "cached": False
            }
        ]
        cls.salutation_intents.insert_many(greeting_intents)

        #TODO: Create a script for adding in entites for search queries
        search_intent = {
            "intent": cls.intent_constants.query_intent,
            "intent_values": ["Show me {recipeType} recipes", "Search the web for {query} " , "Find pictures of {query}", "Google {query}", "Bing {query}", "Search for {query}" ],
            "cached": False
        }
        cls.search_intents.insert_one(search_intent)

        sports_intent = {
            "intent" : cls.intent_constants.sports_intent,
            "intent_values" : ["(Who won|What was the final score of| Who was the winner of| What was the score of) the {event_type} {team} game", "What was the final score of the {event_type} game", "What was the score of the {event_type} {game}",
             "Did the {team} win","How did {team} do {event_type}"],
             "cached": False
        }
        cls.sports_intents.insert_one(sports_intent)

        team_list = cls.load_teams()
        sports_entities = [
            {
                "entity" : cls.intent_constants.event_entity,
                "entity_values" : ["last", "most recent", "last night's", "latest", "past", "most current"],
                "cached" : False
                    
            },

            {
                "entity" : cls.intent_constants.team_entity,
                "entity_values": team_list,
                "cached": False
            }
        ]
        cls.sports_intents.insert_many(sports_entities)



        knowledge_intent = {
            "intent" : cls.intent_constants.wiki_intent,
            "intent_values": ["What is a {wiki_query}", "What is {wiki_query}", " What is an {wiki_query}", "Tell me more about {wiki_query}", "Tell me about {wiki_query}", "What's a {wiki_query}",
            "Show me what a {wiki_query} is", "Display a {wiki_query} for me", "What's an {wiki_query}"],
            "cached" : False
        }

        knowledge_entity = {
            "entity" : cls.intent_constants.wiki_entity,
            "entity_values" : [":0", " :0 :0", ":0 :0 :0"],
            "cached" : False
        }

        celeb_intent = {
            "intent" : cls.intent_constants.celeb_intent,
            "intent_values": ["Who is {celeb_query}", "Show me information about {celeb_query}", "Pull up information about {celeb_query}"],
            "cached" : False
        }

        celeb_entity = {
            "entity" : cls.intent_constants.celeb_entity,
            "entity_values" : [":0", ":0 :0"],
            "cached" : False
        }
        cls.wiki_intents.insert_many([knowledge_entity, knowledge_intent, celeb_intent, celeb_entity])


        entertainment_intent = {
            "intent" : cls.intent_constants.entertainment_intent,
            "intent_values" : ["What is the {ent_type} of {title_query} ", "{ent_type} {title_query}", "Tell me the {ent_type} of {title_query}",
            "What's the {ent_type} of {title_query}", "Show me the {ent_type} of {title_query}", "Who is the {ent_type} of {title_query}", "Who are the {ent_type} of {title_query}",
            "Who {ent_type} {title_query}"],
            "cached" : False 
        }
        #TODO Check how many words we can match
        title_entities = {
            "entity" : cls.intent_constants.title_entity,
            "entity_values" : [':0', ':0 :0', ':0 :0 :0' , ':0 :0 :0 :0'],
            "cached" : False
        }
        entertainment_entities = {
            "entity" : cls.intent_constants.ent_entity,
            "entity_values": ["rating", "director", "cast", "plot", "synopsis", "genre",],
            "cached" : False
        }

        cls.ent_intents.insert_many([entertainment_intent, entertainment_entities, title_entities])

        weather_intent = {
            "intent" : cls.intent_constants.weather_intent,
            "intent_values": ["What's the weather like", "(What is|How is|What's) the (temperature|weather) in {weather_location}", "What is temperature outside",
             "What's the weather today", "What is the weather today", "What is the forecast today" ,"How is the temperature outside",
            "(What's|What is) the weather like in {weather_location}"],
            "cached" : False
        }

        weather_entity = {
            "entity" : cls.intent_constants.weather_entity,
            "entity_values": ["#####", ":0 :0 City", ":0 :0", ":0", ":0 City"],
            "cached" : False
        }
        cls.weather_intents.insert_many([weather_intent, weather_entity])

        time_intent = {
            "intent" : cls.intent_constants.time_intent,
            "intent_values" : ["What time is it", "What time is it in {place}", "When is sunrise", "When is sunset", "When is sunrise"],
            "cached": False
        }
        cls.time_intents.insert_one(time_intent)

        map_intent = {
            "intent": cls.intent_constants.map_intent,
            "intent_values" : ["What's a good {location_query} restaurant near me", "What's the best {location_query} near me", 
            "What's the trafic like to {direction_query}", "Take me to {direction_query}", "Where is the nearest {location_query}",
            "Give me directions to {direction_query}", "Get me directions to {direction_query}", "Give me directions from {origin_query} to {destination_query}",
            "Show me {location_query}","Get me directions to the nearest {direction_query}","Give me directions to the nearest {direction_query}",
            "(Get me | Find me | Show me | Give me | Find me | Can you get me) directions to the nearest {direction_query}", "(Get me | Find me | Show me | Give me | Find me | Can you get me) directions from {origin_query} to {destination_query}"],
            "cached": False
        }

        location_entity = {
            "entity" : cls.intent_constants.location_entity,
            "entity_values": [":0", ":0 :0"],
            "cached" : False
        }

        origin_entity = {
            "entity" : cls.intent_constants.origin_entity,
            "entity_values": ["(#|##|###|####) :0 (Street|Avenue), ", ":0 :0 City", ":0 :0", ":0", ":0 City"],
            "cached": False
        }

        destination_entity = {
            "entity" : cls.intent_constants.dest_entity,
            "entity_values": ["(#|##|###|####) :0 (Street|Avenue), ", ":0 :0 City", ":0 :0", ":0", ":0 City"],
            "cached" : False
        }

        direction_entity = {
            "entity" : cls.intent_constants.direction_entity,
            "entity_values" : ["### :0 (Street|Avenue)", ":0 :0 City", ":0 :0", ":0"],
            "cached": False
        }
        cls.map_intents.insert_many([map_intent, location_entity, direction_entity, origin_entity, destination_entity])
        init_db = {
            "initialized": True
        }
        cls.intent_config.insert_one(init_db)

        #TODO Split these into subIntents
        #TODO Introduce subintent into any db that might have more than one intent.
        #TODO 
        spotify_player_intent = {
            'intent':  cls.intent_constants.spotify_player_intent,
            'db_intent': cls.intent_constants.spotify_intent,
            'intent_values' : [
                '{player_query} this song',
                '{player_query} the current song',
                '(Get the |Toggle |){player_query} (for the|the) current session',
                '(Get the |Toggle |){player_query} (for the|the) current playback',
                'Set the volume to {volume_query}',
                '{player_query} my {playlist_query}',
                '{player_query} my {playlist_query} playlist',
                '{player_query} some {artist_query}',
                'Play the {skip_query} song',
                '{player_query} {track_query}',
                '{player_query} {track_query} by {artist_query}',
                "{player_query} {artist_query}'s latest {type_query}"
            ],
            'cached': False
        }


        player_entity = {
            'entity' : cls.intent_constants.player_entity,
            'entity_values': [
                'play',
                'start',
                'resume',
                'pause',
                'skip',
                'queue',
                'repeat',
                'shuffle',
                'repeat',
                'transfer',
            ],
            'cached' : False
        }
        #TODO track names can be up to 10 words maybe?? See if documentation has updated it
        track_entity = {
            'entity' : cls.intent_constants.track_entity,
            'entity_values' : [
                ':0 (#|##|###|)',
                ':0 :0 (#|##|###|)',
                ':0 :0 :0 (#|##|###|)',
                ':0 :0 :0 :0 (#|##|###|)',
                ':0 :0 :0 :0 :0 (#|##|###|)'
            ],
            'cached' : False
        }

        skip_entity = {
            'entity' : cls.intent_constants.skip_entity,
            'entity_values' : [
                'next',
                'previous'
            ],
            'cached' : False
        }

        artist_entity = {
            'entity': cls.intent_constants.artist_entity,
            'entity_values' : [
                ':0',
                ':0 :0',
                ':0 :0 :0',
                ':0 :0 :0 :0'
            ],
            'cached' : False
        }

        volume_entity = {
            'entity': cls.intent_constants.volume_entity,
            'entity_values' : [
                'zero',
                'low',
                'medium',
                'high',
                'max'
            ],
            'cached' : False
        }

        playlist_entity = {
            'entity': cls.intent_constants.playlist_entity,
            'entity_values': [
                ':0',
                ':0 :0 #',
                ':0 :0 :0',
                ':0 :0 :0 :0'
            ],
            'cached' : False
        }

        type_entity = {
            'entity': cls.intent_constants.type_entity,
            'entity_values' : [
                'album',
                'single'
            ],
            'cached': False
        }

        cls.spotify_intents.insert_many([spotify_player_intent, player_entity,
         track_entity, artist_entity, volume_entity, playlist_entity, type_entity, skip_entity])


        #TODO add options for reccurrence
        #TODO add options for location
        #TODO add examples maybe so that I remember why I did some of this shit
        #TODO add reversable order of queries.
        #TODO add functionality for more than one attendee
        #TODO For queries add calendar specifier so as to not confuse padatious intent parser. 
            #Ex. Instead of "What is my next event" -> "What is my next calendar event" or something like that
        #TODO remove calendar_update_parameters
        #TODO For date paramters, add option for relative dates instead of exact dates when creating new event.
        frequency_extension = '(| every {calendar_frequency}(| for {calendar_frequency_num} (occurrences|weeks|months|years)))'
        options_extension = '(| and set the {calendar_param} to {calendar_update})'
        calendar_intent = {
             'intent': cls.intent_constants.calendar_intent,
             'intent_values': [
                 '{calendar_query} (a|an) {event_type} to my calendar'+ frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} to my calendar with {calendar_attendee}' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} to my calendar (on|at) {calendar_date}' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} to my calendar with {calendar_attendee} (at|on) {calendar_date}' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} to my calendar (on|at) {calendar_date} between {start_time} and {end_time}' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} to my calendar with {calendar_attendee} on {calendar_date} between {start_time} and {end_time}' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} called {event_title} to my calendar' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} called {event_title} to my calendar with {calendar_attendee}' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} called {event_title} to my calendar (on|at) {calendar_date}' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} called {event_title} to my calendar with {calendar_attendee} (on|at) {calendar_date}' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} called {event_title} to my calendar (on|at) {calendar_date} between {start_time} and {end_time}' + frequency_extension + options_extension,
                 '{calendar_query} (a|an) {event_type} called {event_title} to my calendar with {calendar_attendee} (on|at) {calendar_date} between {start_time} and {end_time}' + frequency_extension + options_extension,
                 '{calendar_query} my {event_num}(|for|on) {calendar_date}(|(with|at) {calendar_search})',
                 '{calendar_query} my {event_num} {event_type}(| {calendar_param} to {calendar_update})',
                 '{calendar_query} my {event_num} {event_type}(| for| on) {calendar_date}(| {calendar_param} to {calendar_update})',
                 '{calendar_query} my {event_num} {event_type} (with|at) {calendar_search}(| {calendar_param} to {calendar_update})',
                 '{calendar_query} my {event_num} {event_type} (with|at) {calendar_search} (for|on) {calendar_date}(| {calendar_param} to {calendar_update})'
             ],
             'cached': False
        }

        calendar_task_entity = {
             'entity': cls.intent_constants.calendar_task_entity,
             'entity_values': [
                 'Add',
                 'Schedule',
                 'When is',
                 "When's",
                 'What is',
                 "Where is",
                 "Where's",
                 "What's",
                 'Update',
                 'Cancel',
                 'Reschedule'
             ],
             'cached': False
        }

        calendar_event_entity = {
            'entity': cls.intent_constants.calendar_event_entity,
            'entity_values':[
                'meeting',
                'event'
            ],
            'cached': False
        }

        calendar_num_entity = {
             'entity': cls.intent_constants.calendar_num_entity,
             'entity_values': [
                 'next',
                 'next #',
                 'first',
                 'second',
                 'third',
                 'fourth',
                 'fifth',
                 'sixth',
                 'seveth',
                 'eigth',
                 'ninth',
                 'last',
                 'second to last',
                 'agenda',
                 'schedule'
             ],
             'cached': False
        }

        calendar_attendee_entity = {
            'entity': cls.intent_constants.calendar_attendee_entity,
            'entity_values': [
                ':0',
                ':0 :0',
                ':0 :0 :0'
            ],
            'cached': False
        }
        #TODO Expand this later.
        calendar_date_entity = {
            'entity': cls.intent_constants.calendar_date_entity,
            'entity_values': [
                '(Monday|Tuesday|Wenesday|Thursday|Friday|Saturday|Sunday|Today|Tommorow|Yesterday)',
                '(January|February|March|April|May|June|July|August|September|October|November|December) (#|##)',
                '(January|February|March|April|May|June|July|August|September|October|November|December) (#|##) ####',
                ':0( # ####| ## ####| #| ##|) at (#|##|##:##|#:##)(PM|AM|am|pm| PM| AM| am| pm)',
                ':0 :0( # ####| ## ####| #| ##|) at (#|##|##:##|#:##)(PM|AM|am|pm| PM| AM| am| pm)',
                '(#|##|##:##|#:##)(PM|AM|am|pm| PM| AM| am| pm) on :0( # ####| ## ####| #| ##|)',
                '(#|##|##:##|#:##)(PM|AM|am|pm| PM| AM| am| pm) on :0 :0( # ####| ## ####| #| ##)'
            ],
            'cached': False
        }

        calendar_frequency_entity = {
            'entity': cls.intent_constants.calendar_frequency_entity,
            'entity_values': [
                'daily',
                'weekly',
                'monthly',
                'yearly',
                'minutely',
                'secondly',
                'day',
                'week',
                'month',
                'year',
                'other day',
                'other week',
                'other month',
                'other year'
            ],
            'cached': False
        }

        calendar_frequency_num_entity = {
            'entity': cls.intent_constants.calendar_frequency_num_entity,
            'entity_values': [
                '#',
                '##'
            ],
            'cached': False
        }
        #TODO look up wild card shit
        calendar_search_entity = {
            'entity': cls.intent_constants.calendar_search_entity,
            'entity_values': [
                ':0',
                ':0 :0',
                ':0 :0 :0 :0'
            ],
            'cached': False
        }
        #TODO Work on that notification
        #TODO Add in start date option instead of just the time
        #TODO RELOAD
        calendar_param_entity = {
            'entity': cls.intent_constants.calendar_param_entity,
            'entity_values':[
                'location',
                'attendee list',
                'guests',
                'guest list',
                'notification',
                'color',
                'default color',
                'reminder',
                'popup',
                'email reminder',
                'description',
                'title',
                'start time',
                'start date',
                'event type',
                'type',
                'start',
                'end time',
                'end date',
                'end',
                'frequency'

            ],
            'cached': False
        }

        calendar_update_entity = {
            'entity': cls.intent_constants.calendar_update_entity,
            'entity_values':[
                ':0',
                ':0 :0',
                ':0 :0 :0',
                ':0 :0 :0 :0',
                ':0 :0 :0 :0 :0',
                '(#|##|###)',
                '(#|##|##:##|#:##)(PM|AM|am|pm| PM| AM| am| pm) on :0 :0( # ####| ## ####| #| ##)',
                '(#|##|##:##|#:##)(PM|AM|am|pm| PM| AM| am| pm) on :0( # ####| ## ####| #| ##|)',
                ':0( # ####| ## ####| #| ##|) at (#|##|##:##|#:##)(PM|AM|am|pm| PM| AM| am| pm)',
                ':0 :0( # ####| ## ####| #| ##|) at (#|##|##:##|#:##)(PM|AM|am|pm| PM| AM| am| pm)',

            ],
            'cached': False
        }

        calendar_start_time_entity = {
            'entity': cls.intent_constants.calendar_start_time_entity,
            'entity_values':['(#|##)(PM|AM|am|pm)'],
            'cached': False
        }

        calendar_end_time_entity = {
            'entity': cls.intent_constants.calendar_end_time_entity,
            'entity_values': ['(#|##)(PM|AM|am|pm)'],
            'cached': False
        }
        #TODO If this gets big enough seperate add and remove values
        #TODO DELETE THIS. filter out the update prefixes within api code


        cls.calendar_intents.insert_many([calendar_intent,calendar_task_entity,
        calendar_event_entity,calendar_num_entity,calendar_attendee_entity,calendar_search_entity ,calendar_date_entity, calendar_param_entity,
        calendar_update_entity, calendar_start_time_entity, calendar_end_time_entity, calendar_frequency_entity, calendar_frequency_num_entity])





        


        

    





