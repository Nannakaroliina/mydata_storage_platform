from os import environ

from dotenv import load_dotenv

load_dotenv(".env")


class Config:
    """Base app config"""
    DEBUG = True

    OURA_TOKEN = environ.get('OURA_TOKEN')
