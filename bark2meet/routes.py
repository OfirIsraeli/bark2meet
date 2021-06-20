import json
import os
from flask import render_template, url_for, flash, redirect, request, jsonify
from bark2meet import app, db, bcrypt
from bark2meet.forms import *
from bark2meet.models import User, Friends
from bark2meet.areas import area
from flask_login import login_user, current_user, logout_user, login_required
from bark2meet import socketio
from flask_socketio import emit
from cryptography.fernet import Fernet
from werkzeug.utils import secure_filename
from bark2meet.notifications import Notification, FRIEND_WALK
from bark2meet.event import Event
from datetime import timedelta

# ------ GLOBAL DATA START------

PRIVATE = 1
NO_PRIVATE = 0
OPEN_IMG = "static/GPSgreen.png"
FRIENDS_IMG = "static/GPSorange.png"
PRIVATE_IMG = "static/GPSred.png"

REGISTER_DOG_LEVEL = 1
IMG_LEVEL = 2

DEFAULT_IMG = "static/default-account-img.png"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

users = {}

# todo: check if needed
all_users = None
try:
    all_users = User.query.all()
except:
    print("need to drop db and recreate it")

fernet_with_key = Fernet(b"8eDa1w9-C8THy0nz_dpeoBS0BX_UAf5D_oIhRd8nlgA=")


# ------ GLOBAL DATA END------


# ------ MESSAGING FUNCTIONS ------
def getUserByEmail(email):
    return User.query.filter_by(email=email).first()


def getUserById(user_id):
    return User.query.filter_by(id=user_id).first()


@socketio.on('connect')
def registerConnection():
    print(current_user.email, "has connected")


@socketio.on('disconnect')
def registerConnection():
    # area.remove_user(current_user)
    print(current_user.email, "has disconnected")


@socketio.on('email', namespace='/private')
def receive_user_email():
    users[current_user.email] = request.sid


@socketio.on('friend-walk', namespace='/private')
def register_walk():
    # friends_around = area.getFriendsInRadius(current_user, current_user.radius_view)
    for recipient in users:
        if recipient != current_user.email:
            # recipient_user = getUserByEmail(recipient)
            recipient_session_id = users[recipient]
            emit('new_friend_walk', {"username": current_user.full_name,
                                     "issue_time": datetime.now().isoformat(' ', 'seconds')},
                 room=recipient_session_id)
            Notification(recipient, "", current_user.full_name + " is on the go!",
                         current_user.pos_x, current_user.pos_y, FRIEND_WALK)

    for user in all_users:
        if user.email != current_user.email and user.email not in users:
            Notification(user.email, "", current_user.full_name + " was on the go!",
                         current_user.pos_x, current_user.pos_y, FRIEND_WALK)


@socketio.on('private_message', namespace='/private')
def private_message(payload):
    message = payload['message']
    try:
        # sender = getUserByEmail(payload['email'])
        sender_session_id = users[payload['email']]
        emit('new_private_message',
             {"msg": message, "username": current_user.full_name, "email": current_user.email,
              "send_time": datetime.now().isoformat(' ', 'seconds')},
             room=sender_session_id)
        writeMessageInHistory(current_user.email, payload['email'], message)
    except KeyError:  # so user is not logged in right now
        writeMessageInHistory(current_user.email, payload['email'], message)


# ------ MESSAGING FUNCTIONS END ------

# ------ CHAT HISTORY ------
def getHistoryFileName(sender, recipient):
    HOME_DIR = os.getcwd() + "/bark2meet/databases/chatHistory/"
    if sender < recipient:
        return HOME_DIR + sender + "&" + recipient + ".json"

    return HOME_DIR + recipient + "&" + sender + ".json"


def writeMessageInHistory(sender, recipient, msg):
    encMessage = fernet_with_key.encrypt(msg.encode())
    msg_json = {
        "msg": encMessage.decode(),
        "sender": sender,
        "send_time": datetime.now().isoformat(' ', 'seconds')
    }

    file_path = getHistoryFileName(sender, recipient)
    if os.path.exists(file_path):
        file = open(file_path, "r+")
        data = json.load(file)
        data["chat"].append(msg_json)
        file.seek(0)
        json.dump(data, file, default=str, indent=4)
    else:
        file = open(file_path, "w")
        data = {"chat": [msg_json]}
        json.dump(data, file, default=str, indent=4)
    file.close()


