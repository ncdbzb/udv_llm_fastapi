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

admin_dict: dict[str: Any] = {
    'name': 'admin',
    'surname': 'admin',
    'email': os.environ.get("ADMIN_EMAIL"),
    'password': os.environ.get("ADMIN_PASSWORD"),
    'is_active': True,
    'is_superuser': True,
    'is_verified': True
}