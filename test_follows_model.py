"""Follows model tests."""

# run these tests like:
#
#    python -m unittest test_follows_model.py


import os
from unittest import TestCase

from models import db, User, Follows

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
        Follows.query.delete()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.testuser3 = User.signup(username="testuser3",
                                    email="3test@test.com",
                                    password="3testuser",
                                    image_url=None)

    def test_follows_model(self):
        """Does basic follows model work?"""

        f = Follows(
            user_being_followed_id=self.testuser1.id,
            user_following_id=self.testuser3.id
            )

        db.session.add(f)
        db.session.commit()

        # Follows connections should match.
        self.assertEqual(f.user_being_followed_id, self.testuser1.id)
        self.assertEqual(f.user_following_id, self.testuser3.id)

        # Follows relationships should have one each.
        self.assertEqual(len(self.testuser1.followers), 1)
        self.assertEqual(len(self.testuser3.following), 1)

        # Follows classmethods:
        self.assertEqual(self.testuser1.is_followed_by(self.testuser3), 1)
        self.assertEqual(self.testuser3.is_following(self.testuser1), 1)
