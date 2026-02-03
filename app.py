#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
import time
from datetime import datetime

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


# 模板过滤器：时间戳转日期
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """将时间戳转换为日期格式"""
    if not timestamp:
        return '-'
    try:
        dt = datetime.fromtimestamp(int(timestamp))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return '-'


# 上下文处理器，使datetime在所有模板中可用
@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        # 获取分类筛选参数
        category_filter = request.args.get('category', '')
        
        # 查询待办事项，按优先级排序（P0在前）
        query = TodoList.query
        if category_filter:
            query = query.filter_by(category=category_filter)
        
        # 按优先级排序（P0 < P1 < P2）
        todolists = query.all()
        todolists.sort(key=lambda x: x.get_priority_value())
        
        # 获取所有分类用于筛选
        categories = TodoList.CATEGORIES
        
        return render_template('index.html', todolists=todolists, form=form, 
                               categories=categories, current_category=category_filter)
    else:
        if form.validate_on_submit():
            # 处理截止时间
            deadline = None
            if form.deadline.data:
                deadline = int(form.deadline.data.timestamp())
            
            todolist = TodoList(
                current_user.id, 
                form.title.data, 
                form.status.data,
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
    todolist = TodoList.query.filter_by(id=id).first_or_404()
    if request.method == 'GET':
        form = TodoListForm()
        form.title.data = todolist.title
        form.status.data = str(todolist.status)
        form.category.data = todolist.category
        form.priority.data = todolist.priority
        if todolist.deadline:
            form.deadline.data = datetime.fromtimestamp(todolist.deadline)
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist.title = form.title.data
            todolist.status = form.status.data
            todolist.category = form.category.data
            todolist.priority = form.priority.data
            if form.deadline.data:
                todolist.deadline = int(form.deadline.data.timestamp())
            else:
                todolist.deadline = None
            db.session.commit()
            flash('You have modify a todolist')
        else:
            flash(form.errors)
        return redirect(url_for('show_todo_list'))


@app.route('/alarm/<int:id>')
@login_required
def set_alarm(id):
    """设置系统闹钟/提醒"""
    todolist = TodoList.query.filter_by(id=id).first_or_404()
    
    success, message = todolist.set_alarm()
    if success:
        db.session.commit()  # 保存alarm_set状态
    flash(message)
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
            todo1 = TodoList(user_id=user.id, title='习近平五谈稳中求进织密扎牢民生保障网', status=0)
            todo2 = TodoList(user_id=user.id, title='特朗普获超270张选举人票将入主白宫', status=1)
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.commit()
            
            print("数据库初始化完成，已添加默认用户和测试数据")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
