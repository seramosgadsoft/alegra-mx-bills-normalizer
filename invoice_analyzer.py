import requests as req
import json
from services.webhook_service import send_message_to_webhook

def load_config():
    with open("config.json") as config_file:
        return json.load(config_file)

config = load_config()

def login():
    """
    Realiza el login para consumir la API de invoice analyzer.

    :param user: Usuario.
    :param password: Contraseña.
    :return: Token de autenticación.
    """
    # URL de login
    url = config["adsoft_service"]["invoice_analyzer_login_url"]
    # Cabeceras
    headers = {"Content-Type": "application/json", "x-api-key": config["adsoft_service"]["api_key"]}
    # Cuerpo de la petición
    body = {
        "username": config["adsoft_service"]["username"],
        "password": config["adsoft_service"]["password"]
    }
    # Realizar la petición POST
    response = req.post(url, json=body, headers=headers)
    # Verificar la respuesta
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Error en el login: {response.status_code}: {response.text}")
        send_message_to_webhook(f"Error en el login de Invoice Analyzer: {response.status_code}: {response.text}")
        return None

def invoice_analyzer (name, xml_data):
    """
    Obtiene el contenido de un archivo xml en formato json.

    :param name: Nombre del archivo.
    :param xml_data: Contenido del archivo XML.
    :return: json con la información del archivo xml.
    """
    try:
        #Login
        token = login()
        if not token:
            print("NO TOKEN")
            return None
        # URL de la API de invoice analyzer
        url = config["adsoft_service"]["invoice_analyzer_url"]
        # Cabeceras
        headers = {
            "Authorization": f"Bearer {token}",
            "x-api-key": config["adsoft_service"]["api_key"],
        }
        #file con el nombre del archivo
        file = {"file": (name, xml_data, 'application/xml')}
        # Realizar la petición POST
        response = req.post(url, headers=headers, files=file)
        # Verificar la respuesta
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error en invoice analyzer: {response.status_code}: {response.text}")
            send_message_to_webhook(f"Error en invoice analyzer: {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Error en invoice analyzer: {e}")
        send_message_to_webhook(f"Error en invoice analyzer: {e}")
        return None
    
def invoice_analyzer_ocr(name, pdf_data):
    """
    Obtiene el contenido de un archivo pdf en formato json.

    :param name: Nombre del archivo.
    :param pdf_data: Contenido del archivo PDF.
    :return: json con la información del archivo pdf.
    """
    try:
        #Login
        token = login()
        if not token:
            print("NO TOKEN")
            return None
        # URL de la API de invoice analyzer
        url = config["adsoft_service"]["invoice_analyzer_ocr_url"]
        # Cabeceras
        headers = {
            "Authorization": f"Bearer {token}",
            "x-api-key": config["adsoft_service"]["api_key"],
        }
        #file con el nombre del archivo
        file = {"file": (name, pdf_data, 'application/pdf')}
        # Realizar la petición POST
        response = req.post(url, headers=headers, files=file)
        # Verificar la respuesta
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error en invoice analyzer OCR: {response.status_code}: {response.text}")
            send_message_to_webhook(f"Error en invoice analyzer OCR: {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Error en invoice analyzer OCR: {e}")
        send_message_to_webhook(f"Error en invoice analyzer OCR: {e}")
        return None