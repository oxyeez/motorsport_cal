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
- [Formula 2](webcal://calendar.google.com/calendar/ical/mv5re1mfhfaqg3uoe5l1nhg7ok%40group.calendar.google.com/public/basic.ics)  
- [Formula 3](webcal://calendar.google.com/calendar/ical/664e91rgkvsqbhbuspavcioees%40group.calendar.google.com/public/basic.ics)  
- [Moto GP](webcal://calendar.google.com/calendar/ical/7a1spgbdlvl4p2t4gudi8ccmec%40group.calendar.google.com/public/basic.ics)  
- [Moto 2](webcal://calendar.google.com/calendar/ical/g24ihrfq8apbgqnjf50mf3o1bo%40group.calendar.google.com/public/basic.ics)  
- [Moto 3](webcal://calendar.google.com/calendar/ical/l7messjqqunqm35gn49u6co13c%40group.calendar.google.com/public/basic.ics)  
- [WRC](webcal://calendar.google.com/calendar/ical/lakpim3e6u2e2v9jlkcka3d27g%40group.calendar.google.com/public/basic.ics)  
- [WEC](webcal://calendar.google.com/calendar/ical/5j8vvpa2kfrq8eetgq5d4o03vk%40group.calendar.google.com/public/basic.ics)  
- [European Le Mans Series](webcal://calendar.google.com/calendar/ical/ieqsec5qnrlmff5u7rsl6c0d3s%40group.calendar.google.com/public/basic.ics)  
- [All other Endurance Series](webcal://calendar.google.com/calendar/ical/33fk4udv5a61bgq7jei17mrh18%40group.calendar.google.com/public/basic.ics)  
`or pick the endurance series you want :`   
  - [Super GT](webcal://calendar.google.com/calendar/ical/pvu6u4d1d2kfc0ur4ia7gfo278%40group.calendar.google.com/public/basic.ics)  
  - [Asian Le Mans Series](webcal://calendar.google.com/calendar/ical/tmsg86gj2j83ro0k4he49mkioc%40group.calendar.google.com/public/basic.ics)   
  - [GT World Challenge Europe](webcal://calendar.google.com/calendar/ical/on1bf7bpmi0873u3j2n91edj90%40group.calendar.google.com/public/basic.ics)  
  - [Ultimate Cup Series](webcal://calendar.google.com/calendar/ical/ikh2j99pv63p2jchlvbuoh7vqk%40group.calendar.google.com/public/basic.ics)  
  - [24h Series](webcal://calendar.google.com/calendar/ical/iamsbkl4re6njb3mqj6ri47ark%40group.calendar.google.com/public/basic.ics)   
  - [DTM](webcal://calendar.google.com/calendar/ical/gp6hg32kfqc7metlbolvmi30bk%40group.calendar.google.com/public/basic.ics)
  - [FFSA GT](webcal://calendar.google.com/calendar/ical/sd8ul89d8kd2a35rsfh8tulnck%40group.calendar.google.com/public/basic.ics)  
  - [GT4 European Series](webcal://calendar.google.com/calendar/ical/2etdssca8e864ukmn1kdfb3mm4%40group.calendar.google.com/public/basic.ics)  
  - [Gulf 12 hours](webcal://calendar.google.com/calendar/ical/i0dh0n24piv1cmhcdr69trac94%40group.calendar.google.com/public/basic.ics)  
  - [IMSA](webcal://calendar.google.com/calendar/ical/33u4euop8pg31jsq5hadc9dsrs%40group.calendar.google.com/public/basic.ics)  
  - [Intercontinental GT Challenge](webcal://calendar.google.com/calendar/ical/055gfu254476kkv92hpf4m3iv8%40group.calendar.google.com/public/basic.ics)  
  - [Intercontinental GT Open](webcal://calendar.google.com/calendar/ical/c0gviqo2rtl64937sscncipgt4%40group.calendar.google.com/public/basic.ics)  
  - [Ligier European Series](webcal://calendar.google.com/calendar/ical/7l8da1cna4mpk660q5v5r971c0%40group.calendar.google.com/public/basic.ics)  
  - [ADAC GT Master](webcal://calendar.google.com/calendar/ical/82bn8no55aoconvsi8ak7lkuic%40group.calendar.google.com/public/basic.ics)  
- [IndyCar](webcal://calendar.google.com/calendar/ical/o9n21ogf83a80fq7s1k0hnkfho%40group.calendar.google.com/public/basic.ics)
- [IndyLights](webcal://calendar.google.com/calendar/ical/rn9jr9hfch1fq0ebcsh3f0tir0%40group.calendar.google.com/public/basic.ics)