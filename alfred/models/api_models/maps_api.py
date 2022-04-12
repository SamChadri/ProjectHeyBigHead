import requests
import logging
from requests.exceptions import RequestException

#TODO: Later on. Implement Maps and Routes API with keys and stuff
#TODO: Add functionality for directions without specifiying origin.

TAG = "MapsAPI: "
""" For now this API will return a link that will launch maps on any platform """
class MapsAPI:


    def __init__(self):
        self.search_endpoint = "https://www.google.com/maps/search/?api=1&query={}"
        self.dir_endpoint = "https://www.google.com/maps/dir/?api=1&origin={}&destination={}" 


    def search_location(self, location):
        location = location.replace(' ', '+')
        location = location.replace(',', '%2C')
        logging.info(TAG + 'Returning location search url')
        return {'url' : self.search_endpoint.format(location)}

    #TODO If I'm not feeling 
    def get_directions(self, origin, destination):
        origin = origin.replace(' ', '+')
        origin = origin.replace(',', '%2C')

        destination = destination.replace(' ', '+')
        destination = destination.replace(',', '%2C')
        logging.info(TAG + 'Returning direction url')
        return {'url' : self.dir_endpoint.format(origin, destination)}
    