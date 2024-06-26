import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, ProfileForm
from models import db, connect_db, User, Message, Likes

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    
    flash("You have been logged out.", "success")


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    try:
        do_logout()
        
    except IntegrityError:
        flash("Logout unsuccessful", "error")
        return redirect("/users")
        
    return redirect("/login")
   


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)
    likes = [like.message_id for like in Likes.query.filter_by(user_id=g.user.id).all()]

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    
    return render_template('users/show.html', user=user, messages=messages, likes=likes)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    likes = [like.message_id for like in Likes.query.filter_by(user_id=user_id).all()]
    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user, likes=likes)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    likes = [like.message_id for like in Likes.query.filter_by(user_id=user_id).all()]
    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user, likes=likes)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Handle profile editing."""

    form = ProfileForm()

# ensures a user is logged in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
# gathers user object
    user_id = g.user.id
    user = User.query.get_or_404(user_id)

# validates the edit form
    if form.validate_on_submit():
        try:
            
# ensures the user entered correct password to edit that specific profile 
            if User.authenticate(user.username, form.password.data):

# uses @classmethod 'edit_profile' to update profile
# or uses previous user data
                User.edit_profile(
                    user,
                    username=form.username.data 
                        or user.username,
                    email=form.email.data 
                        or user.email,
                    image_url=form.image_url.data 
                        or User.image_url.default.arg or user.image_url,
                    header_image_url=form.header_image_url.data 
                        or User.header_image_url.default.arg or user.header_image_url,
                    bio=form.bio.data 
                        or user.bio,
                    location=form.location.data 
                        or user.location,
                    )

                flash("Profile updated!", "success")
                return redirect(f'{user_id}')
            else:
                flash("Incorrect password", "danger")
                return render_template('users/edit.html', form=form)

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/edit.html', form=form)
    else:
        return render_template('users/edit.html', form=form)


@app.route('/users/add_like/<int:msg_id>', methods=["POST"])
def add_remove_like(msg_id):
    """Adds or remove a message like."""

    user_id = g.user.id
    likes = [like.message_id for like in Likes.query.filter_by(user_id=user_id).all()]

    if msg_id not in likes:
        Likes.add_like(msg_id, user_id)

        return redirect('/')
    
    else:
        Likes.remove_like(msg_id, user_id)

        return redirect('/')


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET", "POST"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', messages=msg)


@app.route('/messages/<int:user_id>/liked')
def liked_messages_show(user_id):
    """Show a users liked messages."""

    user_id = g.user.id
    liked_msgs = []
    liked_msg_id = [like.message_id for like in Likes.query.filter_by(user_id=user_id).all()]

    for msg_id in liked_msg_id:
        new_msg = Message.query.get(msg_id)
        liked_msgs.append(new_msg)


    return render_template('messages/liked.html', messages=liked_msgs)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        user = User.query.get_or_404(g.user.id)
        messages = []

        for followee in user.following:
            if followee.messages:
                message = (Message
                            .query
                            .filter_by(user_id=followee.id)
                            .order_by(Message.timestamp.desc())
                            .limit(100)
                            .first())
                messages.append(message)

        likes = [like.message_id for like in Likes.query.filter_by(user_id=g.user.id).all()]

        return render_template('home.html', messages=messages, likes=likes)
    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
