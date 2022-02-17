# Motorsport Calendar

A python script that scrap the website [www.motorsport.com](www.motorsport.com) 
and add requested motorsport event to a google calendar.

## Required

The prerequisites shown [here](https://developers.google.com/calendar/api/quickstart/python).

Copy the credential .json file in the project directory and rename it credential.json.

## Before first run

In the config.json file, set to `true` the motorsport series for which one you want to add events to your calendar.

You can add the id of a particular calendar in the config.json file.

## On first run

It will open a navigator window to allow your Google Cloud Project to access your Google Calendar.

## Then

On each run, the script will check if there are new confirmed events on the website and will add to your calendar.

You can change the motorsport series in the config.json file at any moment.
Note that if you set one to false, the already created events will not be deleted from your calendar.
