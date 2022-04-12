from azure.cognitiveservices.search.websearch import WebSearchClient
from azure.cognitiveservices.search.websearch.models import SafeSearch
from msrest.authentication import CognitiveServicesCredentials

from googleapiclient.discovery import build

from requests.exceptions import RequestException
import os
import json
import logging 
from pprint import pprint

TAG = "SearchAPI: "
GOOGLE_ENGINE = 0
BING_ENGINE = 1

azure_endpoint = 'https://bighead-search.cognitiveservices.azure.com'

google_endpoint = "customsearch"

class SearchAPI:

    
    def __init__(self, engine=GOOGLE_ENGINE, key_file=os.path.abspath('alfred/data/keys.json')):
        with open(key_file) as f:
            key_data = json.load(f)
            if engine == BING_ENGINE:
                self.engine = BING_ENGINE
                self.api_key = key_data["azureKey"]
                self.backup_key = key_data['googleKey']
                self.endpoint = azure_endpoint
                self.backup_endpoint = google_endpoint
                self.backup_engine = GOOGLE_ENGINE
            else:
                self.engine = GOOGLE_ENGINE
                self.api_key = key_data['googleKey']
                self.backup_key = key_data['azureKey']
                self.endpoint = google_endpoint
                self.backup_endpoint = azure_endpoint
                self.backup_engine = BING_ENGINE

    def switch_credentials(self):
        og_endpoint = self.endpoint
        og_key = self.api_key
        og_engine = self.engine

        self.api_key = self.backup_key
        self.endpoint = self.backup_endpoint
        self.engine = self.backup_engine

        self.backup_key = og_key
        self.backup_endpoint = og_endpoint
        self.backup_engine = og_engine

        

    def search_request(self, query):            
        try:
            print((self.engine == GOOGLE_ENGINE))
            response = ((self.azure_request, self.google_request) [self.engine == GOOGLE_ENGINE](query))
        except Exception as e:
            logging.error(TAG + "Exception error occurred: " + str(e) + ". Trying backup engine")
            try:
                self.switch_credentials()
                backup_response = ((self.azure_request, self.google_request) [self.engine == GOOGLE_ENGINE](query) )
            except Exception as e:
                logging.error(TAG + "Exception error occurred: " + str(e))
                return {"error" : e}
            else:
                self.switch_credentials()
                return backup_response
        else:
            return response



    """ Returns a WebPage Object from the azure.cognitiveservices.search.websearch.models._models_py3 class """   
    def azure_request(self, query):
        client = WebSearchClient(endpoint=self.endpoint, credentials=CognitiveServicesCredentials(self.api_key))
        r_data = client.web.search(query=query)
        if (not hasattr(r_data.web_pages, 'value')):
            logging.error(TAG + 'Error occurred while retreiving bing search results.')
            return {'error' : 'Results could not be retreived'}
        logging.info(TAG + "Azure request returned successfully")
        data = r_data.web_pages.value
        web_data = []
        for item in data:
            entry = {}
            entry['title'] = item.name
            entry['link'] = item.url
            entry['display_link'] = item.display_url
            entry['snippet'] = item.snippet
            entry['image'] = item.thumbnail_url
            web_data.append(entry)

        return web_data
        
    """ Returns the WebPage dict """
    def google_request(self, query):
        service = build(self.endpoint, "v1", developerKey=self.api_key, cache_discovery=False)
        res= service.cse().list(q=query, cx='014647619269306432050:2wvnpn5sjpj').execute()
        if hasattr(res, 'items'):
            logging.info(TAG + "Google search request returned successfully")
            web_data = []
            data  = res['items']
            #pprint(res)
            for item in data:
                entry = {}
                entry['title'] = item['title']
                entry['link'] = item['link']
                entry['display_link'] = item['displayLink']
                if 'cse_image' in item['pagemap']:
                    entry['image'] = item['pagemap']['cse_image'][0]['src']
                elif 'cse_thumbnail' in item['pagemap']:
                    entry['image'] = item['pagemap']['cse_thumbnail'][0]['src']
                else:
                    entry['image'] = 'NA'

                entry['snippet'] = item['snippet']

                web_data.append(entry)
            return web_data
        else:
            logging.error(TAG + 'Error occurred while retreiving bing search results.')
            return {'error' : 'Results could not be retreived'}
        




