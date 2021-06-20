import os
from datetime import datetime
import json

# types:
FRIEND_WALK = 0
NEW_MSG = 1
NEW_INVITE = 2


class Notification:
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
        HOME_DIR = os.getcwd() + "/bark2meet/databases/notificationsHistory/"
        return HOME_DIR + self.email + ".json"

    def write_notification_in_history(self):
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
            with open(file_path, "r+") as file:
                data = json.load(file)
                data["notifications"].append(msg_json)
                file.seek(0)
                json.dump(data, file, default=str, indent=4)
        else:
            with open(file_path, "w") as file:
                data = {"notifications": [msg_json]}
                json.dump(data, file, default=str, indent=4)

