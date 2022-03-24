# Motorsport Calendar

A python script that scrap the websites of the different motorsport series :  
- [Formula 1](https://www.formula1.com/en/racing/2022.html) - [Formula 2](https://www.fiaformula2.com/Calendar) - [Formula 3](https://www.fiaformula3.com/Calendar)  
- [MotoGP - Moto2 - Moto3](https://www.motogp.com/en/calendar)  
- [WRC](https://www.wrc.com/en/championship/calendar/wrc/)  
- [WEC (not official)](https://wec-magazin.com/calendar-2022/)  
- [European Le Mans Series](https://www.europeanlemansseries.com/en/season)  
- [Other Endurance Series (not official)](https://www.endurance-info.com/calendrier)  
- [IndyCar](https://www.indycar.com/Schedule) and [IndyLights](https://www.indycar.com/indylights/schedule)
- `new series incomming...`  

and add requested motorsport event to a google calendar.  

## Required

The prerequisites and the first step of this quickstart [here](https://developers.google.com/calendar/api/quickstart/python).  

Also run in terminal : 
```bash
pip3 install dateparser
pip3 install beautifulsoup4==4.10.0
pip3 install requests
pip3 install rich
```  

Copy the credential .json file in the project directory and rename it credential.json.  

## Before first run

In the choices.json file, set to `true` the motorsport series for which one you want to add events to your calendar.  

You can add the id of a particular google calendar in the config.json file.  

## On first run

It will open a navigator window to allow your Google Cloud Project to access your Google Calendar.  

## Then

On each run, the script will check if there are new confirmed events on the website and will add to your calendar.  

You can change the motorsport series in the config.json file at any moment.  
If setting one from true to false, upcomming events for this serie will be removed from your calendar.  


## Subscriptions

For those who just want to subscribe to some calendars and add theme to your own calendar, you can download these .ics subscription links:  
- [Formula 1](https://cutt.ly/7SBMdT0)  
- [Formula 2](https://cutt.ly/hSB1kXF)  
- [Formula 3](https://cutt.ly/JSB2Lj0)  
- [Moto GP](https://cutt.ly/kSB20pl)  
- [Moto 2](https://cutt.ly/aSB9uu5)  
- [Moto 3](https://cutt.ly/hSB9nLi)  
- [WRC](https://cutt.ly/NSB9WLF)  
- [WEC](https://cutt.ly/kSB9P0N)  
- [European Le Mans Series](https://cutt.ly/PSB9C39)  
- [24h Series](https://cutt.ly/OSB3Gir)  
- [All other Endurance Series](https://cutt.ly/ZSB3ifV)  
`or pick the endurance series you want :`   
  - [Super GT](https://cutt.ly/OSB6A1h)  
  - [Asian Le Mans Series](https://cutt.ly/cSB6KcK)   
  - [GT World Challenge Europe](https://cutt.ly/kSB62ZD)  
  - [Ultimate Cup Series](https://cutt.ly/cSNqfnv)  
  - [DTM](https://cutt.ly/fSNqbJo)
  - [FFSA GT](https://cutt.ly/YSNqWK9)  
  - [GT4 European Series](https://cutt.ly/fSNq25f)  
  - [Gulf 12 hours](https://cutt.ly/7SNwrJ1)  
  - [IMSA](https://cutt.ly/YSNwurs)  
  - [Intercontinental GT Challenge](https://cutt.ly/USNwzUV)  
  - [Intercontinental GT Open](https://cutt.ly/iSNwLXH)  
  - [Ligier European Series](https://cutt.ly/PSNw1Op)  
  - [ADAC GT Master](https://cutt.ly/SSNejXl)  
- [IndyCar](https://cutt.ly/RSNeEgR)
- [IndyLights](https://cutt.ly/OSNeDxz)