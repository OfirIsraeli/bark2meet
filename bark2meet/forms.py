from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from datetime import date, datetime
from bark2meet.models import User
from wtforms_components import DateRange


class RegistrationUserForm(FlaskForm):
    full_name = StringField('Full Name',
                            validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    birth_date = DateField('Start Date', validators=[DataRequired(), DateRange(max=date.today())])
    submit = SubmitField('Continue', id="submitOwner")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class RegistrationDogForm(FlaskForm):
    dog_name = StringField("What's your dog's name?",
                           validators=[DataRequired(), Length(min=3, max=30)])
    dog_age = IntegerField("How old is your furry friend?", validators=[DataRequired(), NumberRange(min=0, max=20)])
    #dog_age = StringField("How old is your furry friend?", validators=[DataRequired(), Length(min=1, max=4)])
    dog_temperament = StringField("What's his/her's temperament?", validators=[DataRequired(),
                                                                               Length(min=2,
                                                                                      max=120)])
    dog_color = StringField("What's your dog's color/s?", validators=[Length(min=2, max=30)])
    dog_breed = StringField('Breed', validators=[DataRequired(), Length(min=2, max=50)])
    # dog_gender = RadioField('Gender', validators=[DataRequired()], choices=[(1, 'Male'), (0, 'Female')])
    submit = SubmitField('Continue', id="submitDog")


class FileUploadForm(FlaskForm):
    user_img = FileField()
    dog_img = FileField()
    submit = SubmitField('Finish', id="submitImages")


class LoginForm(FlaskForm):
    email = StringField('', validators=[DataRequired(), Email()])
    password = PasswordField('', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class EventForm(FlaskForm):
    title = StringField('Walk Name', validators=[DataRequired(), Length(min=3, max=30)])
    location = StringField('Walk Location', validators=[DataRequired(), Length(min=3, max=30)])
    date = DateField('Start Date', validators=[DataRequired(), DateRange(min=date.today())])
    time = TimeField('Start Time', validators=[DataRequired()])
    #time = TimeField('Start Time', validators=[DataRequired(), DateRange(min=datetime.now().time())])
    # invite = BooleanField('Invite all my friends')
    submit = SubmitField('Continue')


class SearchForm(FlaskForm):
    search_filter = StringField('')
    submit = SubmitField('Search')
