from calendar import calendar
import os
import tempfile
import sys
import pytest
from alfred.alfred_api import app
import logging
import google.oauth2.credentials
from googleapiclient.discovery import build
import json
from datetime import datetime, timedelta
import dateutil
import dateparser


#TODO: Possibly run this in a container due to environment installs

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

    clear_loggers()

    
def clear_loggers():
    loggers = [logging.getLogger()] + list(logging.Logger.manager.loggerDict.values())
    for logger in loggers:
        handlers = getattr(logger, 'handlers', [])
        for handler in handlers:
            logger.removeHandler(handler)

def test_home(client):
    
    response = client.get('/')
    assert b'Welcome to the Aflred API' in response.data

def test_celeb_intent(client):
    request_string = "Who is Barack Obama"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "celeb"

    celeb_data = intent["result"]

    assert "name" in celeb_data
    assert "description" in celeb_data
    assert "image" in celeb_data
    assert "extract" in celeb_data
    assert "birth_date" in celeb_data

    assert "birth_place" in celeb_data
    assert "city" in celeb_data["birth_place"]
    assert "state" in celeb_data["birth_place"]


def test_musician_intent(client):
    request_string = "Who is Kanye West"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "celeb"

    assert intent["result"]["data_type"] == "musician"

    musician_data = intent["result"]

    assert "name" in musician_data
    assert "description" in musician_data
    assert "image" in musician_data
    assert "extract" in musician_data
    assert "birth_date" in musician_data

    assert "birth_place" in musician_data
    assert "city" in musician_data["birth_place"]
    assert "state" in musician_data["birth_place"]

    assert "genres" in musician_data
    assert "label" in musician_data



def test_athlete_intent(client):
    request_string = "Who is Stephen Curry"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "celeb"

    assert intent["result"]["data_type"] == "athlete"

    athlete_data = intent["result"]

    assert "name" in athlete_data
    assert "description" in athlete_data
    assert "image" in athlete_data
    assert "extract" in athlete_data
    assert "birth_date" in athlete_data


    assert "birth_place" in athlete_data
    assert "city" in athlete_data["birth_place"]
    assert "state" in athlete_data["birth_place"]

    assert "team" in athlete_data
    assert "number" in athlete_data
    assert "position" in athlete_data


def test_entertainment_intent(client):
    request_string = "What is the cast of Avengers Endgame"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "entertainment"

    ent_data = intent["result"]

    assert "title_id" in ent_data
    assert "title_name" in ent_data
    assert "title_year" in ent_data
    assert "title_rating" in ent_data
    assert "title_genres" in ent_data
    assert "title_directors" in ent_data
    assert "title_writers" in ent_data
    assert "title_cast" in ent_data
    assert "title_poster" in ent_data
    assert "title_plot" in ent_data
    assert "title_type" in ent_data

def test_sports_intent(client):
    #Note watch out for who is in the playoffs and code for that. Regular season as backup
    request_string = "Who won the last Timberwolves game"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "sports"

    sports_data = intent["result"]

    assert "game_id" in sports_data
    assert "game_time" in sports_data
    assert "away_team" in sports_data
    assert "home_team" in sports_data
    assert "home_logo" in sports_data
    assert "away_logo" in sports_data
    assert "game_name" in sports_data
    assert "home_score" in sports_data
    assert "away_score" in sports_data
    assert "game_quarters" in sports_data

    for entry in sports_data["game_quarters"]:
        assert "quarter_number" in entry
        assert "home_score" in entry
        assert "away_score" in entry
    


def test_sports_intent_backup(client):

    request_string = "Who won the last Bears game"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "sports"

    sports_data = intent["result"]

    assert "game_id" in sports_data
    assert "game_date" in sports_data
    assert "away_team" in sports_data
    assert "home_team" in sports_data
    assert "home_logo" in sports_data
    assert "away_logo" in sports_data
    assert "game_name" in sports_data
    assert "home_score" in sports_data
    assert "away_score" in sports_data

def test_weather_intent(client):

    request_string = "What is the temperature in Chicago"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "weather"

    weather_data = intent["result"]

    assert "city_data" in weather_data

    city_data = weather_data["city_data"]

    assert "country" in city_data
    assert "name" in city_data
    assert "sunrise" in city_data
    assert "sunset" in city_data
    assert "coord" in city_data
    assert "timezone" in city_data

    assert "lat" in city_data["coord"]
    assert "lon" in city_data["coord"]

    assert "forecast" in weather_data

    for entry in weather_data["forecast"]:
        assert "date" in entry
        assert "clouds" in entry
        assert "details" in entry

        details = entry["details"]

        assert "feels_like" in details
        assert "grnd_level" in details
        assert "humidity" in details
        assert "pressure" in details
        assert "sea_level" in details
        assert "temp" in details
        assert "temp_max" in details
        assert "temp_min" in details
        assert "pop" in details
        assert "precip" in details
        assert "snow" in details

        assert "conditions" in entry

        conditions = entry["conditions"]

        assert "condition" in conditions
        assert "details" in conditions
        assert "icon" in conditions



