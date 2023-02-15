"""
Module that provides database model for User with
methods to add or modify the data on database
"""
from flask_login import UserMixin

from src.database import db


class User(db.Model, UserMixin):
    """
    User model class for defining the user
    database model and methods.
    """
    id = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)

    @classmethod
    def get(cls, id_):
        """
        Get the user from database by given id
        :param id_: int
        :return: user
        """
        return cls.query.filter_by(id=id_).first()

    def create(self):
        """
        Create User to database
        """
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """
        Delete User from database
        """
        db.session.add(self)
        db.session.commit()