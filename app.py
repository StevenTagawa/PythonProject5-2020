"""Main module for the Learning Journal app."""

# Imports.
from flask import (
    flash,
    Flask,
    g,
    get_flashed_messages,
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
cur_tag = None
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


# Housekeeping.
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


# View routes for the app.
@app.route("/")
def index(home=True):
    """Home page.

    Displays title and date for all non-hidden entries, and link for all public
    entries.  If a user is logged in, also displays links for the user's private
    and hidden entries.
    """
    global last_route, cur_user, cur_entry, cur_tag
    last_route = "index"
    cur_user = None
    cur_entry = None
    cur_tag = None
    if current_user.is_authenticated:
        if current_user.god:
            entries = models.Entry.select().order_by(models.Entry.date.asc())
        else:
            entries = (models.Entry.select().where(
                ((models.Entry.hidden == False) &  # noqa (must use == )
                 (models.Entry.user != current_user.id)
                 ) |
                (models.Entry.user == current_user.id))
                       .order_by(models.Entry.date.asc()))
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
    """Prevents url_for from constructing "/entries" for "index"."""
    global last_route, cur_user, cur_entry, cur_tag
    last_route = "entries"
    cur_user = None
    cur_entry = None
    cur_tag = None
    return redirect(url_for("index"))


@app.route("/entries/<user>")
def user_entries(user):
    """Displays a user's entries.

        If a logged-in user is viewing their own entries, displays title, date
        and links for all entries.  Otherwise, displays title and date for all
        non-hidden entries, and links for all public entries.
    """
    global last_route, cur_user, cur_entry, cur_tag
    last_route = "user_entries"
    cur_user = user
    cur_entry = None
    cur_tag = None
    # Users not logged in can see non-hidden entries.
    if not current_user.is_authenticated or (current_user.username != user
                                             and current_user.god == False):  # noqa
        entries = (models.Entry.select().where(
            models.Entry.hidden == False)  # noqa E712 (must use == in peewee)
                   .join(models.User)
                   .where(models.User.username == user)
                   .order_by(models.Entry.date.asc()))
    # Logged-in users (and god) can see all their own entries, and non-hidden
    # entries by others.
    else:
        try:
            target_user = models.User.get(models.User.username == user)
        except models.DoesNotExist:
            flash("User does not exist.", "error")
            return redirect(url_for("index"))
        entries = target_user.entries.order_by(models.Entry.date.asc())
    if current_user.is_authenticated:
        user_ = current_user.username
        if current_user.god:
            god = True
        else:
            god = False
        if current_user.username == user:
            by = "You"
        else:
            by = user
    else:
        god = False
        by = user
        user_ = ""
    return render_template("listing.html", entries=entries, user=user_, god=god,
                           home=False, by=by)


@app.route("/register", methods=("GET", "POST"))
def register():
    """Creates a new user account."""
    form = forms.RegisterForm()
    # Create a new user account only if the username doesn't already exist.
    if form.validate_on_submit():
        try:
            models.User.get(models.User.username == form.username.data)
        except models.DoesNotExist:
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
            # If an existing username is used, prompt to log in using it.
            flash("User already exists", "error")
            return redirect(url_for("login"))
    return render_template(
        "form.html", button="Register", form=form, cancel_url=get_last_route())


@app.route("/login", methods=("GET", "POST"))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.username == form.username.data)
        except models.DoesNotExist:
            flash("Incorrect username or password.", "error")
        else:
            # If the login is successful, redirect back to the previous page.
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Login successful.", "success")
                return redirect(get_last_route())
            else:
                flash("Incorrect username or password.", "error")
    return render_template(
        "form.html", button="Log In", form=form, cancel_url=get_last_route())


@app.route("/logout")
def logout():
    # No logging out without being logged in first.
    if not current_user.is_authenticated:
        flash("You cannot log out; you are not logged in.", "error")
        return redirect(url_for("index"))
    logout_user()
    flash("Logout successful.", "success")
    # Just send the user back to the homepage (to avoid landing on a page that
    # will just prompt the user to log in again).
    return redirect(url_for("index"))


