"""Likes model tests."""

# run these tests like:
#
#    python -m unittest test_likes_model.py


import os
from unittest import TestCase

from models import db, Likes, User, Message

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


    def test_add_remove_likes(self):
        """Creates a user, a message, adds a like to the message, and then removes it"""

        u = User(
            email="newtest@test.com",
            username="newtestuser",
            password="NEW_HASHED_PASSWORD"
        )
        u3 = User(
            email="3newtest@test.com",
            username="3newtestuser",
            password="NEW_HASHED_PASSWORD"
        )
        db.session.add(u, u3)
        db.session.commit()

        m = Message(
            text="Test of text",
            user_id=u.id
        )
        db.session.add(m)
        db.session.commit()

        Likes.add_like(m.id, u.id)
        Likes.add_like(m.id, u3.id)

        # Message "m" should have two likes.
        self.assertEqual(len(Likes.query.get(m.id)), 2)

        Likes.remove_like(m.id, u3.id)

        # Message "m" should now have one like.
        self.assertEqual(len(Likes.query.get(m.id)), 2)
