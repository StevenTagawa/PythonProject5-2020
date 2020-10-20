"""Main module for the Learning Journal app."""

from flask import (
    flash,
    Flask,
    g,
    redirect,
    render_template,
    request,
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
@app.route("/entries")
def index():
    """Home page.

    Displays title, date and link for all public entries.  If a user is logged
    in, also displays the user's private/hidden entries.
    """
    if current_user.is_authenticated:
        entries = (models.User.select()
                   .where(
            models.Entry.hidden == False |
            models.Entry.private == False |
            models.User.username == current_user
        )
                   .order_by(models.Entry.date.desc())
                   )
    else:
        entries = models.Entry.select().where(
            models.Entry.private == False | models.Entry.hidden == False)
    return render_template("index.html", entries=entries)


@app.route("/entries/<user>")
@login_required
def entries():
    """Displays title, date and link for a user's entries."""
    entries = current_user.entries
    return render_template("entries.html", entries=entries)


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
        login_user(models.User.get(models.User.username == form.username.data))
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
    return redirect(url_for("index"))


@app.route("/entries/new")
@login_required
def create_entry():
    form = forms.EntryForm()
    if form.validate_on_submit():
        entry = models.Entry.create(
            user=current_user.username,
            title=form.title.data,
            date=form.date.data,
            time_spent=form.time_spent.data,
            learned=form.learned.data,
            resources=form.resources.data,
            private=form.private.data,
            hidden=form.hidden.data
        )
        # Tags need to be added to the Tag and EntryTag tables.  Searches for
        # tags may be case-insensitive, but actual tags will be stored as-is.
        tags = form.tags.data.split(",")
        for tag in tags:
            tag = tag.strip()
            try:
                tag = models.Tag.get(models.Tag.name == tag)
            except models.DoesNotExist:
                tag = models.Tag.create(name=tag)
            models.EntryTag.create(entry=entry, tag=tag)
        return redirect(url_for("index"))
    return render_template("new.html")


@app.route("/entries/<int:entry_id>")
def show_entry(entry_id):
    try:
        entry = models.Entry.get(models.Entry.id == entry_id)
        # Deny that hidden entries exist, except to the author.
        if (entry.hidden is True and
                (not current_user.is_authenticated or
                 current_user.username != entry.user)):
            raise models.DoesNotExist
    except models.DoesNotExist:
        flash("Entry does not exist.", "error")
        return redirect(url_for("index"))
    # Private entries are listed, but not shown except to the author.
    if (entry.private is True and
            (not current_user.is_authenticated or
             current_user.username != entry.user)):
        flash("Entry is private.", "error")
        return redirect(url_for("index"))
    return render_template("detail.html", entry=entry)


@app.route("/entries/<int:entry_id>/edit")
@login_required
def edit_entry(entry_id):
    try:
        # Entries can only be edited by the author.
        entry = models.Entry.get(models.Entry.id == entry_id)
        if current_user.username != entry.user:
            raise models.DoesNotExist
    except models.DoesNotExist:
        flash("Cannot edit entry.", "error")
        return redirect(url_for("index"))
    # Get the current tag list to compare to whatever changes the user makes.
    old_tags = [tag.name for tag in
                models.EntryTag.select().where(models.EntryTag.entry == entry)]
    form = forms.EntryForm()
    if form.validate_on_submit():
        entry = models.Entry.create(
            user=current_user.username,
            title=form.title.data,
            date=form.date.data,
            time_spent=form.time_spent.data,
            learned=form.learned.data,
            resources=form.resources.data,
            private=form.private.data,
            hidden=form.hidden.data
        )
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
            if tag not in old_tags:
                tag = models.Tag.create(name=tag)
                models.EntryTag.create(entry=entry, tag=tag)
        flash("Entry edited.", "success")
        return redirect(url_for("index"))
    return render_template("edit.html", entry_id=entry_id)


@app.route("/entries/<int:entry_id>/delete")
@login_required
def delete_entry(entry_id):
    try:
        # Entries can only be deleted by the author.
        entry = models.Entry.get(models.Entry.id == entry_id)
        if current_user.username != entry.user:
            raise models.DoesNotExist
    except models.DoesNotExist:
        flash("Cannot delete entry.", "error")
        return redirect(url_for("index"))
    # Delete associated tags before deleting the entry.
    models.EntryTag.delete().where(models.EntryTag.entry == entry)
    entry.delete_instance()
    flash("Entry deleted.", "success")
    return redirect(url_for("/entries/<current_user.username>"))


# EXECUTION BEGINS HERE
if __name__ == "__main__":
    models.initialize()
    debug_test.create_user()  # DEBUG - REMOVE BEFORE FINALIZATION
    app.run(debug=DEBUG, host=HOST, port=PORT)
# EXECUTION ENDS HERE
