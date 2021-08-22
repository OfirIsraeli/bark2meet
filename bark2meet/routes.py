import json
import os
from flask import render_template, url_for, flash, redirect, request, jsonify

from bark2meet import app, db, bcrypt
from bark2meet.forms import *
from bark2meet.models import User, Friends, START_WALK, OPEN, PRIVATE, FRIENDS
from flask_login import login_user, current_user, logout_user, login_required
from bark2meet import socketio
from flask_socketio import emit
from werkzeug.utils import secure_filename
from bark2meet.notifications import Notification, FRIEND_REQUEST_APPROVED, WALK_INVITATION_APPROVED, \
    NEW_USER_JOINED_WALK, NEW_FRIEND_REQUEST, NEW_INVITE
from bark2meet.event import Event
from datetime import timedelta

# --------------------------- GLOBAL DATA --------------------------- #

OPEN_IMG = "static/GPSgreen.png"
OPEN_FRIEND_IMG = "static/greenfriend.svg"
FRIENDS_IMG = "static/GPSorange.png"
PRIVATE_IMG = "static/GPSred.png"

REGISTER_DOG_LEVEL = 1
IMG_LEVEL = 2

DEFAULT_IMG = "static/default-account-img.png"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


# --------------------------- FLASK USER QUERIES --------------------------- #

def getUserByEmail(email):
    return User.query.filter_by(email=email).first()


def getUserById(user_id):
    return User.query.filter_by(id=user_id).first()


def get_all_connected_users():
    return User.query.filter_by(is_online=True).all()


# --------------------------- SOCKET CONNECTION EVENTS --------------------------- #

@socketio.on('connect')
@socketio.on('online')
def registerConnection():
    current_user.update_is_online(True)


@socketio.on('disconnect')
@socketio.on('offline')
def registerDisconnection():
    current_user.update_is_online(False)


@socketio.on('email', namespace='/private')
def receive_user_email():
    current_user.update_session(request.sid)


# --------------------------- NOTIFICATIONS BACKEND ROUTING --------------------------- #

def getNotificationsFileName():
    HOME_DIR = os.getcwd() + "/bark2meet/databases/notificationsHistory/"
    return HOME_DIR + current_user.email + ".json"


def get_notifications():
    file_path = getNotificationsFileName()
    if os.path.exists(file_path):
        file = open(file_path, "r")
        data = json.load(file)
        file.close()
        all_notifications = data["notifications"][::-1]
        new_notifications = []
        end = len(all_notifications)
        for i in range(len(all_notifications)):
            if all_notifications[i]['issue_time'] > current_user.date_last_session.isoformat(' ', 'seconds'):
                if all_notifications[i]['type'] == NEW_FRIEND_REQUEST:
                    all_notifications[i]['needApproval'] = True

                elif all_notifications[i]['type'] == NEW_INVITE:
                    all_notifications[i]['needApproval'] = True

                else:
                    all_notifications[i]['needApproval'] = False
                new_notifications.append(all_notifications[i])
            else:
                end = i
                break

        for old in all_notifications[end:]:
            if old['type'] == NEW_FRIEND_REQUEST:
                old['needApproval'] = True

            elif old['type'] == NEW_INVITE:
                old['needApproval'] = True

            else:
                old['needApproval'] = False

        return new_notifications, all_notifications[end:]
    else:
        return [], []


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


# --------------------------- MAIN ROUTES --------------------------- #

@app.route("/")
@app.route("/index")
def landing_page():
    if current_user.is_authenticated:
        return redirect(url_for('map'))
    return render_template('index.html', is_login=current_user.is_authenticated)


@app.route("/notifications")
@login_required
def notifications_page():
    form = SearchForm()
    new, old = get_notifications()
    current_user.update_date_last_session(datetime.now())
    return render_template('notifications.html', title="Notifications", form=form, status=current_user.status,
                           old_notifications=old[:20], new_notifications=new)