def test_search_intent(client):

    request_string = "Search the web for the Dark Knight"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "search"

    search_data = intent["result"]

    for item in search_data:
        assert "title" in item
        assert "link" in item
        assert "display_link" in item
        assert "image" in item
        assert "snippet" in item


def test_direction_intent(client):

    request_string = "What's a good sushi restaurant near me"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "directions"

    assert "url" in intent["result"]


def test_knowledge_intent(client):

    request_string = "What is hip-hop"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "wiki"

    knowledge_data = intent["result"]

    assert "title" in knowledge_data
    assert "extract" in knowledge_data
    assert "image" in knowledge_data

def test_calendar_intent(client):

    request_string = "Add an event to my calendar"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]


    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "calendar"

    calendar_data = intent["result"]

    assert "calendar_event" in calendar_data
    assert "event_type" in calendar_data
    assert "start_date" in calendar_data
    assert "end_date" in calendar_data

def test_calendar_intent_occurence(client):

    token_file = os.path.abspath("alfred/data/token.json")
    assert os.path.exists(token_file) == True

    request_string = "Add an event to my calendar every week for 3 weeks"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "calendar"

    calendar_data = intent["result"]

    assert "calendar_event" in calendar_data
    assert "event_type" in calendar_data
    assert "start_date" in calendar_data
    assert "end_date" in calendar_data

    calendar_event = calendar_data["calendar_event"]

    assert "recurrence" in calendar_event
    assert "id" in calendar_event

    id = calendar_event["id"]


    assert calendar_event["recurrence"][0] == 'RRULE:FREQ=WEEKLY;COUNT=3'


    data = {}
    

    with open(token_file) as file:
        data = json.load(file)

    creds = google.oauth2.credentials.Credentials(data["google_access_token"],
        refresh_token=data["google_refresh_token"],
        token_uri=data["google_refresh_uri"],
        client_id=data["google_client_id"],
        client_secret=data["google_client_secret"])
    
    calendar_api = build('calendar', 'v3', credentials=creds, cache_discovery=False)

    calendar_api.events().delete(calendarId='primary', eventId=id).execute()


def test_calendar_intent_time_1(client):
    token_file = os.path.abspath("alfred/data/token.json")
    assert os.path.exists(token_file) == True

    test_time = datetime.now() + timedelta(days=3)
    test_string = test_time.strftime("%B %d")
    request_string = f"Add an event to my calendar on {test_string} at 9:30AM"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    calendar_data = intent["result"]

    assert "calendar_event" in calendar_data
    assert "event_type" in calendar_data
    assert "start_date" in calendar_data
    assert "end_date" in calendar_data

    start_date = dateutil.parser.parse(calendar_data["start_date"])
    end_date = dateutil.parser.parse(calendar_data["end_date"])

    assert start_date.month == test_time.month
    assert start_date.year == test_time.year
    assert start_date.day == test_time.day

    assert start_date.hour == 9
    assert start_date.minute == 30

    assert end_date.month == test_time.month
    assert end_date.year == test_time.year
    assert end_date.day == test_time.day

    assert end_date.hour == 10
    assert end_date.minute == 30



    calendar_event = calendar_data["calendar_event"]

    assert "id" in calendar_event

    id = calendar_event["id"]


    with open(token_file) as file:
        data = json.load(file)

    creds = google.oauth2.credentials.Credentials(data["google_access_token"],
        refresh_token=data["google_refresh_token"],
        token_uri=data["google_refresh_uri"],
        client_id=data["google_client_id"],
        client_secret=data["google_client_secret"])
    
    calendar_api = build('calendar', 'v3', credentials=creds, cache_discovery=False)

    calendar_api.events().delete(calendarId='primary', eventId=id).execute()

