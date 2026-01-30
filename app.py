#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash, session)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

from forms import TodoListForm, LoginForm
from ext import db, login_manager
from models import TodoList, User, UserSession
import uuid

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
        # 只显示当前用户的待办事项
        todolists = TodoList.query.filter_by(user_id=current_user.id).all()
        # 获取所有已登录的用户
        logged_in_users = get_logged_in_users()
        return render_template('index.html', todolists=todolists, form=form, logged_in_users=logged_in_users)
    else:
        if form.validate_on_submit():
            todolist = TodoList(current_user.id, form.title.data, form.status.data)
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
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id).first_or_404()
            todolist.title = form.title.data
            todolist.status = form.status.data
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
            # 检查是否已有3个用户登录
            logged_in_count = UserSession.query.filter_by(is_active=True).count()
            if logged_in_count >= 3:
                flash('Maximum 3 users can be logged in at the same time')
                form = LoginForm()
                return render_template('login.html', form=form)
            
            # 创建用户会话记录
            session_id = str(uuid.uuid4())
            user_session = UserSession(user_id=user.id, session_id=session_id)
            db.session.add(user_session)
            db.session.commit()
            
            # 将当前用户ID存储在session中
            session['current_user_id'] = user.id
            session['session_id'] = session_id
            
            login_user(user)
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form)


def get_logged_in_users():
    """获取所有已登录的用户"""
    active_sessions = UserSession.query.filter_by(is_active=True).all()
    logged_in_users = []
    for user_session in active_sessions:
        user = User.query.filter_by(id=user_session.user_id).first()
        if user:
            logged_in_users.append(user)
    return logged_in_users


@app.route('/switch_user/<int:user_id>')
@login_required
def switch_user(user_id):
    """切换到指定用户"""
    # 检查该用户是否在已登录列表中
    user_session = UserSession.query.filter_by(user_id=user_id, is_active=True).first()
    if user_session:
        # 更新session中的当前用户ID
        session['current_user_id'] = user_id
        session['session_id'] = user_session.session_id
        
        # 使用Flask-Login切换用户
        user = User.query.filter_by(id=user_id).first()
        login_user(user)
        flash(f'Switched to user: {user.username}')
        return redirect(url_for('show_todo_list'))
    else:
        flash('User not found in active sessions')
        return redirect(url_for('show_todo_list'))


@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    """添加新用户并登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('show_todo_list'))
        
        # 检查是否已有3个用户登录
        logged_in_count = UserSession.query.filter_by(is_active=True).count()
        if logged_in_count >= 3:
            flash('Maximum 3 users can be logged in at the same time')
            return redirect(url_for('show_todo_list'))
        
        # 创建新用户
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        # 为新用户添加默认待办事项
        default_todos = [
            f"{username}的待办事项1",
            f"{username}的待办事项2",
            f"{username}的待办事项3"
        ]
        for todo_title in default_todos:
            todo = TodoList(user_id=new_user.id, title=todo_title, status=0)
            db.session.add(todo)
        db.session.commit()
        
        # 创建用户会话记录
        session_id = str(uuid.uuid4())
        user_session = UserSession(user_id=new_user.id, session_id=session_id)
        db.session.add(user_session)
        db.session.commit()
        
        # 切换到新用户
        session['current_user_id'] = new_user.id
        session['session_id'] = session_id
        login_user(new_user)
        
        flash(f'New user {username} created and logged in!')
        return redirect(url_for('show_todo_list'))
    
    return redirect(url_for('show_todo_list'))


@app.route('/logout')
@login_required
def logout():
    # 获取当前用户的会话记录并标记为非活动状态
    if 'session_id' in session:
        user_session = UserSession.query.filter_by(session_id=session['session_id']).first()
        if user_session:
            user_session.is_active = False
            db.session.commit()
    
    logout_user()
    flash('you have logout!')
    
    # 检查是否还有其他已登录用户
    logged_in_users = get_logged_in_users()
    if logged_in_users:
        # 如果有其他用户登录，切换到第一个用户
        next_user = logged_in_users[0]
        user_session = UserSession.query.filter_by(user_id=next_user.id, is_active=True).first()
        session['current_user_id'] = next_user.id
        session['session_id'] = user_session.session_id
        login_user(next_user)
        flash(f'Switched to user: {next_user.username}')
        return redirect(url_for('show_todo_list'))
    else:
        # 如果没有其他用户登录，返回登录页面
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
            # 添加5个默认用户
            default_users = [
                {'username': 'admin', 'password': 'admin123'},
                {'username': 'user1', 'password': 'user123'},
                {'username': 'user2', 'password': 'user123'},
                {'username': 'user3', 'password': 'user123'},
                {'username': 'user4', 'password': 'user123'}
            ]
            
            # 为每个用户添加默认待办事项
            default_todos = {
                'admin': [
                    '习近平五谈稳中求进织密扎牢民生保障网',
                    '特朗普获超270张选举人票将入主白宫',
                    '完成项目文档编写'
                ],
                'user1': [
                    '学习Python编程',
                    '完成作业',
                    '锻炼身体'
                ],
                'user2': [
                    '准备会议材料',
                    '回复客户邮件',
                    '更新项目进度'
                ],
                'user3': [
                    '购买生活用品',
                    '预约医生',
                    '整理房间'
                ],
                'user4': [
                    '阅读技术书籍',
                    '学习新技术',
                    '编写博客文章'
                ]
            }
            
            for user_data in default_users:
                username = user_data['username']
                password = user_data['password']
                
                # 创建用户
                user = User(username=username, password=password)
                db.session.add(user)
                db.session.commit()
                
                # 为用户添加默认待办事项
                for todo_title in default_todos.get(username, []):
                    todo = TodoList(user_id=user.id, title=todo_title, status=0)
                    db.session.add(todo)
                db.session.commit()
            
            print("数据库初始化完成，已添加5个默认用户和测试数据")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
