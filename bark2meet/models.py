from datetime import datetime
from bark2meet import db, login_manager
from flask_login import UserMixin
DEFAULT_IMG = "static/default-account-img.png"
MALE = 1

OPEN = 0
FRIENDS = 1
PRIVATE = 2


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    # user:
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    gender = db.Column(db.Integer, nullable=False, default=MALE)
    birth_date = db.Column(db.DateTime, nullable=False)

    # user saved data for backend op
    user_img = db.Column(db.String(200), nullable=False, default=DEFAULT_IMG)
    radius_view = db.Column(db.Integer, nullable=False, default=1000)
    pos_x = db.Column(db.Integer, nullable=False, default=31.910664)
    pos_y = db.Column(db.Integer, nullable=False, default=34.896716)
    date_last_update = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    current_area_x = db.Column(db.Integer, nullable=False, default=31.771959)
    current_area_y = db.Column(db.Integer, nullable=False, default=35.217018)
    date_last_session = db.Column(db.DateTime, nullable=False, default=datetime.now())
    status = db.Column(db.Integer, nullable=False, default=0)
    sing_up_level = db.Column(db.Integer, nullable=False, default=0)
    # friends = db.relationship("Friends", backref="user", lazy=True)

    # dog:
    dog_name = db.Column(db.String(30), nullable=False, default="NULL")
    dog_age = db.Column(db.String(30), nullable=False, default="NULL")
    dog_temperament = db.Column(db.String(120), nullable=False, default="NULL")
    dog_color = db.Column(db.String(30), nullable=False, default="No Color")
    dog_breed = db.Column(db.String(50), nullable=False, default="NULL")
    dog_gender = db.Column(db.Integer, nullable=False, default=MALE)
    dog_img = db.Column(db.String(200), nullable=False, default=DEFAULT_IMG)
    # for debugging:
    # date_last_session = datetime.now() - timedelta(1) # just means yesterday

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

    def update_user_and_dog_img(self, user_img, dog_img):
        self.user_img = user_img
        self.dog_img = dog_img
        db.session.commit()

    def update_dog_details(self, name, age, temperament, color, breed, gender=MALE):
        try:
            self.dog_age = float(age)
        except:
            self.dog_age = 2.5
        self.dog_name = name
        self.dog_temperament = temperament
        self.dog_color = color
        self.dog_breed = breed
        self.dog_gender = gender
        db.session.commit()

    def update_sing_level(self):
        self.sing_up_level += 1
        db.session.commit()

    def update_radius_view(self, radius):
        if radius <= 0:
            return
        self.radius_view = radius
        db.session.commit()

    def change_status(self, status):
        if status not in {OPEN, FRIENDS, PRIVATE}:
            return
        self.status = status
        db.session.commit()

    def __repr__(self):
        return f"\n\nUser '{self.full_name}': \n'{self.email}'\n x:'{self.pos_x}'\n y:'{self.pos_y}'" \
               f"\n current_area_x:'{self.current_area_x}'\n current_area_y:'{self.current_area_y}'\n"

    def __eq__(self, other):
        return self.email == other.email

    def __hash__(self):
        return hash(self.email)


class Friends(db.Model):
    # static class of Friends
    id = db.Column(db.Integer, primary_key=True)
    # user_email = db.Column(db.String(120), db.ForeignKey("user.email"), unique=True, nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    # friend_email = db.Column(db.String(120), db.ForeignKey("user.email"), nullable=False)
    friend_email = db.Column(db.String(120), nullable=False)

    def get_all(self):
        friends_emails = set()

        # all_friends = Friends.query.filter_by(user_email=user_email).all()
        all_friends = db.session.query(Friends).all()

        for friend in all_friends:
            friends_emails.add(friend.friend_email)
        return friends_emails

    def get_all_friends_of(self, user_email):
        friends_emails = set()
        all_friends = Friends.query.filter_by(user_email=user_email).all()

        for friend in all_friends:
            friends_emails.add(friend.friend_email)
        return friends_emails

    def add(self, user_email, friend_email):
        if Friends.query.filter_by(user_email=user_email, friend_email=friend_email).first():
            return
        to_add = Friends(user_email=user_email, friend_email=friend_email)
        db.session.add(to_add)
        db.session.commit()

    def delete(self, user_email, friend_email):
        Friends.query.filter_by(user_email=user_email, friend_email=friend_email).delete()
        db.session.commit()
