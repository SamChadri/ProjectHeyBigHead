
from dataclasses import dataclass

@dataclass
class IntentData:
    hello_intent : str = "hello"
    hay_intent : str = "hay"
    bye_intent : str = "goodbye"
    query_intent : str = "search"
    sports_intent : str = "sports"
    entertainment_intent : str  = "entertainment"
    celeb_intent : str = "celeb"
    weather_intent : str = "weather"
    map_intent : str = "directions"
    time_intent : str = "time"
    wiki_intent : str = "wiki"
    spotify_player_intent : str = "spotify_player"
    #TODO maybe divide subintents from the actual intents
    #DB_INTENT
    spotify_intent : str = 'spotify'
    calendar_intent: str = 'calendar'


    
    

    event_entity : str = "event_type"
    team_entity : str = "team"
    wiki_entity : str = "wiki_query"
    celeb_entity : str = "celeb_query"
    ent_entity : str = "ent_type"
    title_entity : str = "title_query"
    location_entity : str = "location_query"
    direction_entity : str = "direction_query"
    weather_entity : str = "weather_location"
    origin_entity : str = "origin_query"
    dest_entity : str = "destination_query"
    player_entity : str = 'player_query'
    track_entity : str = 'track_query'
    artist_entity : str = 'artist_query'
    volume_entity : str = 'volume_query'
    playlist_entity : str = 'playlist_query'
    type_entity : str = 'type_query'
    skip_entity : str = 'skip_query'
    calendar_task_entity: str = "calendar_query"
    calendar_event_entity: str = 'event_type'
    calendar_num_entity: str = 'event_num'
    calendar_attendee_entity : str = 'calendar_attendee'
    calendar_date_entity: str = 'calendar_date'
    calendar_start_time_entity: str = 'calendar_start_time'
    calendar_end_time_entity: str = 'calendar_end_time'
    calendar_search_entity: str = "calendar_search"
    calendar_param_entity: str = "calendar_param"
    calendar_update_entity: str = "calendar_update"
    calendar_frequency_entity: str = "calendar_frequency"
    calendar_frequency_num_entity: str = "calendar_frequency_num"        


    def __init__(self):
        self.__intent_data = {}
        self.__entity_data = {}

        self.__intent_data[self.hello_intent] = "salutation_intents"
        self.__intent_data[self.hay_intent] =  "salutation_intents"
        self.__intent_data[self.bye_intent] = "salutation_intents"
        self.__intent_data[self.query_intent] = "search_intents"
        self.__intent_data[self.sports_intent] = "sports_intents"
        self.__intent_data[self.entertainment_intent] = "entertainment_intents"
        self.__intent_data[self.celeb_intent] = "wiki_intents"
        self.__intent_data[self.weather_intent] = "weather_intents"
        self.__intent_data[self.map_intent] = "map_intents"
        self.__intent_data[self.time_intent] = "time_intents"
        self.__intent_data[self.wiki_intent] = "wiki_intents"
        self.__intent_data[self.spotify_player_intent] = "spotify_intents"
        self.__intent_data[self.calendar_intent] = "calendar_intents"


        self.__entity_data[self.event_entity] = "sports_intents"
        self.__entity_data[self.team_entity] = "sports_intents"
        self.__entity_data[self.wiki_entity] = "wiki_intents"
        self.__entity_data[self.celeb_entity] = "wiki_intents"
        self.__entity_data[self.ent_entity] = "entertainment_intents"
        self.__entity_data[self.title_entity] = "entertainment_intents"
        self.__entity_data[self.direction_entity] = "map_intents"
        self.__entity_data[self.location_entity] = "map_intents"
        self.__entity_data[self.origin_entity] = "map_intents"
        self.__entity_data[self.dest_entity] = "map_intents"
        self.__entity_data[self.weather_entity] = "weather_intents"
        self.__entity_data[self.player_entity] = "spotify_intents"
        self.__entity_data[self.track_entity] = "spotify_intents"
        self.__entity_data[self.artist_entity] = "spotify_intents"
        self.__entity_data[self.volume_entity] = "spotify_intents"
        self.__entity_data[self.playlist_entity] = "spotify_intents"
        self.__entity_data[self.type_entity] = "spotify_intents"
        self.__entity_data[self.skip_entity] = "spotify_intents"
        self.__entity_data[self.calendar_task_entity] = "calendar_intents"
        self.__entity_data[self.calendar_event_entity] = "calendar_intents"
        self.__entity_data[self.calendar_num_entity] = "calendar_intents"
        self.__entity_data[self.calendar_attendee_entity] = "calendar_intents"
        self.__entity_data[self.calendar_date_entity] = "calendar_intents"
        self.__entity_data[self.calendar_start_time_entity] = "calendar_intents"
        self.__entity_data[self.calendar_end_time_entity] = "calendar_intents"
        self.__entity_data[self.calendar_search_entity] = "calendar_intents"
        self.__entity_data[self.calendar_param_entity] = "calendar_intents"
        self.__entity_data[self.calendar_update_entity] = "calendar_intents"
        self.__entity_data[self.calendar_frequency_entity] = "calendar_intents"
        self.__entity_data[self.calendar_frequency_num_entity] = "calendar_intents"




    def get_intent_db(self, intent):
        return self.__intent_data[intent]

    def get_entity_db(self, entity):
        return self.__entity_data[entity]

    def get_data_intents(self):
        return self.__intent_data.keys()

    def get_data_entities(self):
        return self.__entity_data.keys()

    def get_db_names(self):
        return set(self.__intent_data.values())



    