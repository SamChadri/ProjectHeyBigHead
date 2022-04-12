import os
from deepspeech import Model
from timeit import default_timer as timer
from alfred.brain import wavSplit
import logging 
from timeit import default_timer as timer
import numpy as np
import glob
import sox
from datetime import datetime
import webrtcvad

model_dir = os.path.abspath('alfred/data/deepspeech-0.7.1-models')
test_model = os.path.abspath('alfred/data/custom_models/output_graph_607.pb')
TAG = "DecipherClass"
class Decipher:



    def __init__(self, dir_name=model_dir):
        BEAM_WIDTH = 500
        LM_ALPHA = 0.75
        LM_BETA = 1.85

        now = datetime.now().time()
        current_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        logging.info("Decipher module log. DateTime: " + current_time)
        models = glob.glob(dir_name + "/*.pbmm")[0]
        #only use if 
        #lm = glob.glob(dir_name + "/lm.binary")[0]
        scorer = glob.glob(dir_name + "/*.scorer")[0]
        print(scorer)
        self.model = Model(test_model)
        self.model.enableExternalScorer(scorer)
        #self.model.enableDecoderWithLM(lm, trie, LM_ALPHA, LM_BETA)
        self.sample_rate = self.model.sampleRate()



    def batch_decode(self, wav_file):

        segments, sample_rate, audio_length = self.vad_segment_generator(wav_file, 2, self.sample_rate)
        filename = wav_file.rstrip(".wav") + ".txt" 

        f = open(filename ,"w")
        logging.info("Filename: " + wav_file)
        for i, segment in enumerate(segments):
            # Run deepspeech on the chunk that just completed VAD
            inference_time = 0.0
            logging.debug(TAG +"Processing chunk %002d" % (i,))
            audio = np.frombuffer(segment, dtype=np.int16)
            output, total_time = self.inference(self.model, audio, sample_rate)
            inference_time += total_time 
            logging.debug(TAG + "Transcript: %s" % output)
            logging.info(TAG + "Transcript: %s" % output)

            f.write(output + " ")

        # Summary of the files processed
        f.write("\n")
        logging.info("\n \n")
        f.close()
        return output


    def decode(self, wav_file):
        filename = wav_file.rstrip(".wav") + ".txt" 

        f = open(filename,"w")
        logging.info("Filename: " + wav_file)

        audio, sample_rate = wavSplit.convert_wave(wav_file, self.sample_rate)
        logging.debug(TAG + "Processing entire file...")
        output, e_time =self.inference(self.model, audio, sample_rate)

        logging.debug(TAG + "Unsegmented Transcript: %s" % output)
        logging.info(TAG + "Unsegmeneted Transcript: %s" % output)

        f.write(output + "\n" )
        logging.info('\n \n')
        f.close()
        
        return output


    def inference(self, model, audio, sample_rate):
        inference_time = 0.0
        audio_length = len(audio) * (1 / sample_rate)
        
        logging.debug(TAG + "Running inference")
        inference_start = timer()
        output = model.stt(audio)
        inference_end = timer() - inference_start
        
        inference_time += inference_end
        logging.debug(TAG + 'Inference took %0.3fs for %0.3fs audio file.' % (inference_end, audio_length))

        return output, inference_time
    


    def vad_segment_generator(self, wav_file, aggressiveness, model_sample_rate):
        #logging.debug("Caught the wav file @: %s" % (wav_file))
        wav_file =wavSplit.modify_wave(wav_file, model_sample_rate)
        audio, sample_rate, audio_length = wavSplit.read_wave(wav_file)
        logging.debug(TAG + "Sample rate= {0}, Model sample rate= {1}".format(sample_rate, model_sample_rate))
        assert sample_rate == model_sample_rate, \
            "Audio sample rate must match sample rate of used model: {}Hz".format(model_sample_rate)
        vad = webrtcvad.Vad(int(aggressiveness))
        frames = wavSplit.frame_generator(30, audio, sample_rate)
        frames = list(frames)
        logging.debug(TAG + "Audio Length: {}".format(audio_length))
        segments = wavSplit.vad_collector(sample_rate, 30, 300, vad, frames)

        return segments, sample_rate, audio_length


