import os
from datetime import datetime

from flask import jsonify

from web_app import db
import json

# types:
FRIEND_WALK = 0
NEW_MSG = 1


class Notification:
    # email = db.Column(db.String(120), unique=True, nullable=False)
    # title = db.Column(db.String(60), nullable=True)
    # msg = db.Column(db.String(60), nullable=False)
    # # if position is default, the notification is not location based
    # # (could be message for example but not a friend walk)
    # pos_x = db.Column(db.Integer, nullable=False, default=31.910664)
    # pos_y = db.Column(db.Integer, nullable=False, default=34.896716)
    # type = db.Column(db.Integer, nullable=False)
    # issue_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, email, title, msg, pos_x, pos_y, notification_type):
        self.email = email
        self.title = title
        self.msg = msg
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.type = notification_type
        self.issue_time = datetime.now().isoformat(' ', 'seconds')  # datetime.utcnow
        self.write_notification_in_history()

    def getNotificationsFileName(self):
        HOME_DIR = os.getcwd() + "/web_app/notificationsHistory/"
        return HOME_DIR + self.email + ".json"

    def write_notification_in_history(self):
        print("here")
        msg_json = {
            "email": self.email,
            "title": self.title,
            "msg": self.msg,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "type": self.type,
            "issue_time": datetime.now().isoformat(' ', 'seconds')
        }

        file_path = self.getNotificationsFileName()
        if os.path.exists(file_path):
            file = open(file_path, "r+")
            data = json.load(file)
            data["notifications"].append(msg_json)
            file.seek(0)
            json.dump(data, file, default=str, indent=4)
        else:
            print("correct")

            file = open(file_path, "w")
            data = {"notifications": [msg_json]}
            json.dump(data, file, default=str, indent=4)
        file.close()
