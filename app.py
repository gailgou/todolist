#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import time

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
        
        pending_todos = [todo for todo in todolists if todo.status == 0]
        completed_todos = [todo for todo in todolists if todo.status == 1]
        
        now = int(time.time())
        
        return render_template('index.html', 
                           pending_todos=pending_todos, 
                           completed_todos=completed_todos, 
                           form=form, 
                           now=now,
                           sort_order=sort_order,
                           datetime=datetime)
    else:
        if form.validate_on_submit():
            deadline = None
            if form.deadline.data:
                try:
                    deadline_time = datetime.strptime(form.deadline.data, '%Y-%m-%d %H:%M')
                    deadline = int(deadline_time.timestamp())
                except:
                    flash('Invalid deadline format!')
                    return redirect(url_for('show_todo_list'))
            
            todolist = TodoList(current_user.id, form.title.data, int(form.status.data), deadline)
            db.session.add(todolist)
            db.session.commit()
            flash('You have add a new todo list')
        else:
            flash(form.errors)
        return redirect(url_for('show_todo_list'))


@app.route('/delete/<int:id>')
@login_required
def delete_todo_list(id):
     todolist = TodoList.query.filter_by(id=id, user_id=current_user.id).first_or_404()
     db.session.delete(todolist)
     db.session.commit()
     flash('You have delete a todo list')
     return redirect(url_for('show_todo_list'))


@app.route('/change/<int:id>', methods=['GET', 'POST'])
@login_required
def change_todo_list(id):
    todolist = TodoList.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'GET':
        form = TodoListForm()
        form.title.data = todolist.title
        form.status.data = str(todolist.status)
        if todolist.deadline:
            form.deadline.data = datetime.fromtimestamp(todolist.deadline).strftime('%Y-%m-%d %H:%M')
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist.title = form.title.data
            todolist.status = int(form.status.data)
            
            if form.deadline.data:
                try:
                    deadline_time = datetime.strptime(form.deadline.data, '%Y-%m-%d %H:%M')
                    todolist.deadline = int(deadline_time.timestamp())
                except:
                    flash('Invalid deadline format!')
                    return redirect(url_for('show_todo_list'))
            else:
                todolist.deadline = None
                
            db.session.commit()
            flash('You have modify a todolist')
        else:
            flash(form.errors)
        return redirect(url_for('show_todo_list'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    register_form = RegisterForm()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'login':
            if login_form.validate_on_submit():
                user = User.query.filter_by(username=login_form.username.data).first()
                if user and user.check_password(login_form.password.data):
                    login_user(user)
                    flash('you have logged in!')
                    return redirect(url_for('show_todo_list'))
                else:
                    flash('Invalid username or password')
        elif action == 'register':
            if register_form.validate_on_submit():
                if register_form.password.data != register_form.password_confirm.data:
                    flash('Passwords do not match!')
                else:
                    existing_user = User.query.filter_by(username=register_form.username.data).first()
                    if existing_user:
                        flash('Username already exists!')
                    else:
                        user = User(username=register_form.username.data, password=register_form.password.data)
                        db.session.add(user)
                        db.session.commit()
                        flash('Registration successful! Please log in.')
                        return redirect(url_for('login'))
                flash('Registration failed!')
    
    return render_template('login.html', login_form=login_form, register_form=register_form)


@app.route('/batch_complete', methods=['POST'])
@login_required
def batch_complete():
    todo_ids = request.form.getlist('todo_ids')
    if todo_ids:
        for todo_id in todo_ids:
            todo = TodoList.query.filter_by(id=todo_id, user_id=current_user.id).first()
            if todo:
                todo.status = 1
        db.session.commit()
        flash('Selected todos have been marked as completed!')
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
    
    app.run(host='0.0.0.0', port=5008, debug=True)
