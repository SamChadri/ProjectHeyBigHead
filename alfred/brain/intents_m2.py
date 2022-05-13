from html import entities
from typing import Any
from alfred.mongodb.intent_store_m2 import IntentStoreM2
from alfred.mongodb.intent_data import IntentData
from alfred.models.task import *
import os
import logging
import io
import json
from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_EN

TAG = "IntentsM2: "

class IntentsM2:
    SEED = 69
    ENGINE = "engine_v1"
    DATASETS = {
        "CORE":  "core",
        "EXP": "expanded"
    }
    def __init__(self):
        self.data_store = IntentStoreM2()
        self.local_storage = IntentData()
        self.dataset_path = os.path.abspath('alfred/mongodb/intent_datasets/{}_intents_backup.yaml')
        self.final_dataset = os.path.abspath('alfred/mongodb/intent_datasets/final_dataset.json')
        self.engine_path = os.path.abspath('alfred/data/intent_engines/')

        self.convert_dataset()
        if self.engine_exists():
            self.engine = self.load_engine()
        else:
            self.engine = self.create_engine()
            self.save_engine()
        

    def convert_dataset(self) -> None:
        if not os.path.exists(self.final_dataset):
            logging.info(f"{TAG} Json dataset for {self.final_dataset} does not exist. Creating one in inte_datasets/ directory")
            
            core_dataset = self.dataset_path.format(self.DATASETS["CORE"])
            expanded_dataset = self.dataset_path.format(self.DATASETS["EXP"])

            if os.path.exists(expanded_dataset):
                logging.info(f"{TAG} Creating expanded final dataset...")
                os.system(f"snips-nlu generate-dataset en {core_dataset} {expanded_dataset} > {self.final_dataset}")
            else:
                logging.info(f"{TAG} Creating core final dataset...")
                os.system(f"snips-nlu generate-dataset en {core_dataset} > {self.final_dataset}")


    def engine_exists(self) -> bool:
        return os.path.exists(os.path.join(self.engine_path, 'nlu_engine.json'))

    def load_engine(self) -> Any:
        logging.info(f"{TAG} Loading engine from path: {self.engine_path}")
        engine = os.path.exists(os.path.join(self.engine_path, 'nlu_engine.json'))
        loaded_engine = SnipsNLUEngine.from_path(self.engine_path)
        return loaded_engine

    def save_engine(self) -> None:
        logging.info(f"{TAG} Saving engine to path: {self.engine_path}")
        self.engine.persist(self.engine_path)
        #TODO: Save to database


    def create_engine(self) -> SnipsNLUEngine:
        logging.info(f"{TAG} Creating engine from dataset: {self.final_dataset}")
        engine = SnipsNLUEngine(config=CONFIG_EN, random_state=self.SEED)
        with io.open(self.final_dataset) as f:
            dataset = json.load(f)
        engine.fit(dataset)
        return engine

    def get_result(self, data) -> Any:
        result = self.engine.parse(data)
        if result["intent"] == None:
            retval = Message("None", result["input"], {"entities": "none"}, result["intent"]["probability"])
            return retval
    
        entities = {}
        extra_entities = {}
        slots = {}
        for slot in result["slots"]:
            entity = slot["entity"]
            slot_name = slot["slotName"]
            value = slot["value"]["value"]
            if entity in entities:
                if entity not in extra_entities:
                    extra_entities[entity] = []
                extra_entities[entity].append(value)
            else:
                entities[entity] = value
            
            slots[slot_name] = value


        retval = Message(result["intent"]["intentName"],result["input"],entities, result["intent"]["probability"])
        retval.set_slot_names(slots)
        retval.set_extra_entities(extra_entities)
        logging.debug(TAG + "Generated message: " + str(retval))

        return retval
    




if __name__ == '__main__':

    logging.debug(TAG + 'Generating json dataset...')
    yaml_dataset = os.path.abspath("alfred/mongodb/intent_datasets/core_intents_backup.yaml")
    json_dataset = os.path.abspath("alfred/mongodb/intent_datasets/core_dataset.json")

    os.system(f"snips-nlu generate-dataset en {yaml_dataset} > {json_dataset}")
    engine = SnipsNLUEngine(config=CONFIG_EN)
    logging.debug(TAG + 'Loading dataset...')

    with io.open(json_dataset) as f:
        dataset = json.load(f)
    
    request = input('Please provide a phrase for intent parsing.')
    engine.fit(dataset)
    parsing =  engine.parse(request)
    print(json.dumps(parsing, indent=2))