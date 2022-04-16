from alfred.mongodb.api_store import APIStore 
import requests
from requests.exceptions import RequestException
import logging 
import os
import json
from pprint import pprint

NBA = 0
NFL = 1
TAG = "SportsAPI:"

sportsdb_endpoint = "https://www.thesportsdb.com/api/v1/json/2/eventslast.php?id={}"


msf_nba_teamEndpoint = 'https://api.mysportsfeeds.com/v1.2/pull/nba/latest/full_game_schedule.json'
msf_nba_boxEndpoint = "https://api.mysportsfeeds.com/v1.2/pull/nba/latest/scoreboard.json"

msf_nfl_teamEndpoint = 'https://api.mysportsfeeds.com/v1.2/pull/nfl/latest/full_game_schedule.json'
msf_nfl_boxEndpoint = "https://api.mysportsfeeds.com/v1.2/pull/nfl/latest/scoreboard.json"
#TODO: Deal with spaces edge case for team names. And if it cannot find match in sports league.
#TODO: Deal with 76'ers edge case
#TODO: Edge case for when games are canceled/postponed. Fill in Score with something else.

#TODO: Figure out how to get the difference between playoff and regular seaon, and switch between seasons

#TODO: Remeber to set the APIStore db when using this API
class SportsAPI:

    #TODO Maybe get rid of instance and just use class and its methods...again need a good reason why.
    #TODO Add in backup API's. Really get one that supports box score
    #TODO Make the api_keys and password enviromental variables
    def __init__(self, key_file=os.path.abspath('alfred/data/keys.json')):
        self.endpoint = sportsdb_endpoint
        self.storage = APIStore()
        self.key_file = key_file
        with open(self.key_file) as f:
            data = json.load(f)
            msf_password = data["msfPassword"]
            self.msf_password = data["msfPassword"]
            self.msf_key = data["msfKey"]

    
    def set_league(self, team):
        val = self.storage.get_league(team)
        if val == 0:
            self.team_endpoint = msf_nba_teamEndpoint
            self.box_endpoint = msf_nba_boxEndpoint
        elif val == 1:
            self.team_endpoint = msf_nfl_teamEndpoint
            self.box_endpoint = msf_nfl_boxEndpoint   
        if val == -1:
            raise Exception("Cannot match to a valid sports league")

        self.league = val    

    def last_game(self, team):
        team_data = {}
        try:
            #Commented for testing purposes
            #self.set_league(team)
            retval = self.msf_getLastGame(team)
        except Exception as e:
            logging.error(TAG + "MySportsFeed endpoint failed to retrieve data with error: {}. Trying SportsDB endpoint.... ".format(e))

            try:
                retval = self.sdb_getLastGame(team)
            except Exception as e:
                logging.error(TAG + "SposrtsDB endpoint failed to retrieve data.")
                return {"error" : e}
            else:
                return retval

        else:
            return retval



    def msf_getLastGame(self,team):
        logging.debug(TAG + "Starting sportsAPI request...")
        team_data = {}
        if self.league == NBA:
            team_data = self.storage.get_nba_team(team)
        else:
            team_data = self.storage.get_nfl_team(team)

        try:
            team_response= requests.get(self.team_endpoint,params={"date":"from-5-months-ago-to-yesterday","team":team_data["name_short"]}, auth=(self.msf_key, self.msf_password))
            if team_response.status_code != 200:
                raise Exception("API endpoint request failed with status code: " + str(team_response.status_code))
            logging.info(TAG + "MSF request for {} returned successfully with status code: ".format(team) + str(team_response.status_code))
            #pprint(team_response.json()['teamgamelogs'])
            
            if "game_entry" not in team_response.json()["fullgameschedule"]:
                pass
                #TODO check the last regular season here
            #pprint(team_data)
            last_game = team_response.json()["fullgameschedule"]["gameentry"][-1]

            game_date = last_game['date'].replace('-','')

            game_response = requests.get(self.box_endpoint,params={"fordate":game_date,"team":team_data["name_short"]}, auth=(self.msf_key, self.msf_password))

            if game_response.status_code != 200:
                raise Exception("API endpoint request failed with status code: " + str(team_response.status_code))

            logging.info(TAG + "MSF boxscore request returned successfully with status code: ".format(team) + str(team_response.status_code))
            
        except RequestException as e:
            logging.error(TAG + "RequestException error occurred: " + str(e))
            raise Exception(TAG + "RequestException error occurred: " + str(e))

        else:
            data = game_response.json()['scoreboard']['gameScore'][0]
            game_data = {}
            #pprint(data)
            game_data["game_id"] = data['game']['ID']
            #TODO Fixed time key, rebuild image
            game_data["game_time"] = data["game"]["time"]
            game_data["away_team"] = data["game"]["awayTeam"]["City"] + ' ' + data["game"]["awayTeam"]["Name"]
            game_data["home_team"] = data["game"]["homeTeam"]["City"] + ' ' + data["game"]["homeTeam"]["Name"]

            if self.league == NBA:
                game_data["home_logo"] = self.storage.get_nba_team(game_data["home_team"])["team_logo"]
                game_data["away_logo"] = self.storage.get_nba_team(game_data["away_team"])["team_logo"]

            else:
                game_data["home_logo"] = self.storage.get_nfl_team(game_data["home_team"])["team_logo"]
                game_data["away_logo"] = self.storage.get_nfl_team(game_data["away_team"])["team_logo"]

            game_data["game_name"] = game_data["home_team"] + " vs. " + game_data["away_team"]
            game_data["home_score"] = data["homeScore"]
            game_data["away_score"] = data["awayScore"]
            game_data["game_quarters"] = []
            for quarter in data["quarterSummary"]["quarter"]:
                entry = {}
                entry["quarter_number"] = quarter["@number"]
                entry["home_score"] = quarter["homeScore"]
                entry["away_score"] = quarter["awayScore"]
                game_data["game_quarters"].append(entry)

            game_data['source'] = 'msf'
            
            return game_data



    """ Throws possible Custom Exception """
    def sdb_getLastGame(self, team):
        team_data = {}
        if self.league == NBA:
            team_data = self.storage.get_nba_team(team)
        else:
            team_data = self.storage.get_nfl_team(team)

        try:
            response = requests.get(sportsdb_endpoint.format(team_data["team_id"]))
            if(response.status_code != 200):
                raise Exception("API endpoint request failed with status code: {}".format(response.status_code))

            logging.info(TAG + "SDB request for {} returned successfully with status code: ".format(team) + str(response.status_code))

        except RequestException as e:
            logging.error(TAG + "RequestException error occurred: " + str(e))
            raise Exception(TAG + "RequestException error occurred: " + str(e))

        else:
            #print(response.json())
            data = response.json()["results"][0]
            game_data = {}

            game_data["game_id"] = team_data["team_id"]
            game_data['game_date'] = data['dateEvent']
            game_data['home_team'] = data['strHomeTeam']
            game_data['away_team'] = data['strAwayTeam']

            if self.league == NBA:
                game_data["home_logo"] = self.storage.get_nba_team(game_data["home_team"])["team_logo"]
                game_data["away_logo"] = self.storage.get_nba_team(game_data["away_team"])["team_logo"]

            else:
                game_data["home_logo"] = self.storage.get_nfl_team(game_data["home_team"])["team_logo"]
                game_data["away_logo"] = self.storage.get_nfl_team(game_data["away_team"])["team_logo"]
            
            game_data['game_name'] = data['strEvent']
            game_data['home_score'] = data['intHomeScore']
            game_data['away_score'] = data['intAwayScore']
            game_data["game_quarters"] = "Not Available"
            game_data["source"] = "sdb"

            return game_data
            

        


    

