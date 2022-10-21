import os
from dotenv import load_dotenv
import requests
from requests_oauthlib import OAuth2Session

API_HOST = "https://sandbox-api.aife.economie.gouv.fr"
TOKEN_URL = 'https://sandbox-oauth.aife.economie.gouv.fr/api/oauth/token'

# 1. connect using the "client credentials" grant type
# the regular authentication methods don't work, we are passing
# the client id and secret as form data, as suggested by the PISTE team
load_dotenv()
client_id = os.getenv("OAUTH_KEY_2")
client_secret = os.getenv("OAUTH_SECRET_2")
res = requests.post(
  TOKEN_URL,
  data={
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "openid"
  }
)
token = res.json()
print(token)
client = OAuth2Session(client_id, token=token)
print(client.get("/docs"))
# import log_all_http