@app.route("/map", methods=['GET', 'POST'])
@login_required
def map():
    if current_user.sing_up_level == REGISTER_DOG_LEVEL:
        return redirect(url_for('register_dog'))

    update_user_area(current_user)
    connected_users = get_all_connected_users()
    for user in connected_users:
        update_user_area(user)

    return render_template('map.html', title="Map", status=current_user.status, current_user=current_user)


@app.route("/register_user", methods=['GET', 'POST'])
def register_user():
    if current_user.is_authenticated and current_user.sing_up_level > REGISTER_DOG_LEVEL:
        return redirect(url_for('map'))
    if current_user.is_authenticated and current_user.sing_up_level == REGISTER_DOG_LEVEL:
        return redirect(url_for('register_dog'))
    form = RegistrationUserForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        gender = request.form['gender']
        user = User(full_name=form.full_name.data, email=form.email.data,
                    password=hashed_password, gender=gender, birth_date=form.birth_date.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        current_user.update_sing_level()
        return redirect(url_for('register_dog'))
    return render_template('register_user.html', title='Register', form=form)


@app.route("/register_dog", methods=['GET', 'POST'])
def register_dog():
    if current_user.is_authenticated and current_user.sing_up_level != REGISTER_DOG_LEVEL:
        return redirect(url_for('map'))
    form = RegistrationDogForm()
    if form.validate_on_submit():
        gender = request.form['gender']
        current_user.update_dog_details(form.dog_name.data, form.dog_age.data,
                                        form.dog_breed.data, gender)
        current_user.update_sing_level()
        return redirect(url_for('upload_file'))
    return render_template('register_dog.html', title='Register', form=form)


@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if current_user.is_authenticated and current_user.sing_up_level != IMG_LEVEL:
        return redirect(url_for('map'))

    form = FileUploadForm()

    if form.validate_on_submit():
        save_user_img = True
        save_dog_img = True
        user_img_path, dog_img_path = "", ""

        user_img_file = request.files['user_img']
        user_img_filename = secure_filename(user_img_file.filename)

        dog_img_file = request.files['dog_img']
        dog_img_filename = secure_filename(dog_img_file.filename)

        if user_img_filename == "":
            user_img_path = DEFAULT_IMG
            save_user_img = False
        elif not allowed_file(user_img_filename):
            flash('This is not an image file', 'file_format_error')
            return redirect(request.url)

        if dog_img_filename == "":
            dog_img_path = DEFAULT_IMG
            save_dog_img = False
        elif not allowed_file(dog_img_filename):
            flash('This is not an image file', 'file_format_error')
            return redirect(request.url)

        try:
            os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], current_user.email))
        except:
            pass

        if save_user_img:
            user_img_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.email,
                                         user_img_filename)
            user_img_file.save(user_img_path)
        if save_dog_img:
            dog_img_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.email,
                                        dog_img_filename)
            dog_img_file.save(dog_img_path)

        current_user.update_user_and_dog_img(user_img_path, dog_img_path)
        current_user.update_sing_level()
        flash('Your account has been created successfully!', 'register_success')
        return redirect(url_for('welcome_screen'))
    return render_template('upload.html', form=form)


