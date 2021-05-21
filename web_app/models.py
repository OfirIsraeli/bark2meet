from datetime import datetime, timedelta
from web_app import db, login_manager
from flask_login import UserMixin
from web_app.notifications import Notification
DEFAULT_IMG = "static/default-account-img.png"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image = db.Column(db.String(60), nullable=False, default=DEFAULT_IMG)
    pos_x = db.Column(db.Integer, nullable=False, default=31.910664)
    pos_y = db.Column(db.Integer, nullable=False, default=34.896716)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    current_area_x = db.Column(db.Integer, nullable=False, default=31.771959)
    current_area_y = db.Column(db.Integer, nullable=False, default=35.217018)

    # for debbugging:
    date_last_session = datetime.now() - timedelta(1) # just means yesterday

    # actual:
    # date_last_session = db.Column(db.DateTime, nullable=False, default=datetime.now())

    #status = db.Column(db.Integer, nullable=False, default=0)
    #friends = db.relationship("Friends", backref="user", lazy=True)

    def check_new_notifications(self):
        pass
        # all_notifications = db.session.query(Notification).filter_by(email=self.email).all()

    def update_user_location(self, pos_x, pos_y):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.date_last_update = datetime.now()
        db.session.commit()

    def update_user_area(self, current_area_x, current_area_y):
        self.current_area_x = current_area_x
        self.current_area_y = current_area_y
        db.session.commit()

    def update_img(self, filename):
        self.image = filename
        db.session.commit()

    def __repr__(self):
        return f"\n\nUser '{self.username}': \n'{self.email}'\n x:'{self.pos_x}'\n y:'{self.pos_y}'" \
               f"\n current_area_x:'{self.current_area_x}'\n current_area_y:'{self.current_area_y}'\n"


# class Friends(db.Model):
class Friends:
    # static class of Friends
    # user_email = db.Column(db.String(120), db.ForeignKey("user.email"), nullable=False)
    # friend_email = db.Column(db.String(120), db.ForeignKey("user.email"), nullable=False)

    def get_all(self, user_email):
        friends_emails = set()
        # all_friends = Friends.query.filter_by(user_email=user_email).all()
        all_friends = db.session.query(Friends).all()

        for friend in all_friends:
            friends_emails.add(friend.friend_email)
        return friends_emails

    def add(self, user_email, friend_email):
        to_add = Friends(user_email, friend_email)
        db.session.add(to_add)
        db.session.commit()

    def delete(self, user_email, friend_email):
        to_delete = Friends(user_email, friend_email)
        db.session.delete(to_delete)
        db.session.commit()
