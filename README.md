# PythonProject5-2020
 Project #5 of the Treehouse Python Techdegree

This project is coded to "Exceed Expectations."

**Features:**

* Multi-user enabled. Create a user account or login to an existing account
to create entries. (Note that no password recovery mechanism has been built in.)

* Variable security.  Posts marked "private" appear in entry listings but can 
be accessed only by their author.  Posts marked "hidden" do not appear in 
listings except to the author.  Posts can only be edited/deleted by their 
author.

   (Note that god-level users can see/edit/delete all entries.)
 
* Dynamic menus.  (e.g., the "Home" button does not appear on the home page; 
"Register" and "Login" buttons appear only when a user is not logged in; the 
"New Entry" and "Logout" buttons only appear when a user is logged in, etc.)
---
A "journal.db" database file is included, populated with several users and 
entries.  Log in to an existing account or create a new account to test the
application's features.

If you need to recreate the original journal.db, run "debug_test.py".  Note that
if you do not delete the existing journal.py before doing this, "debug_test.py"
will create duplicate entries.

**Users:**

*God user*

username:  "god"  
password:  "iamgod"

*Normal users*

username:  "crashtestdummy"  
password:  "password"

username:  "prez_skroob"  
password:  "12345"

username:  "tip_of_the_day"  
password:  "inspire"

