"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from flask_bcrypt import Bcrypt
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
bcrypt = Bcrypt()

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(u.email, "test@test.com")
        self.assertEqual(u.username, "testuser")
        self.assertEqual(u.password, "HASHED_PASSWORD")


    def test_user_signup(self):
        """Can a new user signup?"""

        newUser = User.signup(
                    "testUsername", 
                    "test@test.com", 
                    "testpassword", 
                    "https://www.google.com"
                )
        
        db.session.commit()
        
        # User.signup should create a new user object and store it in the database.
        self.assertEqual(newUser.username, "testUsername")
        self.assertEqual(newUser.email, "test@test.com")
        # self.assertEqual(newUser.password, bcrypt.check_password_hash(User.password, "testpassword").decode('UTF-8'))
        self.assertEqual(newUser.image_url, "https://www.google.com")


    def test_user_authenticate(self):
        """Can a user be authenticated"""

        oldUser = User(
            username="usertest1",
            password="hashedPassword",
            email="emailtest@test.com"
        )
        db.session.add(oldUser)
        db.session.commit()

        self.assertFalse(User.authenticate("usertest1", "hashedPassword"))
