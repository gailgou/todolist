#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash, jsonify)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user
import subprocess
import datetime

from forms import TodoListForm, LoginForm
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
        category_filter = request.args.get('category', None)
        if category_filter:
            todolists = TodoList.query.filter_by(category=category_filter).order_by(TodoList.priority).all()
        else:
            todolists = TodoList.query.order_by(TodoList.priority).all()
        categories = ['工作', '生活', '学习', '亲子', '家庭']
        return render_template('index.html', todolists=todolists, form=form, categories=categories, selected_category=category_filter)
    else:
        if form.validate_on_submit():
            due_time = None
            if form.due_time.data:
                due_time = int(form.due_time.data.timestamp())
            todolist = TodoList(
                user_id=current_user.id,
                title=form.title.data,
                status=form.status.data,
                category=form.category.data,
                priority=form.priority.data,
                due_time=due_time
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
    todolist = TodoList.query.filter_by(id=id).first_or_404()
    if request.method == 'GET':
        form = TodoListForm()
        form.title.data = todolist.title
        form.status.data = str(todolist.status)
        form.category.data = todolist.category
        form.priority.data = str(todolist.priority)
        if todolist.due_time:
            dt = datetime.datetime.fromtimestamp(todolist.due_time)
            form.due_time.data = dt.strftime('%Y-%m-%dT%H:%M')
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist.title = form.title.data
            todolist.status = form.status.data
            todolist.category = form.category.data
            todolist.priority = form.priority.data
            if form.due_time.data:
                todolist.due_time = int(form.due_time.data.timestamp())
            else:
                todolist.due_time = None
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


@app.template_filter('datetimeformat')
def datetimeformat(timestamp):
    import datetime
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')


@app.route('/set_alarm/<int:id>')
@login_required
def set_alarm(id):
    todolist = TodoList.query.filter_by(id=id).first_or_404()
    if not todolist.due_time:
        flash('该任务没有设置截止时间，无法创建闹钟', 'warning')
        return redirect(url_for('show_todo_list'))
    
    due_datetime = datetime.datetime.fromtimestamp(todolist.due_time)
    title = todolist.title
    
    if due_datetime < datetime.datetime.now():
        flash('截止时间已过期，无法设置闹钟', 'warning')
        return redirect(url_for('show_todo_list'))
    
    calendar_applescript = f'''
    tell application "Calendar"
        set newEvent to make new event at end of events
        set title of newEvent to "待办提醒: {title}"
        set start date of newEvent to date "{due_datetime.strftime('%Y/%m/%d %H:%M:%S')}"
        set end date of newEvent to date "{due_datetime.strftime('%Y/%m/%d %H:%M:%S')}"
        set location of newEvent to "待办事项"
        set allday event of newEvent to false
        
        make new reminder at end of reminders of newEvent with properties {{trigger interval: -300}}
        
        activate
    end tell
    
    display notification "待办提醒已创建: {title}" with title "待办事项" subtitle "截止时间: {due_datetime.strftime('%Y-%m-%d %H:%M')}" sound name "Crystal"
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', calendar_applescript], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            flash(f'✅ 提醒已成功添加到日历应用！\n任务: {title}\n提醒时间: {due_datetime.strftime('%Y-%m-%d %H:%M')}\n将在截止时间前5分钟提醒您', 'success')
        else:
            if 'not running' in result.stderr.lower():
                result_retry = subprocess.run(['open', '-a', 'Calendar'], capture_output=True, text=True)
                result = subprocess.run(['osascript', '-e', calendar_applescript], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    flash(f'✅ 提醒已成功添加到日历应用！\n任务: {title}\n提醒时间: {due_datetime.strftime('%Y-%m-%d %H:%M')}', 'success')
                else:
                    flash(f'❌ 创建提醒失败: {result.stderr}', 'danger')
            else:
                flash(f'❌ 创建提醒失败: {result.stderr}', 'danger')
    except subprocess.TimeoutExpired:
        flash(f'⏰ 提醒设置超时，Calendar应用可能需要权限授权。请在系统偏好设置中允许Calendar通知', 'warning')
    except Exception as e:
        flash(f'❌ 创建提醒失败: {str(e)}', 'danger')
    
    return redirect(url_for('show_todo_list'))


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
