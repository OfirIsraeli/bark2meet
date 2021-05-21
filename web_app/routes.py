import json
import os
from datetime import datetime

from flask import render_template, url_for, flash, redirect, request, jsonify
from web_app import app, db, bcrypt
from web_app.forms import RegistrationForm, LoginForm
from web_app.models import User, Friends
from web_app.areas import area
from flask_login import login_user, current_user, logout_user, login_required
from web_app import socketio
from flask_socketio import emit
from cryptography.fernet import Fernet
from werkzeug.utils import secure_filename
from web_app.notifications import Notification, FRIEND_WALK

# ------ GLOBAL DATA START------

PRIVATE = 1
NO_PRIVATE = 0
OPEN_IMG = ""
FRIENDS_IMG = ""
PRIVATE_IMG = ""

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

users = {}
all_users = User.query.all()
fernet_with_key = Fernet(b"8eDa1w9-C8THy0nz_dpeoBS0BX_UAf5D_oIhRd8nlgA=")


# ------ GLOBAL DATA END------


# ------ MESSAGING FUNCTIONS ------
def getUserByEmail(email):
    for user in all_users:
        if user.email == email:
            return user


@socketio.on('connect')
def registerConnection():
    print(current_user.email, "has connected")


@socketio.on('disconnect')
def registerConnection():
    print(current_user.email, "has disconnected")


@socketio.on('email', namespace='/private')
def receive_user_email():
    users[current_user.email] = request.sid


@socketio.on('friend-walk', namespace='/private')
def register_walk():
    # friends_around = area.getFriendsInRadius(current_user, 3000)
    for recipient in users:
        if recipient != current_user.email:
            # recipient_user = getUserByEmail(recipient)
            recipient_session_id = users[recipient]
            emit('new_friend_walk', {"username": current_user.username, "issue_time": datetime.now().isoformat(' ', 'seconds')}, room=recipient_session_id)
            Notification(recipient, "", current_user.username + " is on the go!", current_user.pos_x, current_user.pos_y, FRIEND_WALK)

    for user in all_users:
        if user.email != current_user.email and user.email not in users:
            Notification(user.email, "", current_user.username + " was on the go!", current_user.pos_x, current_user.pos_y, FRIEND_WALK)


@socketio.on('private_message', namespace='/private')
def private_message(payload):
    message = payload['message']
    try:
        sender = getUserByEmail(payload['email'])
        sender_session_id = users[payload['email']]
        emit('new_private_message', {"msg": message, "username": current_user.username, "email": current_user.email,
                                     "send_time": datetime.now().isoformat(' ', 'seconds')},
             room=sender_session_id)
        writeMessageInHistory(current_user.email, payload['email'], message)
    except KeyError:  # so user is not logged in right now
        writeMessageInHistory(current_user.email, payload['email'], message)


# ------ MESSAGING FUNCTIONS END ------

# ------ CHAT HISTORY ------
def getHistoryFileName(sender, recipient):
    HOME_DIR = os.getcwd() + "/web_app/databases/chatHistory/"
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
    HOME_DIR = os.getcwd() + "/web_app/databases/notificationsHistory/"
    return HOME_DIR + current_user.email + ".json"


def get_notifications(prev_update_time):
    file_path = getNotificationsFileName()
    if os.path.exists(file_path):
        file = open(file_path, "r")
        data = json.load(file)
        file.close()
        all_notifications = data["notifications"][::-1]
        new_notifications = []
        end = len(all_notifications)
        for i in range(len(all_notifications)):
            # print(all_notifications[i]['issue_time'],  current_user.date_last_session)
            print(i)
            if all_notifications[i]['issue_time'] > current_user.date_last_session.isoformat(' ', 'seconds'):
                new_notifications.append(all_notifications[i])
            else:
                end = i
                break
        print(new_notifications)

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
@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    prev_update_time = current_user.date_last_update.isoformat(' ', 'seconds')
    update_user_location()

    current_area_x, current_area_y = area.update(current_user)
    current_user.update_user_area(current_area_x, current_area_y)

    users_in_area = area.getUsersInRadius(current_user, 1000)
    all_users_in_area_except_me = [user for user in users_in_area if user.email != current_user.email]
    new_notifications, old_notifications = get_notifications(prev_update_time)
    return render_template('home.html', title="Home", all_users=all_users_in_area_except_me,
                           users_in_area=users_in_area, new_notifications=new_notifications, old_notifications=old_notifications)


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


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/profile")
@login_required
def get_user_details():
    return render_template('profile.html', user=current_user)


# ------ WEBPAGES BACKEND END ------

# ------ GET LOCATIONS START ------


@app.route("/api/locations", methods=['GET', 'POST'])
@login_required
def get_locations():
    if request.method == 'GET':
        all_locations = []
        # get_all_locations(all_locations)
        return jsonify(all_locations)


def get_private_users():
    emails = set()
    for user in area.getUsersInRadius(current_user, 3000):
        if user.status == PRIVATE:
            emails.add(user.email)
    return emails


def get_all_locations(all_locations):
    users_in_area = area.getUsersInRadius(current_user, 3000)
    private_users = get_private_users()
    friends = Friends().get_all(current_user)
    for user in users_in_area:
        user_info = {
            "username": user.username,
            "pos_x": user.pos_x,
            "pos_y": user.pos_y,
            "image": OPEN_IMG,
            "user_image": user.image,
            "dog_image": user.image,
        }
        if user.email in friends:
            user_info["image"] = FRIENDS_IMG
        elif user.email in private_users:
            user_info["image"] = PRIVATE_IMG
            user_info["user_image"] = PRIVATE_IMG
            user_info["dog_image"] = PRIVATE_IMG

        all_locations.append(user_info)


# ------ GET LOCATIONS END ------


# ------ IMG UPLOAD START ------

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/img_upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.update_img(filename)
            return redirect(url_for('uploaded_file', filename=filename))

# ------ IMG UPLOAD END ------
