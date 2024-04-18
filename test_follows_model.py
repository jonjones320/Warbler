"""Follows model tests."""

# run these tests like:
#
#    python -m unittest test_follows_model.py


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


class FollowsModelTestCase(TestCase):
    """Test views for follows."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

    def test_follows_model(self):
        """Does basic follows model work?"""

        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        u3 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        db.session.add(u1,u3)
        db.session.commit()

        f = Follows(
            user_being_followed_id=u1.id,
            user_following_id=u3.id
        )
        db.session.add(f)
        db.session.commit()

        # Follows connections should match.
        self.assertEqual(f.user_being_followed_id, u1.id)
        self.assertEqual(f.user_following_id, u3.id)

        # Follows relationships should have one each.
        self.assertEqual(len(u1.followers), 1)
        self.assertEqual(len(u3.following), 1)

        # Follows classmethods:
        self.assertEqual(u1.is_followed_by(u3), 1)
        self.assertEqual(u3.is_following(u1), 1)
