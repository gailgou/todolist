#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
import time

from flask import (Flask, render_template, redirect, url_for, request, flash)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime

from forms import TodoListForm, LoginForm, RegisterForm
from ext import db, login_manager
from models import TodoList, User

SECRET_KEY = 'This is my key'

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todolist.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['WTF_CSRF_ENABLED'] = True


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"


@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
    return ''


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        sort_order = request.args.get('sort', 'desc')
        todolists = TodoList.query.filter_by(user_id=current_user.id).all()
        if sort_order == 'asc':
            todolists = sorted(todolists, key=lambda x: x.create_time)
        else:
            todolists = sorted(todolists, key=lambda x: x.create_time, reverse=True)
        return render_template('index.html', todolists=todolists, form=form, sort_order=sort_order, current_time=time.time())
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
            from datetime import datetime
            form.deadline.data = datetime.fromtimestamp(todolist.deadline)
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


@app.route('/batch_complete', methods=['POST'])
@login_required
def batch_complete():
    todo_ids = request.form.getlist('todo_ids')
    for todo_id in todo_ids:
        todolist = TodoList.query.filter_by(id=int(todo_id)).first()
        if todolist and todolist.user_id == current_user.id:
            todolist.status = 1
    db.session.commit()
    flash(f'You have completed {len(todo_ids)} todo items')
    return redirect(url_for('show_todo_list'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.verify_password(request.form['password']):
            login_user(user)
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    register_form = RegisterForm()
    return render_template('login.html', form=form, register_form=register_form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Username already exists')
                return render_template('login.html', form=form, register_form=form)
            user = User(username=form.username.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        else:
            flash(form.errors)
    return render_template('login.html', form=form, register_form=form)


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
        # 检查是否已经有用户，如果没有则添加默认用户
        existing_user = User.query.first()
        if not existing_user:
            # 添加默认用户
            user = User(username='admin', password='admin')
            db.session.add(user)
            db.session.commit()
            
            # 添加默认的待办事项
            now = int(time.time())
            import time as time_module
            now = time_module.time()
            todo1 = TodoList(user_id=user.id, title='习近平五谈稳中求进织密扎牢民生保障网', status=0)
            todo2 = TodoList(user_id=user.id, title='特朗普获超270张选举人票将入主白宫', status=1)
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.commit()
            
            print("数据库初始化完成，已添加默认用户和测试数据")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
