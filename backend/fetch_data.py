import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
TOKEN_FILE = "strava_tokens.json"
DATA_FILE = "data/raw_activities.json"

def get_valid_access_tokens():

    with open(TOKEN_FILE, mode="r") as f:
        tokens = json.load(f)

    if tokens['expires_at'] < time.time():
        print("Refreshing expired token...")
        response = requests.post(
            "https://www.strava.com/oauth/token", 
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'refresh_token',
                'refresh_token': tokens['refresh_token']
            }
        )

        new_tokens = response.json()

        with open("strava_tokens.json", "w") as f:
            json.dump(new_tokens, f)

        return new_tokens['access_token']
    
    return tokens['access_token']

def fetch_activities():
    access_token = get_valid_access_tokens()

    print(access_token)

    print("Fetching activities...")

    url = "https://www.strava.com/api/v3/athlete/activities?per_page=100"
    headers = {'Authorization': f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        activities = response.json()
        
        os.makedirs("data", exist_ok=True)

        with open(DATA_FILE, "w") as f:
            json.dump(activities, f, indent=4)
        
        print(f"Success! {len(activities)} Activities save to {DATA_FILE}.")
    else:
        print("Error, failed to access activities: ", response.json())

if __name__ == "__main__":
    fetch_activities()