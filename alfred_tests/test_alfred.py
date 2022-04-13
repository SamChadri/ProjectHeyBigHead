import os
import tempfile
import sys
import pytest
from alfred.alfred_api import app
import logging

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

    request_string = "Who won the last Bucks game"
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




    









 
