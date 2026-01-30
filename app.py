#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

from forms import TodoListForm, LoginForm, RegisterForm
from ext import db, login_manager
from models import TodoList, User
import datetime

SECRET_KEY = 'This is my key'

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todolist.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

# 添加时间戳转换过滤器
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    """将时间戳转换为可读的日期时间格式"""
    if timestamp:
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return ""


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        # 获取排序参数
        sort_order = request.args.get('sort', 'desc')  # 默认降序
        
        # 查询未完成的待办事项
        if sort_order == 'asc':
            incomplete_todos = TodoList.query.filter_by(user_id=current_user.id, status=0).order_by(TodoList.create_time.asc()).all()
            complete_todos = TodoList.query.filter_by(user_id=current_user.id, status=1).order_by(TodoList.create_time.asc()).all()
        else:
            incomplete_todos = TodoList.query.filter_by(user_id=current_user.id, status=0).order_by(TodoList.create_time.desc()).all()
            complete_todos = TodoList.query.filter_by(user_id=current_user.id, status=1).order_by(TodoList.create_time.desc()).all()
            
        return render_template('index.html', 
                             incomplete_todos=incomplete_todos, 
                             complete_todos=complete_todos, 
                             form=form, 
                             sort_order=sort_order,
                             now=datetime.datetime.now())
    else:
        if form.validate_on_submit():
            # 处理截止时间
            deadline = None
            if form.deadline.data:
                deadline = form.deadline.data.timestamp()
                
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
     todolist = TodoList.query.filter_by(id=id, user_id=current_user.id).first_or_404()
     db.session.delete(todolist)
     db.session.commit()
     flash('You have delete a todo list')
     return redirect(url_for('show_todo_list'))


@app.route('/change/<int:id>', methods=['GET', 'POST'])
@login_required
def change_todo_list(id):
    if request.method == 'GET':
        todolist = TodoList.query.filter_by(id=id, user_id=current_user.id).first_or_404()
        form = TodoListForm()
        form.title.data = todolist.title
        form.status.data = str(todolist.status)
        # 格式化截止时间显示
        if todolist.deadline:
            form.deadline.data = datetime.datetime.fromtimestamp(todolist.deadline)
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id, user_id=current_user.id).first_or_404()
            todolist.title = form.title.data
            todolist.status = form.status.data
            
            # 处理截止时间
            if form.deadline.data:
                todolist.deadline = form.deadline.data.timestamp()
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
    if todo_ids:
        TodoList.query.filter(TodoList.id.in_(todo_ids), TodoList.user_id == current_user.id).update(
            {TodoList.status: 1}, synchronize_session=False)
        db.session.commit()
        flash(f'已完成 {len(todo_ids)} 个待办事项')
    else:
        flash('请选择要完成的待办事项')
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
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('用户名已存在')
            return render_template('register.html', form=form)
        
        # 创建新用户
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


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
            # 添加一个有截止时间和一个没有截止时间的待办事项
            tomorrow = now + 24*60*60  # 明天这个时候
            todo1 = TodoList(user_id=user.id, title='习近平五谈稳中求进织密扎牢民生保障网', status=0, deadline=tomorrow)
            todo2 = TodoList(user_id=user.id, title='特朗普获超270张选举人票将入主白宫', status=1)
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.commit()
            
            print("数据库初始化完成，已添加默认用户和测试数据")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