def test_calendar_intent_time_2(client):
    token_file = os.path.abspath("alfred/data/token.json")
    assert os.path.exists(token_file) == True


    test_time = dateparser.parse("Friday",settings={'PREFER_DATES_FROM': 'future',})
    request_string = f"Schedule a meeting called Wanker to my calendar on Friday between 11:30AM and 12:30PM"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]

    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent
    

    calendar_data = intent["result"]

    assert "calendar_event" in calendar_data
    assert "event_type" in calendar_data
    assert "start_date" in calendar_data
    assert "end_date" in calendar_data

    start_date = dateutil.parser.parse(calendar_data["start_date"])
    end_date = dateutil.parser.parse(calendar_data["end_date"])

    assert start_date.month == test_time.month
    assert start_date.year == test_time.year
    assert start_date.day == test_time.day

    assert start_date.hour == 11
    assert start_date.minute == 30

    assert end_date.month == test_time.month
    assert end_date.year == test_time.year
    assert end_date.day == test_time.day

    assert end_date.hour == 12
    assert end_date.minute == 30


    calendar_event = calendar_data["calendar_event"]

    assert "id" in calendar_event

    id = calendar_event["id"]


    with open(token_file) as file:
        data = json.load(file)

    creds = google.oauth2.credentials.Credentials(data["google_access_token"],
        refresh_token=data["google_refresh_token"],
        token_uri=data["google_refresh_uri"],
        client_id=data["google_client_id"],
        client_secret=data["google_client_secret"])
    
    calendar_api = build('calendar', 'v3', credentials=creds, cache_discovery=False)

    calendar_api.events().delete(calendarId='primary', eventId=id).execute()

def test_calendar_intent_query(client):
    token_file = os.path.abspath("alfred/data/token.json")
    assert os.path.exists(token_file) == True

#------------ADD FIRST TEST EVENT---------------------------
    request_string = "Add an event to my calendar"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]


    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent
    
    calendar_data = intent["result"]


    calendar_event = calendar_data["calendar_event"]

    assert "id" in calendar_event

    id_1 = calendar_event["id"]

#------------ADD SECOND TEST EVENT-------------------------------
    request_string = "Add an event to my calendar on Sunday "
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]


    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent
    
    calendar_data = intent["result"]


    calendar_event = calendar_data["calendar_event"]

    assert "id" in calendar_event

    id_2 = calendar_event["id"]

#-----------------------------------------------------------------

    request_string = "When is my second event"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]


    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "calendar"

    calendar_data = intent["result"]

    assert 'event_num' in calendar_data
    assert calendar_data['event_num'] == 2

    assert 'event_type' in calendar_data
    assert calendar_data['event_type'] == 'event'

    assert 'events' in calendar_data

    assert 'init_query_time' in calendar_data

    assert 'query' in calendar_data
    assert 'query_date' in calendar_data



    with open(token_file) as file:
        data = json.load(file)

    creds = google.oauth2.credentials.Credentials(data["google_access_token"],
        refresh_token=data["google_refresh_token"],
        token_uri=data["google_refresh_uri"],
        client_id=data["google_client_id"],
        client_secret=data["google_client_secret"])
    
    calendar_api = build('calendar', 'v3', credentials=creds, cache_discovery=False)

    calendar_api.events().delete(calendarId='primary', eventId=id_1).execute()

    calendar_api.events().delete(calendarId='primary', eventId=id_2).execute()



def test_calendar_intent_update(client):
    token_file = os.path.abspath("alfred/data/token.json")
    assert os.path.exists(token_file) == True

#------------ADD FIRST TEST EVENT---------------------------
    request_string = "Add an event to my calendar"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]


    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent
    
    calendar_data = intent["result"]


    calendar_event = calendar_data["calendar_event"]

    assert "id" in calendar_event

    id_1 = calendar_event["id"]

#--------------------------------------------------------------

    request_string = "Update my next event location to Scrotal Recall"
    response = client.post('/text_req', data=dict(
        req_text=request_string
    ))
    json_data = response.get_json()
    assert "response_data" in json_data

    intent = json_data["response_data"][0]


    assert "message" in intent
    assert "result" in intent
    assert "intent" in intent
    assert "id" in intent

    assert intent["intent"] == "calendar"

    calendar_data = intent["result"]

    assert 'calendar_param' in calendar_data
    assert calendar_data['calendar_param'] ==  'location'

    assert 'calendar_update' in calendar_data
    assert calendar_data['calendar_update'] == 'Scrotal Recall'

    assert 'updated_event' in calendar_data


    with open(token_file) as file:
        data = json.load(file)

    creds = google.oauth2.credentials.Credentials(data["google_access_token"],
        refresh_token=data["google_refresh_token"],
        token_uri=data["google_refresh_uri"],
        client_id=data["google_client_id"],
        client_secret=data["google_client_secret"])
    
    calendar_api = build('calendar', 'v3', credentials=creds, cache_discovery=False)

    calendar_api.events().delete(calendarId='primary', eventId=id_1).execute()











    
    





    









 
