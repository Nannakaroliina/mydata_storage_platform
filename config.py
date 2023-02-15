from os import environ, urandom

from dotenv import load_dotenv

load_dotenv(".env")


class Config:
    """Base app config"""
    DEBUG = True
    APP_URL = environ.get('APP_URL')
    SECRET_KEY = environ.get("SECRET_KEY") or urandom(24)

    # Oura configs
    OURA_ACCESS_TOKEN = environ.get('OURA_ACCESS_TOKEN')
    OURA_CLIENT_ID = environ.get('OURA_CLIENT_ID')
    OURA_CLIENT_SECRET = environ.get('OURA_CLIENT_SECRET')
    OURA_REFRESH_TOKEN = environ.get('OURA_REFRESH_TOKEN')

    # Database configs
    SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth
    GOOGLE_CLIENT_ID = environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = environ.get('GOOGLE_DISCOVERY_URL')

    # Fitbit configs
    FITBIT_CLIENT_ID = environ.get('FITBIT_CLIENT_ID')
    FITBIT_CLIENT_SECRET = environ.get('FITBIT_CLIENT_SECRET')
    FITBIT_ACCESS_TOKEN = environ.get('FITBIT_ACCESS_TOKEN')
    FITBIT_REFRESH_TOKEN = environ.get('FITBIT_REFRESH_TOKEN')
