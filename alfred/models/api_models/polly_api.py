import boto3
from boto3 import Session
from contextlib import closing
from botocore.exceptions import BotoCoreError, ClientError
import os
import sys
import subprocess
import logging

TAG = 'PollyAPI: '


class PollyAPI:


    def __init__(self, voiceId='Brian'):
        self.session = Session(profile_name="youngtony")
        self.polly = self.session.client("polly", region_name="us-east-2")
        self.speech_dir = os.path.abspath('alfred/data/speech_data/')




    def get_alfred_speech(self, text, task_id):
        try:
            response = self.polly.synthesize_speech(Text=text, OutputFormat="mp3",VoiceId="Brian")
        except (BotoCoreError, ClientError) as error:
            logging.error(TAG + 'Boto error occurred: ' + str(error))
            return {'error' : error}
            #TODO add in a backup maybe?

        if "AudioStream" in response:
                logging.debug(TAG+ 'Successfully got polly response for text: ' + text)
                with closing(response['AudioStream']) as stream:
                    output = os.path.join(self.speech_dir, "alfred_speech_{}.mp3".format(task_id))

                    try:
                        # Open a file for writing the output as a binary stream
                        with open(output, "wb") as file:
                            file.write(stream.read())
                    except IOError as error:
                        # Could not write to file, exit gracefully
                        logging.error(TAG + 'IOError occurred: ' + str(error))
                        return {'error' : error}
                    else:
                        return {'speech_file' : output}
                    

        else:
            return {'error' : 'Stream unavailable'}