def getChatHistory(sender, recipient):
    file_path = getHistoryFileName(sender, recipient)
    if os.path.exists(file_path):
        file = open(file_path, "r")
        data = json.load(file)
        file.close()
        return data
    else:
        return {"chat": []}


@app.route("/api/history/<sender>", methods=['GET', 'POST'])
def getHistory(sender):
    if request.method == 'GET':
        history = getChatHistory(current_user.email, sender)
        for chat in history["chat"]:
            chat["msg"] = fernet_with_key.decrypt(chat["msg"].encode()).decode()
        return jsonify(history)


# ------ CHAT HISTORY END ------

# ------ NOTIFICATIONS START ------
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
            if all_notifications[i]['issue_time'] > current_user.date_last_session.isoformat(' ',
                                                                                             'seconds'):
                new_notifications.append(all_notifications[i])
            else:
                end = i
                break
        return new_notifications, all_notifications[end:]
    else:
        return [], []


# ------ WEBPAGES BACKEND START ------
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


@app.route("/")
@app.route("/index")
def landing_page():
    return render_template('index.html')


@app.route("/map", methods=['GET', 'POST'])
@login_required
def map():
    if current_user.sing_up_level == REGISTER_DOG_LEVEL:
        return redirect(url_for('register_dog'))
    current_area_x, current_area_y = area.update(current_user)
    current_user.update_user_area(current_area_x, current_area_y)
    return render_template('map.html', title="Map")


@app.route("/update_user_location", methods=['GET', 'POST'])
@login_required
def update_user_location():
    information = str(request.data)[3:-2]
    coordinates = information.split(',')

    if coordinates[0] and coordinates[1]:
        coordinate_x = float(coordinates[0])
        coordinate_y = float(coordinates[1])
        current_user.update_user_location(coordinate_x, coordinate_y)

        # TODO: update areas
        # TODO: photo albums
    return "1"


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
        # todo: validate gender field
        gender = request.form['gender']
        current_user.update_dog_details(form.dog_name.data, form.dog_age.data,
                                        form.dog_temperament.data,
                                        form.dog_color.data, form.dog_breed.data, gender)
        current_user.update_sing_level()
        return redirect(url_for('upload_file'))
    return render_template('register_dog.html', title='Register', form=form)


# ------ IMG UPLOAD START ------

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        return redirect(url_for('map'))
    return render_template('upload.html', form=form)


