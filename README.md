# Motorsport Calendar

A python script that scrap the websites of the different motorsport series :  
- [Formula 1](https://www.formula1.com/en/racing/2022.html)  
- [MotoGP - Moto2 - Moto3](https://www.motogp.com/en/calendar)  
- [WRC](https://www.wrc.com/en/championship/calendar/wrc/)  
- [Endurance (not official)](https://www.endurance-info.com/calendrier)  
- `new series incomming...`  

and add requested motorsport event to a google calendar.  

## Required

The prerequisites and the first step of this quickstart [here](https://developers.google.com/calendar/api/quickstart/python).  

Copy the credential .json file in the project directory and rename it credential.json.  

## Before first run

In the choices.json file, set to `true` the motorsport series for which one you want to add events to your calendar.  

You can add the id of a particular google calendar in the config.json file.  

## On first run

It will open a navigator window to allow your Google Cloud Project to access your Google Calendar.  

## Then

On each run, the script will check if there are new confirmed events on the website and will add to your calendar.  

You can change the motorsport series in the config.json file at any moment.  
Note that if you set one to false, the already created events will not be deleted from your calendar.  


## Subscriptions

For those who just want to subscribe to some calendars and add theme to your own calendar, you can download these .ics subscription links:  
- [Formula 1](https://calendar.google.com/calendar/ical/nce9jjita3pc5fi4k3qht4cseg%40group.calendar.google.com/public/basic.ics)  
- [Moto GP](https://calendar.google.com/calendar/ical/7a1spgbdlvl4p2t4gudi8ccmec%40group.calendar.google.com/public/basic.ics)  
- [Moto 2](https://calendar.google.com/calendar/ical/g24ihrfq8apbgqnjf50mf3o1bo%40group.calendar.google.com/public/basic.ics)  
- [Moto 3](https://calendar.google.com/calendar/ical/l7messjqqunqm35gn49u6co13c%40group.calendar.google.com/public/basic.ics)  
- [WRC](https://calendar.google.com/calendar/ical/lakpim3e6u2e2v9jlkcka3d27g%40group.calendar.google.com/public/basic.ics)  
- [All Endurance Series](https://calendar.google.com/calendar/ical/33fk4udv5a61bgq7jei17mrh18%40group.calendar.google.com/public/basic.ics)  
- [WEC](https://calendar.google.com/calendar/ical/5j8vvpa2kfrq8eetgq5d4o03vk%40group.calendar.google.com/public/basic.ics)  
<!-- - [24h of Le Mans (also included in WEC)]()   -->
- [Super GT](https://calendar.google.com/calendar/ical/pvu6u4d1d2kfc0ur4ia7gfo278%40group.calendar.google.com/public/basic.ics)  
- [European Le Mans Series](https://calendar.google.com/calendar/ical/ieqsec5qnrlmff5u7rsl6c0d3s%40group.calendar.google.com/public/basic.ics)  
<!-- - [Asian Le Mans Series]()   -->
- [GT World Challenge Europe](https://calendar.google.com/calendar/ical/on1bf7bpmi0873u3j2n91edj90%40group.calendar.google.com/public/basic.ics)  
- [Ultimate Cup Series](https://calendar.google.com/calendar/ical/ikh2j99pv63p2jchlvbuoh7vqk%40group.calendar.google.com/public/basic.ics)  
<!-- - [24h Series]()  
- [DTM]()   -->
- [FFSA GT](https://calendar.google.com/calendar/ical/sd8ul89d8kd2a35rsfh8tulnck%40group.calendar.google.com/public/basic.ics)  
- [GT4 European Series](https://calendar.google.com/calendar/ical/2etdssca8e864ukmn1kdfb3mm4%40group.calendar.google.com/public/basic.ics)  
- [Gulf 12 hours](https://calendar.google.com/calendar/ical/i0dh0n24piv1cmhcdr69trac94%40group.calendar.google.com/public/basic.ics)  
- [IMSA](https://calendar.google.com/calendar/ical/33u4euop8pg31jsq5hadc9dsrs%40group.calendar.google.com/public/basic.ics)  
- [Intercontinental GT Challenge](https://calendar.google.com/calendar/ical/055gfu254476kkv92hpf4m3iv8%40group.calendar.google.com/public/basic.ics)  
- [Intercontinental GT Open](https://calendar.google.com/calendar/ical/c0gviqo2rtl64937sscncipgt4%40group.calendar.google.com/public/basic.ics)  
- [Ligier European Series](https://calendar.google.com/calendar/ical/7l8da1cna4mpk660q5v5r971c0%40group.calendar.google.com/public/basic.ics)  
<!-- - [ADAC GT Master]() -->