@app.route("/welcome_screen", methods=['GET', 'POST'])
@login_required
def welcome_screen():
    return render_template('welcome.html', user=current_user)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        current_user.change_status(START_WALK)
        update_user_area(current_user)
        return redirect(url_for('map'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            user.change_status(START_WALK)
            next_page = request.args.get('next')
            update_user_area(current_user)
            return redirect(next_page) if next_page else redirect(url_for('map'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'login_error')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
@login_required
def logout():
    current_user.update_is_online(False)
    logout_user()
    return redirect(url_for('map'))


@app.route("/profile")
@login_required
def get_user_details():
    today = date.today()
    age = today.year - current_user.birth_date.year - ((today.month, today.day) < (current_user.birth_date.month,
                                                                                   current_user.birth_date.day))
    return render_template('my_profile.html', title="Profile", status=current_user.status, user=current_user, age=age)


@app.route("/event", methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        event_id = add_to_event_count()
        privacy = request.form['privacy']
        date = request.form['date']
        Event().create_event(email=current_user.email, title=form.title.data,
                             privacy=privacy,
                             location=form.location.data, time=form.time.data, date=date,
                             id=event_id)
        flash('The event has been created successfully', 'event_success')
        return redirect(url_for('invite_friends', event_id=event_id))

    return render_template('create_event.html', status=current_user.status, form=form, title="Create Event")


@app.route("/invite_friends/<event_id>", methods=['GET', 'POST'])
@login_required
def invite_friends(event_id):
    form = SearchForm()
    search_friend = form.search_filter.data
    all_friends_emails = Friends().get_all_friends_of(current_user.email)
    all_friends_users_list = []
    is_send_friend_req_dict = {}

    for friend_email in all_friends_emails:
        complete_user = getUserByEmail(friend_email)
        is_send_friend_req = Notification().check_if_there_is_noti_from(
            friend_email, NEW_INVITE, "invite_" + str(event_id))
        is_send_friend_req_dict[friend_email] = is_send_friend_req

        if search_friend == None:
            all_friends_users_list.append(complete_user)
        elif search_friend in complete_user.full_name:
            all_friends_users_list.append(complete_user)

    return render_template("friends_invite_list.html", title="Invite Friends",
                           friends=all_friends_users_list, status=current_user.status,
                           form=form, event_id=event_id, friend_req=is_send_friend_req_dict)


@app.route("/my_walks", methods=['GET', 'POST'])
@login_required
def my_walks():
    search_form = SearchForm()
    future_walks, past_walks = generateWalks(current_user)
    walks_in_area = get_walks_in_area_today()
    return render_template("my_walks.html", title="My Walks", walks=future_walks, past_walks=past_walks,
                           form=search_form, status=current_user.status, walks_in_area=walks_in_area,
                           my_email=current_user.email)


@app.route("/profile/<user_id>", methods=['GET', 'POST'])
@login_required
def get_profile(user_id):
    user = getUserById(user_id)
    future_events = get_all_future_user_events(user)
    is_friend = user.email in Friends().get_all_friends_of(current_user.email)
    today = date.today()
    age = today.year - user.birth_date.year - ((today.month, today.day) < (user.birth_date.month,
                                                                           user.birth_date.day))
    is_send_friend_req = False
    if not is_friend:
        is_send_friend_req = Notification().check_if_there_is_noti_from(
            user.email, 3, current_user.email)
    return render_template("other_profile.html", title=current_user.full_name + "'s Profile", user=user,
                           status=current_user.status,
                           future_events=future_events, is_friend=is_friend, age=age,
                           current_user=current_user, is_send_friend_req=is_send_friend_req)


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@app.route("/event_details/<id>", methods=['GET', 'POST'])
@login_required
def event_details(id):
    event, event_date = Event().get_event_by_id(id)
    event_date = event_date[:-5].split("-")
    day = event_date[2]
    month = event_date[1]
    year = event_date[0]
    participants = []
    friends = Friends().get_all_friends_of(current_user.email)
    for email in event["joined"]:
        if email == current_user.email:
            continue
        user = getUserByEmail(email)
        participants.append({"user": user, "is_friend": user.email in friends})
    if current_user.email in event['joined']:
        participants = [{"user": current_user, "is_friend": False}] + participants

    return render_template("event_details.html", title="Event Details", event=event, participants=participants, day=day,
                           month=month, year=year, current_user_email=current_user.email, status=current_user.status)


# --------------------------- FRONTEND API CALLS --------------------------- #

@app.route("/api/are_friends_around", methods=['GET', 'POST'])
@login_required
def encourage_walk():
    if request.method == 'GET':
        if current_user.status != START_WALK:
            return "0"
        friends_walking = 0
        friends = Friends().get_all_friends_of(current_user.email)
        for friend_email in friends:
            friend = getUserByEmail(friend_email)
            if friend.is_online and friend.current_area_x == current_user.current_area_x and \
                    friend.current_area_y == current_user.current_area_y:
                friends_walking += 1
        return str(friends_walking)


@app.route("/api/rush_hour_check", methods=['GET', 'POST'])
@login_required
def rush_hour_check():
    if request.method == 'GET':
        RUSH_HOUR_AMOUNT = 5
        if current_user.status != START_WALK:
            return "0"
        connected_in_area_no_radius = User.query.filter_by(current_area_x=current_user.current_area_x,
                                                           current_area_y=current_user.current_area_y,
                                                           is_online=True).all()
        connected_in_area = []
        for user in connected_in_area_no_radius:
            if radius_distance(user.pos_x, user.pos_y) <= current_user.radius_view and user.status != START_WALK:
                connected_in_area.append(user)

        return str(len(connected_in_area))


@app.route("/update_user_location", methods=['GET', 'POST'])
@login_required
def update_user_location():
    information = str(request.data)[3:-2]
    coordinates = information.split(',')

    if coordinates[0] and coordinates[1]:
        coordinate_x = float(coordinates[0])
        coordinate_y = float(coordinates[1])
        current_user.update_user_location(coordinate_x, coordinate_y)

    return "1"


@app.route("/join_to_event", methods=['GET', 'POST'])
@login_required
def join_event_by_id():
    event_id = str(request.data)[3:-2]
    event = add_user_to_event(event_id, True, current_user.email)
    creator = event['creator']
    Notification().create_notification(creator, event["title"] + " just got an addition!",
                                       current_user.full_name + " has joined your walk",
                                       current_user.pos_x, current_user.pos_y,
                                       NEW_USER_JOINED_WALK, current_user.email, current_user.user_img)
    return "1"


@app.route("/api/update_status", methods=['GET', 'POST'])
@login_required
def update_user_status():
    status = str(request.data)[2:-1]
    current_user.change_status(int(status))
    return status


@app.route("/api/update_radius", methods=['GET', 'POST'])
@login_required
def update_user_radius():
    radius = str(request.data)[3:-2]
    current_user.update_radius_view(int(radius) * 1000)
    return radius


@app.route("/api/get_status", methods=['GET', 'POST'])
@login_required
def get_user_status():
    if request.method == 'GET':
        return jsonify(current_user.status)


@app.route("/exit_from_event", methods=['GET', 'POST'])
@login_required
def exit_event_by_id():
    event_id = str(request.data)[3:-2]

    Event().exit_from_event(int(event_id), [current_user.email])

    return "1"


# --------------------------- IMG UPLOAD --------------------------- #

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --------------------------- EVENTS BACKEND ROUTING  --------------------------- #

def get_all_future_user_events(user):
    past, future = generateWalks(user)
    events = past + future
    result = []
    for event in events:
        if user.email in event["joined"]:
            users_images = []
            for joined in event["joined"][:3]:
                joined_user = getUserByEmail(joined)
                users_images.append(joined_user.user_img)
            event['users_images'] = users_images
            result.append(event)

    return result


def getEventsFileName(event_date):
    HOME_DIR = os.getcwd() + "/bark2meet/databases/eventsHistory/"
    return HOME_DIR + event_date + ".json"


def getUserWalksByDate(event_date, user):
    file_path = getEventsFileName(event_date)
    if os.path.exists(file_path):
        result = []
        file = open(file_path, "r")
        data = json.load(file)
        file.close()
        all_events = data["events"]
        for event in all_events:
            if user.email in event["joined"]:
                users_images = []
                for joined in event["joined"][:3]:
                    joined_user = getUserByEmail(joined)
                    users_images.append(joined_user.user_img)
                event['users_images'] = users_images
                result.append(event)
        return result
    else:
        return []


def generateWalks(user):
    today = date.today()
    yesterday = today - timedelta(1)
    tomorrow = today + timedelta(1)
    yesterday_walks = getUserWalksByDate(yesterday.isoformat(), user)
    today_walks = getUserWalksByDate(today.isoformat(), user)
    tomorrow_walks = getUserWalksByDate(tomorrow.isoformat(), user)
    past_walks = []
    future_walks = []
    for walk in today_walks:
        if walk["time"] > datetime.now().time().isoformat('seconds'):
            future_walks.append(walk)
        else:
            past_walks.append(walk)
    future_walks = tomorrow_walks + future_walks
    past_walks = past_walks + yesterday_walks
    return future_walks, past_walks


def get_walks_in_area_today():
    events = Event().get_today_events(current_user.email)
    future_today = []
    for event in events:
        if event["time"] > datetime.now().time().isoformat('seconds'):
            users_images = []
            if current_user.email in event["joined"]:
                users_images.append(current_user.user_img)
            joined_index = 0
            while len(users_images) <= 3 and joined_index < len(event["joined"]):
                joined_email = event["joined"][joined_index]
                if joined_email != current_user.email:
                    joined_user = getUserByEmail(joined_email)
                    users_images.append(joined_user.user_img)
                joined_index += 1
            event['users_images'] = users_images
            future_today.append(event)
    return future_today


def add_to_event_count():
    file_path = os.getcwd() + "/bark2meet/databases/eventsHistory/ID_COUNT"
    if os.path.exists(file_path):
        with open(file_path, "r+") as file:

            current = int(file.read())
            file.close()
            f = open(file_path, "w")
            f.write(str(current + 1))
            f.close()
            return current + 1
    else:
        with open(file_path, "w") as file:
            file.write(str(1))
            file.close()
            return 1


def add_user_to_event(id_event, to_join, user):
    if id_event.startswith("invite_"):
        id_event = id_event[7:]
    dir_path = os.getcwd() + "/bark2meet/databases/eventsHistory/"
    for filename in os.listdir(dir_path):
        if filename.endswith(".json"):
            file_path = dir_path + filename

            file = open(file_path, "r")
            data = json.load(file)
            file.close()
            all_events = data["events"]

            for event in all_events:
                if int(id_event) == event["id"]:

                    if to_join:
                        if user not in event["joined"]:
                            event["joined"].append(user)
                    else:
                        if user in event["joined"]:
                            event["joined"].remove(user)
                    with open(file_path, "w") as file:
                        data = {"events": all_events}
                        json.dump(data, file, default=str, indent=4)
                    return event

    raise Exception("DID NOT FIND THE EVENT", id_event)


@app.route("/event_invite_approve", methods=['GET', 'POST'])
@login_required
def join_event():
    req = str(request.data)[3:-2].split(",")
    should_accept = req[0]
    event_id = req[1][1:-1]

    if should_accept == "true":

        event = add_user_to_event(event_id, True, current_user.email)

        Notification().delete_notifications(current_user.email, NEW_INVITE, "invite_" + str(event["id"]))
        Notification().create_notification(event["creator"],
                                           "Invitation approved",
                                           current_user.full_name + " has accepted your walk invitation!",
                                           current_user.pos_x,
                                           current_user.pos_y,
                                           WALK_INVITATION_APPROVED,
                                           current_user.email, current_user.user_img)

    else:
        event = add_user_to_event(event_id, False, current_user.email)
        Notification().delete_notifications(current_user.email, NEW_INVITE, "invite_" + str(event["id"]))
    return "1"


@app.route("/invite_this_friend", methods=['GET', 'POST'])
@login_required
def create_notification_to_friend():
    friend_id, event_id = str(request.data)[3:-2].split(",")
    friend = getUserById(int(friend_id[1:-1]))
    Notification().create_walk_invitation_notification(current_user, friend.email, event_id)
    return "1"


# --------------------------- FRIENDS API ROUTING  --------------------------- #

@app.route("/unsend_friend_request", methods=['GET', 'POST'])
@login_required
def unsend_friend_request():
    friend_id = str(request.data)[3:-2]
    friend = getUserById(int(friend_id))
    Notification().delete_notifications(friend.email, NEW_FRIEND_REQUEST, current_user.email)
    return "1"


@app.route("/remove_friend", methods=['GET', 'POST'])
@login_required
def remove_friend():
    friend_id = str(request.data)[3:-2]
    friend = getUserById(int(friend_id))
    Friends().delete(current_user.email, friend.email)
    return "1"


@app.route("/friend_request_approve", methods=['GET', 'POST'])
@login_required
def add_friend():
    req = str(request.data)[3:-2].split(",")
    should_accept = req[0]
    requester = req[1][1:-1]

    if should_accept == "true":
        Friends().add(current_user.email, requester)
        Friends().add(requester, current_user.email)
        new_friend = getUserByEmail(requester)
        Notification().delete_notifications(new_friend.email, NEW_FRIEND_REQUEST, current_user.email)
        Notification().delete_notifications(current_user.email, NEW_FRIEND_REQUEST, new_friend.email)
        Notification().create_notification(new_friend.email,
                                           "Friend request approved",
                                           current_user.full_name + " has accepted your friend request!",
                                           current_user.pos_x,
                                           current_user.pos_y,
                                           FRIEND_REQUEST_APPROVED,
                                           current_user.email, current_user.user_img)
    else:
        not_friend = getUserByEmail(requester)
        Notification().delete_notifications(not_friend.email, NEW_FRIEND_REQUEST, current_user.email)
        Notification().delete_notifications(current_user.email, NEW_FRIEND_REQUEST, not_friend.email)
    return "1"


@app.route("/send_friend_request", methods=['GET', 'POST'])
@login_required
def send_friend_request():
    friend_id = str(request.data)[3:-2]
    friend = getUserById(int(friend_id))
    Notification().create_notification(friend.email,
                                       "New friend request",
                                       "You got new friend request from: " + current_user.full_name,
                                       friend.pos_x,
                                       friend.pos_y,
                                       NEW_FRIEND_REQUEST,
                                       current_user.email, current_user.user_img)
    return "1"


# -------------------------------- SOCKET-IO NOTIFICATIONS EMITTING -------------------------------- #
@socketio.on("friend-request-notification", namespace='/private')
def send_friend_request_noti(data):
    friend = getUserById(data)
    recipient_session_id = friend.session
    emit('new_friend_request', {"username": current_user.full_name,
                                "issue_time": datetime.now().isoformat(' ', 'seconds')},
         room=recipient_session_id)


@socketio.on("friend-approve-notification", namespace='/private')
def send_friend_approve_noti(data):
    friend = getUserByEmail(data)
    recipient_session_id = friend.session
    emit('friend_request_approve', {"username": current_user.full_name,
                                    "issue_time": datetime.now().isoformat(' ', 'seconds')},
         room=recipient_session_id)


@socketio.on("event-invite-notification", namespace='/private')
def send_event_invite_noti(data):
    friend = getUserById(data)
    recipient_session_id = friend.session
    emit('new_event_invite', {"username": current_user.full_name,
                              "issue_time": datetime.now().isoformat(' ', 'seconds')},
         room=recipient_session_id)


@socketio.on("event-approve-notification", namespace='/private')
def send_event_approve_noti(data):
    event, filename = Event().get_event_by_id(data[7:])
    friend = getUserByEmail(event["creator"])
    recipient_session_id = friend.session
    emit('event_invite_approve', {"username": current_user.full_name,
                                  "issue_time": datetime.now().isoformat(' ', 'seconds')},
         room=recipient_session_id)


@socketio.on("event-join-notification", namespace='/private')
def send_event_invite_noti(data):
    friend = getUserById(data)
    recipient_session_id = friend.session
    emit('new_event_join', {"username": current_user.full_name,
                            "issue_time": datetime.now().isoformat(' ', 'seconds')},
         room=recipient_session_id)


# -------------------------------- GPS LOCATIONS CHANNELING -------------------------------- #

@app.route("/api/locations", methods=['GET', 'POST'])
@login_required
def get_locations():
    if request.method == 'GET':
        all_locations = []
        get_all_locations(all_locations)
        return jsonify(all_locations)


def map_privacy_to_string(privacy_int, user):
    if user.email == current_user.email:
        return "me"
    if privacy_int == PRIVATE:
        return "red"
    if privacy_int == FRIENDS:
        return "orange"
    if privacy_int == START_WALK:
        return "notWalking"
    if privacy_int == OPEN:
        return "green"

    return "notWalking"


def map_image_to_user(user, is_friend):
    if user.email == current_user.email:
        return "static/userPic.svg"
    if user.status == PRIVATE:
        return PRIVATE_IMG
    if user.status == FRIENDS:
        return FRIENDS_IMG
    if is_friend:
        return OPEN_FRIEND_IMG
    return OPEN_IMG


def radius_distance(user_pos_x, user_pos_y):
    return ((current_user.pos_x - user_pos_x) ** 2 + (current_user.pos_y - user_pos_y) ** 2) ** 0.5


def get_all_locations(all_locations):
    connected_in_area_no_radius = User.query.filter_by(current_area_x=current_user.current_area_x,
                                                       current_area_y=current_user.current_area_y,
                                                       is_online=True, ).all()
    connected_in_area = []
    for user in connected_in_area_no_radius:
        if radius_distance(user.pos_x, user.pos_y) <= current_user.radius_view:
            connected_in_area.append(user)

    connected_in_area = [current_user] + connected_in_area

    all_friends_of_user = Friends().get_all_friends_of(current_user.email)

    for user in connected_in_area:
        today = date.today()
        age = today.year - user.birth_date.year - ((today.month, today.day) < (user.birth_date.month,
                                                                               user.birth_date.day))
        is_send_friend_req = False
        is_friend = user.email in all_friends_of_user

        if not is_friend:
            is_send_friend_req = Notification().check_if_there_is_noti_from(
                user.email, 3, current_user.email)

        privacy = map_privacy_to_string(user.status, user)
        if privacy == "notWalking" or (current_user.status == FRIENDS and not is_friend and privacy != "me") \
                or ((current_user.status == OPEN or current_user.status == PRIVATE) and
                    not is_friend and privacy != "me" and user.status == FRIENDS) or \
                (current_user.status == START_WALK and not is_friend and
                 privacy != "me" and user.status == FRIENDS) or \
                (current_user.status == -1 and not is_friend and privacy != "me" and user.status == FRIENDS):
            continue
        user_info = {
            "privacy": privacy,
            "status": current_user.status,
            "full_name": user.full_name,
            "age": age,
            "pos_x": user.pos_x,
            "pos_y": user.pos_y,
            "image": map_image_to_user(user, is_friend),
            "user_image": user.user_img.replace('\\', '/') if user.status != PRIVATE else "",
            "dog_image": user.dog_img.replace('\\', '/') if user.status != PRIVATE else "",
            "gender": user.gender if user.status != PRIVATE else "",
            "dog_name": user.dog_name,
            "dog_age": user.dog_age if user.status != PRIVATE else "",
            "dog_gender": user.dog_gender,
            "dog_breed": user.dog_breed,
            "id": user.id,
            "is_friend": is_friend,
            "send_friend_req": is_send_friend_req
        }

        all_locations.append(user_info)


X_POS = 0
Y_POS = 1

JERUSALEM = (31.771959, 35.217018)
TEL_AVIV = (32.109333, 34.855499)
MODIIN = (31.89670800658577, 35.007197003536874)
BEER_SHEVA = (31.249006188313423, 34.78929831233399)
HAIFA = (32.794044, 34.989571)
RISHON_LETSION = (31.971446748700092, 34.789905030890395)
EILAT = (29.558427166230377, 34.94631812068723)

Areas_dict = {
    JERUSALEM,
    TEL_AVIV,
    MODIIN,
    BEER_SHEVA,
    HAIFA,
    RISHON_LETSION,
    EILAT,
}


def update_user_area(user):
    min_dist = float("inf")
    curr_x_min = float("inf")
    curr_y_min = float("inf")
    for city in Areas_dict:
        curr_dist = distance(city, user.pos_x, user.pos_y)
        if curr_dist < min_dist:
            min_dist = curr_dist
            curr_x_min = city[X_POS]
            curr_y_min = city[Y_POS]

    # if user is in the same area as before
    if curr_x_min == user.current_area_x and curr_y_min == user.current_area_y:
        return
    else:
        user.update_user_area(curr_x_min, curr_y_min)


def distance(city, user_pos_x, user_pos_y):
    return (city[X_POS] - user_pos_x) ** 2 + (city[Y_POS] - user_pos_y) ** 2
