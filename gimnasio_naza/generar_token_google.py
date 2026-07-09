import os
import sys
import django
from django.conf import settings
from google_auth_oauthlib.flow import InstalledAppFlow

# Configurar Django para usar las rutas de tu proyecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

SCOPES = [
    'https://www.googleapis.com/auth/forms.body', 
    'https://www.googleapis.com/auth/forms.responses.readonly'
]

def generar_token_final():
    credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')
    token_path = os.path.join(settings.BASE_DIR, 'token.json')
    
    try:
        # Inicializar el flujo con el nuevo cliente "installed"
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        flow.redirect_uri = 'http://localhost:8080/'

        # --- CÓDIGO NUEVO ---
        nuevo_codigo = "4/0AdkVLPwwufNbmg-_gWzk7p0XxRhw4IKcc9TtTx2rgCspw9HxQ805e2bc6VODWtHcxBZV1Q"
        # --------------------

        print(f"🔄 Intercambiando código por token permanente...")
        flow.fetch_token(code=nuevo_codigo)
        creds = flow.credentials
        
        # Guardar el token.json definitivo
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
        
        print(f"\n COMPLETADO")
        print(f"Archivo creado en: {token_path}")
        print("Ahora puedes crear y enviar encuestas desde tu app de Django.")
        return True
    except Exception as e:
        print(f" Error: {str(e)}")
        print("Si el error es 'invalid_grant', el código expiro y debes generar uno nuevo .")
        return False

if __name__ == '__main__':
    generar_token_final()