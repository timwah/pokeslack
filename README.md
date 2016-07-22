# PokéSlack
Get Slack messages posted to a #pokealert channel for rare Pokemon close to you. Get walking directions from your search position and the time it expires. 

![PokeSlack](cover.png?raw=true)

## Create your [Slack Webhook](https://api.slack.com/incoming-webhooks)
Create a new webhook for a channel named #pokealerts  
https://my.slack.com/services/new/incoming-webhook/  
And use the web hook url as the SLACK_WEBHOOK_URL in your .env / Heroku config. 

## Configuration 
Create an .env file at the project root with the following content filled out. Do not use your main PokemonGo account information. 

    AUTH_SERVICE=google/ptc
    USERNAME=account@gmail.com
    PASSWORD=password
    LOCATION_NAME=Some location, USA
    RARITY_LIMIT=3
    DISTANCE_LIMIT=0.5
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX

### Pokemon Data
This project contains a file `pokedata.csv` where you can customize the assigned rarity to each Pokemon. 
Receive notifications for any Pokemon with rarity at `RARITY_LIMIT` or higher and distance (in miles) less than `DISTANCE_LIMIT`.

## Running 

Locally:  

    pip install -r requirements
    python main.py
    
Using Heroku:  

    heroku local 

## Deploying to Heroku
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Ideas for improvement
* Immediately send an alert for found Pokemon meeting the alert criteria instead of waiting for the entire scan pass to be complete
* Use distance (plus a buffer, since distance is calculated via a straight line) and walking speed (3 mph) compared with expiration time to calculate if you can walk there in time, then send a notification. Can then eliminate the distance limit. 
* Nicer Slack messages with images to the Pokemon, and a static Google map image of where the Pokemon is in comparison to the search position

## Credits  
This project builds on existing PokemonGo APIs and integrations:  
https://github.com/tejado/pgoapi  
https://github.com/AHAAAAAAA/PokemonGo-Map  
