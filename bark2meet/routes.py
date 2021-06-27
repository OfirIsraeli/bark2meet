import json
import os
from flask import render_template, url_for, flash, redirect, request, jsonify
from bark2meet import app, db, bcrypt
from bark2meet.forms import *
from bark2meet.models import User, Friends, START_WALK, OPEN, PRIVATE, FRIENDS
from flask_login import login_user, current_user, logout_user, login_required
from bark2meet import socketio
from flask_socketio import emit
from cryptography.fernet import Fernet
from werkzeug.utils import secure_filename
from bark2meet.notifications import Notification, FRIEND_WALK, FRIEND_REQUEST_APPROVED, WALK_INVITATION_APPROVED, \
    NEW_USER_JOINED_WALK, NEW_FRIEND_REQUEST, NEW_INVITE
from bark2meet.event import Event
from datetime import timedelta

# ------ GLOBAL DATA START------


OPEN_IMG = "static/GPSgreen.png"
FRIENDS_IMG = "static/GPSorange.png"
PRIVATE_IMG = "static/GPSred.png"

REGISTER_DOG_LEVEL = 1
IMG_LEVEL = 2

DEFAULT_IMG = "static/default-account-img.png"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

fernet_with_key = Fernet(b"8eDa1w9-C8THy0nz_dpeoBS0BX_UAf5D_oIhRd8nlgA=")



# ------ GLOBAL DATA END------


# ------ MESSAGING FUNCTIONS ------
def getUserByEmail(email):
    return User.query.filter_by(email=email).first()


def getUserById(user_id):
    return User.query.filter_by(id=user_id).first()


def get_all_connected_users():
    return User.query.filter_by(is_online=True).all()
    # all_connected_users = []
    # for users_email in connected_users:
    #     user = getUserByEmail(users_email)
    #     all_connected_users.append(user)
    #
    # return all_connected_users


@socketio.on('connect')
@socketio.on('online')
def registerConnection():
    # connected_users[current_user.email] = request.sid
    current_user.update_is_online(True)
    print(current_user.email, "has connected")


# @socketio.on('disconnect')
@socketio.on('offline')
def registerDisconnection():
    # del connected_users[current_user.email]
    current_user.update_is_online(False)
    print(current_user.email, "has disconnected")


@socketio.on('email', namespace='/private')
def receive_user_email():
    # connected_users[current_user.email] = request.sid
    current_user.update_session(request.sid)


#
# @socketio.on('friend-walk', namespace='/private')
# def register_walk():
#     all_users = User.query.all()
#     # friends_around = area.getFriendsInRadius(current_user, current_user.radius_view)
#     connected_users = get_all_connected_users()
#     for recipient in connected_users:
#         if recipient != current_user.email:
#             # recipient_user = getUserByEmail(recipient)
#             recipient_session_id = connected_users[recipient]
#             emit('new_friend_walk', {"username": current_user.full_name,
#                                      "issue_time": datetime.now().isoformat(' ', 'seconds')},
#                  room=recipient_session_id)
#             Notification().create_notification(recipient, "", current_user.full_name + " is on the go!",
#                                                current_user.pos_x, current_user.pos_y, FRIEND_WALK)
#
#     for user in all_users:
#         if user.email != current_user.email and user.email not in connected_users:
#             Notification().create_notification(user.email, "", current_user.full_name + " was on the go!",
#                                                current_user.pos_x, current_user.pos_y, FRIEND_WALK)


@socketio.on('private_message', namespace='/private')
def private_message(payload):
    # message = payload['message']
    # try:
    #     # sender = getUserByEmail(payload['email'])
    #     sender_session_id = connected_users[payload['email']]
    #     emit('new_private_message',
    #          {"msg": message, "username": current_user.full_name, "email": current_user.email,
    #           "send_time": datetime.now().isoformat(' ', 'seconds')},
    #          room=sender_session_id)
    #     writeMessageInHistory(current_user.email, payload['email'], message)
    # except KeyError:  # so user is not logged in right now
    #     writeMessageInHistory(current_user.email, payload['email'], message)
    pass


