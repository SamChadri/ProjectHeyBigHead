from padatious import IntentContainer
from alfred.mongodb.intent_store import IntentStore
from alfred.mongodb.intent_data import IntentData
from alfred.models.task import *
import sys
import os
import logging

intent_path = os.path.curdir+'intent_cache'
TAG = 'Intents: '
class Intents:

    
    def __init__(self, path=intent_path):
        self.path = path
        self.local_storage = IntentData()
        self.data_store = IntentStore()
        self.container = IntentContainer(self.path)


    def load_intents(self):
        logging.debug(TAG + "Loading intents into container....")
        intents = self.local_storage.get_data_intents()
        entities = self.local_storage.get_data_entities()
        for intent in intents:
            intent_data = self.data_store.get_intent_values(intent)
            self.container.add_intent(intent_data["intent"], intent_data["intent_values"], (not intent_data["cached"]) )
            self.data_store.set_intent_cached(intent_data["intent"], True)
        for entity in entities:
            entity_data = self.data_store.get_entity_values(entity)
            self.container.add_entity(entity_data['entity'], entity_data['entity_values'], (not entity_data["cached"]))
            self.data_store.set_entity_cached(entity_data["entity"], True)

        logging.debug(TAG + 'Finished loading intents')



    def train_intents(self):
        self.container.train()
        logging.debug(TAG + 'Trained intents')

    #TODO maybe keep this in the matcher format?
    def get_result(self, data):
        matcher = self.container.calc_intent(data) 
        print(matcher.name)
        retval = Message(matcher.name, matcher.sent, matcher.matches, matcher.conf)
        return retval    






if __name__ == '__main__':
    intents = Intents()
    intents.load_intents()
    intets.train_intents()
    container = IntentContainer(intent_path)

    print(intents.get_result('Hey Big Dog'))
    print(container.calc_intent('Hey Big Dog'))

