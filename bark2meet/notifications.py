import os
from datetime import datetime
import json

# types:
FRIEND_WALK = 0
NEW_MSG = 1
NEW_INVITE = 2
NEW_FRIEND_REQUEST = 3
FRIEND_REQUEST_APPROVED = 4
WALK_INVITATION_APPROVED = 5
NEW_USER_JOINED_WALK = 6


##
# RUSH_HOUR = 1
# NEW_JOIN_WALK_INVITE = 2
# USER_WANTS_TO_JOIN_WALK = 3
##


class Notification:

    def create_notification(self, email, title, msg, pos_x, pos_y, notification_type, noti_from="",
                            img=""):
        self.email = email
        self.title = title
        self.msg = msg
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.type = notification_type
        self.notification_from = noti_from
        self.img = img
        self.issue_time = datetime.now().isoformat(' ', 'seconds')  # datetime.utcnow

        self.write_notification_in_history()

    def getNotificationsFileName(self, email):
        HOME_DIR = os.getcwd() + "/bark2meet/databases/notificationsHistory/"
        return HOME_DIR + email + ".json"

    def create_walk_invitation_notification(self, current_user, user_dest, event_id):
        title = "New event invitation"
        msg = current_user.full_name + " and " + current_user.dog_name + " has sent you an invitation to join their" \
                                                                         " new event!"
        invite_address = "invite_" + str(event_id)
        self.create_notification(user_dest, title, msg, current_user.pos_x, current_user.pos_y,
                                 NEW_INVITE,
                                 invite_address, current_user.user_img)

    def write_notification_in_history(self):
        msg_json = {
            "email": self.email,
            "title": self.title,
            "msg": self.msg,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y,
            "type": self.type,
            "from": self.notification_from,
            "issue_time": datetime.now().isoformat(' ', 'seconds'),
            "image": self.img
        }

        file_path = self.getNotificationsFileName(self.email)
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

    def delete_notifications(self, email, type, notification_from):
        file_path = self.getNotificationsFileName(email)
        all_notifications = {"notifications": []}
        notifications_after_delete = {"notifications": []}
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                all_notifications = json.load(file)

        for noti in all_notifications["notifications"]:
            if noti["type"] == type and noti["from"] == notification_from:
                continue
            else:
                notifications_after_delete["notifications"].append(noti)

        # write the changes to the file
        with open(file_path, "w") as file:
            data = {"notifications": notifications_after_delete["notifications"]}
            json.dump(data, file, default=str, indent=4)

    def check_if_there_is_noti_from(self, email, type, notification_from):
        file_path = self.getNotificationsFileName(email)
        all_notifications = None
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                all_notifications = json.load(file)

        if not all_notifications:
            return False

        for noti in all_notifications["notifications"]:
            if noti["from"] == notification_from and noti["type"] == type:
                return True
        return False
