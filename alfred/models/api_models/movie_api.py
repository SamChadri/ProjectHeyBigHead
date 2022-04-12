import requests
import logging
import json
import os
from pprint import pprint
from requests.exceptions import RequestException

TAG = "MovieAPI: "

omdb_endpoint= "http://www.omdbapi.com/?apikey={0}&t={1}"
search_endpoint = 'https://api.themoviedb.org/3/search/multi?api_key={0}&language=en-US&query={1}&page=1&include_adult=false'
tmdb_endpoint = "https://api.themoviedb.org/3/{0}/{1}?api_key={2}"
image_base = "https://image.tmdb.org/t/p/w500"

class MovieAPI:


    #TODO: Failsafe just load that shit from imdb website in a WebView or something
    def __init__(self, key_file=os.path.abspath('alfred/data/keys.json')):
        self.omdb_endpoint = omdb_endpoint
        self.tmdb_endpoint = tmdb_endpoint
        self.search_endpoint =search_endpoint
        self.image_base = image_base
        self.key_file = key_file
        with open(key_file) as f:
            key_data = json.load(f)
            self.omdb_key = key_data["omdbKey"]
            self.tmdb_key = key_data["tmdbKey"]

    
    """ For general quering of any type of title """
    def get_title(self, title):
        try:
            query_results = self.get_omdbTitle(title)
        except Exception as e:
            logging.error(TAG + "Exception error occurred: " + str(e))
            return {'error' : e}
        else:
            return query_results


    
    def get_movie(self, movie, movie_id):
        try:
            query_results = self.get_omdbTitle(movie)
        except Exception as e:
            logging.error(TAG + "Exception error occurred: " +  str(e) + " Trying backup tmdbMovie source.")
            try:
                backup_results = get_tmdbMovie(movie_id, True)
                
            except Exception as e:
                logging.error(TAG + "Exception error occurred: " + str(e))
                return {"error" : e}
            else:
                return backup_results
        else:
            return query_results

        
    
    def get_tvShow(self, tv_query, tv_id):
        try:
            query_results = self.get_omdbTitle(tv_query)
            if hasattr(query_results, "error"):
                return query_results
        except Exception as e:
            logging.error(TAG + "Exception error occurred: " +  str(e) + " Trying backup tmdbTV source.")
            try:
                backup_results = get_tmdbMovie(tv_id, False)
                if hasattr(query_results, "error"):
                    return query_results
                
            except Exception as e:
                logging.error(TAG + "Exception error occurred: " +  str(e))
                return {"error" : e}
            else:
                return backup_results
        else:
            return query_results

           
        

    
    def get_tmdb_title(self, query_id, movie):
        try:
            search_param = (("tv", "movie"), [movie == True])
            response = requests.get(self.tmdb_endpoint.format(search_param, query_id, self.tmdb_key))
            if response.status_code != 200:
                raise Exception("TMDBAPI endpoint request failed with status code: " + str(response.status_code))
            logging.info(TAG + "TMDB request returned successfully with status code: " + str(response.status_code))
        except Exception as e:
            logging.error(TAG + "RequestException error occurred: " +  str(e))
            return {"error": e}
        
        else:
            web_data = response.json()
            if movie:
                movie_data = process_movie_title(web_data)
                return movie_data
            else:
                tv_data = process_tv_title(web_data)
                return tv_data

    def process_movie_title(self, data):
        movie_data = {}
        movie_data["title_id"] = data["imdb_id"]
        movie_data["title_name"] = data["original_title"]
        movie_data["title_year"] = data["release_date"]
        movie_data["title_genres"] = []
        for genre in data["genres"]:
            movie_data["genres"].append(genre["name"])
        
        movie_data["title_poster"] = image_base + data["poster_path"]
        movie_data["title_plot"] = data["overview"]
        movie_data['title_type'] = 'movie'        
        movie_data["source"]  = "tmdb"

        return movie_data


    def process_tv_title(self, data):
        tv_data = {}
        tv_data["title_id"] = data["id"]
        tv_data["title_name"] = data["name"]
        tv_data["title_year"] = [data["first_air_date"], data["last_air_date"]]

        tv_data["title_genres"] = []
        for genre in data["genres"]:
            tv_data["title_genres"].append(genre["name"])

        tv_data["title_writers"] = []
        for creator in data["created_by"]:
            tv_data["title_writers"].append(creator["name"])

        tv_data["source"] = "tmdb"
        tv_data['title_type'] = 'series'
        return tv_data


    def get_query_results(self, query):
        try:
            response = requests.get(self.search_endpoint.format(self.tmdb_key, query ))
            if response.status_code != 200:
                raise Exception("TMDBAPI endpoint request failed with status code: " + str(response.status_code))
            logging.debug("TMDB query request returned successfully with status code: " + str(response.status_code))
        except RequestException as e:
                logging.error(TAG + "RequestException error occurred: " +  str(e))
                return {"error" : e}
        else:
            data = response.json()['results']
            pprint(data)
            query_results = []
            for entry in data:
                if entry['media_type'] == 'movie':
                    query_results.append(self.process_movie(entry))
                elif entry['media_type'] == 'tv':
                    query_results.append(self.process_tv(entry))
                else:
                    continue


            return query_results
    
    def process_movie(self, movie):
        entry = {}
        entry["movie_id"] = movie["id"]
        entry["movie_title"] = movie["title"]
        entry["movie_year"] = movie["release_date"]
        entry["movie_plot"] = movie["overview"]
        entry['title_type'] = movie['media_type']

        return entry

    def process_tv(self, tv):

        entry = {}
        #pprint(tv)
        entry["tv_id"] = tv["id"]
        entry["tv_title"] = tv["name"]
        entry["tv_year"] = tv["first_air_date"]
        entry["tv_plot"] = tv["overview"]
        entry['title_type'] = tv['media_type']
        return entry


    
    """Throws possible Custom Exception error """
    def get_omdbTitle(self, title):
        try:
            response = requests.get(self.omdb_endpoint.format(self.omdb_key, title))
            if response.status_code != 200:
                raise Exception("Request failed with status code {}".format(response.status_code))            
            logging.debug(TAG + "OMDB title request returned successfully with status code: " + str(response.status_code))

        except RequestException as e:
            logging.erorr(TAG + "RequestException error occurred: " +  str(e))
            return { "error" : e}

        else:

            web_data = response.json()
            movie_data = {}
            movie_data["title_id"] = web_data["imdbID"]
            movie_data["title_name"] = web_data["Title"]
            movie_data["title_year"] = web_data["Released"]
            movie_data["title_rating"] = web_data["Rated"]
            movie_data["title_genres"] = web_data["Genre"].split(',')
            movie_data["title_directors"] = web_data["Director"].split(',')
            movie_data["title_writers"] = web_data["Writer"].split(',')
            movie_data["title_cast"] = web_data["Actors"].split(',')
            movie_data["title_poster"] = web_data["Poster"]
            movie_data["title_plot"] = web_data["Plot"]
            movie_data['title_type'] = web_data['Type']


            movie_data["source"] = "omdb"

            return movie_data 


