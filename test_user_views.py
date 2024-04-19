"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1",
                                    email="test1@test.com",
                                    password="testuser1",
                                    image_url=None)
        
        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)
        
        self.m1 = Message(text="Test 1 of text",
                        user_id=self.testuser1.id)

        db.session.commit()

    def test_list_users(self):
        """Are all users displayed?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

        # Requesting and retrieving the response & HTML:
        resp = c.get("/users")
        html = resp.get_data(as_text=True)

        # Is the request/response making OK connection?
        self.assertEqual(resp.status_code, 200)

        # Is the HTML listing all users?
        self.assertIn('<p>@testuser1</p>', html)
        self.assertIn('<p>@testuser2</p>', html)


    def test_user_profile(self):
        """Is a user's profile loading correctly?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

        # Requesting and retrieving the response & HTML:
        resp = c.get(f"/users/{self.testuser1.id}")
        html = resp.get_data(as_text=True)

        # Is the request/response making OK connection?
        self.assertEqual(resp.status_code, 200)

        # Is the HTML displaying the profile?
        self.assertIn('<h4 id="sidebar-username">@testuser1</h4>', html)

    def test_delete_user(self):
        """Will a user's profile delete correctly?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

        # Requesting and retrieving the response & HTML:
        resp = c.post('/users/delete')
        html = resp.get_data(as_text=True)

        # Is the request/response making OK connection?
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.location, "http://localhost/signup")