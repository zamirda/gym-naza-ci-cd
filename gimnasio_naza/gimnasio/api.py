import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def obtener_servicios_forms():
    with open('token.json','r') as token_file:
        creds_data = json.load(token_file)
    
    creds = Credentials.from_authorized_user_info(creds_data)
    service = build('forms','v1',credentials=creds)
    return service