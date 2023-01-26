"""
This module provides the WSGI HTTP Server runnable for Heroku
"""
from src.app import app

if __name__ == "__main__":
    app.run()
