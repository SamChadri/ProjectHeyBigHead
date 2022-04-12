import requests
import json
from requests.exceptions import RequestException
import logging 
import os
from pprint import pprint

TAG = "WeatherAPI: "

open_endpoint = "https://api.openweathermap.org/data/2.5/forecast?{0}={1}&appid={2}&units=imperial"
wb_endpoint = "https://api.weatherbit.io/v2.0/forecast/daily?{0}={1}&key={2}&units=I&days=8"
#TODO Convert to farenheight
#TODO Implement parameter for units.
#TODO Seperate today's weather from weekly forecast array....maybe?
class WeatherAPI:


    def __init__(self, key_file=os.path.abspath('alfred/data/keys.json')):
        with open(key_file) as f:
            data = json.load(f)
            self.owKey = data['openWeatherKey']
            self.wbkey = data['weatherBitKey']
        
        self.ow_endpoint = open_endpoint
        self.wb_endpoint = wb_endpoint


    def get_forecast(self, location, city):
        try:
            results = self.wb_request(location, city)
        except Exception as e:
            logging.error(TAG + f" OpenWeather request failed with error: {e}. Trying backup WeatherBit API.  ")
            
            try:
                backup_results = self.ow_request(location, city)
            except Exception as e:
                logging.error(TAG + f'Exception error occurred: {e}')
                return {'error' : e}
            else:
                return backup_results
        else:
            return results


    
    def ow_request(self, location, city):
        try:
            query_type = (('zip', 'q') [city == True])
            response = requests.get(self.ow_endpoint.format(query_type, location, self.owKey))
            if response.status_code != 200:
                raise Exception("API endpoint request failed with status code: " + response.status_code)
            
            logging.info(TAG + "Open Weather request successfull with status code: " + str(response.status_code))

        except RequestException as e:
            logging.debug(TAG + "RequestException error occurred: " + e)
            return {'error': e}
        else:
            data = response.json()
            weather_data = {}

            weather_data["city_data"] = data['city']
            weather_data['forecast'] = []
            #pprint(data)
            for forecast in data['list']:
                entry = {}
                entry['date'] = forecast['dt']
                entry['clouds'] = forecast['clouds']
                entry['details'] = forecast['main']
                entry['conditions'] = []
                for condition in forecast['weather']:
                    item = {}
                    item['condition'] = condition['main']
                    item['details'] = condition['description']
                    item['icon'] = condition['icon']

                if 'rain' in forecast:     
                    entry['precip'] = forecast['rain']['3h']
                
                weather_data['forecast'].append(entry)

            weather_data['source'] = 'openWeather'
            
            return weather_data

    def wb_request(self, location, city):
        try:
            query_type = (('postal_code', 'city') [city == True])
            response = requests.get(self.wb_endpoint.format(query_type, location, self.wbkey))
            if response.status_code != 200:
                raise Exception("API endpoint request failed with status code: " + team_response.stats_code)

            logging.info(TAG + "Weather Bit request successfull with status code: " + str(response.status_code))
        except RequestException as e:
            logging.error(TAG + "RequestException error occurred: ", e)
            return {'error': e}
        else:
            data = response.json()
            weather_data = {}

            weather_data['city_data'] = {}
            weather_data['city_data']['country'] = data['country_code']
            weather_data['city_data']['name'] = data['city_name']
            weather_data['city_data']['sunrise'] = data['data'][0]['sunrise_ts']
            weather_data['city_data']['sunset'] = data['data'][0]['sunset_ts']
            weather_data['city_data']['coord'] = {'lat' : data['lat'], 'lon' : data['lon']}
            weather_data['city_data']['timezone'] = data['timezone']
            #pprint(data)

            weather_data['forecast'] = []

            for forecast in data['data']:
                entry = {}
                entry['date'] = forecast['valid_date'] 
                entry['clouds'] = forecast['clouds']

                entry['details'] = {}  
                entry['details']['feels_like'] = forecast['temp']
                entry['details']['grnd_level'] = 'NA'
                entry['details']['humidity'] = forecast['rh']
                entry['details']['pressure'] = forecast['pres']
                entry['details']['sea_level'] = forecast['slp']
                entry['details']['temp'] = forecast['temp']
                entry['details']['temp_max'] = forecast['max_temp']
                entry['details']['temp_min'] = forecast['low_temp']
                entry['details']['pop'] = forecast['pop']
                entry['details']['precip'] = forecast['precip']
                entry['details']['snow'] = forecast['snow']
                #TODO Convert code to an actual message
                entry['conditions']= {}
                entry['conditions']['condition'] = forecast['weather']['code']
                entry['conditions']['details'] = forecast['weather']['description']
                entry['conditions']['icon'] = forecast['weather']['icon']
                weather_data['forecast'].append(entry)

            weather_data['source'] = 'weatherBit'
            return weather_data




