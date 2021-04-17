from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.fields import SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from web_app.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class EnterProject(FlaskForm):
    project_name = StringField('Project Name', validators=[DataRequired(), Length(min=10, max=150)])
    category = SelectField('Category',
                           choices=[(1, 'Development'), (2, "Volunteer"), (3, "Education"),
                                    (4, "Creative")], validate_choice=False)
    project_description = StringField('Project Description', validators=[DataRequired(),
                                                                         Length(min=20, max=2000)])
    need1 = StringField('Project Member 1', validators=[DataRequired()])
    need2 = StringField('Project Member 2')
    need3 = StringField('Project Member 3')
    need4 = StringField('Project Member 4')
    need5 = StringField('Project Member 5')

    submit = SubmitField('Create Project')
