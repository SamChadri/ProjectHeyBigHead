from alfred.mongodb.intent_store import *
from alfred.brain.decipher import *
import json
from alfred.models.api_models.polly_api import *
import uuid 

class Message:

    def __init__(self, intent, msg, entities, confidence):
        self.intent = intent
        self.msg = msg
        self.confidence = confidence 
        self.entities = entities
        
    def set_slot_names(self, slots):
        self.slots = slots

    def check_entity_slot(self, entity) -> str:
        entity_value = self.entities[entity]
        for key, val in self.slots:
            if val == entity_value and key != entity:
                return key
        return entity_value



    def set_db_intent(self, db_intent):
        self.db_intent = db_intent

    def set_device_id(self, device_id):
        self.device_id = device_id

    
    def convert_object(self,obj):
        return obj.__dict__

    def __str__(self):
        return json.dumps(self, indent=4, default=self.convert_object)


class Task(object):

    def __init__(self, message):
        self.message = message
        self.response_message = 'This is what I got'
        self.speech_api = PollyAPI()
        self.id = uuid.uuid4()

    def action(self):
        """ Executes the intented action  """
        #TODO might change this later
        self.result = {'error': 'Query could not be found'}

    def response(self):
        """ Returns a response to the user"""
        """ For when responses get complicated. EX. Unique sports responses """
        return {'message': response_message, 'result': self.result , 'intent':'NA'}


    def generate_speech(self):
        response = self.speech_api.get_alfred_speech(self.response_message, self.id)
        if 'speech_file' in response:
            return response['speech_file']
        else:
            #TODO Return temp error message
            pass


 
