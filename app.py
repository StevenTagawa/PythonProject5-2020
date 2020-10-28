"""Main module for the Learning Journal app."""

# Imports.
from flask import (
    flash,
    Flask,
    g,
    redirect,
    render_template,
    request,
    url_for)
from flask_bcrypt import (
    check_password_hash,
    generate_password_hash)
from flask_login import (
    current_user,
    LoginManager,
    login_required,
    login_user,
    logout_user)
import random

import forms
import models


# Constants.
DEBUG = True
PORT = 8000
HOST = '127.0.0.1'

# Global variables.
last_route = None
cur_user = None
cur_entry = None
"""Global variables are reset by each route, and track both the route and the
    variable elements of the URL for the route.  These are used by the url_for
    method in the get_last_route function to build a URL to which the user is
    redirected after registering or logging in.  
"""


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
def index(home=True):
    """Home page.

    Displays title and date for all non-hidden entries, and link for all public
    entries.  If a user is logged in, also displays links for the user's private
    and hidden entries.
    """
    global last_route, cur_user, cur_entry
    last_route = "index"
    cur_user = None
    cur_entry = None
    if current_user.is_authenticated:
        if current_user.god:
            entries = models.Entry.select().order_by(models.Entry.date.asc())
        else:
            entries = (models.Entry.select().where(
                ((models.Entry.hidden == False) &  # noqa
                 (models.Entry.user != current_user.id)
                 ) |
                (models.Entry.user == current_user.id))
                       .order_by(models.Entry.date.desc()))
        return render_template(
            "listing.html", entries=entries, user=current_user.username,
            god=current_user.god, home=home, by="All")
    else:
        entries = models.Entry.select().where(
            models.Entry.hidden == False).order_by(
            models.Entry.date.asc())  # noqa E712 (must use == for peewee)
        return render_template("listing.html", entries=entries, user="",
                               god=False, home=home, by="All")


@app.route("/entries")
def entries():
    """Prevents url_for from returning "/entries" for "index"."""
    global last_route, cur_user, cur_entry
    last_route = "entries"
    cur_user = None
    cur_entry = None
    index(home=False)


@app.route("/entries/<user>")
def user_entries(user):
    """Displays a user's entries.

    If a logged-in user is viewing their own entries, displays title, date and
    links for all entries.  Otherwise, displays title and date for all non-
    hidden entries, and links for all public entries.
    """
    global last_route, cur_user, cur_entry
    last_route = "user_entries"
    cur_user = user
    cur_entry = None
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    if current_user.username == user:
        entries = current_user.entries.order_by(models.Entry.date.asc())
    else:
        entries = (models.Entry.select().where(
            models.Entry.hidden == False)  # noqa E712 (must use == in peewee)
                   .join(User)
                   .where(User.username == user)
                   .order_by(models.Entry.date.asc()))
    return render_template("listing.html", entries=entries, user="", god=False,
                           home=False, by="You")


@app.route("/register", methods=("GET", "POST"))
def register():
    """Creates a new user account."""
    form = forms.RegisterForm()
    if form.validate_on_submit():
        try:
            models.User.get(models.User.username == form.username.data)
        except models.DoesNotExist:
            flash("Registration successful", "success")
            models.User.create_user(
                username=form.username.data,
                password=form.password.data,
                god=False)
            flash("Registration successful", "success")
            # Automatically log in after registration.
            login_user(models.User.get(
                models.User.username == form.username.data))
            return redirect(get_last_route())
        else:
            flash("User already exists", "error")
            return redirect(url_for("login"))
    return render_template("form.html", button="Register", form=form)


@app.route("/login", methods=("GET", "POST"))
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
                return redirect(get_last_route())
            else:
                flash("Incorrect username or password.", "error")
    return render_template("form.html", button="Log In", form=form)


@app.route("/logout")
def logout():
    if not current_user.is_authenticated:
        flash("You cannot log out; you are not logged in.", "error")
        return redirect(get_last_route())
    logout_user()
    flash("Logout successful.", "success")
    return redirect(url_for("index"))


@app.route("/entries/new", methods=("GET", "POST"))
def create_entry():
    """Creates a new entry."""
    global last_route, cur_user, cur_entry
    last_route = "create_entry"
    cur_user = None
    cur_entry = None
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    user = g.user._get_current_object()  # noqa (accessing private method)
    form = forms.EntryForm()
    if form.validate_on_submit():
        # All entries marked hidden are also private.
        if form.hidden.data:
            form.private.data = True
        models.Entry.create(
            user=user,
            title=form.title.data,
            date=form.date.data,
            time_spent=form.time_spent.data,
            learned=form.learned.data,
            resources=form.resources.data,
            tags=form.tags.data,
            private=form.private.data,
            hidden=form.hidden.data)
        # Tags need to be added to the Tag and EntryTag tables.  Searches for
        # tags may be case-insensitive, but actual tags will be stored as-is.
        if form.tags.data:
            tags = form.tags.data.split(",")
            for tag in tags:
                tag = tag.strip()
                try:
                    tag = models.Tag.get(models.Tag.name == tag)
                except models.DoesNotExist:
                    tag = models.Tag.create(name=tag)
                models.EntryTag.create(entry=entry, tag=tag)
        flash("Entry saved.", "success")
        return redirect(url_for("user_entries", user=user.username))
    return render_template("form.html", button="Create", form=form)


