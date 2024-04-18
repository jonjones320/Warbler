"""Likes model tests."""

# run these tests like:
#
#    python -m unittest test_likes_model.py


import os
from unittest import TestCase

from models import db, Likes, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class LikesModelTestCase(TestCase):
    """Test views for likes."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

    def test_likes_model(self):
        """Does basic likes model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(u)
        db.session.commit()

        m = Message(
            text="Test of text",
            user_id=u.id
        )
        db.session.add(m)
        db.session.commit()

        l = Likes(
            user_id=u.id,
            message_id=m.id
        )
        db.session.add(l)
        db.session.commit()

        # Likes should have matching user and message ID pairs.
        self.assertEqual(l.user_id, u.id)
        self.assertEqual(l.message_id, m.id)
        self.assertEqual(len(u.likes), 1)
