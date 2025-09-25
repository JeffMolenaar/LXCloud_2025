from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegistrationForm(FlaskForm):
    first_name = StringField(
        'First Name',
        validators=[DataRequired(), Length(min=2, max=50)]
    )
    last_name = StringField(
        'Last Name',
        validators=[DataRequired(), Length(min=2, max=50)]
    )
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=4, max=25)]
    )
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=8)]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ]
    )
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')