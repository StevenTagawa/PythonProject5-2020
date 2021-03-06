"""Debugging and testing module for the Learning Journal app.
Will NOT be included in the final build."""
import models

users = [
    ("god", "iamgod", True),
    ("crashtestdummy", "password", False),
    ("prez_skroob", "12345", False),
    ("tip_of_the_day", "inspire", False),
    ("newuser87", "bmx8500", False),
    ("classic_music_reviews", "Elvis", False)
]

entries = [
    ("god",
     "The First Day",
     "0001-01-01",
     "12:30",
     "“Create a universe!” they said.  “It'll be fun!” they said.  Phooey.  "
     "I spent the whole day just trying to get things to light up.",
     "Big Bangs for Dummies, 3rd Ed.\nGravity Made Simple (How to Create a "
     "Non-Collapsing Universe)\nDark Matter, Dark Energy, and Other Pranks You "
     "Can Play on Unsuspecting Mortals (revised)",
     "creation, big bang, light",
     False, False),
    ("god",
     "So Much for the Garden Idea",
     "0001-01-25",
     "2:15",
     "Lesson one: If you're going to make curious people, don’t expect them to "
     "pay attention to your instructions.  Lesson two:  Making it a kumquat "
     "tree wasn't a good look.  When this gets written up later, change it to "
     "something more basic.  Maybe an apple.  Note to self:  create predators "
     "for snakes.  LOTS of predators.",
     "50 Ways to Skin a Snake",
     "Eden, forbidden fruit",
     True, False),
    ("crashtestdummy",
     "Furloughs???",
     "2004-08-20",
     "01:20",
     "Heard from two fellow dummies this morning that a bunch of us might get "
     "laid off because of some new thing called “computer modeling.”  That’s "
     "just nuts.  There’s nothing like getting hurled through a windshield.",
     "T-Bone Vs. Head-On: A Memoir",
     "technology",
     False, False),
    ("prez_skroob",
     "Plans for the Future",
     "5454-10-14",
     "0:25",
     "Air!  Air!  Where to get more air?!  TIL that that annoying little "
     "planet Druidia has tons of it!  Will have to consult with that annoying "
     "little man Dark Helmet on this.",
     "How to Con Friends and Fleece People",
     "air supply, Dark Helmet, Druidia",
     True, True),
    ("prez_skroob",
     "Planet of the Apes",
     "5455-03-28",
     "8:00",
     "I should’ve known better than to trust those idiots!  Helmet and that "
     "chicken Col. Sanders are both fired, as soon I get back home.\n\nAt "
     "least there’s air here.  Maybe I can find a way to steal it when I "
     "leave.", "So You've Crash-Landed on an Unknown Planet (Now What?)",
     "air supply, Dark Helmet",
     False, False),
    ("tip_of_the_day",
     "Progress",
     "2020-10-25",
     "00:00",
     "Strive for progress, not perfection.",
     "https://themindfool.com/5-reasons-why-strive-progress-not-perfection/",
     "inspire, progress, success",
     False, False),
    ("tip_of_the_day",
     "Goals",
     "2020-10-26",
     "00:00",
     "What you get by achieving your goals is not as important as what you "
     "become by achieving your goals.",
     "Henry David Thoreau",
     "inspire, goals, achievement",
     False, False),
    ("tip_of_the_day",
     "Vision",
     "2020-10-27",
     "00:00",
     "Chase the vision, not the money.  The money will end up following you.",
     "Tony Hsieh, Zappos.com CEO",
     "inspire, vision",
     False, False),
    ("prez_skroob",
     "Vacation Plans?",
     "5454-03-10",
     "2:25",
     "I need some time off Planet Spaceball.  New Vegas sounds nice, but "
     "flights are too expensive right now.  Druidia?  Meh.  Druids are too "
     "stodgy.",
     "How to Stay in New Vegas on $150,000 a Day",
     "vacation, Druidia, Vegas",
     True, False),
    ("tip_of_the_day",
     "Art",
     "2020-10-28",
     "00:00",
     "Everything you can imagine is real.",
     "Pablo Picasso",
     "inspire, art, imagine",
     False, False),
    ("tip_of_the_day",
     "Music",
     "2020-10-29",
     "00:00",
     "Without music, life would be a mistake.",
     "Twilight of the Idols by Friedrich Nietzsche",
     "inspire, music, life",
     False, False),
    ("tip_of_the_day",
     "Opportunity",
     "2020-10-30",
     "00:00",
     "If opportunity doesn’t knock, build a door.",
     "Kurt Cobain",
     "inspire, opportunity",
     False, False),
    ("classic_music_reviews",
     "Now And Forever (1982)",
     "2018-07-15",
     "00:28",
     "One of Air Supply’s better efforts by the Aussie duo, though "
     "overshadowed by their earlier successes.\n\nSingles: Even The Nights Are "
     "Better; Young Love; Two Less Lonely People In The World",
     "https://en.wikipedia.org/wiki/Now_and_Forever_(Air_Supply_album)",
     "Air Supply, Australia, pop",
     False, False),
]


def create_database():
    for user, password, god in users:
        try:
            models.User.create_user(
                username=user,
                password=password,
                god=god)
        except models.IntegrityError:
            pass
    for (username, title, date, time_spent, learned, resources, tags, private,
         hidden) in entries:
        user = models.User.get(username=username)
        entry = models.Entry.create(
            user=user,
            title=title,
            date=date,
            time_spent=time_spent,
            learned=learned,
            resources=resources,
            tags=tags,
            private=private,
            hidden=hidden)
        # Tags need to be added to the Tag and EntryTag tables.  Searches for
        # tags may be case-insensitive, but actual tags will be stored as-is.
        if tags:
            tags = tags.split(",")
            for tag in tags:
                tag = tag.strip()
                try:
                    tag = models.Tag.get(models.Tag.name == tag)
                except models.DoesNotExist:
                    tag = models.Tag.create(name=tag)
                models.EntryTag.create(entry=entry, tag=tag)


if __name__ == "__main__":
    models.initialize()
    create_database()
