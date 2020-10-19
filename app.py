"""Main module for the Learning Journal app."""

from flask import (
    flash,
    Flask,
    g,
    redirect,
    render_template,
    url_for
)
from flask_bcrypt import generate_password_hash
from flask_login import (
    current_user,
    LoginManager,
    login_required,
    login_user,
    logout_user
)
import random

import forms
import models

import debug_test  # DEBUGGING MODULE - REMOVE BEFORE FINALIZATION

DEBUG = True
PORT = 8000
HOST = '127.0.0.1'


def get_secret_key():
    """Generates a secret key for the flask app."""
    return generate_password_hash(str(random.randint(100000, 999999)))


app = Flask(__name__, template_folder="templates")
app.secret_key = get_secret_key()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


# Routes for the flask app.
@app.before_request
def before_request():
    """Connect to the database before each request."""
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """Close the database connection after each request."""
    g.db.close()
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/entries")
def show_entries():
    return render_template("entries.html")


@app.route("/register", methods=("GET", "POST"))
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash("Registration successful", "success")
        models.User.create_user(
            username=form.username.data,
            password=form.password.data,
            god=False
        )
        return redirect(url_for("index"))
    return render_template("form.html", button="Register", form=form)


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.username == form.username.data)
        except models.DoesNotExist:
            flash("Incorrect username or password.", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Login successful.", "success")
                return redirect(url_for("index"))
            else:
                flash("Incorrect username or password.", "error")
    return render_template("form.html", button="Log In", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout successful.", "success")
    return redirect(url_for('index'))


@app.route("/entries/new")
@login_required
def create_entry():
    pass


@app.route("/entries/<id>")
def show_entry():
    pass


@app.route("/entries/<id>/edit")
@login_required
def edit_entry():
    pass


@app.route("/entries/<id>/delete")
@login_required
def delete_entry():
    pass


# EXECUTION BEGINS HERE
if __name__ == "__main__":
    models.initialize()
    debug_test.create_user()  # DEBUG - REMOVE BEFORE FINALIZATION
    app.run(debug=DEBUG, host=HOST, port=PORT)
# EXECUTION ENDS HERE
