"""
Module for the app
"""
import json
import logging
import os

import click
import requests
from flask import Flask, redirect, request, url_for
from flask.cli import with_appcontext
from flask_login import LoginManager, current_user, login_required, logout_user, login_user
from flask_migrate import Migrate
from oauthlib.oauth2 import WebApplicationClient
from oura import OuraClient, OuraOAuth2Client
from requests import RequestException

from src.database import db
from src.models.models import User

app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.Config")
app.config.from_object(env_config)
db.init_app(app)
migrate = Migrate(app, db)

# Logging session manager for Flask
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth2 Client setup
client = WebApplicationClient(app.config.get('GOOGLE_CLIENT_ID'))

# Configuration for Oura OAuth2 client to authorise use of Oura data
app_url = app.config.get('APP_URL')
auth_client = OuraOAuth2Client(client_id=app.config.get('OURA_CLIENT_ID'),
                               client_secret=app.config.get('OURA_CLIENT_SECRET'))
oura_authorise_url = auth_client.authorize_endpoint(redirect_uri=app_url + '/callback')


@login_manager.user_loader
def load_user(user_id):
    """
    Get user from the database
    :param user_id: id of the user
    :return: user
    """
    return User.get(user_id)


@app.route("/", methods=['GET'])
def index():
    """
    Render the index page for the app
    :return: template for web app
    """
    if current_user.is_authenticated:
        return (
            '<p>Welcome to MyData Storage Platform, {}! </p>'
            '<br>'
            "<p>You're logged in! Email: {}</p>"
            '<br>'
            '<p>To perform Oura auth click the link below</p>'
            '<p><a href="/authorise-oura"> Oura Auth </a> </p>'
            '<br>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email
            )
        )
    else:
        return ('<a class="button" href="/login">Google Login</a>')


@app.route("/login")
def login():
    """
    Login the user
    :return: Request uri for login
    """
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )

    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    """
    Callback for Google login
    """
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config.get('GOOGLE_CLIENT_ID'), app.config.get('GOOGLE_CLIENT_SECRET')),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    # Endpoint for userdata
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Verify user
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user with the information provided by Google
    user = User(
        id=unique_id, name=users_name, email=users_email
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        user.create()

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    """
    Logout the current user.
    :return: homepage
    """
    logout_user()
    return redirect(url_for("index"))


@app.route("/authorise-oura", methods=['GET'])
@login_required
def authorise_oura():
    """
    Endpoint to redirect the user to Oura auth page
    :return: redirect to Oura authorise url
    """
    return redirect(oura_authorise_url[0])


@app.route("/callback", methods=['GET'])
@login_required
def callback_oura():
    """
    Endpoint for successful auth
    :return: redirect to data endpoint
    """
    try:
        logging.info('Successful authorisation')
        code = request.args.get('code')
        token = auth_client.fetch_access_token(code=code)
        app.config['OURA_ACCESS_TOKEN'] = token['access_token']
        app.config['OURA_REFRESH_TOKEN'] = token['refresh_token']
        return redirect(url_for('.get_user_data'))
    except Exception as e:
        logging.error(e)
        return 'Authorisation needed for platform usage', 401


@app.route("/oura", methods=['GET'])
@login_required
def get_user_data():
    """
    Render the index page for the app
    :return: template for web app
    """
    try:
        oura = create_client()
        summary = oura.user_info()
    except Exception as e:
        logging.error(e)
        summary = 'Something went wrong, make sure you have authorised first.'
    return summary


@app.route("/oura/<string:stat>", methods=['GET'])
@login_required
def get_oura_activity(stat: str):
    """
    Return Oura stat summary for prefered stat which are:
     - Readiness
     - Sleep
     - Bedtime
     - Activity
    :return: list of stats
    """
    try:
        oura = create_client()
        summary = ''
        if stat == 'readiness':
            summary = oura.readiness_summary()
        elif stat == 'sleep':
            summary = oura.sleep_summary()
        elif stat == 'bedtime':
            summary = oura.bedtime_summary()
        elif stat == 'activity':
            summary = oura.activity_summary()
    except Exception as e:
        logging.error(e)
        summary = 'Something went wrong, make sure you have authorised first.'
    return summary


def create_client():
    """
    Create Oura client with client id and access token
    :return: Oura client
    """
    try:
        oura_client = OuraClient(client_id=app.config.get('OURA_CLIENT_ID'), access_token=app.config.get('OURA_ACCESS_TOKEN'))
        return oura_client
    except Exception as e:
        logging.error(e)
        return 'Make sure you have provided needed credentials for Oura client'


def get_google_provider_cfg():
    """
    Retrieve the Google's provider configuration
    :return: configuration
    """
    try:
        return requests.get(app.config.get('GOOGLE_DISCOVERY_URL'), timeout=60).json()
    except TimeoutError:
        logging.info('Request timeout.')
        return 'Request timeout occurred', 504
    except RequestException as e:
        logging.error(e)
        return 'Error occurred', 500


@click.command("create-tables")
@with_appcontext
def create_tables_cmd():
    """
    Create all the tables for the database
    """
    db.create_all()


@click.command("delete-tables")
@with_appcontext
def delete_tables_cmd():
    """
    Delete all the data from database
    """
    db.drop_all()


app.cli.add_command(create_tables_cmd)
app.cli.add_command(delete_tables_cmd)
