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
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX
    DISTANCE_UNIT=meters/miles
    NUM_STEPS=5

### Pokemon Data
This project contains a file `pokedata.csv` where you can customize the assigned rarity to each Pokemon.
Receive notifications for any Pokemon with rarity at `RARITY_LIMIT` or higher and at a distance walkable before the expiration time.

## Running

Locally:  

    pip install -r requirements.txt
    python main.py

Using Heroku:  

    heroku local

## Deploying to Heroku
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Ideas for improvement
Check out the [wiki](https://github.com/timwah/pokeslack/wiki) for a roadmap

## Credits  
This project builds on existing PokemonGo APIs and integrations:  
https://github.com/tejado/pgoapi  
https://github.com/AHAAAAAAA/PokemonGo-Map  
[@mastermindmatt](https://github.com/mastermindmatt) for the rarity data in pokedata.csv

## Donations
[Donate Bitcoins](https://www.coinbase.com/checkouts/2dba5a7fe26b5073e47c50f5d666469b)
 
