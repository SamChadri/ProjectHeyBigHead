import requests
from requests.exceptions import RequestException
from requests_oauthlib import OAuth1Session
import logging 
import os
import json
from datetime import datetime
from pprint import pprint
from alfred.mongodb.api_store import APIStore 
from pprint import pprint


#TODO: If app is open on device, handle intent here. If not handle intent on device with sdk
#TODO: Keep track of devices in the database. I think we will go with the spotify decice id's for now.
#TODO: Do the tokens expire? Yes, keep track of the last refreshed toke. Next up, refresh that bih

class BearerToken(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


TAG = 'SpotifyAPI: '

RECENT_TAG = 'RECENT'
PLAYER_TAG = 'PLAYER'
DEVICES_TAG = 'DEVICES'
CURRENT_TAG = 'CURRENT'
NEXT_TAG = 'NEXT'
PREVIOUS_TAG = 'PREVIOUS'
QUEUE_TAG = 'QUEUE'
PAUSE_TAG = 'PAUSE'
PLAY_TAG = 'PLAY'
REPEAT_TAG = 'REPEAT'
SEEK_TAG = 'SEEK'
SHUFFLE_TAG = 'SHUFFLE'
TRANSFER_TAG = 'TRANSFER'
VOLUME_TAG = 'VOLUME'

factory_init = {'init' : False}

def set_init(val):
    internal_init = not factory_init
    
#
#TODO Have it so you do not have to refresh the token everytime instance starts again
class SpotifyAPI:

    @classmethod
    def is_init(cls, init=False):
        return factory_init['init']

    
    @classmethod
    def factory(cls):
        logging.info(TAG +"Initializing Spotify Factory")
        cls.__api_pool = {}
        cls.__devices = APIStore.get_devices()
        cls.__device_settings = {}
        for device in cls.__devices:
            id = device['id']
            logging.info(TAG + "Creating Spotify API instace with id {}".format(id))
            cls.__device_settings[id] = {
                'shuffle': False,
                'state': 'off'
            }
            api_instance = SpotifyAPI(id)
            cls.__api_pool[id] = api_instance

        factory_init['init'] = True

    @classmethod
    def acquire(cls, id):
        return cls.__api_pool.pop(id)

    @classmethod
    def release(cls, id, obj):
        cls.__api_pool[id] = obj

    @classmethod
    def get_state_setting(cls, curr_state):
        if curr_state == 'track':
            return 'context'

        elif curr_state == 'context':
            return 'off'
        
        else:
            return 'track'

    @classmethod
    def get_setting(cls, id, setting):
        return cls.__device_settings[id][setting]

    @classmethod
    def set_setting(cls, id, setting, value):
        cls.__device_settings[id][setting] = value

    def __init__(self, device_id, key_file=os.path.abspath("alfred/data/keys.json")):
        self.key_file = key_file
        logging.debug(TAG + 'Loading keyfile from path {}'.format(self.key_file))
        with open(self.key_file) as f:
            data = json.load(f)
            logging.debug(TAG + f'KeyData: {data}')
            self.__client_id = data['spotify_client_id']
            #logging.debug(TAG + 'Set client id')
            self.__client_secret = data['spotify_client_secret']
            self.__refresh_token = data['spotify_refresh_token']
            logging.debug(TAG + 'Finished reading keyfile')

        self.__refresh_endpoint = 'https://accounts.spotify.com/api/token'
        self.__search_endpoint = 'https://api.spotify.com/v1/search?query={}&type={}&offset=0&limit=50'
        self.__playlist_endpoint = 'https://api.spotify.com/v1/users/beatfreak50/playlists?offset=0&limit=50'
        self.refresh_token()
        self.device_id = device_id
        self.market = 'US'
        logging.debug(TAG + 'Done initializing Spotify API')
        self.__search_result = None
        self.__playlist_result = None
        self.result_name = None
        #self.state = SpotifyAPI.get_setting('state')
        #self.shuffle = SpotifyAPI.get_setting('shuffle')
        print('Done init SpotifyAPI')





    def refresh_token(self):
        refresh_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.__refresh_token
        }
        try:
            response = requests.post(self.__refresh_endpoint, data=refresh_data, auth=(self.__client_id,self.__client_secret))
            if response.status_code != 200:
                status_error = TAG + 'Spotify refresh token endpoint failed with status code {}'.format(response.status_code)
                logging.error(status_error)
                return {'status': 'Failed', 'error' : status_error}

            logging.info(TAG + 'Spotify refresh token request returned successfully.')
        except RequestException as e:
            exception_message = TAG + 'RequestException error occurred: {}'.format(e)
            logging.error(exception_message)
            return {'status': 'Failed', 'error' : exception_message}
        else:
            self.__access_token = response.json()['access_token']
            self.last_refresh_time = datetime.now()
            return {'status': 'Success'}

    def is_session_expired(self):
        print(f'Last Refresh Time: {self.last_refresh_time}')
        print(f'Curr Time: {datetime.now()}')
        curr_time = datetime.now() - self.last_refresh_time
        if curr_time.seconds >= 3600:
            return True
        else:
            return False
        


    def check_device_availability(self):            
        endpoint = APIStore.get_spotify_endpoint('devices')
    
        try:
            if self.is_session_expired():
                token_result = self.refresh_token()
                if 'error' in token_result:
                    raise Exception(token_result['error'])

            response = requests.get(endpoint['url'], auth=BearerToken(self.__access_token))
            if response.status_code != 200:
                logging.error(TAG + 'Spotify device list endpoint failed with status code {}'.format(response.status_code))
                raise Exception(TAG + 'Spotify device list endpoint failed with status code {}'.format(response.status_code))
            
            logging.info(TAG + 'Spotify Device Availability request returned successfully. Processing response...')
        except RequestException or Exception as e:
            logging.error(TAG + 'Exception error occurred: {}'.format(e))
            return False

        else:
            devices = response.json()['devices']
            for device in devices:
                if device['id'] == self.device_id:
                    return True

            return False

    #TODO Might change how to handle appostraphes in artist names later
    def spotify_search(self, query, query_type):
        data_result = 'tracks'
        if query_type == 'album':
            query = query.replace("'", '')
            data_result = 'albums'
        try:
            if self.is_session_expired():
                token_result = self.refresh_token()
                if 'error' in token_result:
                    raise Exception(token_result['error'])

            response = requests.get(self.__search_endpoint.format(query, query_type), auth=BearerToken(self.__access_token))
            if response.status_code != 200:
                logging.error(TAG + 'Spotify Request failed with error code {}'.format(response.status_code))
                raise Exception(TAG + 'Spotify Request failed with error code {}'.format(response.status_code))

            logging.info(TAG + 'Spotify Search request returned successfully. Processing response...')
        except Exception or RequestException as e:
            logging.error(TAG + 'Exception error occurred: {}'.format(e))
            return {'error' : e}

        else:
            search_results = response.json()[data_result]['items']
            if len(search_results) == 0:
                return {'error' : 'Search results not found'}

            if query_type != 'album':
                for item in search_results:
                    print(item)
                    print('Item name: {}'.format(item['name']))
                    query_name = query.split(':')[0].replace(' artist', '').lower()
                    item_name = item['name'].lower()
                    print(f'Query name: {query_name}')
                    if item_name == query_name or item_name.find(query_name) != -1:
                        print('Found match')
                        self.__search_result = item
                        self.result_name = self.__search_result['name']
                        return self.__search_result['uri']
                print('Could not find search result tracks, search albums... ')
                for item in search_results:
                    query_name = query.split(':')[0].replace(' artist', '').lower()
                    item_name = item['album']['name'].lower()
                    print(f'Item name: {item_name}')
                    print(f'Query name: {query_name}')
                    if item_name == query_name or item_name.find(query_name) != -1:
                        self.__search_result = item
                        self.result_name = self.__search_result['album']['name']
                        return self.__search_result['album']['uri']

                self.__search_result = response.json()[data_result]['items'][0]
                self.result_name = self.__search_result['name']
                return self.__search_result['uri']

            self.__search_result = response.json()[data_result]['items'][0]
            self.result_name = self.__search_result['name']
            return self.__search_result['uri']

    #TODO Implement playlist search for daily mixes    
    def spotify_playlists(self, query):
        try:
            if self.is_session_expired():
                token_result = self.refresh_token()
                if 'error' in token_result:
                    raise Exception(token_result['error'])

            response = requests.get(self.__playlist_endpoint, auth=BearerToken(self.__access_token))
            if response.status_code != 200:
                status_error = 'Spotify Request failed with error code {}'.format(response.status_code)
                logging.error(TAG + status_error)
                raise Exception(TAG + status_error)

            logging.info(TAG + 'Spotify Playlists request returned successfully. Processing response...')
        except Exception or RequestException as e:
            logging.error(TAG + 'Exception error occurred: {}'.format(e))
            return {'error' : e}
        else:
            playlist_data = response.json()['items']

            for playlist in playlist_data:
                if playlist['name'].lower() == query.lower():
                    self.__playlist_result = playlist
                    self.result_name = playlist['name']
                    return playlist['uri']

            
            logging.error(TAG + 'Playlist not found')
            return {'error': 'Playlist not found'}


    
    def spotify_request(self, intent, endpoint_entity=None, track_uri=None, state=None, shuffle=False, volume_level=None):
        APIStore.set_spotify_db(intent)
        if volume_level == None:
            endpoint = APIStore.get_spotify_endpoint(endpoint_entity)
        else:
            endpoint = APIStore.get_spotify_endpoint('volume')

        self.volume_level = volume_level
        print(endpoint_entity)
        print(intent)
        print(endpoint)
        print('Param track_uri: ' + str(type(track_uri)))
        self.track_uri = track_uri
        print('Member track_uri: ' + str(type(self.track_uri)))
        if state != None:
            self.state = state

        if shuffle != None:
            self.shuffle = shuffle

        request_params, request_data = self.set_request_params(endpoint['tag'])

        if 'error' in request_data:
            return request_data

        endpoint['request_data'] = request_data

        if self.check_device_availability() == False :
            endpoint['handle_on_device'] = True
            return endpoint
        
        else:
            endpoint['handle_on_device'] = False

        try:
            endpoint_url = endpoint['url']
            if endpoint['method'] == 'GET':
                response  = requests.get(endpoint_url, params=request_params, auth=BearerToken(self.__access_token))
            elif endpoint['method'] == 'POST':
                print('Executing post method')
                response = requests.post(endpoint_url,params=request_params, json=request_data, auth=BearerToken(self.__access_token))
            else:
                print('Executing put method')
                response = requests.put(endpoint_url,params=request_params ,json=request_data, auth=BearerToken(self.__access_token))

            if response.status_code != 200 and response.status_code != 204:
                raise Exception(TAG + 'Spotify Reuquest failed with status code: {} and message: {}'.format(response.status_code, response.reason))

            logging.info(TAG + 'Spotify API request returned successfully. Processing response...')
        except Exception or RequestException as e:
            logging.error(TAG + 'Exception error occurred: {}'.format(e))
            return {'error': e}

        else:
            if endpoint_url == 'GET':
                return response.json()
            else:
                return endpoint



    #TODO Maybe do like a lambda for the request methods? set them in a different method?
    def set_request_params(self, tag):
        request_body  = {}
        request_params = {}

        if tag == RECENT_TAG:
            request_params['limit'] = 10

        elif tag == PLAYER_TAG:
            request_params['market'] = self.market

        elif tag == DEVICES_TAG:
            pass
        elif tag == CURRENT_TAG:
            request_params['market'] = self.market

        elif tag == NEXT_TAG or tag == PREVIOUS_TAG:
            request_params['device_id'] = self.device_id

        elif tag == QUEUE_TAG:
            if self.track_uri == None:
                return {'error': 'Missing track uri'}
            request_params['uri'] = self.track_uri
            request_params['device_id'] = self.device_id

        elif tag == PAUSE_TAG:
            request_params['device_id'] = self.device_id

        elif tag == PLAY_TAG:
            #requires body_params
            print('using play tag')
            request_params['device_id'] = self.device_id
            if self.track_uri != None:
                print('setting context_uri')
                print(self.track_uri)
                if self.track_uri.find('track') != -1:
                    request_body['uris'] = [self.track_uri]
                else:
                    request_body['context_uri'] = self.track_uri
                request_body['position'] = 0

        elif tag == REPEAT_TAG:
            curr_setting = SpotifyAPI.get_setting(self.device_id, 'state')
            next_setting = SpotifyAPI.get_state_setting(curr_setting)
            request_params['state'] = next_setting
            request_params['device_id'] = self.device_id
            SpotifyAPI.set_setting(self.device_id, 'state', next_setting)

        elif tag == SEEK_TAG:
            #TODO Provide user different default lengths for seeking maybe
            request_params['position_m'] = 10
            request_params['device_id'] = self.device_id

        elif tag == SHUFFLE_TAG:
            if SpotifyAPI.get_setting(self.device_id,'shuffle'):
                print(f'Toggling shuffle from True to False')
                request_params['state'] = False
                SpotifyAPI.set_setting(self.device_id,'shuffle', False)
            else:
                print(f'Toggling shuffle from False to True')
                request_params['state'] = True
                SpotifyAPI.set_setting(self.device_id, 'shuffle', True) 

            request_params['device_id'] = self.device_id

        elif tag == TRANSFER_TAG:
            #requires body_params
            request_body['device_id'] = self.device_id
            request_body['play'] = True

        else:

            if self.volume_level == 'zero':
                self.volume_level = 0
            elif self.volume_level == 'low':
                self.volume_level = 25
            elif self.volume_level == 'medium':
                self.volume_level = 50
            elif self.volume_level == 'high':
                self.volume_level = 75
            else:
                self.volume_level = 100
  
            request_params['volume_percent'] = self.volume_level
            request_params['device_id'] = self.device_id


        return request_params, request_body
            







