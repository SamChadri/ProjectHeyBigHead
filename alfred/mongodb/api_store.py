import pymongo
import os 
import requests
import logging
import sys
from requests.exceptions import RequestException
import pandas as pd
import json

NBA = 0
NFL = 1

TAG = 'APIStore: '

class BearerToken(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

class APIStore:


    def __init__(self):
        self.class_init()


    @classmethod
    def class_init(cls):
        mongo_client = pymongo.MongoClient(os.environ['MONGO_IP'])
        api_db = mongo_client["api_database"]
        cls.nfl_sports_db = api_db["theSportsDb"]["NFL"]
        cls.nba_sports_db = api_db["theSportsDb"]["NBA"]
        cls.spotify_db = api_db["spotify"]
        cls.device_db = api_db["devices"]
        cls.calendar_db = api_db["calendar"]
        cls.endpoint = 'https://www.thesportsdb.com/api/v1/json/2/search_all_teams.php?l={}'
        cls.spotify_path = os.path.abspath('alfred/data/spotify_data/spotify_{}_endpoints.csv') 

    @classmethod
    def get_nba_team(cls, name):
        query = {"team_name" : {"$regex" : name, "$options" : "i"} }
        return cls.nba_sports_db.find_one(query)

    @classmethod
    def get_nfl_team(cls, name):
        query = {"team_name" : {"$regex" : name, "$options": "i" } }
        return cls.nfl_sports_db.find_one(query)

    @classmethod
    def get_league(cls, name):
        query = {"team_name" : {"$regex" : name, "$options": "i" } }
        nba_query = cls.nba_sports_db.find_one(query)
        nfl_query = cls.nfl_sports_db.find_one(query)

        if nba_query != None and nfl_query == None:
            return NBA
        elif nfl_query != None and nba_query == None:
            return NFL
        else:
            return -1

    @classmethod
    def set_spotify_db(cls, intent):
        sub_db = intent.split('_')[1]
        cls.curr_spotify_db = cls.spotify_db[sub_db]

    @classmethod
    def get_spotify_endpoint(cls, entity_value):
        entity_value = '^' + entity_value
        query = {'entity_value' : {'$regex' : entity_value, '$options' : 'i'}}
        return cls.curr_spotify_db.find_one(query)

    @classmethod
    def verify_device(cls, device_id):
        query = {'id' : device_id}
        query_result = cls.device_db.find_one(query)

        if query_result == None:
            return False
        else:
            return True

    
    @classmethod
    def get_device(cls, device_id):
        query = {'id': device_id}
        return cls.device_db.find_one(query)

    @classmethod
    def get_devices(cls):
        return cls.device_db.find()

    @classmethod
    def init_sports_cache(cls):
        try:
            nba_response = requests.get(cls.endpoint.format('NBA'))
            nfl_response = requests.get(cls.endpoint.format('NFL'))
            if nba_response.status_code != 200 or nfl_response.status_code != 200:
                logging.error(TAG + 'SportsDB request failed with status code {}'.format(nba_response.status_code))
                sys.exit(-1)
        except RequestException as e:
            logging.error(TAG + 'RequestException error occurred: {}'.format(e))
            sys.exit(-1)
        
        else:
            if 'teams' not in nba_response.json() or 'teams' not in nfl_response.json():
                #logging.error(TAG + 'Invalid json recieved')
                #sys.exit(-1)
                pass
            nba_dict = nba_response.json()['teams']
            nfl_dict = nfl_response.json()['teams']

            nba_teams = []
            nfl_teams = []
            for team in nba_dict:
                entry = {}
                entry['team_id'] = team['idTeam']
                entry['team_name'] = team['strTeam']
                entry['name_short'] = team['strTeamShort']
                entry['team_description'] = team['strDescriptionEN']
                entry['team_stadium'] = team['strStadiumDescription']
                entry['team_website'] = team['strWebsite']
                entry['team_logo'] = team['strTeamBadge']
                nba_teams.append(entry)
            
            for team in nfl_dict:
                entry = {}
                entry['team_id'] = team['idTeam']
                entry['team_name'] = team['strTeam']
                entry['name_short'] = team['strTeamShort']
                entry['team_description'] = team['strDescriptionEN']
                entry['team_stadium'] = team['strStadiumDescription']
                entry['team_website'] = team['strWebsite']
                entry['team_logo'] = team['strTeamBadge']
                nfl_teams.append(entry)
            
            cls.nba_sports_db.insert_many(nba_teams)
            cls.nfl_sports_db.insert_many(nfl_teams)

    #TODO Adjust so its more of a verification for devices online matching with devices on servers.
    @classmethod
    def load_device_data(cls,device_data=os.path.abspath("alfred/data/spotify_data/spotify_devices.csv")):

        endpoint_df = pd.read_csv(device_data)
        df_len = len(endpoint_df.index)
        device_data = []
        for row in range(df_len):
            entry = {}
            entry['id'] = endpoint_df.iloc[row]['id']
            entry['name']  = endpoint_df.iloc[row]['name']
            entry['type'] = endpoint_df.iloc[row]['type']
            device_data.append(entry)


        cls.device_db.insert_many(device_data)

    @classmethod
    def load_calendar_data(cls, calendar_data=os.path.abspath("alfred/data/calendar_data/{}_data.json")):

        file = open(calendar_data.format("reccurence"))
        data = json.load(file)
        cls.calendar_db.insert_many(data['reccur_data'])


    @classmethod
    def get_frequency(cls, freq_val):
        query = {"reccur_val":  {"$regex" : freq_val, "$options": "i" }}
        return cls.calendar_db.find_one(query)
        

                


    @classmethod
    def load_spotify_endpoints(cls, intent):
        cls.curr_spotify_db = cls.spotify_db[intent]
        endpoint_df = pd.read_csv(cls.spotify_path.format(intent))
        df_len = len(endpoint_df.index)
        endpoint_data = []
        for row in range(df_len):
            entry = {}
            entry['method'] = endpoint_df.iloc[row]['method']
            entry['url'] = endpoint_df.iloc[row]['url']
            entry['usage'] = endpoint_df.iloc[row]['usage']
            entry['intent'] = endpoint_df.iloc[row]['intent']
            entry['scope'] = endpoint_df.iloc[row]['scope']
            entry['entity_value'] = endpoint_df.iloc[row]['entity_value']
            entry['tag'] = endpoint_df.iloc[row]['tag']

            values = endpoint_df.iloc[row]['entity_value'].split(' ')
            index = 0
            for string in values:
                if string.find('-') != -1:
                    values[index] = string.replace('-', ' ')
                
                index += 1

            entry['entity_value'] = values
            endpoint_data.append(entry)

        cls.curr_spotify_db.insert_many(endpoint_data)

    @classmethod
    def init_spotify_cache(cls):
        #TODO player endpoints.
        cls.load_spotify_endpoints("player")
        cls.load_calendar_data()
        cls.load_device_data()

    @classmethod
    def init_database(cls):
        cls.init_sports_cache()
        cls.init_spotify_cache()




