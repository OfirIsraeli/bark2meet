from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO


app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628b3b0b13ce0c676dfde280ba245'
app.config['GOOGLEMAPS_KEY'] = "AIzaSyBP2kPsOHfmf-XJMKhf-lBWeQdl5SqSRR8"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'bark2meet/static/users_data/'
socketio = SocketIO(app, cors_allowed_origins='*')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from bark2meet import routes
from bark2meet.areas import area

# try:
#     area.init_areas()
# except:
#     print("no users in db")