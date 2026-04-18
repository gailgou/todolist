#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

import time
from datetime import datetime
from flask import (Flask, render_template, redirect, url_for, request, flash, session)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

from forms import TodoListForm, LoginForm, RegisterForm
from ext import db, login_manager
from models import TodoList, User

SECRET_KEY = 'This is my key'

MAX_LOGGED_USERS = 3

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


@app.template_filter('is_overdue')
def is_overdue(todo):
    return todo.is_overdue()


app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todolist.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"


def get_logged_users():
    logged_users = session.get('logged_users', [])
    users = []
    for user_id in logged_users:
        user = User.query.filter_by(id=user_id).first()
        if user:
            users.append(user)
    return users


def get_active_user_id():
    return session.get('active_user_id', current_user.id if current_user.is_authenticated else None)


def get_active_user():
    user_id = get_active_user_id()
    if user_id:
        return User.query.filter_by(id=user_id).first()
    return None


def add_logged_user(user_id):
    logged_users = session.get('logged_users', [])
    if user_id not in logged_users:
        if len(logged_users) >= MAX_LOGGED_USERS:
            logged_users.pop(0)
        logged_users.append(user_id)
    session['logged_users'] = logged_users
    session['active_user_id'] = user_id


def remove_logged_user(user_id):
    logged_users = session.get('logged_users', [])
    if user_id in logged_users:
        logged_users.remove(user_id)
    session['logged_users'] = logged_users
    if session.get('active_user_id') == user_id:
        if logged_users:
            session['active_user_id'] = logged_users[-1]
        else:
            session.pop('active_user_id', None)


