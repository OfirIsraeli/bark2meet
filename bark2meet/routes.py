import json
import os
from datetime import datetime

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

# ------ GLOBAL DATA START------

PRIVATE = 1
NO_PRIVATE = 0
OPEN_IMG = "static/GPSgreen.png"
FRIENDS_IMG = "static/GPSorange.png"
PRIVATE_IMG = "static/GPSred.png"

OPEN = "green"
FRIENDS = "orange"
HIDDEN = "red"

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
        sender = getUserByEmail(payload['email'])
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
            if all_notifications[i]['issue_time'] > current_user.date_last_session.isoformat(' ',
                                                                                             'seconds'):
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
@app.route("/index")
def landing_page():
    return render_template('index.html')


@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    prev_update_time = current_user.date_last_update.isoformat(' ', 'seconds')
    update_user_location()

    current_area_x, current_area_y = area.update(current_user)
    current_user.update_user_area(current_area_x, current_area_y)

    users_in_area = area.getUsersInRadius(current_user, current_user.radius_view)
    all_users_in_area_except_me = [user for user in users_in_area if
                                   user.email != current_user.email]
    new_notifications, old_notifications = get_notifications(prev_update_time)
    return render_template('home.html', title="Home", all_users=all_users_in_area_except_me,
                           users_in_area=users_in_area, new_notifications=new_notifications,
                           old_notifications=old_notifications)


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
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationUserForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        gender = request.form['gender']
        user = User(full_name=form.full_name.data, email=form.email.data,
                    password=hashed_password, gender=gender)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        current_user.update_sing_level()
        return redirect(url_for('register_dog'))
    return render_template('register_user.html', title='Register', form=form)


@app.route("/register_dog", methods=['GET', 'POST'])
def register_dog():
    if current_user.is_authenticated and current_user.sing_up_level != REGISTER_DOG_LEVEL:
        return redirect(url_for('home'))
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
        return redirect(url_for('home'))

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
        flash('Your account has been created! You are now able to log in', 'success')
        current_user.update_sing_level()
        return redirect(url_for('home'))
    return render_template('upload.html', form=form)


# ------ IMG UPLOAD END ------


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
            flash('Login Unsuccessful. Please check email and password', 'login_error')
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
        get_all_locations(all_locations)
        return jsonify(all_locations)


def get_private_users():
    emails = set()
    for user in area.getUsersInRadius(current_user, current_user.radius_view):
        if user.status == PRIVATE:
            emails.add(user.email)
    return emails


def get_all_locations(all_locations):
    users_in_area = area.getUsersInRadius(current_user, current_user.radius_view)
    #private_users = get_private_users()
    #friends = Friends().get_all(current_user)
    for user in users_in_area:
        user_info = {
            "privacy": OPEN,
            "username": user.full_name,
            "pos_x": user.pos_x,
            "pos_y": user.pos_y,
            "image": OPEN_IMG,
            "user_image": user.user_img,
            "dog_image": user.dog_img,
            "gender": user.gender,
            "dog_name": user.dog_name,
            "dog_age": user.dog_age,
        }
        # todo: need to be else if and last one after debug
        #if user.email == current_user.email:
            #user_info["image"] = "static/userPic.png"
        all_locations.append(user_info)
        return
        if user.email in friends:
            user_info["privacy"] = FRIENDS
            user_info["image"] = FRIENDS_IMG
        elif user.email in private_users:
            user_info["privacy"] = HIDDEN
            user_info["image"] = PRIVATE_IMG
            user_info["user_image"] = ""
            user_info["dog_image"] = ""
            user_info["gender"] = ""
            user_info["dog_age"] = ""

        all_locations.append(user_info)

# ------ GET LOCATIONS END ------


############ DEBUG FUNCTIONS ################

def debug_friends():
    try:
        Friends.add("d@d.com", "o@o.com")
    except:
        print("this friend has been added before")