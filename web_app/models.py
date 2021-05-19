from datetime import datetime
from web_app import db, login_manager
from flask_login import UserMixin

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

    def update_user_location(self, pos_x, pos_y):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.date_last_update = datetime.now()
        db.session.commit()

    def update_user_area(self, current_area_x, current_area_y):
        self.current_area_x = current_area_x
        self.current_area_y = current_area_y
        db.session.commit()

    def __repr__(self):
        return f"\n\nUser '{self.username}': \n'{self.email}'\n x:'{self.pos_x}'\n y:'{self.pos_y}'" \
               f"\n current_area_x:'{self.current_area_x}'\n current_area_y:'{self.current_area_y}'\n"



