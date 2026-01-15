#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
import datetime
import time

from flask import (Flask, render_template, redirect, url_for, request, flash)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

from forms import TodoListForm, LoginForm, RegisterForm
from ext import db, login_manager
from models import TodoList, User

SECRET_KEY = 'This is my key'

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todolist.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        sort_order = request.args.get('sort', 'desc')
        if sort_order == 'asc':
            todolists = TodoList.query.filter_by(user_id=current_user.id).order_by(TodoList.create_time.asc()).all()
        else:
            todolists = TodoList.query.filter_by(user_id=current_user.id).order_by(TodoList.create_time.desc()).all()
        
        # 分离已完成和未完成的待办
        pending_todos = [todo for todo in todolists if todo.status == 0]
        completed_todos = [todo for todo in todolists if todo.status == 1]
        
        return render_template('index.html', 
                             pending_todos=pending_todos, 
                             completed_todos=completed_todos, 
                             form=form, 
                             sort_order=sort_order)
    else:
        if form.validate_on_submit():
            deadline = None
            if form.deadline.data:
                deadline = int(form.deadline.data.timestamp())
            todolist = TodoList(current_user.id, form.title.data, form.status.data, deadline)
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
     db.session.delete(todolist)
     db.session.commit()
     flash('You have delete a todo list')
     return redirect(url_for('show_todo_list'))


@app.route('/change/<int:id>', methods=['GET', 'POST'])
@login_required
def change_todo_list(id):
    if request.method == 'GET':
        todolist = TodoList.query.filter_by(id=id).first_or_404()
        form = TodoListForm()
        form.title.data = todolist.title
        form.status.data = str(todolist.status)
        if todolist.deadline:
            form.deadline.data = datetime.datetime.fromtimestamp(todolist.deadline)
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id).first_or_404()
            todolist.title = form.title.data
            todolist.status = form.status.data
            if form.deadline.data:
                todolist.deadline = int(form.deadline.data.timestamp())
            else:
                todolist.deadline = None
            db.session.commit()
            flash('You have modify a todolist')
        else:
            flash(form.errors)
        return redirect(url_for('show_todo_list'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    form = RegisterForm()
    return render_template('login.html', form=form, register_mode=True)


@app.route('/batch_complete', methods=['POST'])
@login_required
def batch_complete():
    todo_ids = request.form.getlist('todo_ids')
    if todo_ids:
        TodoList.query.filter(TodoList.id.in_(todo_ids), TodoList.user_id == current_user.id).update({'status': 1}, synchronize_session=False)
        db.session.commit()
        flash('Selected todos have been marked as completed')
    return redirect(url_for('show_todo_list'))


def format_timestamp(timestamp):
    if not timestamp:
        return ''
    try:
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ''

app.jinja_env.filters['datetimeformat'] = format_timestamp


def current_timestamp():
    return int(time.time())

app.jinja_env.globals.update(current_timestamp=current_timestamp)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have logout!')
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


if __name__ == '__main__':
    # 初始化数据库
    with app.app_context():
        db.create_all()
        print("数据库初始化完成")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
