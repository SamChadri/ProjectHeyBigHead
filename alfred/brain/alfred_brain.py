from alfred.brain.decipher import Decipher 
from alfred.models.task_handler import TaskHandler
from alfred.models.task import *
from alfred.brain.intents import Intents
from alfred.mongodb.intent_store_m2 import *
from alfred.brain.intents_m2 import IntentsM2
import logging
import json


logger = logging.getLogger('alfred_logger')
logging.basicConfig(level=logging.DEBUG)

TAG = 'AlfredBrain: '
class AlfredBrain:


    def __init__(self):
        self.sst = Decipher()
        #self.intents = Intents()
        self.req_handler = TaskHandler()
        #self.intents.load_intents()
        #Test Intent store M2
        self.intents = IntentsM2()
        #self.intents.generate_containers()
        #self.intents.train_containers()
        #self.intents.train_intents()
        logger.debug("Alfred ready to proccess requests.")
        logging.basicConfig(level=logging.DEBUG)



    def process_req(self, data, audio=True, device_id='076dd3b443fad1d9065c41502a77db37fb8695a8'):
        if audio:
            data = self.sst.decode(data)
        result = self.intents.get_result(data)
        result.set_device_id(device_id)
        self.req_handler.process_message(result)

    def process_intent(self, data, audio=False):
        if audio:
            data = self.sst.decode(data)
        #TODO: Change this.
        result = self.intents.get_best_result(data)
        return json.dumps({'response_data' : result.__dict__}, default=str)

    def get_result(self):
        result = self.req_handler.get_results()
        index = 0
        yield '{ "response_data" : ['
        for data in result:
            logging.info("AlfredAPI Result: " + str(data))
            if index != 0:
                yield (',' + json.dumps(data.result(), default=str))
            else:
                yield json.dumps(data.result(), default=str)
            self.mark_done(data)
            index += 1
        yield ']}'

    def mark_done(self, task):
        self.req_handler.set_future_processed(task)


    def shut_down(self):
        self.req_handler.clean_up()


if __name__ == '__main__':
    brain = AlfredBrain()

    test_file = os.path.abspath('alfred/data/voice_data/sports_intent2.wav')
    request = input('How can I help you? ')
    if request == 'audio':
        logging.debug(TAG + 'Processing test audio file...')
        brain.process_req(test_file)
    else:
        brain.process_req(request, audio=False)
    
    results = brain.get_result()
    #for item in results:
        #print(item.)
    print('Done with the requests')
    brain.shut_down()


    