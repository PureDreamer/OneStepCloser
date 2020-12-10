import datetime
import os
import requests
from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from flask_bootstrap import Bootstrap
from flask_login import (LoginManager, UserMixin, current_user, login_user,
                         logout_user)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

from flaskos import *

app = Flask(__name__)
app.static_folder = 'static'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)
Bootstrap(app)
app.secret_key = os.environ.get('SECRET')
login = LoginManager(app)
login.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(25),
                          nullable=False)
    email = db.Column(db.String(50),
                      unique=True, nullable=False)
    password = db.Column(db.String(50),
                         nullable=False)
    date_of_birth = db.Column(db.Date)
    city = db.Column(db.String(40))
    spirit_animal = db.Column(db.String(30))


class List(db.Model):
    __tablename__ = 'list'
    id = db.Column(db.Integer, primary_key=True)
    list_name = db.Column(db.String(25), nullable=False)
    list_color = db.Column(db.String(25), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creation_date = db.Column(db.Date, default=datetime.datetime.utcnow)


class Mission(db.Model):
    __tablename__ = 'mission'
    id = db.Column(db.Integer, primary_key=True)
    mission = db.Column(db.String(50), nullable=False)
    place = db.Column(db.String(100))
    creation_date = db.Column(db.DateTime,
                              default=datetime.datetime.utcnow)
    due_date = db.Column(db.DateTime)
    important = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'))


db.create_all()
db.session.commit()
@login.user_loader
def load_user(id):
    return User.query.get(int(id))


def get_random_quote():
    random_quote = requests.get(
        'http://thebotbox.pythonanywhere.com/get-random-quote')
    the_quoter = random_quote.json()['author']
    random_quote = random_quote.json()['quote']
    return the_quoter, random_quote


@app.route("/", methods=['GET', 'POST'])
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('regis'))
    list_form = ListForm()
    if list_form.validate_on_submit():
        list_name = list_form.list_name.data
        color = list_form.color_choice.data
        creation_date = datetime.datetime.now()
        list_mis = List(list_name=list_name, list_color=color,
                        creation_date=creation_date, user_id=current_user.id)
        db.session.add(list_mis)
        db.session.commit()
        session['current_list'] = str(list_mis.id)
        flash(f'{list_name} was created succesfully')
        return redirect(url_for('order', list_id=session['current_list']))
    list_lists = List.query.filter_by(user_id=current_user.id)
    random = get_random_quote()
    return render_template('home.html', random_quote=random[1],
                           the_quoter=random[0], form=list_form,
                           list_lists=list_lists)


