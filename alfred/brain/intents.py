from padatious import IntentContainer
from alfred.mongodb.intent_store import IntentStore
from alfred.mongodb.intent_data import IntentData
from alfred.models.task import *
import sys
import os
import logging

intent_path = os.path.curdir+'intent_cache'
intent_template = os.path.abspath('alfred/data/container_data/{}_intent_cache')
TAG = 'Intents: '
class Intents:

#TODO maybe change the use of instance to just the class....but I need a good reason why
    def __init__(self, path=intent_path):
        self.path = path
        self.local_storage = IntentData()
        #self.data_store = IntentStore()
        self.container = IntentContainer(self.path)
        self.container_dict = {}


    def load_intents(self):
        logging.debug(TAG + "Loading intents into container....")
        intents = self.local_storage.get_data_intents()
        entities = self.local_storage.get_data_entities()
        for intent in intents:
            intent_data = self.data_store.get_intent_values(intent)
            self.container.add_intent(intent_data["intent"], intent_data["intent_values"], (not intent_data['cached']))
            self.data_store.set_intent_cached(intent_data["intent"], True)
        for entity in entities:
            entity_data = self.data_store.get_entity_values(entity)
            self.container.add_entity(entity_data['entity'], entity_data['entity_values'], (not entity_data['cached']))
            self.data_store.set_entity_cached(entity_data["entity"], True)

        logging.debug(TAG + 'Finished loading intents')

    def generate_containers(self):
        logging.debug(TAG + "Generating containers for each database collection...")
        intents = self.local_storage.get_data_intents()
        entities = self.local_storage.get_data_entities()
        db_names = self.local_storage.get_db_names()

        for name in db_names:
            self.container_dict[name] = IntentContainer(intent_template.format(name)) 

        for intent in intents:
            db_name = self.local_storage.get_intent_db(intent)
            intent_data = self.data_store.get_intent_values(intent)
            self.container_dict[db_name].add_intent(intent_data["intent"], intent_data["intent_values"], (not intent_data['cached']))
            self.data_store.set_intent_cached(intent_data["intent"], True)
        for entity in entities:
            db_name = self.local_storage.get_entity_db(entity)
            entity_data = self.data_store.get_entity_values(entity)
            self.container_dict[db_name].add_entity(entity_data['entity'], entity_data['entity_values'], (not entity_data['cached']))
            self.data_store.set_entity_cached(entity_data["entity"], True)
        logging.debug(TAG + "Finished generating containers")
    def train_containers(self):
        #TODO Check this out later...
        for container in self.container_dict.values():
            container.train(timeout=40)

    #TODO differentiate between sports cities. Ex. Who won the last Chicago game?
    def get_best_result(self, data):
        results = []
        for container in self.container_dict.values():
            results.append(container.calc_intent(data))
        
        print(str(results) + '\n \n')
        max_value =  results.pop()
        for result in results:
            if result.conf > max_value.conf:
                max_value = result

        retval = Message(max_value.name, max_value.sent, max_value.matches, max_value.conf)
        db_intent = self.check_sub_intent(max_value.name)
        if db_intent != 'NA':
            retval.set_db_intent(db_intent)

        logging.debug(TAG + "Generated message: " + str(retval))
        return retval



    def train_intents(self):
        self.container.train(timeout=40)
        logging.debug(TAG + 'Trained intents')

    #TODO maybe keep this in the matcher format?
    def get_result(self, data):
        matcher = self.container.calc_intent(data) 
        retval = Message(matcher.name, matcher.sent, matcher.matches, matcher.conf)
        print('Matcher name: {}'.format(matcher.name))
        db_intent = self.check_sub_intent(matcher.name)
        if db_intent != 'NA':
            print('Setting db_intent')
            print(retval)
            retval.set_db_intent(db_intent)

        return retval    


    def check_sub_intent(self, label):
        if label.find('_') != -1:
            return label.split('_')[0]

        return 'NA'
    



if __name__ == '__main__':
    intents = Intents()
    #intents.load_intents()
    intents.generate_containers()

    intents.train_containers()
    print(intents.data_store.get_intent_values('sports'))
    print(intents.data_store.get_entity_values('event_type'))
    print(intents.data_store.get_entity_values('team'))

    container = IntentContainer(intent_path)

    #print("Get Result: " + str(intents.get_result('Who won the last Heat game')))
    print("Get Best Result: " + str(intents.get_best_result('Who won the last lakers game')))
    print(container.calc_intent('Hey Big Dog'))