# ------ IMG UPLOAD END ------
event_id = 0


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('map'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            print("on login")
            # TODO: AREA INSTANCE PROBLEM - LOGIN AREA UPDATE DO NOT UPDATE AREAS OF USERS THAT ARE ALREADY LOGGED IN
            current_area_x, current_area_y = area.update(current_user, True)
            current_user.update_user_area(current_area_x, current_area_y)

            return redirect(next_page) if next_page else redirect(url_for('map'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'login_error')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
@login_required
def logout():
    area.remove_user(current_user)
    logout_user()
    return redirect(url_for('map'))


@app.route("/profile")
@login_required
def get_user_details():
    return render_template('profile.html', user=current_user)


@app.route("/event", methods=['GET', 'POST'])
@login_required
def create_event():
    global event_id
    form = EventForm()
    if form.validate_on_submit():
        privacy = request.form['privacy']
        date = request.form['date']
        Event().create_event(email=current_user.email, title=form.title.data,
                             privacy=privacy,
                             location=form.location.data, time=form.time.data, date=date,
                             id=event_id)

        if form.invite.data:
            Friends().get_all_friends_of(current_user.email)

        event_id += 1
        flash('The event has been created successfully', 'event_success')
        # return redirect(url_for('home'))

    return render_template('create_event.html', form=form, title="Create Event")


@app.route("/join", methods=['GET', 'POST'])
@login_required
def join_walk():
    form = SearchForm()
    event_filter = form.search_filter.data
    all_today_events = Event().get_today_events(current_user.email)
    show_events = []
    users_imgs = []

    counter = 0
    if event_filter == None:
        show_events = all_today_events
    else:
        for event in all_today_events:
            if event_filter in event["title"]:
                show_events.append(event)

    for event in show_events:
        img_dict = {
            "id": event["id"],
            "imgs": []
        }
        for email in event["joined"]:
            if counter > 2: break
            user_img = getUserByEmail(email).user_img
            img_dict["imgs"].append(user_img)

        users_imgs.append(img_dict)
        counter = 0
    return render_template("join_walk.html", title="Join a Walk", events=show_events,
                           my_email=current_user.email, users_imgs=users_imgs, form=form)


@app.route("/join_to_event", methods=['GET', 'POST'])
@login_required
def join_event_by_id():
    event_id = str(request.data)[3:-2]

    Event().join_to_event(int(event_id), [current_user.email])

    return "1"


@app.route("/exit_from_event", methods=['GET', 'POST'])
@login_required
def exit_event_by_id():
    event_id = str(request.data)[3:-2]

    Event().exit_from_event(int(event_id), [current_user.email])

    return "1"


NEW_INVITE = 2
NEW_FRIEND_REQUEST = 3


@app.route("/invite_friends", methods=['GET', 'POST'])
@login_required
def invite_friends():
    form = SearchForm()
    search_friend = form.search_filter.data
    all_friends_emails = Friends().get_all_friends_of(current_user.email)
    all_friends_users_list = []

    for friend_email in all_friends_emails:
        complete_user = getUserByEmail(friend_email)
        if search_friend == None:
            all_friends_users_list.append(complete_user)
        elif search_friend in complete_user.full_name:
            all_friends_users_list.append(complete_user)

    return render_template("friends_invite_list.html", title="Invite Friends",
                           friends=all_friends_users_list,
                           form=form)


@app.route("/invite_this_friend", methods=['GET', 'POST'])
@login_required
def create_notification_to_friend():
    friend_id = str(request.data)[3:-2]
    friend = getUserById(int(friend_id))
    Notification(friend.email,
                 "New walk invite",
                 "You got new invite from: ",
                 friend.pos_x,
                 friend.pos_y,
                 NEW_INVITE)

    return "1"

@socketio.on('friend_request_approve', namespace='/private')
def add_friend(payload):
    friend = payload["friend"]
    Friends().add(current_user.email, friend.email)
    Friends().add(friend.email, current_user.email)


@app.route("/add_friend", methods=['GET', 'POST'])
@login_required
def add_friend():
    friend_id = str(request.data)[3:-2]
    friend = getUserById(int(friend_id))
    # Friends().add(current_user.email, friend.email)
    Notification(friend.email,
                 "New friend request",
                 "You got new friend request from: ",
                 friend.pos_x,
                 friend.pos_y,
                 NEW_FRIEND_REQUEST)
    if friend.email not in users.keys():
        return
    recipient_session_id = users[friend.email]
    emit('new_friend_request', {"username": current_user.full_name,
                                "email": current_user.email,
                             "issue_time": datetime.now().isoformat(' ', 'seconds')},
         room=recipient_session_id)
    return "1"


@app.route("/remove_friend", methods=['GET', 'POST'])
@login_required
def remove_friend():
    friend_id = str(request.data)[3:-2]
    friend = getUserById(int(friend_id))
    Friends().delete(current_user.email, friend.email)
    return "1"


def getEventsFileName(event_date):
    HOME_DIR = os.getcwd() + "/bark2meet/databases/eventsHistory/"
    return HOME_DIR + event_date + ".json"


def getUserWalksByDate(event_date):
    file_path = getEventsFileName(event_date)
    if os.path.exists(file_path):
        result = []
        file = open(file_path, "r")
        data = json.load(file)
        file.close()
        all_events = data["events"]
        for event in all_events:
            if current_user.email in event["joined"]:
                result.append(event)
        return result
    else:
        return []


def generateWalks():
    today = date.today()
    yesterday = today - timedelta(1)
    tomorrow = today + timedelta(1)
    yesterday_walks = getUserWalksByDate(yesterday.isoformat())
    today_walks = getUserWalksByDate(today.isoformat())
    tomorrow_walks = getUserWalksByDate(tomorrow.isoformat())
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


@app.route("/my_walks", methods=['GET', 'POST'])
@login_required
def my_walks():
    # todo: implement
    search_form = SearchForm()
    # walk_filter = search_form.search_filter.data
    # past_walks = getUserWalksByDate("2021-06-02")
    # future_walks = getUserWalksByDate("2021-06-07")
    future_walks, past_walks = generateWalks()
    return render_template("my_walks.html", title="My Walks", walks=future_walks + past_walks,
                           form=search_form)


@app.route("/profile/<user_id>", methods=['GET', 'POST'])
def get_profile(user_id):
    user = getUserById(user_id)
    return render_template("profile.html", title="Profile", user=user)


# ------ WEBPAGES BACKEND END ------

# ------ GET LOCATIONS START ------


FRIENDS = 1


@app.route("/api/locations", methods=['GET', 'POST'])
@login_required
def get_locations():
    if request.method == 'GET':
        all_locations = []
        get_all_locations(all_locations)
        return jsonify(all_locations)


def get_private_users(users_in_area):
    emails = set()
    for user in users_in_area:
        if user.status == PRIVATE:
            emails.add(user.email)
    return emails


def get_all_locations(all_locations):
    users_in_area = area.getUsersInRadius(current_user, current_user.radius_view)
    connected_in_area = {user for user in users_in_area if user.email in users.keys()}
    if current_user not in connected_in_area:
        connected_in_area.add(current_user)

    private_users = get_private_users(users_in_area)

    all_friends_of_user = Friends().get_all_friends_of(current_user.email)
    all_users_with_friend_status = {user.email for user in connected_in_area if
                                    user.status == FRIENDS and user.email not in all_friends_of_user}
    if current_user.email == "o@o.com":
        # print("connected users", [user for user in users.keys()])
        # print("users_in_area", [user.email for user in users_in_area])
        # print("connected_in_area", [user.email for user in connected_in_area])
        pass

    for user in connected_in_area:
        user_info = {
            "privacy": "green",
            "full_name": user.full_name,
            "pos_x": user.pos_x,
            "pos_y": user.pos_y,
            "image": OPEN_IMG,
            "user_image": user.user_img.replace('\\', '/'),
            "dog_image": user.dog_img.replace('\\', '/'),
            "gender": user.gender,
            "dog_name": user.dog_name,
            "dog_age": user.dog_age,
            "dog_gender": user.dog_gender,
            "dog_breed": user.dog_breed,
            "id": user.id
        }

        if user.email in all_users_with_friend_status:
            user_info["privacy"] = "orange"
            user_info["image"] = FRIENDS_IMG
        elif user.email in private_users:
            user_info["privacy"] = "red"
            user_info["image"] = PRIVATE_IMG
            user_info["user_image"] = ""
            user_info["dog_image"] = ""
            user_info["gender"] = ""
            user_info["dog_age"] = ""
        elif user.email == current_user.email:
            # user_info["privacy"] = "me"
            user_info["image"] = "static/userPic.png"

        all_locations.append(user_info)


# ------ GET LOCATIONS END ------

# ------ GET MAINTAIN START ------

# s = sched.scheduler(time.time, time.sleep)
# TWELVE_HOURS = 43200


# def scheduled_func(arg1):
# do your stuff
# s.enter(5, 1, scheduled_func, (arg1, ))


# s.enter(5, 1, scheduled_func, (s, ))
# s.run()


# ------ GET MAINTAIN END ------


# ------ DEBUG FUNCTIONS ------ #

def debug_friends():
    try:
        Friends.add("d@d.com", "o@o.com")
    except:
        print("this friend has been added before")


@app.route("/temp", methods=['GET', 'POST'])
def temp():
    return render_template("my_walks.html")