# ------ MESSAGING FUNCTIONS END ------

# ------ CHAT HISTORY ------
# def getHistoryFileName(sender, recipient):
#     HOME_DIR = os.getcwd() + "/bark2meet/databases/chatHistory/"
#     if sender < recipient:
#         return HOME_DIR + sender + "&" + recipient + ".json"
#
#     return HOME_DIR + recipient + "&" + sender + ".json"
#
#
# def writeMessageInHistory(sender, recipient, msg):
#     encMessage = fernet_with_key.encrypt(msg.encode())
#     msg_json = {
#         "msg": encMessage.decode(),
#         "sender": sender,
#         "send_time": datetime.now().isoformat(' ', 'seconds')
#     }
#
#     file_path = getHistoryFileName(sender, recipient)
#     if os.path.exists(file_path):
#         file = open(file_path, "r+")
#         data = json.load(file)
#         data["chat"].append(msg_json)
#         file.seek(0)
#         json.dump(data, file, default=str, indent=4)
#     else:
#         file = open(file_path, "w")
#         data = {"chat": [msg_json]}
#         json.dump(data, file, default=str, indent=4)
#     file.close()
#
#
# def getChatHistory(sender, recipient):
#     file_path = getHistoryFileName(sender, recipient)
#     if os.path.exists(file_path):
#         file = open(file_path, "r")
#         data = json.load(file)
#         file.close()
#         return data
#     else:
#         return {"chat": []}
#
#
# @app.route("/api/history/<sender>", methods=['GET', 'POST'])
# def getHistory(sender):
#     if request.method == 'GET':
#         history = getChatHistory(current_user.email, sender)
#         for chat in history["chat"]:
#             chat["msg"] = fernet_with_key.decrypt(chat["msg"].encode()).decode()
#         return jsonify(history)


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


@app.route("/notifications")
@login_required
def notifications_page():
    form = SearchForm()
    new, old = get_notifications()
    print(old)
    current_user.update_date_last_session(datetime.now())
    return render_template('notifications.html', title="Notifications", form=form, status=current_user.status, old_notifications=old[:20], new_notifications=new)


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
    return render_template('index.html', is_login=current_user.is_authenticated)


@app.route("/map", methods=['GET', 'POST'])
@login_required
def map():
    if current_user.sing_up_level == REGISTER_DOG_LEVEL:
        return redirect(url_for('register_dog'))

    update_user_area(current_user)
    connected_users = get_all_connected_users()
    for user in connected_users:
        update_user_area(user)

    return render_template('map.html', title="Map", status=current_user.status)


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
        return redirect(url_for('welcome_screen'))
    return render_template('upload.html', form=form)


@app.route("/welcome_screen", methods=['GET', 'POST'])
def welcome_screen():
    return render_template('welcome.html', user=current_user)

# ------ IMG UPLOAD END ------


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('map'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            user.update_is_online(True)
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

    return render_template('my_profile.html', status=current_user.status, user=current_user, age=age)


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


@app.route("/event", methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        event_id = add_to_event_count()
        privacy = request.form['privacy']
        date = request.form['date']
        event = Event().create_event(email=current_user.email, title=form.title.data,
                                     privacy=privacy,
                                     location=form.location.data, time=form.time.data, date=date,
                                     id=event_id)

        # if form.invite.data:
        #     Friends().get_all_friends_of(current_user.email)

        flash('The event has been created successfully', 'event_success')
        # return redirect(url_for('home'))
        return redirect(url_for('invite_friends', event_id=event_id))

    return render_template('create_event.html',status=current_user.status, form=form, title="Create Event")


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
                           my_email=current_user.email, users_imgs=users_imgs, form=form,
                           status=current_user.status)


@app.route("/join_to_event", methods=['GET', 'POST'])
@login_required
def join_event_by_id():
    event_id = str(request.data)[2:-1]
    event = add_user_to_event(event_id, True, current_user.email)
    # Event().join_to_event(int(event_id), [current_user.email])
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
    print("before:", current_user.status)
    print("changing status to: ", status)
    current_user.change_status(int(status))
    print("after:", current_user.status)
    return status


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


@app.route("/invite_friends/<event_id>", methods=['GET', 'POST'])
@login_required
def invite_friends(event_id):
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
                           form=form, event_id=event_id)


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
def join_event():
    req = str(request.data)[3:-2].split(",")
    should_accept = req[0]
    event_id = req[1][1:-1]

    if should_accept == "true":

        event = add_user_to_event(event_id, True, current_user.email)

        Notification().delete_notifications(current_user.email, NEW_INVITE, event["id"])
        Notification().create_notification(event["creator"],
                                           "Invitation approved",
                                           current_user.full_name + " has accepted your walk invitation!",
                                           current_user.pos_x,
                                           current_user.pos_y,
                                           WALK_INVITATION_APPROVED,
                                           current_user.email, current_user.user_img)

    else:
        event = add_user_to_event(event_id, False, current_user.email)
        Notification().delete_notifications(current_user.email, NEW_INVITE, event["id"])
    return "1"


