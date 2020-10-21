"""Forms module for the Learning Journal app."""
import datetime
from flask_wtf import Form
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    StringField,
    TextAreaField
)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    Length,
    Regexp,
    ValidationError
)

from models import User


def name_exists(_, field):
    if User.select().where(User.username == field.data).exists():
        raise ValidationError("Username already exists.")


class RegisterForm(Form):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Regexp(
                r"^[a-zA-Z0-9]+$",
                message="Usernames may only contain letters and numbers."
            ),
            name_exists
        ])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(
                min=8,
                message="Password must be at least 8 characters"
            ),
            EqualTo("confirm_password", message="Passwords must match")
        ])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired()]
    )


class LoginForm(Form):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


class EntryForm(Form):
    title = StringField("Title", validators=[DataRequired()])
    date = DateField(
        "Date",
        default=datetime.datetime.today,
        validators=[DataRequired()]
    )
    time_spent = IntegerField("Time Spent", validators=[DataRequired()])
    learned = TextAreaField("What You Learned", validators=[DataRequired()])
    resources = TextAreaField(
        "Resources to Remember",
        validators=[DataRequired()]
    )
    tags = StringField("Tags")
    private = BooleanField(default=False)
    hidden = BooleanField(default=False)
