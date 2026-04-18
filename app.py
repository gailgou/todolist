#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

import time
from datetime import datetime
from flask import (Flask, render_template, redirect, url_for, request, flash)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

from forms import TodoListForm, LoginForm, RegisterForm
from ext import db, login_manager
from models import TodoList, User

SECRET_KEY = 'This is my key'

app = Flask(__name__)
bootstrap = Bootstrap(app)


@app.template_filter('datetime_format')
def datetime_format(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp


@app.template_filter('status_text')
def status_text(status):
    return '已完成' if status == 1 else '未完成'


@app.template_filter('priority_class')
def priority_class(priority):
    if priority == 'P0':
        return 'danger'
    elif priority == 'P1':
        return 'warning'
    else:
        return 'default'

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
        sort_by = request.args.get('sort', 'priority')
        if sort_by == 'priority':
            todolists = TodoList.query.filter_by(user_id=current_user.id).order_by(TodoList.priority).all()
        elif sort_by == 'create_time':
            todolists = TodoList.query.filter_by(user_id=current_user.id).order_by(TodoList.create_time.desc()).all()
        else:
            todolists = TodoList.query.filter_by(user_id=current_user.id).order_by(TodoList.priority).all()
        return render_template('index.html', todolists=todolists, form=form, sort_by=sort_by)
    else:
        if form.validate_on_submit():
            todolist = TodoList(
                current_user.id, 
                form.title.data, 
                form.status.data,
                form.priority.data,
                form.due_date.data
            )
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
        form.priority.data = todolist.priority
        form.due_date.data = todolist.due_date
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id).first_or_404()
            todolist.title = form.title.data
            todolist.status = form.status.data
            todolist.priority = form.priority.data
            todolist.due_date = form.due_date.data
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
        if request.form['password'] != request.form['confirm_password']:
            flash('Two passwords do not match!')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=request.form['username']).first()
        if existing_user:
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    form = RegisterForm()
    return render_template('register.html', form=form)


@app.route('/batch_complete', methods=['POST'])
@login_required
def batch_complete():
    todo_ids = request.form.getlist('todo_ids')
    for todo_id in todo_ids:
        todolist = TodoList.query.filter_by(id=int(todo_id), user_id=current_user.id).first()
        if todolist:
            todolist.status = 1
    db.session.commit()
    flash(f'已完成 {len(todo_ids)} 个待办事项')
    return redirect(url_for('show_todo_list'))


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
            import time
            now = int(time.time())
            todo1 = TodoList(user_id=user.id, title='习近平五谈稳中求进织密扎牢民生保障网', status=0)
            todo2 = TodoList(user_id=user.id, title='特朗普获超270张选举人票将入主白宫', status=1)
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.commit()
            
            print("数据库初始化完成，已添加默认用户和测试数据")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