@app.route("/invite_this_friend", methods=['GET', 'POST'])
@login_required
def create_notification_to_friend():
    friend_id, event_id = str(request.data)[3:-2].split(",")
    print("id's are:", friend_id[1:-1], event_id)
    friend = getUserById(int(friend_id[1:-1]))
    Notification().create_walk_invitation_notification(current_user, friend.email, event_id)

    return "1"


@app.route("/friend_request_approve", methods=['GET', 'POST'])
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
        print(requester)
        not_friend = getUserByEmail(requester)
        # todo: okay?
        Notification().delete_notifications(not_friend.email, NEW_FRIEND_REQUEST, current_user.email)
        Notification().delete_notifications(current_user.email, NEW_FRIEND_REQUEST, not_friend.email)
    return "1"


@app.route("/send_friend_request", methods=['GET', 'POST'])
@login_required
def send_friend_request():
    friend_id = str(request.data)[3:-2]
    print(request.data, "asad")
    friend = getUserById(int(friend_id))
    Notification().create_notification(friend.email,
                                       "New friend request",
                                       "You got new friend request from: " + current_user.full_name,
                                       friend.pos_x,
                                       friend.pos_y,
                                       NEW_FRIEND_REQUEST,
                                       current_user.email, current_user.user_img)
    # connected_users = get_all_connected_users()
    # if friend.email not in connected_users:
    #     return
    # recipient_session_id = connected_users[friend.email]
    # emit('new_friend_request', {"username": current_user.full_name,
    # "email": current_user.email,
    # "issue_time": datetime.now().isoformat(' ', 'seconds')},room=recipient_session_id)
    return "1"


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
                users_images = []
                for joined in event["joined"][:3]:
                    joined_user = getUserByEmail(joined)
                    users_images.append(joined_user.user_img)
                event['users_images'] = users_images
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
            # for joined in event["joined"][:3]:
            #     joined_user = getUserByEmail(joined)
            #     users_images.append(joined_user.user_img)
            event['users_images'] = users_images
            future_today.append(event)
    print(events)
    return future_today


@app.route("/my_walks", methods=['GET', 'POST'])
@login_required
def my_walks():
    search_form = SearchForm()
    future_walks, past_walks = generateWalks()
    walks_in_area = get_walks_in_area_today()
    return render_template("my_walks.html", title="My Walks", walks=future_walks, past_walks=past_walks,
                           form=search_form, status=current_user.status, walks_in_area=walks_in_area,
                           my_email=current_user.email)


def get_all_future_user_events(user):
    start_date = date.today()
    file_path = os.getcwd() + "/bark2meet/databases/eventsHistory/" + start_date.isoformat() + ".json"
    one_day = timedelta(days=1)
    result = []
    while os.path.exists(file_path):
        with open(file_path, "r") as file:
            data = json.load(file)

        for event in data["events"]:
            if user.email in event["joined"]:
                users_images = []
                for joined in event["joined"][:3]:
                    joined_user = getUserByEmail(joined)
                    users_images.append(joined_user.user_img)
                event['users_images'] = users_images
                result.append(event)
        start_date += one_day
        file_path = os.getcwd() + "/bark2meet/databases/eventsHistory/" + start_date.isoformat() + ".json"
    return result


