import json
import os
from datetime import datetime
from bark2meet.models import Friends

# TODO: add joined users' images
class Event:
    def create_event(self, email, title, privacy, location, time, date, id):
        self.time = time
        self.date = date
        self.location = location
        self.title = title
        self.email = email
        self.privacy = privacy
        self.id = id

        self.write_event()

    def getEventFileName(self, date):
        HOME_DIR = os.getcwd() + "/bark2meet/databases/eventsHistory/"
        return HOME_DIR + date + ".json"

    def write_event(self):
        event_json = {
            "id": self.id,
            "privacy": self.privacy,
            "creator": self.email,
            "title": self.title,
            "joined": [self.email],
            "location": self.location,
            "time": self.time,
        }

        file_path = self.getEventFileName(self.date)
        if os.path.exists(file_path):
            with open(file_path, "r+") as file:
                data = json.load(file)
                data["events"].append(event_json)
                file.seek(0)
                json.dump(data, file, default=str, indent=4)
        else:
            with open(file_path, "w") as file:
                data = {"events": [event_json]}
                json.dump(data, file, default=str, indent=4)

    def get_today_events(self, user_email):
        all_events = []
        data = ""
        time = datetime.today().strftime('%Y-%m-%d')
        file_path = self.getEventFileName(time)
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                data = json.load(file)

            for event in data["events"]:
                friends = Friends().get_all_friends_of(event["creator"])
                if event["privacy"] == "orange" and user_email in friends:
                    all_events.append(event)
                elif event["privacy"] == "green":
                    all_events.append(event)

            return all_events
        else:
            return []

    def get_event_by_id(self, id):
        todayEvents = {"events": []}
        time = datetime.today().strftime('%Y-%m-%d')
        file_path = self.getEventFileName(time)
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                todayEvents = json.load(file)

        for event in todayEvents["events"]:
            if event["id"] == id:
                return event
        return []

    def join_to_event(self, id, emails):
        self.write_changes_to_joined_event(id, emails, to_join=True)

    def exit_from_event(self, id, emails):
        self.write_changes_to_joined_event(id, emails, to_join=False)

    def get_all_joined(self, id):
        event = self.get_event_by_id(id)
        return event["joined"]

    def write_changes_to_joined_event(self, id, emails, to_join):
        todayEvents = {"events": []}
        time = datetime.today().strftime('%Y-%m-%d')
        file_path = self.getEventFileName(time)
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                todayEvents = json.load(file)

        for event in todayEvents["events"]:
            if event["id"] == id:
                for email in emails:
                    if to_join:
                        if email not in event["joined"]:
                            event["joined"].append(email)
                    else:
                        if email in event["joined"]:
                            event["joined"].remove(email)
                break
        # write the changes to the file
        with open(file_path, "w") as file:
            data = {"events": todayEvents["events"]}
            json.dump(data, file, default=str, indent=4)