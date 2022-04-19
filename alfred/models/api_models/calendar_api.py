from re import S, T
import requests
from requests.exceptions import RequestException
from requests.models import HTTPError
from requests_oauthlib import OAuth1Session
import logging 
import os
import json
import copy
from datetime import datetime
from datetime import timedelta
from pprint import pprint
from alfred.mongodb.api_store import APIStore 
from pprint import pprint
import google.oauth2.credentials
from googleapiclient.discovery import build
from dateutil.rrule import *
from dateutil.parser import *
from dateparser import parse
from pprint import pprint


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
TAG = 'GoogleCalendarAPI: '



default_event = {
    'summary': 'Event',
    'start' : {
        'dateTime': None,
        'timeZone': 'America/Chicago'
    },
    'end' : {
        'dateTime': None,
        'timeZone': 'America/Chicago',
    },
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'popup', 'minutes': 30},
            {'method': 'popup', 'minutes': 10},
    ],
  },
}

#TODO implement timeMax
#TODO implement last second to last
#TODO implement index
#TODO as batch index, timeMax etc is implemented, put this in DB 
event_num = {
    'next': 1,
    'first': 1,
    'second': 2,
    'third': 3,
    'fourth': 4,
    'fifth': 5,
    'sixth': 6,
    'seventh': 7,
    'eighth': 8,
    'ninth': 9,
    'last': {
        'index': -1,
        'timeMax': 'TODO'
    },
    'second to last': {
        'index': -2,
        'timeMax': 'TODO'
    },
    'agenda': None,
    'schedule': None

}


rule_constants = {
    "MONTHLY": MONTHLY,
    'WEEKLY': WEEKLY,
    'DAILY': DAILY,
    'YEARLY': YEARLY,
    'MINUTELY': MINUTELY
}
#TODO Eventually put this in a DB as it gets biggger.
update_params = {
    'start time': 'start_time',
    'end time':  'end_time',
    'initial time': 'start_time',
    'start date': 'start_date',
    'start' : 'start_date',
    'kickoff': 'start_time',
    'starting time': 'start_time',
    'end date': 'end_date',
    'end': 'end_time',
    'event type': 'description',
    'type': 'description',
    'name': 'summary',
    'title': 'summary',
    'label': 'summary',
    'location': 'location',
    'guest list': 'attendees',
    'guests': 'attendees',
    'attendee list': 'attendees',
    'email reminder': 'email',
    'reminder': 'popup',
    'popup': 'popup',
    'color': 'colorId',
    'default color': 'colorId',
    'add': 0,
    'invite': 0,
    'include': 0,
    'remove': 1,
    'uninvite': 1,
    'delete': 1,
    'omit': 1
}


event_colors = {
    "lavender": 1,
    "sage": 2,
    "grape": 3,
    "flamingo": 4,
    "banana": 5,
    "tangerine": 6,
    "peacock": 7,
    "graphite": 8,
    "blueberry": 9,
    "basil": 10,
    "tomato": 11
}

