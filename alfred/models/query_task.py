from alfred.models.task import Task 
from alfred.mongodb.intent_data import IntentData
from alfred.models.api_models.search_api import SearchAPI

from azure.cognitiveservices.search.websearch import WebSearchClient
from azure.cognitiveservices.search.websearch.models import SafeSearch
from msrest.authentication import CognitiveServicesCredentials

import logging 
import asyncio

class QueryTask(Task):

    GOOGLE_ENGINE = 0
    BING_ENGINE = 1

    search_response = 'This is what I got'
    

    #TODO: Make the api_key an enviroment variable later.


    
    def action(self):
        if 'query' in self.message.matches:
            self.result = self.api.search_request(self.message.matches['query'])
        web_data = client.web.search(query=data)
        
        

    def response(self):
        return {'message' : search_response, 'result' : self.result, 'intent': self.message.intent}


class SportsTask(Task):


    def action(self):
        if 'event_type' in self.message.matches and 'team' in self.message.matches:
            pass





