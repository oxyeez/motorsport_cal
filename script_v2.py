from __future__ import print_function

import json
import os.path
import re
import sched
import sys
import time
from datetime import datetime, timedelta
from pprint import pprint
from random import choices

import dateparser
import requests
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


## Genral functions
def load_json(name):
    with open(name) as f:
        return json.load(f)


def write_schedule(schedule):
    with open('schedule_v2.json', 'w') as f:
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


def clear_past_events(schedule):
    for race_serie in schedule.values():
        for event in reversed(race_serie):
            if datetime.fromisoformat(event['end_date']).date() < datetime.now().date():
                race_serie.remove(event)
    return schedule


def create_global_event(serie, event):
    cal_event = {
        'summary': f"[{CHOICES[serie]['name'] if serie in CHOICES else CHOICES['endurance']['series'][serie]['name']}] {event['title']}",
        'start': {
            'date': datetime.fromisoformat(event['start_date']).date().isoformat(),
            },
        'end': {
            'date': (datetime.fromisoformat(event['end_date']).date() + timedelta(days=1)).isoformat(),
            }
        }
    return cal_event


def create_sub_event(serie, event, sub_event):
    cal_event = {
        'summary': f"[{CHOICES[serie]['name'] if serie in CHOICES else CHOICES['endurance']['series'][serie]['name']}] {event['title']} - {sub_event['title']}",
        'start': {
            'dateTime': sub_event['start_time']
            },
        'end': {
            'dateTime': sub_event['end_time']
            }
        }
    return cal_event


def write_event2cal(event, service):
    service.events().insert(calendarId=CONFIG['calendar_id'], body=event).execute()


def add_events2cal(schedule):
    added_in_a_row = 0
    service = get_cal_service()
    while service == None:
        time.sleep(5*60)
        service = get_cal_service()
    
    for serie, events in schedule.items():
        for event in events:
            if not event['added2cal']:
                cal_event = create_global_event(serie, event)
                write_event2cal(cal_event, service)
                event['added2cal'] = True
                time.sleep(0.6)
            for sub_event in event['sub_events']:
                if not sub_event['added2cal']:
                    cal_event = create_sub_event(serie, event, sub_event)
                    write_event2cal(cal_event, service)
                    sub_event['added2cal'] = True
                    time.sleep(0.6)
    
    return schedule


## Formula 1 functions
def update_f1_schedule(schedule):
    if 'f1' not in schedule:
        schedule['f1'] = []

    url = f"https://www.formula1.com/en/racing/{datetime.now().year}.html"
    print(f"Loading from url : {url} ...")

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    for event in soup.find_all('a', 'event-item-wrapper event-item-link'):
        url = f"https://www.formula1.com/{event.get('href')}"

        start_day = event.find('span', 'start-date').text
        end_day = event.find('span', 'end-date').text
        month = event.find('span', 'month-wrapper f1-wide--xxs').text
        start_date = f"{start_day} {month if '-' not in month else month.split('-')[0]} {datetime.now().year}"
        end_date = f"{end_day} {month if '-' not in month else month.split('-')[1]} {datetime.now().year}"
        start_date = datetime.strptime(start_date, '%d %b %Y').isoformat()
        end_date = datetime.strptime(end_date, '%d %b %Y').isoformat()

        title = event.find('div', 'event-title f1--xxs').text.replace('\n', '').replace('FORMULA 1', '').strip()
    
        if (len(schedule['f1']) == 0 or not any(event['title'] == title for event in schedule['f1'])) and datetime.fromisoformat(end_date).date() > datetime.today().date():
            schedule['f1'].append({'url': url, 'added2cal': False, 'start_date': start_date, 'end_date': end_date, 'title': title, 'sub_events': []})
    
    return add_f1_sub_events(schedule)