def switch_user(user_id):
    logged_users = session.get('logged_users', [])
    if user_id in logged_users:
        session['active_user_id'] = user_id
        return True
    return False


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    active_user = get_active_user()
    if not active_user:
        active_user = current_user
        session['active_user_id'] = active_user.id
    
    form = TodoListForm()
    if request.method == 'GET':
        sort_by = request.args.get('sort', 'priority')
        order = request.args.get('order', 'asc')
        
        query = TodoList.query.filter_by(user_id=active_user.id)
        
        if sort_by == 'priority':
            if order == 'desc':
                query = query.order_by(TodoList.priority.desc())
            else:
                query = query.order_by(TodoList.priority.asc())
        elif sort_by == 'create_time':
            if order == 'desc':
                query = query.order_by(TodoList.create_time.desc())
            else:
                query = query.order_by(TodoList.create_time.asc())
        else:
            query = query.order_by(TodoList.priority.asc())
        
        all_todos = query.all()
        
        incomplete_todos = []
        complete_todos = []
        for todo in all_todos:
            if todo.status == 1:
                complete_todos.append(todo)
            else:
                incomplete_todos.append(todo)
        
        logged_users = get_logged_users()
        
        return render_template('index.html', 
                             incomplete_todos=incomplete_todos,
                             complete_todos=complete_todos,
                             form=form, sort_by=sort_by, order=order,
                             logged_users=logged_users,
                             active_user=active_user,
                             max_logged_users=MAX_LOGGED_USERS)
    else:
        if form.validate_on_submit():
            todolist = TodoList(
                active_user.id, 
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
    active_user = get_active_user()
    if not active_user:
        active_user = current_user
    
    todolist = TodoList.query.filter_by(id=id, user_id=active_user.id).first_or_404()
    db.session.delete(todolist)
    db.session.commit()
    flash('You have delete a todo list')
    return redirect(url_for('show_todo_list'))


@app.route('/change/<int:id>', methods=['GET', 'POST'])
@login_required
def change_todo_list(id):
    active_user = get_active_user()
    if not active_user:
        active_user = current_user
    
    if request.method == 'GET':
        todolist = TodoList.query.filter_by(id=id, user_id=active_user.id).first_or_404()
        form = TodoListForm()
        form.title.data = todolist.title
        form.status.data = str(todolist.status)
        form.priority.data = todolist.priority
        form.due_date.data = todolist.due_date
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id, user_id=active_user.id).first_or_404()
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
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user._is_hashed():
                user.set_password(password)
                db.session.commit()
            
            logged_users = session.get('logged_users', [])
            if user.id in logged_users:
                flash(f'用户 {username} 已经登录了')
                switch_user(user.id)
                return redirect(url_for('show_todo_list'))
            
            if len(logged_users) >= MAX_LOGGED_USERS:
                flash(f'已达登录上限！最多同时登录 {MAX_LOGGED_USERS} 个用户，请先登出其他用户。')
                if logged_users:
                    return redirect(url_for('show_todo_list'))
                else:
                    form = LoginForm()
                    return render_template('login.html', form=form, logged_users=get_logged_users())
            
            login_user(user)
            add_logged_user(user.id)
            flash(f'你已成功登录，用户：{username}!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    
    form = LoginForm()
    return render_template('login.html', form=form, logged_users=get_logged_users())


@app.route('/switch_user/<int:user_id>')
@login_required
def switch_user_route(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user and switch_user(user_id):
        flash(f'已切换到用户：{user.username}')
    else:
        flash('切换用户失败')
    return redirect(url_for('show_todo_list'))


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
    active_user = get_active_user()
    if not active_user:
        active_user = current_user
    
    todo_ids = request.form.getlist('todo_ids')
    for todo_id in todo_ids:
        todolist = TodoList.query.filter_by(id=int(todo_id), user_id=active_user.id).first()
        if todolist:
            todolist.status = 1
    db.session.commit()
    flash(f'已完成 {len(todo_ids)} 个待办事项')
    return redirect(url_for('show_todo_list'))


@app.route('/logout')
@login_required
def logout():
    active_user = get_active_user()
    if active_user:
        remove_logged_user(active_user.id)
        flash(f'用户 {active_user.username} 已登出')
    
    logged_users = session.get('logged_users', [])
    if logged_users:
        return redirect(url_for('show_todo_list'))
    else:
        logout_user()
        return redirect(url_for('login'))


@app.route('/logout_user/<int:user_id>')
@login_required
def logout_user_by_id(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user:
        remove_logged_user(user_id)
        flash(f'用户 {user.username} 已登出')
    
    logged_users = session.get('logged_users', [])
    if logged_users:
        return redirect(url_for('show_todo_list'))
    else:
        logout_user()
        return redirect(url_for('login'))


@app.route('/logout_all')
@login_required
def logout_all():
    logged_users = session.get('logged_users', [])
    session['logged_users'] = []
    session.pop('active_user_id', None)
    logout_user()
    flash('所有用户已登出')
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


def init_default_users():
    existing_users = User.query.all()
    
    if not existing_users:
        admin = User(username='admin', password='admin')
        db.session.add(admin)
        db.session.commit()
        
        now = int(time.time())
        past_date = (datetime.now() - __import__('datetime').timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        future_date = (datetime.now() + __import__('datetime').timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        
        todo1 = TodoList(user_id=admin.id, title='习近平五谈稳中求进织密扎牢民生保障网', status=0, priority='P0', due_date=past_date)
        todo2 = TodoList(user_id=admin.id, title='特朗普获超270张选举人票将入主白宫', status=1, priority='P1', due_date=future_date)
        db.session.add(todo1)
        db.session.add(todo2)
        db.session.commit()
        
        print("已添加默认用户 admin")
    
    for i in range(1, 6):
        username = f'user{i}'
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            user = User(username=username, password=f'password{i}')
            db.session.add(user)
            db.session.commit()
            
            past_date = (datetime.now() - __import__('datetime').timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S')
            future_date1 = (datetime.now() + __import__('datetime').timedelta(days=i*2)).strftime('%Y-%m-%d %H:%M:%S')
            future_date2 = (datetime.now() + __import__('datetime').timedelta(days=i*3)).strftime('%Y-%m-%d %H:%M:%S')
            
            todo1 = TodoList(
                user_id=user.id, 
                title=f'{username} 的待办事项 1 - 已过期测试', 
                status=0,
                priority='P0' if i % 3 == 0 else 'P1' if i % 3 == 1 else 'P2',
                due_date=past_date
            )
            todo2 = TodoList(
                user_id=user.id, 
                title=f'{username} 的待办事项 2 - 未完成', 
                status=0,
                priority='P1' if i % 3 == 0 else 'P2' if i % 3 == 1 else 'P0',
                due_date=future_date1
            )
            todo3 = TodoList(
                user_id=user.id, 
                title=f'{username} 的待办事项 3 - 已完成', 
                status=1,
                priority='P2' if i % 3 == 0 else 'P0' if i % 3 == 1 else 'P1',
                due_date=future_date2
            )
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.add(todo3)
            db.session.commit()
            print(f"已添加用户 {username} 及其待办事项")
    
    print("默认用户初始化完成")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_default_users()
    
    app.run(host='0.0.0.0', port=5003, debug=True)