@app.route("/entries/new", methods=("GET", "POST"))
def create_entry():
    """Creates a new entry."""
    global last_route, cur_user, cur_entry, cur_tag
    last_route = "create_entry"
    cur_user = None
    cur_entry = None
    cur_tag = None
    # Prompt to login, if the user isn't already.
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    user = g.user._get_current_object()  # noqa (accessing private method)
    form = forms.EntryForm()
    if form.validate_on_submit():
        # All entries marked hidden are also private.
        if form.hidden.data:
            form.private.data = True
        # Record creation.
        entry = models.Entry.create(
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
        update_tags(entry, entry.tags, "")
        flash("Entry saved.", "success")
        # Send the user back to their own page.
        return redirect(url_for("user_entries", user=user.username))
    return render_template(
        "form.html", button="Create", form=form, cancel_url=url_for("index"))


@app.route("/entries/<int:entry_id>", methods=("GET", "POST"))
def show_entry(entry_id):
    """Displays a single entry, if the user is authorized to view it."""
    global last_route, cur_user, cur_entry, cur_tag
    last_route = "show_entry"
    cur_user = None
    cur_entry = entry_id
    cur_tag = None
    message = None
    category = None
    try:
        entry = models.Entry.get(models.Entry.id == entry_id)
        # Deny that hidden entries exist, except to the author (and god).
        if not (current_user.is_authenticated and
                (current_user.id == entry.user.id or current_user.god)):
            if entry.hidden:
                message = "Entry does not exist."
                category = "error"
                raise models.DoesNotExist
            elif entry.private:
                message = "Entry is private."
                category = "error"
                raise models.DoesNotExist
    except models.DoesNotExist:
        if not message:
            message = "Entry does not exist."
            category = "error"
        flash(message, category)
        return redirect(url_for("index"))
    # The template needs the entry's tags in list form.
    tags = [tag.strip() for tag in entry.tags.split(",")]
    # If there are no tags, send an empty list rather than an empty string.
    if tags == [""]:
        tags = []
    # Set flag to show delete link (only if the user is the entry's author or is
    # god).
    if (current_user.is_authenticated and
            (current_user.id == entry.user.id or current_user.god)):
        author = True
    else:
        author = False
    return render_template("detail.html", entry=entry, tags=tags, author=author)


@app.route("/entries/<int:entry_id>/edit", methods=("GET", "POST"))
def edit_entry(entry_id):
    """Allows the user to edit an entry, if they are authorized to do so."""
    global last_route, cur_user, cur_entry, cur_tag
    last_route = "edit_entry"
    cur_user = None
    cur_entry = entry_id
    cur_tag = None
    # Prompt to login if the user isn't already.
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    user = g.user._get_current_object()  # noqa (accessing private method)
    try:
        # Entries can only be edited by the author (or god).
        entry = models.Entry.get(models.Entry.id == entry_id)
        if (user != entry.user and user.god == False):  # noqa
            raise models.DoesNotExist
    except models.DoesNotExist:
        # Display a non-specific error message. (If redirected from the login
        # page, flush the login message.)
        get_flashed_messages()
        flash("Cannot edit entry.", "error")
        return redirect(url_for("show_entry", entry_id=entry_id))
    form = forms.EntryForm()
    old_tags = []
    # Only pre-populate the fields before initial display.
    if request.method == "GET":
        # Get the current tag list to compare to any changes the user makes.
        old_tags = entry.tags
        form.title.data = entry.title
        form.date.data = entry.date
        form.time_spent.data = entry.time_spent
        form.learned.data = entry.learned
        form.resources.data = entry.resources
        form.tags.data = entry.tags
        form.private.data = entry.private
        form.hidden.data = entry.hidden
    # Process the submitted form.
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
        update_tags(entry, entry.tags, old_tags)
        flash("Entry edited.", "success")
        return redirect(url_for("show_entry", entry_id=entry_id))
    return render_template(
        "form.html", button="Update", form=form, cancel_url=get_last_route())


@app.route("/entries/<int:entry_id>/delete", methods=("GET", "POST"))
def delete_entry(entry_id):
    """Deletes an entry, if the user is authorized to do so."""
    global last_route, cur_user, cur_entry, cur_tag
    last_route = "delete_entry"
    cur_user = None
    cur_entry = entry_id
    cur_tag = None
    # Prompt to log in if the user isn't already.
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    user = g.user._get_current_object()  # noqa (accessing private method)
    try:
        # Entries can only be deleted by the author.
        entry = models.Entry.get(models.Entry.id == entry_id)
        if (user != entry.user and user.god == False):  # noqa
            raise models.DoesNotExist
    except models.DoesNotExist:
        get_flashed_messages()
        flash("Cannot delete entry.", "error")
        return redirect(url_for("show_entry", entry_id=entry_id))
    target_user = entry.user.username
    # Delete associated tags before deleting the entry.
    update_tags(entry, "", entry.tags)
    entry.delete_instance()
    flash("Entry deleted.", "success")
    return redirect(url_for("user_entries", user=target_user))


@app.route("/tags/<tag>")
def show_tag(tag):
    """Shows all non-hidden entries which contain the specified tag.

        Shows hidden entries only to the author (or to god).
    """
    global last_route, cur_user, cur_entry, cur_tag
    last_route = "show_tag"
    cur_user = None
    cur_entry = None
    cur_tag = tag
    # Make sure some variation of the tag exists. Doesn't matter which one is
    # used as the search pattern.
    try:
        search_tag = models.Tag.select().where(models.Tag.name ** tag).get()
    except models.DoesNotExist:
        flash(f"Tag {tag} not found.", "error")
        return redirect(get_last_route())
    all_entries = search_tag.entries()
    print(len(all_entries))
    # Users who are not logged in do not see any hidden entries.
    if not current_user.is_authenticated:
        entries = []
        for entry in all_entries:
            if not entry.hidden:
                entries.append(entry)
    # Non-god users see only their own hidden entries.
    elif not current_user.god:
        entries = []
        for entry in all_entries:
            if not (entry.hidden and entry.user.id != current_user.id):
                entries.append(entry)
    else:
        entries = all_entries
    # If all matching records got filtered out, do not reveal that there were
    # matching hidden records.
    if len(entries) == 0:
        flash(f"Tag {tag} not found.", "error")
        # Note request.referrer actually works for non-form views.
        return redirect(request.referrer)
    if current_user.is_authenticated:
        user_ = current_user.username
        if current_user.god:
            god = True
        else:
            god = False
    else:
        god = False
        user_ = ""
    return render_template("tag_listing.html", entries=entries, user=user_,
                           god=god, home=False, by="All", tag=tag)


# Supporting functions.
def get_last_route():
    """Returns data for the url_for method based on the last route processed.

        Used to redirect the user to the previous page.
    """
    if last_route is None:
        return url_for("index")
    elif last_route in ["user_entries"]:
        return url_for(last_route, user=cur_user)
    elif last_route in ["show_entry", "edit_entry", "delete_entry"]:
        return url_for(last_route, entry_id=cur_entry)
    elif last_route in ["show_tag"]:
        return url_for(last_route, tag=cur_tag)
    else:
        return url_for(last_route)


def update_tags(entry, new_tags: str, old_tags: str) -> None:
    """Updates tag references as needed."""
    # Turn the tag strings into lists (without empty members).
    new_tags = listify(new_tags)
    old_tags = listify(old_tags)
    # Delete removed tags:
    for tag in old_tags:
        if tag not in new_tags:
            # First, delete the instance of the entry/tag combo.
            search_tag = models.Tag.get(models.Tag.name == tag)
            entry_tag = models.EntryTag.get(
                models.EntryTag.entry == entry,
                models.EntryTag.tag == search_tag)
            entry_tag.delete_instance()
            # If no more instances of the tag exist, delete the tag itself.
            search = (models.EntryTag.select()
                      .where(models.EntryTag.tag == search_tag))
            if len(search) == 0:
                search_tag.delete_instance()
    # Add new tags:
    for tag in new_tags:
        if tag not in old_tags:
            # First, see if the tag already exists; create it if it doesn't.
            try:
                search_tag = models.Tag.create(name=tag)
            except models.IntegrityError:
                search_tag = models.Tag.get(models.Tag.name == tag)
            # Check to see if the entry/tag combo already exists.
            try:
                models.EntryTag.get(
                    models.EntryTag.entry == entry,
                    models.EntryTag.tag == search_tag)
            # If it does, do nothing.  If it doesn't, create it.
            except models.DoesNotExist:
                models.EntryTag.create(entry=entry, tag=search_tag)
    return


def listify(string: str) -> list:
    """Turns a CSV string into a list, deleting any empty members."""
    raw_list = string.split(",")
    final_list = []
    for tag in raw_list:
        stripped_tag = tag.strip()
        if stripped_tag != "":
            final_list.append(stripped_tag)
    return final_list


# EXECUTION BEGINS HERE
if __name__ == "__main__":
    models.initialize()
    app.run(debug=DEBUG, host=HOST, port=PORT)
# EXECUTION ENDS HERE
