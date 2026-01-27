import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"

def get_tokens():
    
    print("1. Go to this URL in your browser:\n")
    print(f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all")

    print("\n2. Click \"Authorize\" to be redirected. You should see a message \"this site can't be reached\"")

    print("\n3. Copy the authorization code in the url header.")
    auth_code = input("Paste the code here: ")

    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code'
    }

    response = requests.post(TOKEN_URL, payload)

    if response.status_code == 200:
        tokens = response.json()

        with open("strava_tokens.json", "w") as f:
            json.dump(tokens, f)
        print("\nSUCCESS! Tokens saved to 'strava_tokens.json'.")
        print(f"Access Token: {tokens['access_token']}")
    else:
        print("\nERROR:", response.json())

if __name__ == "__main__":
    get_tokens()