from __future__ import print_function

import json
import os.path
import re
import time
import warnings
from datetime import datetime, timedelta

import dateparser
import requests
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rich.progress import track


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
    for race_serie_events in schedule.values():
        for event in reversed(race_serie_events):
            if datetime.fromisoformat(event['end_date']).date() < datetime.now().date():
                race_serie_events.remove(event)
    return schedule


def set_all_to_remove(schedule):
    for serie in schedule.values():
        for event in serie:
            if event['added2cal']:
                event['to_remove'] = True
                for sub_event in event['sub_events']:
                    sub_event['to_remove'] = True
    return schedule


def event_cal_title(serie, event):
    return f"[{CHOICES[serie]['name'] if serie in CHOICES else CHOICES['endurance']['series'][serie]['name']}] {event['title']}"


def create_global_event(serie, event):
    cal_event = {
        'summary': event_cal_title(serie, event),
        'start': {
            'date': datetime.fromisoformat(event['start_date']).date().isoformat(),
            },
        'end': {
            'date': (datetime.fromisoformat(event['end_date']).date() + timedelta(days=1)).isoformat(),
            }
        }
    return cal_event


def sub_event_cal_title(serie, event, sub_event):
    return f"{event_cal_title(serie, event)} - {sub_event['title']}"


def create_sub_event(serie, event, sub_event):
    cal_event = {
        'summary': sub_event_cal_title(serie, event, sub_event),
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


def grab_cal_events(service):
    events = {}
    page_token = None
    while True:
        response = service.events().list(calendarId=CONFIG['calendar_id'], pageToken=page_token).execute()
        for event in response['items']:
            events[event['summary']] =  event['id']
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    
    return events


def delete_cal_event(event_id, service):
    service.events().delete(calendarId=CONFIG['calendar_id'], eventId=event_id).execute()


def update_cal_event(event_id, event, service):
    service.events().update(calendarId=CONFIG['calendar_id'], eventId=event_id, body=event).execute()


def update_calendar(schedule):
    added_events = []
    removed_events = []
    updated_events = []
    service = get_cal_service()
    while service == None:
        time.sleep(60)
        service = get_cal_service()
    cal_events = grab_cal_events(service)
    
    start_updating_cal = time.time()
    for serie, events in track(schedule.items()):
        for event in reversed(events):
            for sub_event in reversed(event['sub_events']):
                if not sub_event['added2cal']:
                    cal_event = create_sub_event(serie, event, sub_event)
                    write_event2cal(cal_event, service)
                    sub_event['added2cal'] = True
                    added_events.append(cal_event['summary'])
                    time.sleep(0.6)
                elif 'to_remove' in sub_event and sub_event['to_remove']:
                    cal_event_title = sub_event_cal_title(serie, event, sub_event)
                    if cal_event_title in cal_events:
                        delete_cal_event(cal_events[cal_event_title], service)
                        event['sub_events'].remove(sub_event)
                        removed_events.append(cal_event_title)
                        time.sleep(0.6)
                elif 'to_update' in sub_event and sub_event['to_update']:
                    cal_event_title = sub_event_cal_title(serie, event, sub_event)
                    if cal_event_title in cal_events:
                        cal_event = create_sub_event(serie, event, sub_event)
                        update_cal_event(cal_events[cal_event_title], cal_event, service)
                        sub_event['to_update'] = False
                        updated_events.append(cal_event_title)
                        time.sleep(0.6)
            if not event['added2cal']:
                cal_event = create_global_event(serie, event)
                write_event2cal(cal_event, service)
                event['added2cal'] = True
                added_events.append(cal_event['summary'])
                time.sleep(0.6)
            elif 'to_remove' in event and event['to_remove']:
                cal_event_title = event_cal_title(serie, event)
                if cal_event_title in cal_events:
                    delete_cal_event(cal_events[cal_event_title], service)
                    events.remove(event)
                    removed_events.append(cal_event_title)
                    time.sleep(0.6)
            elif 'to_update' in event and event['to_update']:
                cal_event_title = event_cal_title(serie, event)
                if cal_event_title in cal_events:
                    cal_event = create_global_event(serie, event)
                    update_cal_event(cal_events[cal_event_title], cal_event, service)
                    event['to_update'] = False
                    updated_events.append(cal_event_title)
                    time.sleep(0.6)

    end_updating_cal = time.time()
    if len(added_events) > 0:
        print(f"Added {len(added_events)} events to calendar :")
        for event in added_events:
            print(f"\t{event}")
    else:
        print('No event added to calendar')
    if len(updated_events) > 0:
        print(f"Updated {len(updated_events)} events in calendar :")
        for event in updated_events:
            print(f"\t{event}")
    else:
        print('No event updated in calendar')
    if len(removed_events) > 0:
        print(f"Removed {len(removed_events)} events from calendar :")
        for event in removed_events:
            print(f"\t{event}")
    else:
        print('No event removed from calendar')
    if len(added_events) > 0 or len(removed_events) > 0 or len(updated_events) > 0:
        print(f"Calendar update done in {end_updating_cal - start_updating_cal} seconds")

    return schedule


## Formula 1 functions
def update_f1_schedule(schedule):
    if 'f1' not in schedule:
        schedule['f1'] = []

    url = f"https://www.formula1.com/en/racing/{datetime.now().year}.html"
    print(f"Getting {CHOICES['f1']['name']} schedule")

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    for event in soup.find_all('a', 'event-item-wrapper event-item-link'):
        url = f"https://www.formula1.com/{event.get('href')}"

        start_day = event.find('span', 'start-date').text
        end_day = event.find('span', 'end-date').text
        month = event.find('span', 'month-wrapper f1-wide--xxs').text
        start_date = f"{start_day} {month if '-' not in month else month.split('-')[0]} {datetime.now().year}"
        end_date = f"{end_day} {month if '-' not in month else month.split('-')[1]} {datetime.now().year}"
        start_date = datetime.strptime(start_date, '%d %b %Y')
        end_date = datetime.strptime(end_date, '%d %b %Y')

        title = event.find('div', 'event-title f1--xxs').text.replace('\n', '').replace('FORMULA 1', '').strip()
    
        if (len(schedule['f1']) == 0 or not any(event['title'] == title for event in schedule['f1'])) and end_date.date() >= datetime.today().date():
            schedule['f1'].append({'url': url, 'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})
        else:
            for event in schedule['f1']:
                if event['title'] == title and event['added2cal']:
                    event['to_remove'] = False
                    if event['start_date'] != start_date.isoformat() or event['end_date'] != end_date.isoformat():
                        event['start_date'] = start_date.isoformat()
                        event['end_date'] = end_date.isoformat()
                        event['to_update'] = True
                    break

    return add_f1_sub_events(schedule)


def add_f1_sub_events(schedule):
    for event in track(schedule['f1'], description='adding sub events'):
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
                else:
                    for sub_event in event['sub_events']:
                        if sub_event['title'] == title and sub_event['added2cal']:
                            sub_event['to_remove'] = False
                            if sub_event['start_time'] != start_time or sub_event['end_time'] != end_time:
                                sub_event['start_time'] = start_time
                                sub_event['end_time'] = end_time
                                sub_event['to_update'] = True
                            break

    return schedule


## Formula 2 and Formula 3 functions
def update_lower_formula_schedule(serie, schedule):
    if serie not in schedule:
        schedule[serie] = []

    url = f"https://www.fiaformula{serie.replace('f','')}.com/Calendar"
    print(f"Getting {CHOICES[serie]['name']} schedule from {url} ...")

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    for event in soup.find_all('div', 'col-12 col-sm-6 col-lg-4 col-xl-3 result-card pre-race-wrapper'):
        url = f"https://www.formula{serie.replace('f','')}.com{event.find('a').get('href')}"
        title = f"{event.find('p', 'h6').text.strip()} : {event.find('span', 'ellipsis').text.strip()}"

        start_date = datetime.strptime(f"{event.find('span', 'start-date').text.strip()} {event.find('span', 'month').text.strip()} {datetime.now().year}", '%d %B %Y')
        end_date = datetime.strptime(f"{event.find('span', 'end-date').text.strip()} {event.find('span', 'month').text.strip()} {datetime.now().year}", '%d %B %Y')
        if end_date < start_date:
            start_date = start_date - timedelta(months=1)
        
        if (len(schedule[serie]) == 0 or not any(event['title'] == title for event in schedule[serie])) and end_date.date() >= datetime.today().date():
            schedule[serie].append({'url': url, 'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})
        else:
            for event in schedule[serie]:
                if event['title'] == title and event['added2cal']:
                    event['to_remove'] = False
                    if event['start_date'] != start_date.isoformat() or event['end_date'] != end_date.isoformat():
                        event['start_date'] = start_date.isoformat()
                        event['end_date'] = end_date.isoformat()
                        event['to_update'] = True
                    break

    return add_lower_formula_sub_events(serie, schedule)


def add_lower_formula_sub_events(serie, schedule):
    for event in schedule[serie]:
        if event['url'] is not None and event['url'] != '':
            url = f"https://api.formula1.com/v1/f2f3-fom-results/races/{event['url'][-4:]}?website={serie}"
            
            apikey = 'Ij4Lwi0yPPhuTstW1hhmmd9ntwTGhjNe' if serie == 'f2' else 'uwwf2TIPm5aMRFIAUfjwF5HQBMWAGSeE'
            response = requests.request(method='GET', url=url, headers={'apikey': apikey})
            event_json = json.loads(response.text)

            for sub_event in event_json['SessionResults']:
                title = sub_event['SessionName']
                start_time = sub_event['SessionStartTime']
                end_time = sub_event['SessionEndTime']

                if not sub_event['Unconfirmed'] and (len(event['sub_events']) == 0 or not any(sub_event['title'] == title for sub_event in event['sub_events'])):
                    event['sub_events'].append({'title': title, 'added2cal': False, 'start_time': start_time, 'end_time': end_time})
                else:
                    for sub_event in event['sub_events']:
                        if sub_event['title'] == title and sub_event['added2cal']:
                            sub_event['to_remove'] = False
                            if sub_event['start_time'] != start_time or sub_event['end_time'] != end_time:
                                sub_event['start_time'] = start_time
                                sub_event['end_time'] = end_time
                                sub_event['to_update'] = True
                            break

    return schedule


## MotoGP, 2 and 3 functions
def update_moto_schedule(serie, schedule):
    if serie not in schedule:
        schedule[serie] = []

    url = 'https://www.motogp.com/en/calendar'
    print(f"Getting {CHOICES[serie]['name']} schedule from {url} ...")

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

                if (len(schedule[serie]) == 0 or not any(event['title'] == title for event in schedule[serie])) and end_date.date() >= datetime.today().date():
                    schedule[serie].append({'url': url, 'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})
                else:
                    for event in schedule[serie]:
                        if event['title'] == title and event['added2cal']:
                            event['to_remove'] = False
                            if event['start_date'] != start_date.isoformat() or event['end_date'] != end_date.isoformat():
                                event['start_date'] = start_date.isoformat()
                                event['end_date'] = end_date.isoformat()
                                event['to_update'] = True
                            break

    return add_moto_sub_events(serie, schedule)


def add_moto_sub_events(serie, schedule):
    for event in schedule[serie]:
        if event['url'] is not None and event['url'] != '' and event['url'] != '#schedule':
            url = event['url']
            soup = BeautifulSoup(requests.get(url).text, 'html.parser')

            reg = re.compile('c-schedule__table-row.*')
            for sub_event in soup.find_all('div', reg):
                if serie in sub_event.text.lower() and ('report' in sub_event.text.lower() or 'timing' in sub_event.text.lower() or 'result' in sub_event.text.lower()):
                    dates = sub_event.find('div', 'c-schedule__table-cell visible-lg c-schedule__time').find_all('span')
                    start_time = dates[0].get('data-ini-time')
                    start_time = f"{start_time[:-2]}:{start_time[-2:]}"
                    if len(dates) > 1:
                        end_time = sub_event.find('div', 'c-schedule__table-cell visible-lg c-schedule__time').find_all('span')[1].get('data-end')
                        end_time = f"{end_time[:-2]}:{end_time[-2:]}"
                    elif 'race' in sub_event.text.lower():
                        end_time = (datetime.fromisoformat(start_time) + timedelta(hours=1)).isoformat()
                    else: 
                        end_time = None
                    
                    if end_time is not None:
                        title = sub_event.find('span', 'hidden-xs').text.replace('\n', '').strip()
                        if len(event['sub_events']) == 0 or not any(sub_event['title'] == title for sub_event in event['sub_events']):
                            event['sub_events'].append({'title': title, 'added2cal': False, 'start_time': start_time, 'end_time': end_time})
                        else:
                            for sub_event in event['sub_events']:
                                if sub_event['title'] == title and sub_event['added2cal']:
                                    sub_event['to_remove'] = False
                                    if sub_event['start_time'] != start_time or sub_event['end_time'] != end_time:
                                        sub_event['start_time'] = start_time
                                        sub_event['end_time'] = end_time
                                        sub_event['to_update'] = True
                                    break
    
    return schedule


## WRC functions
def update_wrc_schedule(schedule):
    if 'wrc' not in schedule:
        schedule['wrc'] = []

    url = 'https://api.wrc.com/contel-page/83388/calendar/season/160/competition/2'
    print(f"Getting WRC schedule from {url} ...")

    response = requests.request(method='GET', url=url)
    while response.status_code != 200:
        response = requests.request(method='GET', url=url)
    
    schedule_json = json.loads(response.text)
    for event in schedule_json['rallyEvents']['items']:
        if event['status']['name'] != 'Post Event':
            url = f"https://api.wrc.com/sdb/rallyevent/{event['id']}"
            title = event['name']
            start_date = datetime.strptime(event['eventDays'][0]['eventDay'], '%Y-%m-%d')
            end_date = datetime.strptime(event['eventDays'][len(event['eventDays'])-1]['eventDay'], '%Y-%m-%d')
            
            if (len(schedule['wrc']) == 0 or not any(event['title'] == title for event in schedule['wrc'])):
                schedule['wrc'].append({'url': url, 'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})
            else:
                for event in schedule['wrc']:
                    if event['title'] == title and event['added2cal']:
                        event['to_remove'] = False
                        if event['start_date'] != start_date.isoformat() or event['end_date'] != end_date.isoformat():
                            event['start_date'] = start_date.isoformat()
                            event['end_date'] = end_date.isoformat()
                            event['to_update'] = True
                        break

    return add_wrc_sub_events(schedule)


def add_wrc_sub_events(schedule):
    for event in schedule['wrc']:
        if event['url'] is not None and event['url'] != '':
            url = event['url']
            response = requests.request(method='GET', url=url)
            while response.status_code != 200:
                response = requests.request(method='GET', url=url)
            
            event_json = json.loads(response.text)
            for sub_event in event_json['eventDays']:
                for day in sub_event['spottChannel']['assets']:
                    if 'Pre Show' in day['alternative']['title'] or 'SS' in day['alternative']['title']:
                        title = day['alternative']['title'].split('-')[0].strip()
                        start_time = day['start']
                        end_time = day['end']

                        if len(event['sub_events']) == 0 or not any(sub_event['title'] == title for sub_event in event['sub_events']):
                            event['sub_events'].append({'title': title, 'added2cal': False, 'start_time': start_time, 'end_time': end_time})
                        else:
                            for sub_event in event['sub_events']:
                                if sub_event['title'] == title and sub_event['added2cal']:
                                    sub_event['to_remove'] = False
                                    if sub_event['start_time'] != start_time or sub_event['end_time'] != end_time:
                                        sub_event['start_time'] = start_time
                                        sub_event['end_time'] = end_time
                                        sub_event['to_update'] = True
                                    break

    return schedule


## WEC functions
def update_wec_schedule(schedule):
    if 'wec' not in schedule:
        schedule['wec'] = []

    url = f"https://wec-magazin.com/calendar-{datetime.now().year}/"
    print(f"Getting {CHOICES['wec']['name']} schedule")

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    for event in soup.find_all('div', 'wp-block-themeisle-blocks-advanced-column'):
        if event.find('p') is not None:
            url = event.find('a').get('href')
            title = event.find('h4').text.replace('\n', '').strip()
            
            dates = event.find('p').text.replace('\n', '').strip().split('–')
            if len(dates) == 1:
                start_date = datetime.strptime(dates[0].strip(), '%d/%m/%Y')
                end_date = start_date + timedelta(days=2)
            else:
                start_date = datetime.strptime(dates[0].strip() + dates[1].split('/')[-1].strip(), '%d/%m/%Y')
                end_date = datetime.strptime(dates[1].strip(), '%d/%m/%Y')        
        
            if (len(schedule['wec']) == 0 or not any(event['title'] == title for event in schedule['wec'])) and end_date.date() >= datetime.today().date():
                schedule['wec'].append({'url': url, 'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})
            else:
                for event in schedule['wec']:
                    if event['title'] == title and event['added2cal']:
                        event['to_remove'] = False
                        if event['start_date'] != start_date.isoformat() or event['end_date'] != end_date.isoformat():
                            event['start_date'] = start_date.isoformat()
                            event['end_date'] = end_date.isoformat()
                            event['to_update'] = True
                        break

    return add_wec_sub_events(schedule)


def add_wec_sub_events(schedule):
    for event in schedule['wec']:
        if event['url'] is not None and event['url'] != '':
            url = event['url']
            soup = BeautifulSoup(requests.get(url).text, 'html.parser')

            reg = re.compile('wp-block-kadence-tab kt-tab-inner-content kt-inner-tab-2.*')
            table = soup.find('div', reg).find('table')
            timezone = None
            for sub_event in table.find_all('tr'):
                if sub_event.find('strong') is not None and timezone is None:
                    timezone = sub_event.find_all('td')[2].text.split('(')[1].split(')')[0].strip()
                elif timezone is not None:
                    info = sub_event.find_all('td')
                    title = info[0].text.replace('\n', '').strip()
                    date = info[1].text.replace('\n', '').strip()
                    if title.lower() != 'race (end)' and str(datetime.now().year) in date:
                        if title.lower() == 'race (start)':
                            time = info[2].text.replace('\n', '').strip()
                            start_time = datetime.strptime(f"{date} {time} +0100", '%d/%m/%Y %H:%M %z')
                            end_time = start_time + timedelta(days=1)
                        else:
                            times = info[2].text.replace('\n', '').strip().split('–')
                            if 'am' in times[0].lower() or 'pm' in times[0].lower():
                                start_time = datetime.strptime(f"{date} {times[0].strip().replace('00:', '12:')} +0100", '%d/%m/%Y %I:%M %p %z')
                                end_time = datetime.strptime(f"{date} {times[1].strip().replace('00:', '12:')} +0100", '%d/%m/%Y %I:%M %p %z')
                            else:
                                start_time = datetime.strptime(f"{date} {times[0].strip()} +0100", '%d/%m/%Y %H:%M %z')
                                end_time = datetime.strptime(f"{date} {times[1].strip()} +0100", '%d/%m/%Y %H:%M %z')
                        
                        if end_time < start_time:
                            end_time += timedelta(days=1)

                        if len(event['sub_events']) == 0 or not any(sub_event['title'] == title for sub_event in event['sub_events']):
                            event['sub_events'].append({'title': title, 'added2cal': False, 'start_time': start_time.isoformat(), 'end_time': end_time.isoformat()})
                        else:
                            for sub_event in event['sub_events']:
                                if sub_event['title'] == title and sub_event['added2cal']:
                                    sub_event['to_remove'] = False
                                    if sub_event['start_time'] != start_time or sub_event['end_time'] != end_time:
                                        sub_event['start_time'] = start_time
                                        sub_event['end_time'] = end_time
                                        sub_event['to_update'] = True
                                    break
    return schedule

## Other endurance series function
def update_endurance_schedule(serie, schedule):
    if serie not in schedule:
        schedule[serie] = []

    url = f"https://www.endurance-info.com/calendrier?category=5&championship={str(CHOICES['endurance']['series'][serie]['url_code'])}&year={datetime.now().year}&month=all"
    print(f"Getting {CHOICES['endurance']['series'][serie]['name']} schedule from {url} ...")

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    cal = soup.find('div', 'block system-main-block contenudelapageprincipale')
    for event in cal.find_all('div', 'views-row'):
        title = event.find('div', 'field field--name-title field--type-string field__item').text.replace('\n', '').strip()
        dates = event.find('div', 'date')
        start_date = re.search('(\d{1,2}\s[a-zûé]{3,4})', dates.find('div', 'field field--name-field-beginning-date field--type-datetime field__item').text.strip()).group(0)
        start_date = dateparser.parse(f"{start_date} {datetime.now().year}")
        end_date = re.search('(\d{1,2}\s[a-zûé]{3,4})', dates.find('div', 'field field--name-field-ending-date field--type-datetime field__item').text.strip()).group(0)
        end_date = dateparser.parse(f"{end_date} {datetime.now().year}")

        if (len(schedule[serie]) == 0 or not any(event['title'] == title for event in schedule[serie])) and end_date.date() >= datetime.today().date():
            schedule[serie].append({'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})
        else:
            for event in schedule[serie]:
                if event['title'] == title and event['added2cal']:
                    event['to_remove'] = False
                    if event['start_date'] != start_date.isoformat() or event['end_date'] != end_date.isoformat():
                        event['start_date'] = start_date.isoformat()
                        event['end_date'] = end_date.isoformat()
                        event['to_update'] = True
                    break
    
    return schedule


## IndyCar and IndyLights functions
def update_indycar_schedule(schedule, lights=False):
    serie = 'indycar' if not lights else 'indylights'
    if serie not in schedule:
        schedule[serie] = []
    
    url = 'https://www.indycar.com/Schedule' if not lights else 'https://www.indycar.com/indylights/schedule'
    print(f"Getting {CHOICES[serie]['name']} schedule from {url} ...")

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    for event in soup.find('div', 'schedule-list').find_all('li', 'schedule-list__item'):
        url = f"https://www.indycar.com{event.find('a', 'panel-trigger schedule-list__title').get('href')}"
        title = re.sub(' +', ' ', event.find('a', 'panel-trigger schedule-list__title').find('span').text.replace('\n', '').strip())
        
        event_soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        if event_soup.find('div', 'page-heading__title') is not None:
            dates = event_soup.find('div', 'page-heading__title').find('h2').text.replace('\n', '').replace('\r', '').strip()
            start_date = datetime.strptime(f"{datetime.now().year} {dates.split('-')[0].strip()}", '%Y %B %d')
            if len(dates.split('-')[1].strip()) < 3:
                end_date = datetime.strptime(f"{datetime.now().year} {datetime.strftime(start_date, '%m')} {dates.split('-')[1].strip()}", '%Y %m %d')
            else: 
                end_date = datetime.strptime(f"{datetime.now().year} {dates.split('-')[1].strip()}", '%Y %B %d')

        if (len(schedule[serie]) == 0 or not any(event['title'] == title for event in schedule[serie])) and end_date.date() >= datetime.today().date():
            schedule[serie].append({'url': url, 'added2cal': False, 'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'title': title, 'sub_events': []})
        else:
            for event in schedule[serie]:
                if event['title'] == title and event['added2cal']:
                    event['to_remove'] = False
                    if event['start_date'] != start_date.isoformat() or event['end_date'] != end_date.isoformat():
                        event['start_date'] = start_date.isoformat()
                        event['end_date'] = end_date.isoformat()
                        event['to_update'] = True
                    break
    
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
                        start_time = datetime.strptime(f"{date} {start_time} -0500", '%Y %b %d %I:%M %p %z')
                        end_time = datetime.strptime(f"{date} {end_time} -0500", '%Y %b %d %I:%M %p %z')
                        
                        if len(event['sub_events']) == 0 or not any(sub_event['title'] == title for sub_event in event['sub_events']):
                            event['sub_events'].append({'title': title, 'added2cal': False, 'start_time': start_time.isoformat(), 'end_time': end_time.isoformat()})
                        else:
                            for sub_event in event['sub_events']:
                                if sub_event['title'] == title and sub_event['added2cal']:
                                    sub_event['to_remove'] = False
                                    if sub_event['start_time'] != start_time.isoformat() or sub_event['end_time'] != end_time.isoformat():
                                        sub_event['start_time'] = start_time.isoformat()
                                        sub_event['end_time'] = end_time.isoformat()
                                        sub_event['to_update'] = True
                                    break
    
    return schedule


## Main
def main():
    global CHOICES, CONFIG
    CHOICES = load_json('choices.json')
    CONFIG = load_json('config.json')

    warnings.filterwarnings("ignore")

    if os.path.exists('schedule_v2.json'):
        schedule = load_json('schedule_v2.json')
        schedule = clear_past_events(schedule)
        schedule = set_all_to_remove(schedule)
    else: 
        schedule = {}

    start_scraping = time.time()

    for serie_name, serie in CHOICES.items():
        if serie_name == 'f1' and serie['track']:
            schedule = update_f1_schedule(schedule)
        elif (serie_name in ['f2', 'f3']) and serie['track']:
            schedule = update_lower_formula_schedule(serie_name, schedule)
        elif (serie_name in ['motogp', 'moto2', 'moto3']) and serie['track']:
            schedule = update_moto_schedule(serie_name, schedule)
        elif serie_name == 'wrc' and serie['track']:
            schedule = update_wrc_schedule(schedule)
        elif serie_name == 'wec' and serie['track']:
            schedule = update_wec_schedule(schedule)
        elif serie_name == 'endurance':
            for sub_serie_name, sub_serie in serie['series'].items():
                if sub_serie['track'] or serie['track_all']:
                    schedule = update_endurance_schedule(sub_serie_name, schedule)
        elif (serie_name in ['indycar', 'indylights']) and serie['track']:
            schedule = update_indycar_schedule(schedule, lights=(serie_name == 'indylights'))

    end_scraping = time.time()
    print(f"Scraping done in {end_scraping - start_scraping} seconds")

    schedule = update_calendar(schedule)

    write_schedule(schedule)

if __name__ == '__main__':
    main()
