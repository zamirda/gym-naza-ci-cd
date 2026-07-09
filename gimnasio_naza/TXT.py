import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes necesarios
SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly"
]

def main():
    creds = None
    # 1. Intentar cargar el token existente
    if os.path.exists("token.json"):
        # Importante: Usamos from_authorized_user_file para leer el JSON directamente
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # 2. Si no hay credenciales o no son válidas
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refrescando token de acceso...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"No se pudo refrescar: {e}. Reintentando login completo.")
                creds = None # Forzar login si el refresh falla

        # 3. Login completo si es necesario
        if not creds:
            print("Iniciando flujo de autenticación en el navegador...")
            flow = InstalledAppFlow.from_client_secrets_file(
                r"C:\Users\Fernando\proyecto_gimnasio\gimnasio_naza\credentials.json", SCOPES
            )
            
            # --- LAS LÍNEAS CLAVE ESTÁN AQUÍ ---
            creds = flow.run_local_server(
                port=8080,
                prompt='consent',      # Obliga a mostrartoken.json la pantalla de permisos
                access_type='offline'  # INDISPENSABLE para obtener el refresh_token
            )
            
        # 4. Guardar el token (ahora sí incluirá el refresh_token)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Construir el servicio de Forms
        service = build("forms", "v1", credentials=creds)

        print("Creando un nuevo formulario...")
        nuevo_form_body = {
            "info": {
                "title": "Formulario Proyecto Colegio",
                "documentTitle": "Registro_Estudiantes_2026"
            }
        }

        result = service.forms().create(body=nuevo_form_body).execute()
        
        print("-" * 30)
        print(f"✅ Formulario Creado")
        print(f"ID: {result['formId']}")
        print(f"URL para editar: {result['editUri']}")
        print(f"URL para enviar: {result['responderUri']}")
        print("-" * 30)

    except HttpError as error:
        print(f"❌ Error de la API de Google: {error}")

if __name__ == "__main__":
    main()