@app.route("/profile/<user_id>", methods=['GET', 'POST'])
@login_required
def get_profile(user_id):
    user = getUserById(user_id)
    future_events = get_all_future_user_events(user)
    is_friend = user.email in Friends().get_all_friends_of(current_user.email)
    print(is_friend)
    today = date.today()
    age = today.year - current_user.birth_date.year - ((today.month, today.day) < (current_user.birth_date.month,
                                                                                   current_user.birth_date.day))
    return render_template("other_profile.html", title=current_user.full_name+"'s Profile", user=user, status=current_user.status,
                           future_events=future_events, is_friend=is_friend, age=age, current_user=current_user)


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
    print(friends)
    for email in event["joined"]:
        if email == current_user.email:
            continue
        user = getUserByEmail(email)
        participants.append({"user": user, "is_friend": user.email in friends})
    if current_user.email in event['joined']:
        participants = [{"user": current_user, "is_friend": False}] + participants
    return render_template("event_details.html", title="Event Details", event=event, participants=participants, day=day,
                           month=month, year=year, current_user_email=current_user.email)


# ------ WEBPAGES BACKEND END ------

# ------ GET LOCATIONS START ------


@app.route("/api/locations", methods=['GET', 'POST'])
@login_required
def get_locations():
    if request.method == 'GET':
        all_locations = []
        get_all_locations(all_locations)
        return jsonify(all_locations)


def map_privacy_to_string(privacy_int, is_friend, user):
    if user.email == current_user.email:
        return "me"
    if privacy_int == PRIVATE:
        return "red"
    if privacy_int == START_WALK:
        return "notWalking"
    if privacy_int == OPEN:
        return "green"

    if privacy_int == FRIENDS:
        if is_friend:
            return "green"
        else:
            return "orange"
    raise Exception("PRIVACY MODE ERROR", privacy_int)


def map_image_to_user(user, is_friend):
    if user.email == current_user.email:
        return "static/userPic.png"
    if user.status == PRIVATE:
        return PRIVATE_IMG
    if user.status == FRIENDS:
        if is_friend:
            return OPEN_IMG
        else:
            return FRIENDS_IMG
    return OPEN_IMG


def get_all_locations(all_locations):
    #print(current_user.email)
    #print(User.query.all())
    connected_in_area = User.query.filter_by(current_area_x=current_user.current_area_x,
                                             current_area_y=current_user.current_area_y, is_online=True).all()
    #print(connected_in_area)

    # TODO: check if necessary
    if current_user not in connected_in_area:
        connected_in_area.append(current_user)

    all_friends_of_user = Friends().get_all_friends_of(current_user.email)

    for user in connected_in_area:
        today = date.today()
        age = today.year - user.birth_date.year - ((today.month, today.day) < (user.birth_date.month,
                                                                               user.birth_date.day))

        is_friend = user.email in all_friends_of_user
        privacy = map_privacy_to_string(user.status, is_friend, user)
        if privacy == "notWalking":
            print("skipping", user.email)
            continue
        user_info = {
            "privacy": privacy,
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
            "is_friend": is_friend
        }
        print("current user:", current_user.email, "\tstatus of:", user_info["full_name"], user.status, "and:",
              map_privacy_to_string(user.status, is_friend, user))
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


X_POS = 0
Y_POS = 1

JERUSALEM = (31.771959, 35.217018)
TEL_AVIV = (32.109333, 34.855499)
MODIIN = (31.89670800658577, 35.007197003536874)
BEER_SHEVA = (31.249006188313423, 34.78929831233399)
# todo: add haifa and more cities

Areas_dict = {
    JERUSALEM,
    TEL_AVIV,
    MODIIN,
    BEER_SHEVA
}


def update_user_area(user):
    min_dist = 999999999999
    curr_x_min = 999999999999
    curr_y_min = 999999999999
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
