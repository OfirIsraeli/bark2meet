import json
import os
from datetime import datetime

from flask import render_template, url_for, flash, redirect, request, jsonify
from web_app import app, db, bcrypt
from web_app.forms import RegistrationForm, LoginForm
from web_app.models import User
from web_app.areas import area
from flask_login import login_user, current_user, logout_user, login_required
from web_app import socketio
from flask_socketio import emit


class SendMessageToSelfError:
    pass


# ------ MESSAGING FUNCTIONS ------


users = {}
allUsers = db.session.query(User).all()


@socketio.on('connect')
def registerConnection():
    print(current_user.username, "has connected")


@socketio.on('disconnect')
def registerConnection():
    print(current_user.username, "has disconnected")


@socketio.on('username', namespace='/private')
def receive_username():
    users[current_user.username] = request.sid


@socketio.on('private_message', namespace='/private')
def private_message(payload):
    message = payload['message']
    try:
        recipient_session_id = users[payload['username']]
        emit('new_private_message', {"msg": message, "username": current_user.username,
                                     "send_time": datetime.now().isoformat(' ', 'seconds')}, room=recipient_session_id)
        writeMessageInHistory(current_user.username, payload['username'], message)
    except KeyError:  # so user is not logged in right now
        writeMessageInHistory(current_user.username, payload['username'], message)


# ------ MESSAGING FUNCTIONS END ------
# ------ CHAT HISTORY ------
def getHistoryFileName(sender, recipient):
    HOME_DIR = os.getcwd() + "/web_app/chatHistory/"
    if sender < recipient:
        return HOME_DIR + sender + "&" + recipient + ".json"

    return HOME_DIR + recipient + "&" + sender + ".json"


def writeMessageInHistory(sender, recipient, msg):
    msg_json = {
        "msg": msg,
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
        return data
    else:
        print("NO HISTORY")
        return {"chat": []}


@app.route("/api/history/<sender>", methods=['GET', 'POST'])
def getHistory(sender):
    if request.method == 'GET':
        history = getChatHistory(current_user.username, sender)
        return jsonify(history)

# ------ CHAT HISTORY END ------


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
    information = str(request.data)[3:-2]
    coordinates = information.split(',')

    if coordinates[0] and coordinates[1]:
        coordinate_x = float(coordinates[0])
        coordinate_y = float(coordinates[1])
        current_user.update_user_location(coordinate_x, coordinate_y)

    current_area_x, current_area_y = area.update(current_user)
    current_user.update_user_area(current_area_x, current_area_y)

    users_in_area = area.getUsersInRadius(current_user, 1000)
    allUsersExceptMe = [user for user in allUsers if user.email != current_user.email]
    return render_template('home.html', title="Home", all_users=allUsersExceptMe, users_in_area=users_in_area)


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
def logout():
    logout_user()
    return redirect(url_for('home'))
