import pymongo
from .intent_data import IntentData
import os
import json
import io 
import logging
from datetime import datetime
from alfred.mongodb.api_store import APIStore

from snips_nlu import SnipsNLUEngine
from snips_nlu.default_configs import CONFIG_EN

logger = logging.getLogger('alfred_logger')
logging.basicConfig(level=logging.DEBUG)

TAG = "intentStoreM2::"

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

