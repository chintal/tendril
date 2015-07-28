

from flask_user.forms import RegisterForm
from flask_wtf import Form
from wtforms import StringField, SubmitField, validators


# Define the User registration form
# It augments the Flask-User RegisterForm with additional fields
class MyRegisterForm(RegisterForm):
    full_name = StringField('Full name', validators=[validators.DataRequired('Full name is required')])


# Define the User profile form
class UserProfileForm(Form):
    full_name = StringField('Full name', validators=[validators.DataRequired('Full name is required')])
    submit = SubmitField('Save')
