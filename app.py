#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

import time
from datetime import datetime
from flask import (Flask, render_template, redirect, url_for, request, flash, jsonify)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

from forms import TodoListForm, LoginForm
from ext import db, login_manager
from models import TodoList, User, CATEGORIES, PRIORITIES

SECRET_KEY = 'This is my key'

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todolist.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"


def parse_deadline(deadline_str):
    if not deadline_str:
        return None
    try:
        if 'T' in deadline_str:
            dt = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        else:
            dt = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M')
        return int(time.mktime(dt.timetuple()))
    except ValueError:
        return None

def format_deadline(deadline_timestamp):
    if not deadline_timestamp:
        return None
    return datetime.fromtimestamp(deadline_timestamp).strftime('%Y-%m-%d %H:%M')

def format_deadline_local(deadline_timestamp):
    if not deadline_timestamp:
        return ''
    return datetime.fromtimestamp(deadline_timestamp).strftime('%Y-%m-%dT%H:%M')

def get_overdue_info(deadline_timestamp):
    if not deadline_timestamp:
        return None
    now = time.time()
    if deadline_timestamp > now:
        return None
    overdue_seconds = now - deadline_timestamp
    if overdue_seconds < 60:
        return '刚刚过期'
    elif overdue_seconds < 3600:
        minutes = int(overdue_seconds / 60)
        return f'逾期{minutes}分钟'
    elif overdue_seconds < 86400:
        hours = int(overdue_seconds / 3600)
        return f'逾期{hours}小时'
    elif overdue_seconds < 2592000:
        days = int(overdue_seconds / 86400)
        return f'逾期{days}天'
    elif overdue_seconds < 31536000:
        months = int(overdue_seconds / 2592000)
        return f'逾期{months}个月'
    else:
        years = int(overdue_seconds / 31536000)
        return f'过期{years}年'

def priority_order(priority):
    order = {'P0': 0, 'P1': 1, 'P2': 2}
    return order.get(priority, 3)

@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        all_todos = TodoList.query.filter_by(user_id=current_user.id).all()
        all_todos.sort(key=lambda x: priority_order(x.priority))
        todos_by_category = {}
        for todo in all_todos:
            cat = todo.category
            if cat not in todos_by_category:
                todos_by_category[cat] = []
            todos_by_category[cat].append(todo)
        category_names = {cat[0]: cat[1] for cat in CATEGORIES}
        return render_template('index.html', 
                               todos_by_category=todos_by_category, 
                               form=form,
                               category_names=category_names,
                               format_deadline=format_deadline,
                               get_overdue_info=get_overdue_info,
                               CATEGORIES=CATEGORIES)
    else:
        if form.validate_on_submit():
            deadline = parse_deadline(form.deadline.data)
            todolist = TodoList(
                current_user.id, 
                form.title.data, 
                int(form.status.data),
                form.category.data,
                form.priority.data,
                deadline
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
        form.category.data = todolist.category
        form.priority.data = todolist.priority
        form.deadline.data = format_deadline(todolist.deadline)
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id).first_or_404()
            todolist.title = form.title.data
            todolist.status = int(form.status.data)
            todolist.category = form.category.data
            todolist.priority = form.priority.data
            todolist.deadline = parse_deadline(form.deadline.data)
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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have logout!')
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()

@app.route('/create_reminder/<int:id>', methods=['POST'])
@login_required
def create_reminder(id):
    todolist = TodoList.query.filter_by(id=id).first_or_404()
    reminder_time = format_deadline(todolist.deadline) if todolist.deadline else None
    
    mac_command = ''
    windows_command = ''
    
    if reminder_time:
        dt = datetime.fromtimestamp(todolist.deadline)
        mac_command = f'osascript -e \'tell application "Reminders" to make new reminder with properties {{name:"{todolist.title}", due date:date "{reminder_time}"}}\''
        
        win_time = dt.strftime('%H:%M')
        win_date = dt.strftime('%m/%d/%Y')
        windows_command = f'schtasks /create /tn "待办提醒_{todolist.title}" /tr "msg * {todolist.title}" /sc once /st {win_time} /sd {win_date} /ru system'
    else:
        mac_command = f'osascript -e \'display notification "{todolist.title}" with title "待办事项提醒" sound name "default"\''
        windows_command = f'msg * {todolist.title}'
    
    return jsonify({
        'success': True,
        'title': todolist.title,
        'reminder_time': reminder_time,
        'mac_command': mac_command,
        'windows_command': windows_command
    })


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
    
    app.run(host='0.0.0.0', port=5000, debug=True)
