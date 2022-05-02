import string
from typing import Any, Iterator, List
import pymongo
from .intent_data import IntentData
import os
import json
import io 
import logging
import yaml
from datetime import datetime
from alfred.mongodb.api_store import APIStore

from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_EN

logger = logging.getLogger('alfred_logger')
logging.basicConfig(level=logging.DEBUG)

TAG = "intentStoreM2::"

class IntentStoreM2:

    def __init__(self) -> None:
        logging.basicConfig(filename='alfred.log', level=logging.INFO)
        now = datetime.now().time()
        current_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        logging.info('Run DateTime: ' + current_time)

        self.intent_file = os.path.abspath('alfred/mongodb/intent_datasets/core_intents_backup.yaml')
        self.intent_constants = IntentData()
        self.init_collections()
        self.api_store = APIStore()        
        self.init_db()
    
    def init_collections(self) -> None:
        mongo_client = pymongo.MongoClient(os.environ['MONGO_IP'])
        self.intent_db = mongo_client["intent_database"]
        self.intent_config = mongo_client["config"]["intent_db"]
        self.salutation_intents = self.intent_db["salutation_intents"]
        self.search_intents = self.intent_db["search_intents"]
        self.sports_intents = self.intent_db["sports_intents"]
        self.wiki_intents = self.intent_db["wiki_intents"]
        self.map_intents = self.intent_db["map_intents"]
        self.ent_intents = self.intent_db["entertainment_intents"]
        self.weather_intents = self.intent_db["weather_intents"]
        self.time_intents = self.intent_db["time_intents"]
        self.spotify_intents = self.intent_db['spotify_intents']
        self.calendar_intents = self.intent_db['calendar_intents']
       
    def init_db(self) -> None:
        if not self.check_db():
            logging.info(TAG + "Intent database not initialized")
            self.populate_db()
            self.api_store.init_database()

        else:
            logging.info(TAG + "Intent database already intitialized")
            self.check_updates()
    
    def populate_db(self)-> None:
        logging.info(f"{TAG} Populating database...")
    
        data : list
        with open(self.intent_file,'r') as file:
            data = list(yaml.load_all(file, Loader=yaml.FullLoader))
        for document in data:
            collection_name = ""
            if document["type"] == "intent":
                collection_name = self.intent_constants.get_intent_db(document["name"])
            else:
                collection_name= self.intent_constants.get_entity_db(document["name"])


            result = self.intent_db[collection_name].insert_one(document)
            d_type = document["type"]
            d_name = document["name"]
            logging.info(f"{TAG} Inserted {d_type}::{d_name} with into {collection_name} with id: {result.inserted_id} ")
        init_db = {
            "initialized": True
        }
        self.intent_config.insert_one(init_db)
    
    def check_updates(self)-> None:
        logging.info(f"{TAG} Checking for intent and entity updates....")

        update = {
            "database": False,
            "file": False,
        }

        data: list 
        with open(self.intent_file,'r') as file:
            data = list(yaml.load_all(file, Loader=yaml.FullLoader))
        
        data_list = data
        for i in range(len(data_list)):
            document = data_list[i]
            d_type = document["type"]
            d_name = document["name"]
            db_doc : Any
            colleciton_name :string
            doc_values : List
            db_values : List
            if d_type == "intent":
                collection_name = self.intent_constants.get_intent_db(d_name)
                db_doc = self.get_intent_values(d_name)
                doc_values : List = document["utterances"]
                db_values : List = db_doc["utterances"]
                pass
            else:
                collection_name = self.intent_constants.get_entity_db(d_name)
                db_doc = self.get_entity_values(d_name)
                doc_values : List = document["values"]
                db_values : List = db_doc["values"]
                pass
            
            
            
            for item in db_values:
                if item not in doc_values:
                    logging.info(f"{TAG} New intent value:{item} added to the database. Writing to local file for backup...")
                    doc_values.append(item)
                    update["file"] = True
                    if d_type == "intent":
                        document["utterances"] = doc_values
                    else:
                        document["values"] = doc_values
            
            data_list[i] = document

            for item in  doc_values:
                if item not in db_values:
                    logging.info(f"{TAG} New intent value:{item} added to the local file. Writing change to database...")
                    update["database"] = True
                    if d_type == "intent":
                        self.add_intent_value(d_name, item)
                    else:
                        self.add_entity_value(d_name, item)


        if update["file"]:
            logging.info(f"{TAG} Finalizing local file store update... ")
            with open(self.intent_file, 'w') as outfile:
                yaml.dump_all(data_list, outfile, default_flow_style=False)
        elif update["database"]:
            logging.info(f"{TAG} Finalized databse update...")
            pass
        else:
            logging.info(f"{TAG} No changes detected. No updates performed")


        pass

    def insert_intent(self, intent, slots, utterances):
        entry = {
            "type": "intent",
            "name": intent,
            "slots": slots,
            "utterances": utterances
        }
        db_name = self.intent_constants.get_intent_db(intent)
        retval  = self.intent_db[db_name].insert_one(entry)

        logging.info(f"{TAG} Inserting intent:{intent} with id: {retval.inserted_id} ")

        return retval.inserted_id
    

    def add_intent_value(self, intent, intent_value) -> Any:
        param = {}
        param["name"] = intent

        new_val = {"$push" :{"utterances": intent_value}}
        db_name = self.intent_constants.get_intent_db(intent)
        retval = self.intent_db[db_name].update_one(param, new_val)
        logging.info(f"{TAG} Adding intent value: {intent_value}, to document with id: {retval.upserted_id}")
        return retval.modified_count

    def get_intent_values(self, intent) -> Any :
        param = {
            "name": intent
        }

        
        db_name = self.intent_constants.get_intent_db(intent)
        #print("db_name: " + db_name)
        #print("intent: "+ intent)
        
        return self.intent_db[db_name].find_one(param)

    

    def add_slot_value(self, intent, slot_name, slot_entity) -> Any:
        param = {
            "name": intent
        }


        slot_values = {
            "name": slot_name,
            "entity": slot_entity
        }

        new_val = {"$push" :{"slots": slot_values}}
        db_name = self.intent_constants.get_intent_db(intent)
        retval = self.intent_db[db_name].update_one(param, new_val)
        logging.info(f"{TAG} Adding slot value: {slot_values}, to document with id: {retval.upserted_id}")
        return retval.modified_count
    
    def insert_entity(self, entity, entity_values)-> Any:
        entry = {
            "type": "entity",
            "name": entity,
            "values": entity_values
        }
        db_name = self.intent_constants.get_entity_db(entity)
        retval = self.intent_db[db_name].insert_one(entry)
        logging.info(f"{TAG} Inserting entity:{entity} with id: {retval.inserted_id} ")

        return retval.inserted_id

    def add_entity_value(self, entity, entity_value) -> Any:
        param = {
            "name": entity
        }

        new_val = {"$push" :{"values": entity_value}}
        db_name = self.intent_constants.get_entity_db(entity)
        retval = self.intent_db[db_name].update_one(param, new_val)
        logging.info(f"{TAG} Adding entity value: {entity_value}, to document with id: {retval.upserted_id}")
        return retval.modified_count
    
    def get_entity_values(self, entity) -> Any:
        param = {
            "name": entity
        }

        
        db_name = self.intent_constants.get_entity_db(entity)
        #print("db_name: " + db_name)
        #print("intent: "+ intent)
        
        return self.intent_db[db_name].find_one(param)
    

    def check_db(self) -> bool:
        param = {"initialized": True}

        result =  self.intent_config.find_one(param) 
        return (result != None)
    

if __name__ == '__main__':


    logging.debug(TAG + 'Generating json dataset...')
    yaml_dataset = os.path.abspath("alfred/mongodb/intent_datasets/core_intents.yaml")
    json_dataset = os.path.abspath("alfred/mongodb/intent_datasets/core_dataset.json")

    os.system(f"snips-nlu generate-dataset en {yaml_dataset} > {json_dataset}")
    engine = SnipsNLUEngine(config=CONFIG_EN)
    logging.debug(TAG + 'Loading dataset...')

    with io.open(json_dataset) as f:
        dataset = json.load(f)
    
    request = input('Please provide a phrase for intent parsing. ')
    engine.fit(dataset)
    parsing =  engine.parse(request)
    print(json.dumps(parsing, indent=2))

