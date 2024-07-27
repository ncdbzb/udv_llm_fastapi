from typing import Any

from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

SECRET_MANAGER = os.environ.get("SECRET_MANAGER")
SECRET_JWT = os.environ.get("SECRET_JWT")

SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 465

CORS_ORIGINS = os.environ.get("CORS_ORIGINS")

if CORS_ORIGINS:
    CORS_ORIGINS = eval(CORS_ORIGINS)
else:
    print('CORS_ORIGINS not set in environment')

admin_dict: dict[str: Any] = {
    'name': 'admin',
    'surname': 'admin',
    'email': os.environ.get("ADMIN_EMAIL"),
    'password': os.environ.get("ADMIN_PASSWORD"),
    'is_active': True,
    'is_superuser': True,
    'is_verified': True
}
SEND_ADMIN_NOTICES = os.getenv('SEND_ADMIN_NOTICES', 'False').lower() in ('true', '1', 't', 'y', 'yes')

SERVER_DOMEN = os.environ.get("SERVER_DOMEN")

REDIS_PORT = int(os.environ.get("REDIS_PORT"))

