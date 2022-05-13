import logging 
import asyncio
from alfred.mongodb.intent_data import *
from alfred.models.task import Message
from alfred.models.event_tasks import *
from concurrent.futures import *
from pprint import pformat

TAG = "TaskHandler: "

class TaskHandler:

    # Idea behind this is that every time a message comes in, we put it in a queue and generate a worker from a pool of workers to process the queue.
    # If all workers are busy the code should block theoretically.
    def __init__(self, workers=3):
        self.workers = workers
        self.wait_queue = asyncio.Queue()
        self.tasks = []
        self.run = True
        self.executor = ThreadPoolExecutor(max_workers=workers)


    def worker(self, name, queue):
        try:
            message  = queue.get_nowait()
        except RuntimeError as e:
            #This really shouldn't happen, but who knows
            logging.debug(TAG + e)
            return {'error' : 'Request not found'}
        else:
            task  = self.generate_task(message)
            task.action()
            response = task.response()
            logging.debug(TAG + f"Alfred API result: {pformat(response)}")
            #task.generate_speech()
            queue.task_done()
            return response

    

    def process_message(self, message):
        self.wait_queue.put_nowait(message)
        future = self.executor.submit(self.worker, f'worker = {message.intent}', self.wait_queue)
        logging.debug(TAG + f"Submitted worker to process message  '{message.msg}' ")
        logging.debug(TAG + f"Entities found: {message.entities}")
        self.tasks.append(future)

    
    def get_results(self):
        print(self.tasks)
        results =  as_completed(self.tasks)
        #for i in results:
            #print("Future object finished: " + str(i.done()))
            #print(i.result())
            #print('future completion:  ' + str(i))
        return results

    def set_future_processed(self, future):
        for task in self.tasks:
            if task.result() == future.result() and future.done():
                self.tasks.remove(task)

    def clean_up(self):
        self.executor.shutdown()

    def generate_task(self, message):
        intent_data = IntentData()
        intent = message.intent

        if intent == intent_data.hello_intent or intent == intent_data.bye_intent or intent == intent_data.hay_intent:
            logging.debug(TAG + f'Intent: {intent}. Creating ConversationTask to be processed.')
            task = ConversationTask(message)
            #Create Specialized task
        elif intent == intent_data.query_intent:
            logging.debug(TAG + f'Intent: {intent}. Creating QueryTask to be processed.')
            task = QueryTask(message)

        elif intent == intent_data.sports_intent:
            logging.debug(TAG + f'Intent: {intent}. Creating SportsTask to be processed.')
            task = SportsTask(message)

        elif intent == intent_data.entertainment_intent:
            logging.debug(TAG + f'Intent: {intent}. Creating EntertainmentTask to be processed.')
            task = EntertainmentTask(message)

        elif intent == intent_data.map_intent:
            logging.debug(TAG + f'Intent: {intent}. Creating MapTask to be processed')
            task = MapTask(message)
        
        elif intent == intent_data.weather_intent:
            logging.debug(TAG + f'Intent: {intent}. Creating WeatherTask to be processed')
            task = WeatherTask(message)

        elif intent == intent_data.wiki_intent or intent == intent_data.celeb_intent:
            logging.debug(TAG + f'Intent: {intent}. Creating WikiTask to be processed')
            task = WikiTask(message)

        elif intent == intent_data.spotify_player_intent or intent == intent_data.spotify_intent:
            logging.debug(TAG + f'Intent: {intent}. Creating SpotifyTask to be processed')
            task = SpotifyTask(message)
            print('Spotify Task created')
        
        elif intent == intent_data.calendar_intent:
            logging.debug(TAG + f'Intent: {intent}. Creating CalendarTask to be processed')
            task = CalendarTask(message)


        else:
            logging.debug(TAG + f'Intent {intent}. Creating generic task to be processed')
            task = QueryTask(message)
            #Create Generic task?

        return task
        