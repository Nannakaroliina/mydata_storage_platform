"""
Module for the app
"""
import os

from flask import Flask
from requests import request

app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.Config")
app.config.from_object(env_config)


@app.route("/")
def index():
    """
    Render the index page for the app
    :return: template for web app
    """
    return get_oura_activity()


def get_oura_activity():
    """
    Get OURA daily activity from OURA API
    :return: Daily activity
    """
    url = 'https://api.ouraring.com/v2/usercollection/daily_activity'
    params = {
        'start_date': '2022-11-01',
        'end_date': '2022-12-01'
    }
    headers = {
        'Authorization': 'Bearer ' + str(app.config.get('OURA_TOKEN'))
    }

    response = request('GET', url, headers=headers, params=params)
    return response.text


if __name__ == "__main__":
    print(app.config)
    # print(get_oura_activity())