@app.route('/<list_id>', methods=['GET', 'POST'])
def order(list_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    tasks = Mission.query.filter_by(list_id=list_id)
    update = UpdateTaskForm()
    task_form = TaskForm()
    complete_update = UpdateTaskForm()
    colorof = List.query.filter_by(id=list_id).first()
    if colorof:
        colorof = colorof.list_color
    else:
        colorof = 'Red'
    if task_form.validate_on_submit() and task_form.submit_button.data:
        mission = task_form.mission.data
        creation_date = datetime.datetime.now()
        due_date = task_form.due_date.data
        place = task_form.place.data
        important = task_form.important.data
        completed = task_form.completed.data
        miss = Mission(mission=mission, due_date=due_date,
                       place=place, important=important, completed=completed,
                       creation_date=creation_date, list_id=list_id)
        db.session.add(miss)
        db.session.commit()
        flash("Task created Successfully")
        return redirect(url_for('order', list_id=miss.list_id, f1=task_form, f2=update))
    if update.validate_on_submit() and update.update_task_submit.data:
        if request.method == 'POST':
            mission = Mission.query.filter_by(
                id=request.form['hidden']).first()
            mission.important = update.important.data
            mission.completed = update.completed.data
        db.session.commit()
        flash("Task Updated Successfully")
        return redirect(url_for('order', list_id=list_id))
    random = get_random_quote()
    return render_template('list_missions.html', random_quote=random[1],
                           the_quoter=random[0], colorof=colorof,
                           list_id=list_id, f1=task_form, f2=update, f3=complete_update, tasks=tasks)


@app.route('/<list_id>/orderby/', methods=['GET', 'POST'])
def order_by(list_id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    update = UpdateTaskForm()
    task_form = TaskForm()
    colorof = List.query.filter_by(id=list_id).first()
    if colorof:
        colorof = colorof.list_color
    else:
        colorof = 'Red'
    random = get_random_quote()
    if request.form['parameter'] == "due_date":
        tasks = Mission.query.filter_by(
            list_id=list_id).order_by(desc(Mission.due_date))
    elif request.form['parameter'] == "completed":
        tasks = Mission.query.filter_by(
            list_id=list_id).order_by(desc(Mission.completed))
    elif request.form['parameter'] == "important":
        tasks = Mission.query.filter_by(
            list_id=list_id).order_by(desc(Mission.important))
    else:
        tasks = Mission.query.filter_by(list_id=list_id)
    return render_template('list_missions.html', random_quote=random[1], the_quoter=random[0], colorof=colorof, list_id=list_id, f1=task_form, f2=update, tasks=tasks)


@app.route('/update_complete/<row_id>', methods=['GET', 'POST'])
def update_complete(row_id):
    mission_to_update = Mission.query.get(int(row_id))
    list_to_go = mission_to_update.list_id
    mission_to_update.completed = True
    db.session.commit()
    flash('Horray you completed it!')
    return redirect(url_for('order', list_id=list_to_go))


@app.route('/delete_list/<id>/', methods=['GET', 'POST'])
def delete_list(id):
    list_to_delete = List.query.get(int(id))
    missions_delete = Mission.query.filter_by(list_id=list_to_delete.id).all()
    for mission in missions_delete:
        db.session.delete(mission)
    db.session.delete(list_to_delete)
    db.session.commit()
    flash("List Deleted Successfully")
    return redirect(url_for('home'))


@app.route('/delete_mission/<id>/', methods=['GET', 'POST'])
def delete_mission(id):
    mission_to_delte = Mission.query.get(int(id))
    lista = mission_to_delte.list_id
    if mission_to_delte:
        db.session.delete(mission_to_delte)
        db.session.commit()
        flash("List Deleted Successfully")
    else:
        flash("No mission like that")
    return redirect(url_for('order', list_id=lista))


@app.route("/registration", methods=['GET', 'POST'])
def regis():
    reg_form = RegForm()
    if reg_form.validate_on_submit():
        email = reg_form.email.data
        full_name = reg_form.full_name.data
        password = reg_form.password.data
        hash_power = pbkdf2_sha512.hash(password)
        user = User(full_name=full_name, password=hash_power, email=email)
        db.session.add(user)
        db.session.commit()
        flash('User has been created')
        return redirect(url_for('login'))
    random = get_random_quote()
    return render_template('reg_form.html', random_quote=random[1],
                           the_quoter=random[0], form=reg_form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    log_form = LogForm()
    if log_form.validate_on_submit():
        user_object = User.query.filter_by(email=log_form.email.data).first()
        login_user(user_object)
        user_name = user_object.full_name
        flash(f'Welcome {user_name}!')
        return redirect(url_for('home'))
    random = get_random_quote()
    return render_template('login_form.html', random_quote=random[1],
                           the_quoter=random[0], form=log_form)


@app.route("/logout", methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/profile", methods=['POST', 'GET'])
def profile():
    user = User.query.get(current_user.id)
    name = ['Name', user.full_name]
    email = ['Email', user.email]
    date_of_birth = ['Date of Birth', user.date_of_birth]
    city = ['City', user.city]
    spirit_animal = ['Spirit Animal', user.spirit_animal]
    user_list = [name, email, date_of_birth, city, spirit_animal]
    random = get_random_quote()
    return render_template('profile2.html', random_quote=random[1],
                           the_quoter=random[0],
                           user_list=user_list,
                           user=user)


@app.route('/profile/edit', methods=['POST', 'GET'])
def update_profile():
    user = User.query.get(current_user.id)
    update = UpdateUser()
    if update.validate_on_submit():
        if update.full_name.data:
            user.full_name = update.full_name.data
        if update.city.data:
            user.city = update.city.data
        if update.date_of_birth.data:
            user.date_of_birth = update.date_of_birth.data
        if update.spirit_animal.data:
            user.spirit_animal = update.spirit_animal.data
        db.session.commit()
        flash('Profile has been updated!')
        return redirect(url_for('profile'))
    random = get_random_quote()
    return render_template('edit_profile.html', random_quote=random[1], the_quoter=random[0], form=update, user=user)


@app.route('/update_list/<list_id>', methods=['POST', 'GET'])
def update_list(list_id):
    list = List.query.get(list_id)
    update = ListForm()
    if update.validate_on_submit():
        if update.list_name.data:
            list.list_name = update.list_name.data
        if update.color_choice.data:
            list.list_color = update.color_choice.data
        db.session.commit()
        flash('List has been updated!')
        return redirect(url_for('home'))
    random = get_random_quote()
    return render_template('edit_list.html', random_quote=random[1], the_quoter=random[0], form=update, list=list)


@app.route('/update_mission/<mission_id>', methods=['POST', 'GET'])
def update_mission(mission_id):
    mission = Mission.query.get(mission_id)
    update = TaskForm()
    if update.validate_on_submit():
        if update.mission.data:
            mission.mission = update.mission.data
        if update.due_date.data:
            mission.due_date = update.due_date.data
        if update.place.data:
            mission.place = update.place.data
        if update.important.data:
            mission.important = update.important.data
        db.session.commit()
        flash('Mission has been updated!')
        return redirect(url_for('order', list_id=mission.list_id))
    random = get_random_quote()
    return render_template('edit_mission.html', random_quote=random[1], the_quoter=random[0], form=update, mission=mission)


@app.route('/aboutus')
def about_us():
    random = get_random_quote()
    return render_template('index.html', random_quote=random[1], the_quoter=random[0])


if __name__ == "__main__":
    app.run()
