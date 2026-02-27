#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash, session)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

from forms import TodoListForm, LoginForm
from ext import db, login_manager
from models import TodoList, User, LoggedSession

SECRET_KEY = 'This is my key'

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todolist.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

MAX_LOGGED_USERS = 3

DEFAULT_USERS = [
    {'username': 'admin', 'password': 'admin'},
    {'username': 'user1', 'password': '123456'},
    {'username': 'user2', 'password': '123456'},
    {'username': 'user3', 'password': '123456'},
    {'username': 'user4', 'password': '123456'},
]

DEFAULT_TODOS = {
    'admin': [
        ('完成项目文档编写', 0),
        ('代码审查', 1),
        ('部署测试环境', 0),
    ],
    'user1': [
        ('学习Python基础', 1),
        ('完成练习题', 0),
        ('阅读技术博客', 0),
    ],
    'user2': [
        ('整理工作周报', 0),
        ('参加会议', 1),
        ('回复邮件', 0),
    ],
    'user3': [
        ('健身锻炼', 0),
        ('购买生活用品', 1),
        ('预约医生', 0),
    ],
    'user4': [
        ('学习新技术', 0),
        ('完成在线课程', 0),
        ('做项目笔记', 1),
    ],
}


def get_logged_users():
    logged_sessions = LoggedSession.query.all()
    logged_users = []
    for ls in logged_sessions:
        user = User.query.get(ls.user_id)
        if user:
            logged_users.append({
                'user': user,
                'session_id': ls.session_id
            })
    return logged_users


def add_logged_user(user_id, session_id):
    existing = LoggedSession.query.filter_by(user_id=user_id).first()
    if existing:
        existing.session_id = session_id
        existing.login_time = int(__import__('time').time())
    else:
        logged_sessions = LoggedSession.query.all()
        if len(logged_sessions) >= MAX_LOGGED_USERS:
            oldest = min(logged_sessions, key=lambda x: x.login_time)
            db.session.delete(oldest)
        ls = LoggedSession(user_id, session_id)
        db.session.add(ls)
    db.session.commit()


def remove_logged_user(user_id):
    ls = LoggedSession.query.filter_by(user_id=user_id).first()
    if ls:
        db.session.delete(ls)
        db.session.commit()


def get_current_session_user():
    session_id = session.get('current_session_id')
    if session_id:
        ls = LoggedSession.query.filter_by(session_id=session_id).first()
        if ls:
            return User.query.get(ls.user_id)
    return None


def set_current_session_user(user_id, session_id):
    session['current_session_id'] = session_id
    add_logged_user(user_id, session_id)


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    current_session_user = get_current_session_user()
    if not current_session_user:
        return redirect(url_for('switch_account'))
    
    form = TodoListForm()
    if request.method == 'GET':
        todolists = TodoList.query.filter_by(user_id=current_session_user.id).all()
        logged_users = get_logged_users()
        return render_template('index.html', todolists=todolists, form=form, 
                               logged_users=logged_users, current_session_user=current_session_user)
    else:
        if form.validate_on_submit():
            todolist = TodoList(current_session_user.id, form.title.data, form.status.data)
            db.session.add(todolist)
            db.session.commit()
            flash('You have add a new todo list')
        else:
            flash(form.errors)
        return redirect(url_for('show_todo_list'))


@app.route('/delete/<int:id>')
@login_required
def delete_todo_list(id):
     todolist = TodoList.query.filter_by(id=id).first_or_404()
     current_session_user = get_current_session_user()
     if current_session_user and todolist.user_id == current_session_user.id:
         db.session.delete(todolist)
         db.session.commit()
         flash('You have delete a todo list')
     else:
         flash('You can only delete your own todo list')
     return redirect(url_for('show_todo_list'))


@app.route('/change/<int:id>', methods=['GET', 'POST'])
@login_required
def change_todo_list(id):
    current_session_user = get_current_session_user()
    if not current_session_user:
        return redirect(url_for('switch_account'))
    
    if request.method == 'GET':
        todolist = TodoList.query.filter_by(id=id, user_id=current_session_user.id).first_or_404()
        form = TodoListForm()
        form.title.data = todolist.title
        form.status.data = str(todolist.status)
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id, user_id=current_session_user.id).first_or_404()
            todolist.title = form.title.data
            todolist.status = form.status.data
            db.session.commit()
            flash('You have modify a todolist')
        else:
            flash(form.errors)
        return redirect(url_for('show_todo_list'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            import uuid
            session_id = str(uuid.uuid4())
            login_user(user)
            set_current_session_user(user.id, session_id)
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    logged_users = get_logged_users()
    return render_template('login.html', form=form, logged_users=logged_users)


@app.route('/logout')
@login_required
def logout():
    current_session_user = get_current_session_user()
    if current_session_user:
        remove_logged_user(current_session_user.id)
    session.pop('current_session_id', None)
    logout_user()
    flash('you have logout!')
    return redirect(url_for('login'))


@app.route('/switch_account')
@login_required
def switch_account():
    logged_users = get_logged_users()
    return render_template('switch_account.html', logged_users=logged_users)


@app.route('/switch_to/<int:user_id>')
@login_required
def switch_to(user_id):
    ls = LoggedSession.query.filter_by(user_id=user_id).first()
    if ls:
        session['current_session_id'] = ls.session_id
        flash('Switched account successfully!')
    return redirect(url_for('show_todo_list'))


@app.route('/logout_specific/<int:user_id>')
@login_required
def logout_specific(user_id):
    ls = LoggedSession.query.filter_by(user_id=user_id).first()
    if ls:
        current_session_user = get_current_session_user()
        if current_session_user and current_session_user.id == user_id:
            session.pop('current_session_id', None)
            logout_user()
        db.session.delete(ls)
        db.session.commit()
        flash('Account logged out!')
    logged_users = get_logged_users()
    if not logged_users:
        return redirect(url_for('login'))
    return redirect(url_for('switch_account'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


def init_default_data():
    for user_data in DEFAULT_USERS:
        existing = User.query.filter_by(username=user_data['username']).first()
        if not existing:
            user = User(username=user_data['username'], password=user_data['password'])
            db.session.add(user)
            db.session.commit()
            
            if user_data['username'] in DEFAULT_TODOS:
                for todo_title, todo_status in DEFAULT_TODOS[user_data['username']]:
                    todo = TodoList(user_id=user.id, title=todo_title, status=todo_status)
                    db.session.add(todo)
                db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_default_data()
        print("数据库初始化完成")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
