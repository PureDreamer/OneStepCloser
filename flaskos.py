from typing import Optional
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, SelectField, BooleanField
from wtforms.fields.html5 import EmailField, DateField
from wtforms.validators import (DataRequired, Email, EqualTo, InputRequired,
                                Length, ValidationError, Optional)
from passlib.hash import pbkdf2_sha512
from app import User


def wrong_answers(form, field):
    user_try = form.email.data
    password_try = field.data
    user_object = User.query.filter_by(email=user_try).first()
    if user_object is None:
        raise ValidationError("Email or Password is incorrect!")
    elif not pbkdf2_sha512.verify(password_try, user_object.password):
        raise ValidationError("Email or Password is incorrect!")


class RegForm(FlaskForm):
    full_name = StringField('Full_name_label',
                            validators=[InputRequired(message="Full name required"),
                                        Length(
                                min=4, max=50, message="Full name must be between 4 and 50 letters")
                            ])
    email = EmailField('Email address', [DataRequired(), Email()])
    password = PasswordField('password_label',
                             validators=[InputRequired(message="Password required"),
                                         Length(min=4, max=50,
                                                message="Password must be between 4 and 50 letters")]
                             )
    confirm_pass = PasswordField('confirm_password_label',
                                 validators=[InputRequired(
                                     message="Password required"),
                                     EqualTo('password', message="Passwords must match")])
    submit_button = SubmitField('Make It RAIN!')

    def validate_email(self, email):
        user_object = User.query.filter_by(email=email.data).first()
        if user_object:
            raise ValidationError('Email is already being used!')


class LogForm(FlaskForm):
    email = EmailField('Email address', [DataRequired(), Email()])
    password = PasswordField('password_label',
                             validators=[InputRequired(message="Password required"),
                                         wrong_answers]
                             )

    submit_button = SubmitField('Start tasking!')


class ListForm(FlaskForm):
    list_name = StringField('list_name_label',
                            validators=[InputRequired(message="A list must have a name"),
                                        Length(
                                min=3, max=50, message="List must be between 3 and 50 letters")])

    color_choice = SelectField('Color', choices=[(
        'Red', 'Red'), ('Blue', 'Blue'), ('Green', 'Green'), ('White', 'White')])
    submit_button = SubmitField('List it!')


class TaskForm(FlaskForm):
    mission = StringField('task_name_label',
                          validators=[InputRequired(message="A mission must have a description"),
                                      Length(
                              min=3, max=50, message="Mission must be between 3 and 50 letters")])
    due_date = DateField(
        'due_date_label', format='%Y-%m-%d', validators=[Optional()])
    place = StringField()
    important = BooleanField(
        'Is it important?', default=False)
    completed = BooleanField('Is it completed?', default=False)
    submit_button = SubmitField('Mission!?')


class UpdateTaskForm(FlaskForm):
    completed = BooleanField()
    update_task_submit = SubmitField('Apply')


class UpdateUser(FlaskForm):
    full_name = StringField('name_label',
                            validators=[Optional(), Length(min=4, max=50, message="Name must be atleast between 4 and 50 letters")])
    spirit_animal = StringField('spirit_animal_label',
                                validators=[Optional(), Length(min=3, max=50, message="Animal must be between 3 and 50 letters")])
    date_of_birth = DateField(
        'birth_date_label', format='%Y-%m-%d', validators=[Optional()])
    city = StringField('city_label',
                       validators=[Optional(), Length(min=3, max=50, message="City must be between 3 and 50 letters")])
    change_submit = SubmitField('Update')
