import requests
import pywikibot
import re
import logging 
import datetime
from requests.exceptions import RequestException

TAG = 'WikiAPI: '
#TODO Think about reformatting the celeb object
class Celeberty(object):

    def __init__(self, name, description, image, extract, birth_date, birth_place):
        self.name = name
        self.description = description
        self.image = image
        self.extract =extract
        self.birth_date = birth_date
        self.birth_place = birth_place
        self.data_type = 'celeb'
        #TODO: Add in variables for London City combo for virth place.
    
    def set_occupation(self, occupation):
        self.occupation = occupation

    def set_website(self, website):
        self.website = website

    
    
    

class Athlete(Celeberty):

    def __init__(self, name, description, image, extract, birth_date, birth_place,
            team, number, position):
        
        super().__init__(name, description, image, extract, birth_date, birth_place)
        self.team = team
        self.number = number
        self.position = position
        self.data_type = 'athlete'

    def set_height(self, height_ft, height_in):
        self.height_ft = height_ft
        self.height_in = height_in
        self.measurement_type = 'us'

    def set_weight(self, weight):
        self.weight = weight
    
    def set_championship(self, championship):
        self.championship = championship

    def set_career(self, career_start, career_end):
        self.career_start = career_start
        self.career_end = career_end

class Musician(Celeberty):

    def __init__(self, name, description, image , extract, birth_date, birth_place,
             genres, label):
        super().__init__(name, description, image ,extract, birth_date, birth_place)
        self.genres = genres
        self.label = label
        self.data_type = 'musician'

    
    def set_instruments(self, instruments):
        self.instruments = instruments


