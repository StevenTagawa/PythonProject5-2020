"""Forms module for the Learning Journal app."""
import datetime
import time
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    PasswordField,
    StringField,
    TextAreaField,
    TimeField)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    InputRequired,
    Length,
    NoneOf,
    Regexp,
    ValidationError)

from models import User


def name_exists(_, field):
    if User.select().where(User.username == field.data).exists():
        raise ValidationError("Username already exists.")


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            InputRequired(),
            Regexp(r"^[a-z0-9_]+$",
                   message="Usernames may only contain lowercase letters, "
                           "numbers, and underscores"),
            NoneOf(["you"], message="Invalid username (reserved)"),
            name_exists])
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(),
            Length(
                min=8,
                message="Password must be at least 8 characters"),
            EqualTo("confirm_password", message="Passwords must match")])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[InputRequired()])


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])


class EntryForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    date = DateField(
        "Date",
        default=datetime.datetime.today,
        validators=[DataRequired()],
        description=" (yyyy-mm-dd)")
    time_spent = TimeField(
        "Time Spent",
        validators=[DataRequired()],
        description=" (hours:minutes)")
    learned = TextAreaField("What You Learned", validators=[InputRequired()])
    resources = TextAreaField("Resources to Remember")
    tags = StringField("Tags",
                       description=" (Please enter tags separated by commas.)")
    private = BooleanField("Private", default=False,
                           description=" (Private entries cannot be read by "
                                       "anyone but you.)")
    hidden = BooleanField("Hidden", default=False,
                          description=" (Hidden entries will not appear to "
                                      "anyone but you.)")

    def validate_date(form, field):  # noqa
        if type(field) == str:
            try:
                _ = datetime.datetime.strptime(field.data, "%Y-%m-%d")
            except ValueError:
                raise ValidationError(
                    "Please enter a date in the format yyyy-mm-dd.")

    def validate_time_spent(form, field):  # noqa
        if type(field) == str:
            try:
                _ = time.strptime(field.data, "%H:%M")
            except ValueError:
                raise ValidationError(
                    "Please enter a time spent in the format hh:mm.")
