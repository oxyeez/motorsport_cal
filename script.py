from __future__ import print_function

import json
import os.path
import sys
from datetime import datetime, timedelta, time
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def load_json(name):
    with open(name) as f:
        return json.load(f)


def write_schedule(schedule):
    with open('schedule.json', 'w') as f:
        json.dump(schedule, f)


def get_cal_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', CONFIG['SCOPES'])

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', CONFIG['SCOPES'])
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build(CONFIG['API_NAME'], CONFIG['API_VERSION'], credentials=creds)
        return service

    except HttpError as error:
        print('An error occurred: %s' % error)
        return None


def write_event2cal(race_serie, event, sub_event, service):
    sub_event_values = VALUES[race_serie]['sub_event'][sub_event['title']]
    title = f"[{VALUES[race_serie]['name']}] {event['title']} - {sub_event_values['full_name']}"
    cal_event = {
        'summary': title,
        'start': {
            'dateTime': f"{sub_event['date']}",
            'timeZone': 'Europe/Paris',
            },
        'end': {
            'dateTime': f"{(datetime.fromisoformat(sub_event['date']) + timedelta(hours=int(sub_event_values['duration'].split(':')[0]), minutes=int(sub_event_values['duration'].split(':')[1]))).isoformat()}",
            'timeZone': 'Europe/Paris',
            }
        }
    pprint(f"Adding {cal_event['summary']} to calendar ...")
    service.events().insert(calendarId=CONFIG['calendar_id'], body=cal_event).execute()

    
def clear_schedule(schedule):
    for race_serie in schedule.values():
        for event in reversed(race_serie):
            if datetime.fromisoformat(event['date']).date() < datetime.now().date():
                race_serie.remove(event)
    return schedule


def update_serie_schedule(schedule, race_serie):
    if race_serie not in schedule:
        schedule[race_serie] = []
            
    page = 1
    while True:
        url = f"https://www.motorsport.com/{race_serie}/schedule/{datetime.today().year}/?event_types%5B%5D=race&p={page}"
        print(f"Loading from url : {url} ...")
        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        
        if soup.find('div', 'ms-schedule-fullwidth ms-mb').text.strip() == 'No results found':
            break
        else: page += 1

        for tbody in soup.find_all('tbody', ['ms-schedule-table__item ms-schedule-table__item--upcoming', 'ms-schedule-table__item ms-schedule-table__item--upcoming ms-schedule-table__item--open']):
            event_code = tbody.get('data-url').split('/')[2]
            confirmed = ''.join(tbody.find('div', 'ms-schedule-table-date ms-schedule-table-date--your').text.strip().split(' ')) == ''
            date = datetime.strptime(tbody.find('div', 'ms-schedule-table-date ms-schedule-table-date--local').text.strip() + ' 2022', '%d %b %Y').isoformat()
            title = tbody.find('div', 'ms-schedule-table-item-main__event').text.strip().split('  ')[0]

            if (len(schedule[race_serie]) == 0 or not any(event['event_code'] == event_code for event in schedule[race_serie])) and datetime.fromisoformat(date).date() > datetime.today().date():
                schedule[race_serie].append({'event_code': event_code, 'confirmed': confirmed, 'added2cal': False, 'date': date, 'title': title, 'sub-events': []})
            elif confirmed:
                for event in schedule[race_serie]:
                    if event['event_code'] == event_code and not event['added2cal']:
                        event['confirmed'] = confirmed
                        event['date'] = date
                        event['title'] = title
                        break
        
        schedule[race_serie].sort(key=lambda event: datetime.fromisoformat(event['date']))
    
    return schedule


def add_sub_events(schedule):
    for race_serie, events in schedule.items():
        for event in events:
            if event['confirmed'] and not event['added2cal']:
                url = f"https://www.motorsport.com/{race_serie}/event/{event['title'].lower().replace(' ', '-')}-{event['event_code']}/{event['event_code']}"
                soup = BeautifulSoup(requests.get(url).text, 'html.parser')
                schedule_div = soup.find('div', 'ms-schedule-table-day-subevents ms-schedule-table-day-subevents--your')
                for sub_event_div in schedule_div.find_all('div', 'ms-schedule-table-subevent-day'):
                    sub_event_title = sub_event_div.find('div', 'ms-schedule-table-subevent-day__main').text.strip()
                    sub_event_timestamp = int(sub_event_div.find('span', 'ms-schedule-table-subevent-day__time').get('data-datems'))
                    sub_event_date = datetime.fromtimestamp(sub_event_timestamp).isoformat()
                    event['sub-events'].append({'title': sub_event_title, 'date': sub_event_date})

            event['sub-events'].sort(key=lambda sub_event: datetime.fromisoformat(sub_event['date']))
    
    return schedule


def add_events_to_calendar(schedule):
    service = get_cal_service()
    while service == None:
        time.sleep(5*60)
        service = get_cal_service()
    
    for race_serie, events in schedule.items():
        for event in events:
            if event['confirmed'] and not event['added2cal'] and len(event['sub-events']) > 0:
                for sub_event in event['sub-events']:
                    if sub_event['title'] in VALUES[race_serie]['sub_event']:
                        write_event2cal(race_serie, event, sub_event, service)
                
                event['added2cal'] = True
    
    return schedule


def main():
    global VALUES, CONFIG
    VALUES = load_json('values.json')
    CONFIG = load_json('config.json')

    if os.path.exists('token.json'):
        schedule = load_json('schedule.json')
    else: 
        schedule = {}
    
    schedule = clear_schedule(schedule)
    for serie, wanted in CONFIG['wanted_series'].items():
        if wanted:
            schedule = update_serie_schedule(schedule, serie)
    
    schedule = add_sub_events(schedule)
    schedule = add_events_to_calendar(schedule)
    write_schedule(schedule)

if __name__ == '__main__':
    main()
