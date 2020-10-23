"""Debugging and testing module for the Learning Journal app.
Will NOT be included in the final build."""
import models


def create_god():
    try:
        models.User.create_user(
            username="god",
            password="iamgod",
            god=True)
    except models.IntegrityError:
        pass


def create_user(username, password):
    try:
        models.User.create_user(
            username=username,
            password=password,
            god=False)
    except models.IntegrityError:
        pass