@app.route("/entries/<int:entry_id>", methods=("GET", "POST"))
def show_entry(entry_id):
    """Displays a single entry, if the user is authorized to view it."""
    global last_route, cur_user, cur_entry
    last_route = "show_entry"
    cur_user = None
    cur_entry = entry_id
    try:
        entry = models.Entry.get(models.Entry.id == entry_id)
        # Deny that hidden entries exist, except to the author (and god).
        if (not current_user.is_authenticated or
                (not current_user.god and current_user.id != entry.user)):
            if entry.hidden:
                flash("Entry does not exist.", "error")
                raise models.DoesNotExist
            elif entry.private:
                flash("Entry is private.", "error")
                raise models.DoesNotExist
    except models.DoesNotExist:
        return redirect(url_for("index"))
    return render_template("detail.html", entry=entry)


@app.route("/entries/<int:entry_id>/edit", methods=("GET", "POST"))
def edit_entry(entry_id):
    """Allows the user to edit an entry, if they are authorized to do so."""
    global last_route, cur_user, cur_entry
    last_route = "edit_entry"
    cur_user = None
    cur_entry = entry_id
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    try:
        # Entries can only be edited by the author.
        entry = models.Entry.get(models.Entry.id == entry_id)
        if g.user._get_current_object() != entry.user:  # noqa
            raise models.DoesNotExist
    except models.DoesNotExist:
        flash("Cannot edit entry.", "error")
        return redirect(url_for("index"))
    form = forms.EntryForm()
    old_tags = []
    if request.method == "GET":
        # Get the current tag list to compare to any changes the user makes.
        old_tags = [tag.name for tag in entry.get_tags()]
        form.title.data = entry.title
        form.date.data = entry.date
        form.time_spent.data = entry.time_spent
        form.learned.data = entry.learned
        form.resources.data = entry.resources
        form.tags.data = entry.tags
        form.private.data = entry.private
        form.hidden.data = entry.hidden
    if form.validate_on_submit():
        entry.title = form.title.data
        entry.date = form.date.data
        entry.time_spent = form.time_spent.data
        entry.learned = form.learned.data
        entry.resources = form.resources.data
        entry.tags = form.tags.data
        entry.private = form.private.data
        entry.hidden = form.hidden.data
        # All entries that are hidden are also private.
        #
        # (Yes, I could use two radio buttons to implement this.  I'm not.)
        if form.hidden.data:
            entry.private = True
        entry.save()
        # Update tags (add new tags, delete deleted tags).
        new_tags = form.tags.data.split(",")
        for ndx in range(len(new_tags)):  # iterate through (but not over) list.
            new_tags[ndx] = new_tags[ndx].strip()
        for tag in old_tags:
            if tag not in new_tags:
                tag = models.Tag.get(models.Tag.name == tag)
                entry_tag = models.EntryTag.get(
                    models.EntryTag.entry == entry, models.EntryTag.tag == tag)
                entry_tag.delete_instance()
        for tag in new_tags:
            if (tag != "") and (tag not in old_tags):
                tag = models.Tag.create(name=tag)
                models.EntryTag.create(entry=entry, tag=tag)
        flash("Entry edited.", "success")
        return redirect(url_for("show_entry", entry_id=entry_id))
    return render_template("form.html", button="Update", form=form)


@app.route("/entries/<int:entry_id>/delete", methods=("GET", "POST"))
def delete_entry(entry_id):
    """Deletes an entry, if the user is authorized to do so."""
    global last_route, cur_user, cur_entry
    last_route = "delete_entry"
    cur_user = None
    cur_entry = None
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    user = g.user._get_current_object()  # noqa (accessing private method)
    try:
        # Entries can only be deleted by the author.
        entry = models.Entry.get(models.Entry.id == entry_id)
        if user != entry.user:
            raise models.DoesNotExist
    except models.DoesNotExist:
        flash("Cannot delete entry.", "error")
        return redirect(url_for(last_route))
    # Delete associated tags before deleting the entry.
    models.EntryTag.delete().where(models.EntryTag.entry == entry)
    entry.delete_instance()
    flash("Entry deleted.", "success")
    return redirect(url_for("user_entries", user=user.username))


def get_last_route():
    """Returns data for the url_for method based on the last route processed.

        Used to redirect the user to the previous page.
    """
    if last_route in ["user_entries"]:
        return url_for(last_route, user=cur_user)
    elif last_route in ["show_entry", "edit_entry", "delete_entry"]:
        return url_for(last_route, entry_id=cur_entry)
    else:
        return url_for(last_route)


# EXECUTION BEGINS HERE
if __name__ == "__main__":
    models.initialize()
    app.run(debug=DEBUG, host=HOST, port=PORT)
# EXECUTION ENDS HERE
