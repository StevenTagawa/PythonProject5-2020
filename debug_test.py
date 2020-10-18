"""Debugging and testing module for the Learning Journal app.
Will NOT be included in the final build."""
import models


def create_user():
    models.User.create_user(
        username="stagawa",
        password="iamgod",
        god=True
    )
