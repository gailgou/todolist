#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

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


@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    import datetime
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')


@app.context_processor
def utility_processor():
    import time
    return dict(current_timestamp=lambda: int(time.time()))


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        category_filter = request.args.get('category', '')
        todolists_query = TodoList.query
        
        if category_filter:
            todolists_query = todolists_query.filter_by(category=category_filter)
        
        todolists = todolists_query.all()
        
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2}
        todolists.sort(key=lambda x: (priority_order.get(x.priority, 3), x.create_time))
        
        return render_template('index.html', todolists=todolists, form=form, current_category=category_filter)
    else:
        if form.validate_on_submit():
            deadline = None
            if form.deadline.data:
                import time
                deadline = int(time.mktime(form.deadline.data.timetuple()))
            
            todolist = TodoList(current_user.id, form.title.data, form.status.data, 
                               form.category.data, form.priority.data, deadline)
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
        if todolist.deadline:
            import datetime
            form.deadline.data = datetime.datetime.fromtimestamp(todolist.deadline)
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id).first_or_404()
            todolist.title = form.title.data
            todolist.status = form.status.data
            todolist.category = form.category.data
            todolist.priority = form.priority.data
            if form.deadline.data:
                import time
                todolist.deadline = int(time.mktime(form.deadline.data.timetuple()))
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


@app.route('/alarm/<int:id>')
@login_required
def set_alarm(id):
    todolist = TodoList.query.filter_by(id=id).first_or_404()
    if not todolist.deadline:
        flash('请先设置截止时间')
        return redirect(url_for('show_todo_list'))
    
    import datetime
    import subprocess
    import os
    deadline_dt = datetime.datetime.fromtimestamp(todolist.deadline)
    alarm_time = deadline_dt.strftime('%H:%M')
    alarm_date = deadline_dt.strftime('%Y-%m-%d')
    
    try:
        notification_script = f'''display notification "{todolist.title}" with title "待办提醒" sound name "Glass"'''
        
        temp_script_path = f'/tmp/todo_alarm_{id}.scpt'
        with open(temp_script_path, 'w') as f:
            f.write(notification_script)
        
        at_time = deadline_dt.strftime('%H:%M %m/%d/%Y')
        subprocess.run(['at', at_time], input=f'osascript {temp_script_path}\nrm {temp_script_path}', text=True)
        
        flash(f'已设置闹钟提醒: {alarm_date} {alarm_time}')
    except Exception as e:
        flash(f'设置闹钟失败: {str(e)}')
    
    return redirect(url_for('show_todo_list'))


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
            todo1 = TodoList(user_id=user.id, title='习近平五谈稳中求进织密扎牢民生保障网', status=0, category='工作', priority='P0', deadline=now + 86400)
            todo2 = TodoList(user_id=user.id, title='特朗普获超270张选举人票将入主白宫', status=1, category='生活', priority='P1', deadline=now + 172800)
            todo3 = TodoList(user_id=user.id, title='学习Python编程', status=0, category='学习', priority='P2', deadline=now - 3600)
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.add(todo3)
            db.session.commit()
            
            print("数据库初始化完成，已添加默认用户和测试数据")
    
    app.run(host='0.0.0.0', port=5007, debug=True)
