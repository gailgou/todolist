#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash, jsonify)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import time
import subprocess
import platform
import os

from forms import TodoListForm, LoginForm
from ext import db, login_manager
from models import TodoList, User

SECRET_KEY = 'This is my key'

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todolist.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# 添加模板过滤器
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
    return ""

# 添加设置提醒的路由
@app.route('/set_reminder', methods=['POST'])
@login_required
def set_reminder():
    try:
        todo_id = request.form.get('id')
        title = request.form.get('title')
        deadline = request.form.get('deadline')
        
        if not deadline:
            return jsonify({'success': False, 'message': '没有设置截止时间'})
        
        # 转换时间戳为datetime对象
        deadline_datetime = datetime.fromtimestamp(int(deadline))
        
        # 根据操作系统设置提醒
        system = platform.system()
        if system == 'Windows':  # Windows
            # 使用Windows通知
            reminder_script = f'''
import time
import subprocess
from datetime import datetime

# 计算等待时间（秒）
deadline = datetime.strptime("{deadline_datetime.strftime('%Y-%m-%d %H:%M')}", "%Y-%m-%d %H:%M")
now = datetime.now()
wait_seconds = (deadline - now).total_seconds()

# 只在截止时间未到时设置提醒
if wait_seconds > 0:
    time.sleep(wait_seconds)
    # 显示Windows通知
    subprocess.run([
        "powershell", "-Command", 
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$notify = New-Object System.Windows.Forms.NotifyIcon; "
        "$notify.Icon = [System.Drawing.SystemIcons]::Information; "
        "$notify.BalloonTipTitle = '待办事项提醒'; "
        "$notify.BalloonTipText = '{title} - 截止时间: {deadline_datetime.strftime('%Y-%m-%d %H:%M')}'; "
        "$notify.Visible = $true; "
        "$notify.ShowBalloonTip(10000);"
    ])
'''
            # 创建一个临时脚本来设置提醒
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reminder_script.py')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(reminder_script)
            
            # 在后台运行脚本
            subprocess.Popen(['python', script_path])
            
            return jsonify({'success': True, 'message': '提醒设置成功'})
        elif system == 'Darwin':  # macOS
            # 使用macOS通知
            reminder_script = f'''
import time
import subprocess
from datetime import datetime

# 计算等待时间（秒）
deadline = datetime.strptime("{deadline_datetime.strftime('%Y-%m-%d %H:%M')}", "%Y-%m-%d %H:%M")
now = datetime.now()
wait_seconds = (deadline - now).total_seconds()

# 只在截止时间未到时设置提醒
if wait_seconds > 0:
    time.sleep(wait_seconds)
    # 显示macOS通知
    subprocess.run([
        "osascript", "-e", 
        f'display notification "{title}" with title "待办事项提醒" subtitle "截止时间: {deadline_datetime.strftime("%Y-%m-%d %H:%M")}" sound name "Glass"'
    ])
'''
            # 创建一个临时脚本来设置提醒
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reminder_script.py')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(reminder_script)
            
            # 在后台运行脚本
            subprocess.Popen(['python', script_path])
            
            return jsonify({'success': True, 'message': '提醒设置成功'})
        else:
            return jsonify({'success': False, 'message': '当前系统不支持提醒功能'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        # 按优先级和创建时间排序
        todolists = TodoList.query.order_by(TodoList.priority.asc(), TodoList.create_time.desc()).all()
        # 传递当前时间戳用于计算逾期时间
        import time
        now_timestamp = int(time.time())
        return render_template('index.html', todolists=todolists, form=form, now_timestamp=now_timestamp)
    else:
        if form.validate_on_submit():
            # 处理deadline字段
            deadline = form.deadline.data
            deadline_timestamp = None
            if deadline:
                try:
                    # 将字符串转换为datetime对象
                    deadline_datetime = datetime.strptime(deadline, '%Y-%m-%d %H:%M')
                    # 转换为时间戳
                    deadline_timestamp = int(deadline_datetime.timestamp())
                except ValueError:
                    flash('截止时间格式不正确，请使用 YYYY-MM-DD HH:MM 格式', 'danger')
                    return redirect(url_for('show_todo_list'))
            
            todolist = TodoList(
                current_user.id, 
                form.title.data, 
                form.status.data,
                form.category.data,
                form.priority.data,
                deadline_timestamp
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
        # 转换时间戳为datetime对象
        if todolist.deadline:
            form.deadline.data = datetime.fromtimestamp(todolist.deadline).strftime('%Y-%m-%d %H:%M')
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id).first_or_404()
            todolist.title = form.title.data
            todolist.status = form.status.data
            todolist.category = form.category.data
            todolist.priority = form.priority.data
            # 处理deadline字段
            deadline = form.deadline.data
            if deadline:
                try:
                    # 将字符串转换为datetime对象
                    deadline_datetime = datetime.strptime(deadline, '%Y-%m-%d %H:%M')
                    # 转换为时间戳
                    todolist.deadline = int(deadline_datetime.timestamp())
                except ValueError:
                    flash('截止时间格式不正确，请使用 YYYY-MM-DD HH:MM 格式', 'danger')
                    return redirect(url_for('change_todo_list', id=id))
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
            todo1 = TodoList(user_id=user.id, title='习近平五谈稳中求进织密扎牢民生保障网', status=0, category='工作', priority='P0')
            todo2 = TodoList(user_id=user.id, title='特朗普获超270张选举人票将入主白宫', status=1, category='生活', priority='P1')
            todo3 = TodoList(user_id=user.id, title='学习Python编程', status=0, category='学习', priority='P2', deadline=now + 3*24*3600)  # 3天后
            todo4 = TodoList(user_id=user.id, title='陪孩子去公园', status=0, category='亲子', priority='P0', deadline=now + 2*24*3600)  # 2天后
            todo5 = TodoList(user_id=user.id, title='家庭聚餐', status=0, category='家庭', priority='P1', deadline=now + 24*3600)  # 1天后
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.add(todo3)
            db.session.add(todo4)
            db.session.add(todo5)
            db.session.commit()
            
            print("数据库初始化完成，已添加默认用户和测试数据")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