class WikiAPI:



    def __init__(self):
        self.site = pywikibot.Site('en', 'wikipedia')
        self.endpoint = 'https://en.wikipedia.org/api/rest_v1/page/summary/{}'
        self.search_endpoint = 'https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={}&prop=pageimages|images|extracts&exintro=true&explaintext=true&piprop=original&format=json'
        self.image_endpoint = 'https://www.mediawiki.org/w/api.php?action=query&titles={}&prop=imageinfo&iiprop=url&format=json'

    def set_page(self, page):
        self.page = pywikibot.Page(self.site, page)

    def search_wiki(self, query):
        try:
            response = requests.get(self.search_endpoint.format(query))
            if response.status_code != 200:
                logging.error(TAG + 'Error occurred with status code: ' + str(response.status_code))
                return {'error' : 'Bad request with status code: ' + str(response.status_code)}
            logging.info(TAG + 'Wiki search request returned successfully with status code ' + str(response.status_code))
        except RequestException as e:
            logging.error(TAG + 'RequestException error occured: ' + e)
            return {'error' : e}
        else:
            query_data = {}
            data = response.json()
            result = {}
            for value in data['query']['pages'].values():
                if value['index'] == 1:
                    result = value
            query_data['title'] = result['title']
            query_data['extract'] = result['extract']
            if 'original' in result.keys():
                query_data['image'] = result['original']['source']
            elif 'images' in result.keys():
                image_file = result['images'][0]['title']
                query_data['image'] = self.get_image(image_file)
                #TODO: make a new call to get image
            else:
                query_data['image'] = 'NA'

            return query_data

    def get_image(self, image_file):
        try:
            response = requests.get(self.image_endpoint.format(image_file))
            if response.status_code != 200:
                logging.error(TAG + 'Error occurred with status code: ' + str(response.status_code))
                return 'NA'
            logging.info(TAG + 'Wiki image request returned with status code: ' + str(response.status_code))
        except RequestException as e:
            logging.error(TAG + 'RequestException error occured: ' + e)
            return 'NA'
        else:
            data = response.json()['query']['pages']['-1']
            if 'imageinfo' in data.keys():
                return data['imageinfo'][0]['url']
            else:
                return 'NA'

    def get_summary(self, query):

        try:
            response = requests.get(self.endpoint.format(query))
            if response.status_code != 200:
                raise Exception('Response code error occurred with status code: ' + str(response.status_code))
            logging.error(TAG + 'Wiki summary successfull with status code: ' + str(response.status_code))
        except RequestException as e:
            logging.error(TAG + 'RequestException error occurred: ' + e)
            return {'error' : e}            
        else:
            summary_data = {}
            data = response.json()
            summary_data['title'] = data['title']
            summary_data['description'] = data['description']
            summary_data['extract'] = data['extract']
            summary_data['image'] = data['thumbnail']['source']

            return summary_data


    def get_celeberty(self, name):
        query_list = name.split(' ')
        delimeter = '_'
        for item in query_list:
            query_list[query_list.index(item)] = item.capitalize()
        name = delimeter.join(query_list)
        logging.debug(TAG + f"Celeb Name: {name}")

        page = pywikibot.Page(self.site, name)

        intro = page.text.split('\n')[:100]
        if len(intro) != 100:
            return {'error' : 'Could not find celeberty'}

        logging.info(TAG + 'Wiki page for {} retrieved successfully'.format(name))
        date = self.get_bday(intro)
        location = self.get_bplace(intro)
        values, tag = self.get_occupation(intro)
        musician_dict = self.get_musician_data(intro)
        athlete_dict = self.get_athlete_data(intro)
        
        birth_date = {tag}


        try:
            data = self.get_summary(name)
        except Exception as e:
            logging.error(TAG + 'RequestException error occurred: ' + e)
            return {'error' : str(e)}
        else:
            if date == None or location == None:
                return {'error': 'Could not find celeberty'}
            
            if set(['team', 'number', 'position']).issubset(set(athlete_dict.keys())):
                retval = Athlete(data['title'], data['description'], data['image'], data['extract'],
                    date, location, athlete_dict['team'], athlete_dict['number'], athlete_dict['position']
                )
                if 'height_ft' in athlete_dict and 'height_in' in athlete_dict:
                    retval.set_height(athlete_dict['height_ft'], athlete_dict['height_in'])


            elif set(['genres', 'label']).issubset(set(musician_dict.keys())):
                retval = Musician( data['title'], data['description'], data['image'], data['extract'],
                    date, location, musician_dict['genres'], musician_dict['label']
                )
                if len(values) != 0:
                    retval.set_occupation(values)
            else:
                retval = Celeberty(data['title'], data['description'], data['image'], data['extract'], date, location)
                if len(values) != 0 :
                    retval.set_occupation(values)

        return retval.__dict__
            
    
    #TODO Test about 100 celebs
    def run_tests(self, file):
        with open(file, 'r') as f:
            names = f.readlines()
            for name in names:
                name = name.strip('\n')
                page = pywikibot.Page(self.site, name)
                intro = page.text.split('\n')[:100]
                print(name)
                print(len(intro))
                self.get_bday(intro)
                self.get_bplace(intro)
                self.get_occupation(intro)
                print('\n')
    
    #TODO Test about 50 athletes
    def run_athlete_test(self, file='athlete_test.txt'):
        with open(file, 'r') as f:
            names = f.readlines()
            for name in names:
                name = name.strip('\n')
                page = pywikibot.Page(self.site, name)
                intro  = page.text.split('\n')[:100]
                print(name)
                print(len(intro))
                self.get_athlete_data(intro)
                print('\n')

    def run_musician_test(self, file='musician_test.txt', counter = 0):
        with open(file, 'r') as f:
            names = f.readlines()
            for name in names:
                if counter == 40:
                    break
                name = name.strip('\n')
                page = pywikibot.Page(self.site, name)
                intro = page.text.split('\n')[:100]
                print(name)
                print(len(intro))
                self.get_musician_data(intro)
                counter += 1
                

    def get_bday(self,intro):
        for line in intro:
                if line.find('| birth_date') == 0:
                        line = line.strip('\n')
                        entries = line.split('=', 1)
                        tag = entries[0].strip('| ')  
                        entries[1] = re.sub(r'}}.*' ,'', entries[1])
                        value= re.sub(r'.*{{', '', entries[1])
                        #value = entries[1].strip('{{}} ')
                        values = value.split('|')
                        if len(values) == 5:
                                if values[-1].find('df') != -1:
                                        day = values[-2]
                                        month = values[-3]
                                        year = values[-4]
                                elif values[1].find('df') != -1:
                                        day = values[-1]
                                        month = values[-2]
                                        year = values[-3]
                                elif values[1].find('mf') != -1:
                                        day = values[-1]
                                        month = values[-2]
                                        year = values[-3]
                                else:
                                        day = values[-2]
                                        month = values[-3]
                                        year = values[-4]
                        else:
                            day = values[-1]
                            month = values[-2]
                            year = values[-3]
                        print('TAG: ' + tag)
                        print('VALUES: ' + str(value) + '\n')
                        print(tag + ' : ' + month + ' / ' + day + ' / ' + year)
                        month = int(month.strip())
                        day = int(day.strip())
                        year = int(year.strip())
                        dt = datetime.datetime(year=year, month=month, day=day)
                        return dt
    #TODO: Differentiate between U.S. and non U.S birth_places
    def get_bplace(self,intro):
        for line in intro:
                if line.find('| birth_place') == 0:
                        line = line.strip('\n')
                        entries = line.split('=' , 1)
                        tag = entries[0].strip('| ')
                        print('TAG: ' + tag)
                        if entries[1].find('[[') == -1:
                            entries[1] = re.sub(r'<.*', '', entries[1])  
                        values = (entries[1].split(','))
                        print('VALUES: ' + str(values) + '\n') 
                        city = re.sub(r'.*\[\[', '', values[0])
                        city = re.sub(r']].*', '', city)
                        state = re.sub(r']].*', '', values[1])
                        state = re.sub(r'.*\[\[', '', state)
                        if city.find('|') != -1:
                            city = city.split('|')[0]
                        if state.find('|') != -1:
                            state = state.split('|')[0]

                        print(tag + ' : ' + city + ' ' + state )
                        loc = {'city': city, 'state': state}
                        return loc

    def get_occupation(self, intro):
        flat_list = False
        values = []
        tag = ''
        for line in intro:
                if flat_list:
                    if line.find('*') == 0:
                        print('Found Occupation: ' + line)
                        line = line.strip('*')
                        line = re.sub(r'.*\[\[', '', line)
                        line = re.sub(r'.*{{', '', line)
                        line = re.sub(r'}}.*', '', line)
                        line = re.sub(r']].*', '', line)
                        if line.find('|') != 0:
                            line = line.split('|')[-1]
                        line.strip()
                        values.append(line)
                    else:
                        flat_list = False
                        
                if line.find('| occupation') == 0:
                        line = line.strip('\n')
                        entries = line.split('=', 1)
                        tag= entries[0].strip('| ')
                        entries[1] = re.sub(r'<.*', '', entries[1])
                        values = entries[1].strip(' {{}} ').split('|')
                        if values[0] == 'flatlist':
                            print('FlatList found. Searching following lines for occupation')
                            flat_list = True
                            values.clear()

                        else:
                            values.pop(0)
                            index = 0
                            for value in values:
                                values[index] = re.sub(r']].*','',value)
                                values[index] = re.sub(r'.*\[\[', '', values[index])
                                values[index] = re.sub(r'(.*{{|}}.*)', '', values[index])
                                values[index] = re.sub(r'<.*', '', values[index])
                                print(value)
                                index += 1

        print(tag + ':' + str(values))
        return values, tag              


    def get_athlete_data(self, intro):
        athlete_dict = {}
        edge_case = False
        for line in intro:

            if edge_case:
                if line.find('| ') != 0:
                    value += line
                else:
                    value = re.sub(r'<.*>(\d+)<.*>', r'\1', value)
                    print(value)
        
            if line.find('| height_ft') == 0:
                line = line.strip('\n')
                value = line.split('=', 1)[1]
                if value.find('<!') == 0  and value[-1] == ' ':
                    edge_case = True
                else:
                    value = re.sub(r'<.*>(\d+)<.*>', r'\1', value)
                    print(value)
                    tag = 'height_ft'
                    athlete_dict[tag] = int(value.strip())

            if line.find('| height_in') == 0:
                line = line.strip('\n')
                value = line.split('=', 1)[1]
                print(value)
                if value.find('<!') == 0  and value[-1] == ' ':
                    edge_case = True
                else:
                    value = re.sub(r'<.*>(\d+)<.*>', r'\1', value)
                    print(value)
                    tag = 'height_in'
                    athlete_dict[tag] = int(value.strip())

            if line.find('| weight_lbs') == 0:
                line = line.strip('\n')
                value = line.split('=', 1)[1]
                if value.find('<!') == 0  and value[-1] == ' ':
                    edge_case = True
                else:
                    value = value = re.sub(r'<.*>(\d+)<.*>', r'\1', value)
                    tag = 'weight_lb'
                    athlete_dict[tag] = int(value.strip())
        
            if line.find('| team ') == 0 or line.find('| current_team ') == 0 or line.find('| currentclub ') == 0:
                line = line.strip('\n')
                value = line.split('=',1)[1]
                tag = 'team'
                value = re.sub(r'(.*\[\[|]].*|<.*)', '', value)
                if value.find('|') != -1:
                    value = value.split('|')[-1]
                print(value)
                athlete_dict[tag] = value

            if line.find('| position') == 0:
                line = line.strip('\n')
                value = line.split('=', 1)[1]
                tag = 'position'
                value = re.sub(r'(.*\[\[|]].*|<.*)', '', value)
                if value.find('|') != -1:
                    value = value.split('|')[-1]
                athlete_dict[tag] = value

            if line.find('| clubnumber') == 0 or line.find('| number') == 0:
                line = line.strip('\n')
                value = line.split('=', 1)[1]
                tag = 'number'
                value = re.sub(r'<.*', '', value)
                if value.find(',') != -1:
                    values = value.split(',')
                    retval = []
                    for num in values:
                        print(num)
                        retval.append(int(num.strip()))
                    athlete_dict[tag] = retval
                else:
                    athlete_dict[tag] = int(value.strip())


        print('Athlete Data: ' + str(athlete_dict))
        return athlete_dict


    def get_musician_data(self, intro):
        musician_dict = {}
        flat_list = False
        values = []
        tag = ''
        for line in intro:
            if flat_list:
                if line.find('*') == 0:
                    line = line.strip('*')
                    line = re.sub(r'(.*\[\[|]].*)','',line)
                    line = re.sub(r'(.*{{|}}.*)', '', line)
                    line = re.sub(r'<!.*>', '', line)
                    if line.find('|') != -1:
                        line = line.split('|')[-1]
                    line.strip()
                    values.append(line)

                else:
                    flat_list = False
                    musician_dict[tag] = values
                    values = []

            if line.find('| genre') == 0:
                line = line.strip('\n')
                tag = 'genres'
                print("Processing genre")
                line = line.split('=' , 1)[1]
                #Provide check if the <!> brackets surround the data provided
                if line.count('<!')  == 2:
                    line = re.sub(r'<.*>(\w.*)<.*>', r'\1', line)
                else:
                    line = re.sub(r'<.*>', '', line)
                #Check if flatlist. If so move to the next line to process
                if line.find('flatlist') != -1 or line.find('flat list') != -1:
                    values.clear()
                    flat_list = True
                else:
                    #Since genres can be specified as links we replace the | with , and then split accordingly
                    if line.find('hlist') != -1:
                        line = re.sub(r'(.*{{|}}.*)', '', line)
                        line = re.sub(r'hlist\||nowrap\|', '', line)
                        line = line.replace(']|[', '],[')

                    values = line.split(',')
                    index = 0
                    for value in values:
                        values[index] = re.sub(r'.*\[\[|]].*', '', value)
                        if values[index].find('|') != -1:
                            values[index] = values[index].split('|')[-1]
                        index += 1
                    musician_dict[tag] = values
                    values = []

            if line.find('| instrument') == 0:
                line = line.strip('\n')
                tag = 'instruments'
                hlist = False
                line = line.split('=' , 1)[1]
                #Provide check if the <!> brackets surround the data provided
                if line.count('<!')  == 2:
                    line = re.sub(r'<.*>(\w.*)<.*>', r'\1', line)
                else:
                    line = re.sub(r'<.*>', '', line)
                #Check if flatlist. If so move to the next line to process
                if line.find('flatlist') != -1 or line.find('flat list') != -1:
                    flat_list = True
                else:
                    if line.find('hlist') != -1:
                        hlist = True
                        line = re.sub(r'.*{{|}}.*', '', line)
                        line = re.sub(r'hlist\||nowrap\|', '', line)

                    values = line.split(('|', ',')[hlist])
                    index = 0 
                    for value in values:
                        values[index] = re.sub(r'.*\[\[|]].*', '', value)
                        if values[index].find('|') != -1:
                            values[index] = values[index].split('|')[-1]
                        index += 1
                    musician_dict[tag] = values
                    values = []

            if line.find('| label') == 0:
                line = line.strip('\n')
                tag = 'label'
                line = line.split('=' , 1)[1]
                #Provide check if the <!> brackets surround the data provided
                if line.count('<!')  == 2:
                    line = re.sub(r'<.*>(\w.*)<.*>', r'\1', line)
                else:
                    line = re.sub(r'<.*>', '', line)
                #Check if flatlist. If so move to the next line to process
                if line.find('flatlist') != -1 or line.find('flat list') != -1:
                    flat_list = True
                else:
                    #Since genres can be specified as links we replace the | with , and then split accordingly
                    if line.find('hlist') != -1:
                        line = re.sub(r'(.*{{|}}.*)', '', line)
                        line = re.sub(r'hlist\||nowrap\|', '', line)
                        line = line.replace(']|[', '],[')

                    values = line.split(',')

                    index = 0
                    for value in values:
                        values[index] = re.sub(r'.*\[\[|]].*', '', value)
                        if values[index].find('|') != -1:
                            values[index] = values[index].split('|')[-1]
                        index += 1
                    musician_dict[tag] = values
                    values = []

        #logging.debug("Musician Dict: " + str(musician_dict))
        return musician_dict



            
                


