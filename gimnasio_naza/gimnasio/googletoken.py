import os
from django.conf import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/forms.responses.readonly'
]

def get_credentials():
    token_path = os.path.join(settings.BASE_DIR, 'token.json')

    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(
            token_path,
            SCOPES
        )

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())

            with open(token_path, 'w') as token:
                token.write(creds.to_json())

            print("Token renovado correctamente")

        except Exception as e:
            print(f"Error renovando token: {e}")

    elif not creds:
        raise Exception(
            "No existe token.json. Debes generarlo una vez manualmente."
        )

    return creds