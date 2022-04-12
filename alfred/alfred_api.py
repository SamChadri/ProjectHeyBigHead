import os.path
import logging 
import sys
from alfred.brain.alfred_brain import AlfredBrain
from flask import Flask, flash, request, redirect, url_for, Response, escape, send_from_directory
import json

#TODO Implement clean shutdown of the task_handler


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
brain = AlfredBrain()

UPLOAD_FOLDER = os.path.abspath('alfred/data/voice_data/')
SPEECH_FOLDER = os.path.abspath('alfred/data/speech_data/')
ALLOWED_EXTENSIONS = {'mp3', 'wav'}
SPEECH_TEMPLATE = 'alfred_speech_{}.mp3'

TAG = 'AlfredAPI: '

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SPEECH_FOLDER'] = SPEECH_FOLDER

def allowed_file(file):
    return '.' in file and file.split('n', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def hello_world():
    return 'Welcome to the Aflred API'

@app.route('/voice_req', methods=['POST'])
def submit_voice_request():
    if request.method == 'POST':
        if 'req_file' not in request.files:
            flash('No file found')
            return 'invalid request', 400
        req_file = request.files['req_file']
        if req_file.filename == '':
            flash('invalid file')
            return 'invalid file', 400
        logging.info(TAG + 'Received {} file successfully'.format(req_file.filename))
        if allowed_file(req_file.filename):
            filename = secure_filename(req_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            req_file.save(file_path)
            brain.proccess_req(file_path)
            return Response(brain.get_result(), content_type='application/json')

    else:
        return 'Please submit POST request with voice file.'


@app.route('/text_req', methods=['POST'])
def submit_text_request():
    if request.method == 'POST':
        logging.info('Request form: ' + str(list(request.form.keys())))
        if 'req_text' not in request.form:
            flash('No request found')
            return 'invalid request', 400
        req_text = request.form['req_text']
        if req_text == '':
            flash('invalid request')
            return 'invalid file', 400
        logging.info(TAG + 'Received request: '.format(req_text))
        brain.process_req(req_text, audio=False)
        return Response(brain.get_result(), content_type='application/json')
    else:
        return 'Please submit POST request with text request'


@app.route('/speech_req/<string:task_id>', methods=['GET'])
def get_speech_response(task_id):
    if request.method == 'GET':
        task_id = escape(task_id)
        req_file = SPEECH_TEMPLATE.format(task_id)

        if os.path.exists(os.path.join(app.config['SPEECH_FOLDER'], req_file)):
            return send_from_directory(app.config['SPEECH_FOLDER'], req_file, as_attachment=True)

        else:
            return 'File not found', 400

@app.route('/intent_req', methods=['POST'])
def submit_intent_request():
    if request.method == 'POST':
        logging.info('Request form: ' + str(list(request.form.keys())))
        if 'intent_text' not in request.form:
            flash('No request found')
            return 'invalid request', 400
        intent_text = request.form['intent_text']
        print(f'Intent Text: {intent_text}')
        if intent_text == '':
            flash('invalid request')
            return 'invalid file', 400
        logging.info(TAG + 'Received request: {}'.format(intent_text))
        result = brain.process_intent(intent_text, audio=False)
        return Response(result, content_type='application/json')
    else:
        return 'Please submit POST request with text request'




 
def main():

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    dir_name = "data/deepspeech-0.6.1-models"
    wav_file = "data/media.io_VoiceTestBigHead.wav"
    voice_decoder = Decipher(dir_name)
    voice_decoder.batch_decode(wav_file)



if __name__ == '__main__':
    app.run(host='0.0.0.0')