#TODO Add funtionality for reminders
#TODO Add funtionality for tasks
factory_init = {'init' : False}
class GoogleCalendarAPI:

    @classmethod
    def is_init(cls, init=False):
        return factory_init['init']

    @classmethod
    def factory(cls):
        logging.info(TAG +"Initializing Google Factory")
        cls.__api_pool = {}
        cls.__devices = APIStore.get_devices()
        cls.__device_settings = {}
        for device in cls.__devices:
            id = device['id']
            logging.info(TAG + "Creating Google API instace with id {}".format(id))
            api_instance = GoogleCalendarAPI(device_id=id)
            cls.__api_pool[id] = api_instance

        factory_init['init'] = True

    @classmethod
    def acquire(cls, id):
        return cls.__api_pool.pop(id)

    @classmethod
    def release(cls, id, obj):
        obj.refresh_event()
        cls.__api_pool[id] = obj

    def __init__(self, device_id=None ,key_file=os.path.abspath("alfred/data/keys.json")):
        self.key_file = key_file

        SCOPES = ['https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/contacts']
        logging.info(TAG + "Creating credentials...")
        #self.refresh_token()
        #self.__credentials = google.oauth2.credentials.Credentials(self.__access_token,
        #    refresh_token=self.__refresh_token,
        #    token_uri=self.__refresh_uri,
        #    client_id=self.__client_id,
        #    client_secret=self.__client_secret)
        self.__credentials =  self.create_credentials(os.path.abspath("alfred/data/token.json"),SCOPES)
            

        self.device_id = device_id

        self.calendar_api = build('calendar', 'v3', credentials=self.__credentials, cache_discovery=False)
        self.people_api = build('people', 'v1', credentials=self.__credentials,  cache_discovery=False)
        self.__event_num_data = event_num

        self.curr_date = datetime.now()
        self.curr_year = self.curr_date.year
        self.curr_month = self.curr_date.month
        self.curr_day = self.curr_date.day

        self.__event = copy.deepcopy(default_event)
        logging.info(TAG + "Finished creating GoogleAPI instance.")

    def create_credentials(self, token_file, scopes, credential_file=os.path.abspath("alfred/data/project_heyBigHead_credentials.json")):
        creds = None
        try:
            if os.path.exists(token_file):
                with open(token_file) as file:
                    data = json.load(file)
                    self.__access_token = data["google_access_token"]
                    self.__client_id = data["google_client_id"]
                    self.__client_secret = data["google_client_secret"]
                    self.__refresh_token = data["google_refresh_token"]
                    self.__refresh_uri = data["google_refresh_uri"]
                
                creds = google.oauth2.credentials.Credentials(self.__access_token,
                    refresh_token=self.__refresh_token,
                    token_uri=self.__refresh_uri,
                    client_id=self.__client_id,
                    client_secret=self.__client_secret)
                logging.info(f'{TAG} Token file exists, credentials valid: {creds.valid}')
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credential_file, scopes=scopes)
                    creds = flow.run_local_server(port=0)
                    logging.info(f'{TAG} Finished retreiving credentials from app flow. Credentials valid : {creds.valid}')
                # Save the credentials for the next run
                with open(token_file, 'w') as file:
                    data = {}
                    data["google_access_token"] = creds.token
                    data["google_client_id"] = creds.client_id
                    data["google_client_secret"] = creds.client_secret
                    data["google_refresh_token"] = creds.refresh_token
                    data["google_refresh_uri"] =  creds.token_uri
                    self.__client_id = creds.client_id
                    self.__client_secret = creds.client_secret
                    self.__refresh_token = creds.refresh_token
                    self.__refresh_uri = creds.token_uri
                    json.dump(data, file, indent=4)

        except Exception as e:
            logging.error(f'{TAG} Exception occured: {e}')
            return None
        else:
            logging.info(f'{TAG} Successfully created credentials.')
            return creds

    def refresh_token(self):
        refresh_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.__refresh_token,
            'client_id': self.__client_id,
            'client_secret': self.__client_secret
        }

        try:
            response = requests.post(self.__refresh_uri, data=refresh_data)
            
            if response.status_code != 200:
                error_message =  TAG + f'Google Calendar API failed with status code {response.status_code} and message {response.text}'
                logging.error(error_message)
                raise Exception(error_message)
            
        except Exception or RequestException as e:
            logging.error(TAG + f'Exception occured: {e}')
            return {'error' : e}

        else:
            self.__access_token = response.json()['access_token']

    def refresh_event(self):
        self.__event = copy.deepcopy(default_event)

    def create_event(self, **kwargs):
        print('Creating event')
        logging.info(TAG + f'Creating Google Calendar Event')
        if 'calendar_date' in kwargs:
            calendar_date = kwargs['calendar_date']
            logging.info(TAG + f'Found calendar date parameters {calendar_date}...adding to event')
            curr_date = datetime.now()
            curr_year = curr_date.year
            curr_month = curr_date.month
            curr_day = curr_date.day
            #TODO Add default time just in case one is not provided
            if 'start_time' in kwargs and 'end_time' in kwargs:
                start_time_string = '{} {}'.format(calendar_date, kwargs['start_time'])
                start_date = parse(start_time_string, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime(self.curr_year,self.curr_month,self.curr_day)}).astimezone()

                end_time_string = '{} {}'.format(calendar_date, kwargs['end_time'])
                end_date = parse(end_time_string, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime(self.curr_year,self.curr_month,self.curr_day)}).astimezone()
            elif 'start_time' in kwargs and 'end_time' not in kwargs:
                start_time_string = calendar_date + kwargs['start_time']
                start_date = parse(start_time_string, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime(self.curr_year,self.curr_month,self.curr_day)}).astimezone()

                end_date = start_date + timedelta(hours=1)
            else:
                start_date = parse(calendar_date, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime(self.curr_year,self.curr_month,self.curr_day,0,0)}).astimezone()
                #start_date = start_date + timedelta(hours=17)
                end_date = start_date + timedelta(hours=1)

        else:
            start_date, end_date = self.create_date_pair()
        

        self.__event['start']['dateTime'] = start_date.isoformat()
        self.__event['end']['dateTime'] = end_date.isoformat()
            
        if 'calendar_frequency' in kwargs:
            recurrence = kwargs['calendar_frequency']
            reccur_data = APIStore.get_frequency(recurrence)
            rule_count = None
            if 'calendar_frequency_num' in kwargs:
                rule_count = kwargs['calendar_frequency_num']
            if 'interval' in reccur_data:
                rule = rrule(freq=rule_constants[reccur_data['frequency']], count=rule_count, interval=reccur_data['interval'])
            else:
                rule = rrule(freq=rule_constants[reccur_data['frequency']], count=rule_count)

            rule = str(rule).split('\n')[1]
            self.__event['recurrence'] = []
            self.__event['recurrence'].append(rule)
            logging.info(TAG + f'Found calendar interval {recurrence}. Creating rule: {rule} for event...')


        if 'calendar_param' in kwargs:
            event_param = update_params[kwargs['calendar_param']]

            if event_param == 'colorId':
                color_name = kwargs['calendar_update']
                logging.info(TAG + f'Setting color to: {color_name}')
                self.__event[event_param] = event_colors[color_name]

            elif event_param == 'email' or event_param == 'popup':
                minutes = self.parse_reminder_string(kwargs['calendar_update'])
                if minutes == -1:
                    return {'error': 'An invalid time unit was provided'}
                logging.info(TAG+ f'Setting {event_param} reminder to {minutes} minutes...')
                reminder = {'method': event_param, 'minutes': minutes}
                self.__event['reminders']['overrides'].append(reminder)
            else:
                self.__event[event_param] = kwargs['calendar_update']

            
        if 'calendar_attendee' in kwargs:
            person = kwargs['calendar_attendee']
            #TODO: Account for more than one person in the future
            logging.info(TAG + f'Found calendar attendee {person}')
            contact = self.get_contact(person)
            if contact == 'NA':
                logging.info(TAG + f'Could not find contact: {person}. Setting event without invite')
            else:
                self.__event['attendees'] = []
                attendee = {'email': contact}
                self.__event['attendees'].append(attendee)
                logging.info(TAG + f'Found contact {contact}. Adding to attendee list')

        
        if 'calendar_location' in kwargs:
            self.__event['location'] = kwargs['calendar_location']

        event_type = None
        if 'event_title' in kwargs and 'event_type' in kwargs:
            self.__event['summary'] = kwargs['event_title']
            self.__event['description'] = kwargs['event_type'] 
            event_type = kwargs['event_type']
        elif 'event_title' in kwargs and 'event_type' not in kwargs:
            self.__event['summary'] = kwargs['event_type']
            self.__event['description'] = 'Event'
            event_type = 'Event'
        elif 'event_title' not in kwargs and 'event_type' in kwargs:
            self.__event['summary'] = kwargs['event_type']
            self.__event['description'] = kwargs['event_type']
        else:
            self.__event['summary'] = 'Alfred Calendar Event'
            self.__event['description'] = 'Event'

        pprint(self.__event)
        calendar_event = self.calendar_api.events().insert(calendarId='primary', body=self.__event).execute()
        link = calendar_event.get('htmlLink')
        logging.info(TAG+ f'Created event {link}')

        return { 
            'calendar_event': calendar_event,
            'event_type': event_type,
            'start_date': start_date,
            'end_date': end_date
        
        }

            

    def get_contact(self, name):

        results = self.people_api.otherContacts().list(readMask="names,emailAddresses").execute()
        contacts = results['otherContacts']
        
        for person in contacts:
            if 'names' in person and 'emailAddresses' in person:
                if person['names'][0]['displayName'].lower() == name.lower():
                    return person['emailAddresses'][0]['value']

        return 'NA'



    def parse_reminder_string(self,reminder):
        value = reminder.split(' ')[0]
        unit = reminder.split(' ')[1]
        if unit == 'minutes':
            return int(value)
            pass
        elif unit == 'hour' or 'hours':
            return int(value) * 60
        else:
            -1

    #TODO  Add functionality for type like type: Meeting and event
    #TODO  Add in timeMax for queries like "I want today's agenda"
    def get_events(self, **kwargs):

        query = None
        if 'calendar_search' in kwargs:
            query = kwargs['calendar_search']

        if 'calendar_date' in kwargs:
            curr_date = datetime.now()
            curr_year = curr_date.year
            curr_month = curr_date.month
            curr_day = curr_date.day
            query_date = parse(kwargs['calendar_date'], settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime(self.curr_year,self.curr_month,self.curr_day,0,0)}).astimezone().isoformat()
        
        else:
            query_date = datetime.now().astimezone().isoformat()

        
        if 'event_num' in kwargs:
            event_num = self.__event_num_data[kwargs['event_num']]
        
        else:
            event_num = 1

        event_type = None
        if 'event_type' in kwargs:
            event_type = kwargs['event_type']

            

        now = datetime.now().astimezone().isoformat()
        results = self.calendar_api.events().list(calendarId='primary', maxResults=10, orderBy='startTime', singleEvents=True,timeMin=query_date, q=query).execute()

        events = results['items']

        calendar_events = {}
        calendar_events['event_num'] = event_num
        calendar_events['query_date'] = query_date
        calendar_events['query'] = query
        calendar_events['events'] = []
        pprint(events)
        if event_num != None and event_type != None:
            #Find the matching event types then select the appropriate event number.
            #TODO add possibility for batch requests. EX. next 5 meetings
            event_list = []
            for event in events:
                if 'description' in event and event['description'].lower() == event_type.lower():
                    event_list.append(event)
            
            if event_num <= len(event_list):
                calendar_events['events'].append(event_list[event_num - 1])
            elif len(event_list) == 0:
                return {'error': 'No events were found'}
            else:
                calendar_events['events'].append(event_list[len(event_list) - 1])
        elif event_num != None and event_type == None:
            #TODO add possibility for batch requests. EX. next 5 meetings
            if event_num <= len(events):
                calendar_events['events'].append(events[event_num - 1])
            elif len(events) == 0:
                return {'error': 'No events were found'}
            else:
                calendar_events['events'].append(events[len(events) - 1])
            event_type = 'appointment'
        elif event_num == None and event_type != None:
        # No event number paramter specified. This possibility is only if a date is specified instead possibly
            for event in events:
                if 'description' in event and event['description'].lower() == event_type.lower():
                    calendar_events['events'].append(event)
        else:
            calendar_events['events'] = results['items']
            event_type = 'appointment'

        if len(calendar_events) == 0:
            return {'error': 'No events found'}
        
        if 'location' in calendar_events['events'][0]:
            calendar_events['init_query_location'] = calendar_events['events'][0]['location']
        
        calendar_events['event_type'] = event_type
        calendar_events['init_query_time'] = parse(calendar_events['events'][0]['start']['dateTime'])

        return calendar_events

    #TODO batch result
    def update_event(self, batch_result=False, **kwargs):

        #TODO Get the specified event with id with api call
        if 'calendar_date' in kwargs:
            query_date = parse(kwargs['calendar_date'], settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime(self.curr_year, self.curr_month, self.curr_day,0,0)}).astimezone().isoformat()
        else:
            query_date = datetime.now().astimezone().isoformat()

        
        query = None
        if 'calendar_search' in kwargs:
            query = kwargs['calendar_search']

        event_num = None
        if 'event_num' in kwargs:
            event_num = self.__event_num_data[kwargs['event_num']]

        event_type = None
        if 'event_type' in kwargs:
            event_type = kwargs['event_type']

        calendar_param = None
        calendar_update = None
        if 'calendar_update' in kwargs and 'calendar_param':
            calendar_param = kwargs['calendar_param']
            calendar_update = kwargs['calendar_update']

        
            
        timeMax = None


        results = self.calendar_api.events().list(calendarId='primary', maxResults=20,
            orderBy='startTime', singleEvents=True, timeMin=query_date, q=query).execute()

        events = results['items']
        query_event = None

        if event_num != None and event_type != None:
            #Find the matching event types then select the appropriate event number.
            #TODO add possibility for batch requests. EX. next 5 meetings
            event_list = []
            for event in events:
                if 'description' in event and event['description'].lower() == event_type.lower():
                    event_list.append(event)
                    print('Found event')
            #TODO add exception for index out of range
            if event_num > len(event_list):
                return {'error': 'Event not found'}
            query_event = event_list[event_num - 1]
        elif event_num != None and event_type == None:
            #TODO add possibility for batch requests. EX. next 5 meetings
            if event_num > len(events):
                return {'error': 'Event not found'}
            query_event = results['items'][event_num - 1]
            event_type = 'event'
        elif event_num == None and event_type != None:
        # No event number paramter specified. This possibility is only if a date is specified instead possibly
            for event in events:
                if 'description' in event and event['description'].lower() == event_type.lower():
                    query_event = event
        else:
            logging.info(TAG + f'Event number and event type werer not specified. Therefore could not update event.')
            return {'error': 'Could not find specified event'}

        if query_event == None:
            logging.info(TAG+ f'Could not find speicified event')
            return {'error': 'Could not find specified event'}


        event_param = update_params[calendar_param]

        if event_param == 'start_time':
            old_time = parse(query_event['start']['dateTime'])
            updated_dateTime = parse(calendar_update, settings={'RELATIVE_BASE': old_time})
            query_event['start']['dateTime'] = updated_dateTime.astimezone().isoformat()
        elif event_param == 'end_time':
            old_time = parse(query_event['end']['dateTime'])
            updated_dateTime = parse(calendar_update, settings={'RELATIVE_BASE': old_time})
            query_event['end']['dateTime'] = updated_dateTime.astimezone().isoformat()

        elif event_param == 'start_date':
            old_time = parse(query_event['start']['dateTime'])
            updated_dateTime = parse(calendar_update, settings={'RELATIVE_BASE': datetime(old_time.year,old_time.month,old_time.day,old_time.hour,old_time.minute)})
            query_event['start']['dateTime'] = updated_dateTime.astimezone().isoformat()
            pass

        elif event_param == 'end_date':
            old_time = parse(query_event['start']['dateTime'])
            updated_dateTime = parse(calendar_update, settings={'RELATIVE_BASE': datetime(old_time.year,old_time.month,old_time.day,old_time.hour,old_time.minute)})
            query_event['end']['dateTime'] = updated_dateTime.astimezone().isoformat()
            pass
        elif event_param == 'attendees':
            update_string = calendar_update.split(' ')[0]
            if update_string in update_params.keys():
                update_param = update_params[update_string]
                calendar_update = calendar_update.replace(f'{update_string} ', '')
                print(calendar_update)
                if update_param == 0:
                    if event_param not in query_event:
                        query_event[event_param] = []

                    email = self.get_contact(calendar_update)
                    contact = {'email': email}
                    if email == 'NA':
                        return {'error': f'Could not find {calendar_update} contact'}
                    query_event[event_param].append(contact)
                else:
                    if event_param not in query_event:
                        return {'error': 'No attendee list available'}
                    email = self.get_contact(calendar_update)
                    print(f'Get contact result {email}')
                    if email == 'NA':
                        return {'error': f'Could not find {calendar_update} in Google People API request.'}

                    removed = False
                    for contact in query_event[event_param]:
                        pprint(contact)
                        if contact['email'] == email:
                            query_event[event_param].remove(contact)
                            removed = True

                    if not removed:
                        return {'error': f'Could not find {calendar_update} contact in event'}
                         
            else:
                return {'error': 'Need calendar update paramter'}
                pass
            pass
        elif event_param == 'colorId':
            query_event[event_param] = event_colors[calendar_update]
        else:
            query_event[event_param] = calendar_update

        pprint(query_event)
        updated_event = self.calendar_api.events().update(calendarId='primary', eventId=query_event['id'], body=query_event).execute()

        logging.info(TAG + f"Event updated: {updated_event['updated']}")
        
        calendar_result = {}

        calendar_result['updated_event'] = updated_event
        calendar_result['calendar_param'] = calendar_param
        calendar_result['calendar_update'] = calendar_update

        return calendar_result

    #TODO implement batch requests
    def delete_event(self, **kwargs):

        if 'calendar_date' in kwargs:
            query_date = parse(kwargs['calendar_date'], {'PREFER_DATES_FROM': 'future'}).astimezone().isoformat()
        else:
            query_date = datetime.now().astimezone().isoformat()

        
        query = None
        if 'calendar_search' in kwargs:
            query = kwargs['calendar_search']

        event_num = None
        if 'event_num' in kwargs:
            event_num = self.__event_num_data[kwargs['event_num']]

        event_type = None
        if 'event_type' in kwargs:
            event_type = kwargs['event_type']


        results = self.calendar_api.events().list(calendarId='primary', maxResults=20,
            orderBy='startTime', singleEvents=True, timeMin=query_date, q=query).execute()

        events = results['items']
        query_event = None

        if event_num != None and event_type != None:
            #Find the matching event types then select the appropriate event number.
            #TODO add possibility for batch requests. EX. next 5 meetings
            event_list = []
            for event in events:
                if 'description' in event and event['description'].lower() == event_type.lower():
                    event_list.append(event)
                    print('Found event')
                elif event['summary'].lower() == event_type.lower():
                    event_list.append(event)
                else:
                    #TODO add exception for index out of range
                    pass
            query_event = event_list[event_num - 1]
        elif event_num != None and event_type == None:
            #TODO add possibility for batch requests. EX. next 5 meetings
            query_event = results['items'][event_num - 1]
            event_type = 'event'
        elif event_num == None and event_type != None:
        # No event number paramter specified. This possibility is only if a date is specified instead possibly
            for event in events:
                if 'description' in event and event['description'].lower() == event_type.lower():
                    query_event = event
        else:
            logging.info(TAG + f'Event number and event type werer not specified. Therefore could not update event.')
            return {'error': 'Could not find specified event'}

        if query_event == None:
            return {'error': 'Could not find specified event'}

        self.calendar_api.events().delete(calendarId='primary', eventId=query_event['id'], sendUpdates='all').execute()

        deleted_event = {}

        deleted_event['init_query_event_type'] = event_type
        
        if 'location' in event_type:
            deleted_event['location'] = query_event['location']

        deleted_event['init_query'] = query_event
        deleted_event['init_query_start_date'] = parse(query_event['start']['dateTime'])
        logging.info(TAG + f"Event Deleted: {query_event['id']}")

        return deleted_event

        

        

    def create_date_pair(self):
        start_time = datetime.now().astimezone()
        if start_time.minute < 30:
            start_time += timedelta(minutes=(30-start_time.minute))
        else:
            start_time += timedelta(minutes=(60-start_time.minute))

        end_time = start_time + timedelta(hours=1)
        logging.info(TAG + f'Created default date pair: {start_time} and {end_time}')
        return start_time, end_time