def add_f1_sub_events(schedule):
    for event in schedule['f1']:
        if event['url'] is not None and event['url'] != '':
            url = event['url']
            soup = BeautifulSoup(requests.get(url).text, 'html.parser')

            reg = re.compile('row js-.*')
            for sub_event in soup.find_all('div', reg):
                title = sub_event.find('p', 'f1-timetable--title').text.replace('\n', '').strip()
                start_time = f"{sub_event.get('data-start-time')}{sub_event.get('data-gmt-offset')}"
                end_time = f"{sub_event.get('data-end-time')}{sub_event.get('data-gmt-offset')}"
                
                if 'tbc' not in start_time.lower() and 'tbc' not in end_time.lower() and (len(event['sub_events']) == 0 or not any(sub_event['title'] == title for sub_event in event['sub_events'])):
                    event['sub_events'].append({'title': title, 'added2cal': False, 'start_time': start_time, 'end_time': end_time})
    
    return schedule


## MotoGP, 2 and 3 functions
def update_moto_schedule(serie, schedule):
    if serie not in schedule:
        schedule[serie] = []

    url = 'https://www.motogp.com/en/calendar'
    print(f"Loading from url : {url} ...")

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    reg = re.compile('event_container.*')
    for event in soup.find_all('div', reg):
        url = event.find('a', 'event_name').get('href') + '#schedule'
        title = event.find('a', 'event_name').text.replace('\n', '').strip()
        if '-' in title:
            title = title.split('-')[1].strip()

        if url != '#schedule':
            event_soup = BeautifulSoup(requests.get(url).text, 'html.parser')
            if event_soup.find('div', 'event-date__date') is not None:
                dates = event_soup.find('div', 'event-date__date').text.strip()
                year = re.search('([2][0]\d{2})', event_soup.find('div', 'c-schedule__date active').text).group(0)
                start_date = datetime.strptime(f"{dates.split('-')[0].strip()} {year}", '%d %b %Y')
                end_date = datetime.strptime(f"{dates.split('-')[1].strip()} {year}", '%d %b %Y')

                if (len(schedule[serie]) == 0 or not any(event['title'] == title for event in schedule[serie])) and end_date.date() > datetime.today().date():
                    schedule[serie].append({'url': url, 'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})
    
    return add_moto_sub_events(serie, schedule)


def add_moto_sub_events(serie, schedule):
    for event in schedule[serie]:
        if event['url'] is not None and event['url'] != '' and event['url'] != '#schedule':
            url = event['url']
            soup = BeautifulSoup(requests.get(url).text, 'html.parser')

            reg = re.compile('c-schedule__table-row.*')
            for sub_event in soup.find_all('div', reg):
                if serie in sub_event.text.lower() and 'Report' in sub_event.text and 'Timing' in sub_event.text:
                    dates = sub_event.find('div', 'c-schedule__table-cell visible-lg c-schedule__time').find_all('span')
                    start_time = dates[0].get('data-ini-time')
                    start_time = f"{start_time[:-2]}:{start_time[-2:]}"
                    if len(dates) > 1:
                        end_time = sub_event.find('div', 'c-schedule__table-cell visible-lg c-schedule__time').find_all('span')[1].get('data-end')
                        end_time = f"{end_time[:-2]}:{end_time[-2:]}"
                    elif 'Race' in sub_event.text:
                        end_time = (datetime.fromisoformat(start_time) + timedelta(hours=1)).isoformat()
                    else: 
                        end_time = None
                    
                    if end_time is not None:
                        title = sub_event.find('span', 'hidden-xs').text.replace('\n', '').strip()
                        if len(event['sub_events']) == 0 or not any(sub_event['title'] == title for sub_event in event['sub_events']):
                            event['sub_events'].append({'title': title, 'added2cal': False, 'start_time': start_time, 'end_time': end_time})
    return schedule


## WRC functions
def update_wrc_schedule(schedule):
    if 'wrc' not in schedule:
        schedule['wrc'] = []

    url = 'https://api.wrc.com/contel-page/83388/calendar/season/160/competition/2'
    print(f"Loading from url : {url} ...")

    response = requests.request(method="GET", url=url)
    while response.status_code != 200:
        response = requests.request(method="GET", url=url)
    
    schedule_json = json.loads(response.text)
    for event in schedule_json['rallyEvents']['items']:
        if event['status']['name'] != 'Post Event':
            url = f"https://api.wrc.com/sdb/rallyevent/{event['id']}"
            title = event['name']
            start_date = datetime.strptime(event['eventDays'][0]['eventDay'], '%Y-%m-%d').isoformat()
            end_date = datetime.strptime(event['eventDays'][len(event['eventDays'])-1]['eventDay'], '%Y-%m-%d').isoformat()
            
            if (len(schedule['wrc']) == 0 or not any(event['title'] == title for event in schedule['wrc'])):
                schedule['wrc'].append({'url': url, 'added2cal': False, 'start_date': start_date, 'end_date': end_date, 'title': title, 'sub_events': []})

    return add_wrc_sub_events(schedule)


def add_wrc_sub_events(schedule):
    for event in schedule['wrc']:
        if event['url'] is not None and event['url'] != '':
            url = event['url']
            response = requests.request(method="GET", url=url)
            while response.status_code != 200:
                response = requests.request(method="GET", url=url)
            
            event_json = json.loads(response.text)
            for sub_event in event_json['eventDays']:
                for day in sub_event['spottChannel']['assets']:
                    if 'Pre Show' in day['alternative']['title'] or 'SS' in day['alternative']['title']:
                        title = day['alternative']['title'].split('-')[0].strip()
                        start_time = day['start']
                        end_time = day['end']

                        if len(event['sub_events']) == 0 or not any(sub_event['title'] == title for sub_event in event['sub_events']):
                            event['sub_events'].append({'title': title, 'added2cal': False, 'start_time': start_time, 'end_time': end_time})

    return schedule


## Endurance functions
def update_endurance_schedule(serie, schedule):
    if serie not in schedule:
        schedule[serie] = []

    url = f"https://www.endurance-info.com/calendrier?category=5&championship={str(CHOICES['endurance']['series'][serie]['url_code'])}&year={datetime.now().year}&month=all"
    print(f"Loading from url : {url} ...")

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    cal = soup.find('div', 'block system-main-block contenudelapageprincipale')
    for event in cal.find_all('div', 'views-row'):
        title = event.find('div', 'field field--name-title field--type-string field__item').text.replace('\n', '').strip()
        dates = event.find('div', 'date')
        start_date = re.search('(\d{1,2}\s[a-zûé]{3,4})', dates.find('div', 'field field--name-field-beginning-date field--type-datetime field__item').text.strip()).group(0)
        start_date = dateparser.parse(f"{start_date} {datetime.now().year}")
        end_date = re.search('(\d{1,2}\s[a-zûé]{3,4})', dates.find('div', 'field field--name-field-ending-date field--type-datetime field__item').text.strip()).group(0)
        end_date = dateparser.parse(f"{end_date} {datetime.now().year}")

        if (len(schedule[serie]) == 0 or not any(event['title'] == title for event in schedule[serie])) and end_date.date() > datetime.today().date():
            schedule[serie].append({'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})

    return schedule


## IndyCar and IndyLights functions
def update_indycar_schedule(schedule, lights=False):
    serie = 'indycar' if not lights else 'indylights'
    if serie not in schedule:
        schedule[serie] = []
    
    url = 'https://www.indycar.com/Schedule' if not lights else 'https://www.indycar.com/indylights/schedule'
    print(f"Loading from url : {url} ...")

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    for event in soup.find('div', 'schedule-list').find_all('li', 'schedule-list__item'):
        url = f"https://www.indycar.com{event.find('a', 'panel-trigger schedule-list__title').get('href')}"
        title = re.sub(' +', ' ', event.find('a', 'panel-trigger schedule-list__title').find('span').text.replace('\n', '').strip())
        end_day = re.sub(' +', ' ', event.find('div', 'schedule-list__date').text.replace('\n', '').replace('\r', '').strip())
        end_date = datetime.strptime(f"{end_day} {datetime.now().year}", '%b %d %Y')
        start_date = (end_date - timedelta(days=2))

        if (len(schedule[serie]) == 0 or not any(event['title'] == title for event in schedule[serie])) and end_date.date() > datetime.today().date():
            schedule[serie].append({'url': url, 'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})

    return add_indycar_sub_events(schedule, lights)


def add_indycar_sub_events(schedule, lights=False):
    serie = 'indycar' if not lights else 'indylights'
    for event in schedule[serie]:
        if event['url'] is not None and event['url'] != '':
            url = event['url']
            soup = BeautifulSoup(requests.get(url).text, 'html.parser')

            for div in soup.find_all('div', 'detail-section'):
                if 'Weekend Schedule/Results' in div.text:
                    for sub_event in div.find('div', 'race-list').find_all('div', 'race-list__item'):
                        title = sub_event.find('div', 'race-list__race text').text.replace('\n', '').strip()
                        day = sub_event.find('div', 'race-list__date text').text.replace('\n', '').replace('\r', '').split(',')[1].strip()
                        date = f"{datetime.now().year} {day}"
                        start_time = sub_event.find('div', 'race-list__time text').text.replace('ET', '').replace('\n', '').replace('\r', '').split('-')[0].strip()
                        end_time = sub_event.find('div', 'race-list__time text').text.replace('ET', '').replace('\n', '').replace('\r', '').split('-')[1].strip()
                        start_time = datetime.strptime(f"{date} {start_time} -0500", '%Y %b %d %I:%M %p %z').isoformat()
                        end_time = datetime.strptime(f"{date} {end_time} -0500", '%Y %b %d %I:%M %p %z').isoformat()
                        
                        if len(event['sub_events']) == 0 or not any(sub_event['title'] == title for sub_event in event['sub_events']):
                            event['sub_events'].append({'title': title, 'added2cal': False, 'start_time': start_time, 'end_time': end_time})
    
    return schedule



## Main
def main():
    global CHOICES, CONFIG
    CHOICES = load_json('choices.json')
    CONFIG = load_json('config.json')

    if os.path.exists('schedule_v2.json'):
        schedule = load_json('schedule_v2.json')
    else: 
        schedule = {}

    start_scraping = time.time()
    if CHOICES['f1']['track']:
        schedule = update_f1_schedule(schedule)
    if CHOICES['motogp']['track']:
        schedule = update_moto_schedule('motogp', schedule)
    if CHOICES['moto2']['track']:
        schedule = update_moto_schedule('moto2', schedule)
    if CHOICES['moto3']['track']:
        schedule = update_moto_schedule('moto3', schedule)
    if CHOICES['wrc']['track']:
        schedule = update_wrc_schedule(schedule)
    for serie_name, serie in CHOICES['endurance']['series'].items():
        if serie['track'] or CHOICES['endurance']['track_all']:
            if serie_name == '24lemans' and (CHOICES['endurance']['series']['wec']['track'] or CHOICES['endurance']['track_all']):
                pass
            else:
                schedule = update_endurance_schedule(serie_name, schedule)
    if CHOICES['indycar']['track']:
        schedule = update_indycar_schedule(schedule)
    if CHOICES['indylights']['track']:
        schedule = update_indycar_schedule(schedule, lights=True)
    
    end_scraping = time.time()
    print(f"Scraping done in {end_scraping - start_scraping} seconds")

    start_writing2cal = time.time()
    add_events2cal(schedule)
    end_writing2cal = time.time()
    print(f"Writing to calendar done in {end_writing2cal - start_writing2cal} seconds")

    write_schedule(schedule)

if __name__ == "__main__":
    main()