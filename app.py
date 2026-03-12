#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
import uuid
import time

from flask import (Flask, render_template, redirect, url_for, request, flash, session, g)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

from forms import TodoListForm, LoginForm
from ext import db, login_manager
from models import TodoList, User, LoginSession

SECRET_KEY = 'This is my key'
MAX_LOGIN_USERS = 3

app = Flask(__name__)
bootstrap = Bootstrap(app)

import os
basedir = os.path.abspath(os.path.dirname(__file__))

app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, "instance", "todolist.db").replace('\\', '/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"


def get_logged_in_users():
    """获取当前已登录的用户列表"""
    if 'logged_in_users' not in session:
        session['logged_in_users'] = []
    return session['logged_in_users']


def add_logged_in_user(user_id, username):
    """添加用户到已登录列表"""
    logged_in = get_logged_in_users()
    # 检查是否已登录
    for user in logged_in:
        if user['id'] == user_id:
            return True
    # 检查是否超过最大登录数
    if len(logged_in) >= MAX_LOGIN_USERS:
        return False
    logged_in.append({'id': user_id, 'username': username})
    session['logged_in_users'] = logged_in
    session.modified = True
    return True


def remove_logged_in_user(user_id):
    """从已登录列表移除用户"""
    logged_in = get_logged_in_users()
    logged_in = [u for u in logged_in if u['id'] != user_id]
    session['logged_in_users'] = logged_in
    session.modified = True


def get_current_active_user():
    """获取当前活跃用户"""
    if 'active_user_id' in session:
        return User.query.get(session['active_user_id'])
    return None


@app.before_request
def load_current_user():
    """加载当前用户到g对象"""
    g.current_user = get_current_active_user()
    g.logged_in_users = get_logged_in_users()


@app.context_processor
def inject_user_context():
    """注入用户上下文到所有模板"""
    if current_user.is_authenticated:
        return {
            'active_user': get_current_active_user(),
            'logged_in_users': get_logged_in_users()
        }
    return {}


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    active_user = get_current_active_user()
    
    if request.method == 'GET':
        # 只显示当前账号的待办事项
        todolists = TodoList.query.filter_by(user_id=active_user.id).all()
        return render_template('index.html', todolists=todolists, form=form, 
                             logged_in_users=get_logged_in_users(),
                             active_user=active_user)
    else:
        if form.validate_on_submit():
            todolist = TodoList(active_user.id, form.title.data, form.status.data)
            db.session.add(todolist)
            db.session.commit()
            flash('You have add a new todo list')
        else:
            flash(form.errors)
        return redirect(url_for('show_todo_list'))


@app.route('/delete/<int:id>')
@login_required
def delete_todo_list(id):
    active_user = get_current_active_user()
    todolist = TodoList.query.filter_by(id=id, user_id=active_user.id).first_or_404()
    db.session.delete(todolist)
    db.session.commit()
    flash('You have delete a todo list')
    return redirect(url_for('show_todo_list'))


@app.route('/change/<int:id>', methods=['GET', 'POST'])
@login_required
def change_todo_list(id):
    active_user = get_current_active_user()
    
    if request.method == 'GET':
        todolist = TodoList.query.filter_by(id=id, user_id=active_user.id).first_or_404()
        form = TodoListForm()
        form.title.data = todolist.title
        form.status.data = str(todolist.status)
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id, user_id=active_user.id).first_or_404()
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
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            # 检查是否已在登录列表
            logged_in = get_logged_in_users()
            for u in logged_in:
                if u['id'] == user.id:
                    # 切换到该用户
                    session['active_user_id'] = user.id
                    login_user(user)
                    flash(f'已切换到用户: {username}')
                    return redirect(url_for('show_todo_list'))
            
            # 添加到登录列表
            if add_logged_in_user(user.id, username):
                session['active_user_id'] = user.id
                login_user(user)
                flash(f'用户 {username} 登录成功!')
                return redirect(url_for('show_todo_list'))
            else:
                flash(f'最多只能登录 {MAX_LOGIN_USERS} 个账号，请先登出其他账号')
        else:
            flash('Invalid username or password')
    
    form = LoginForm()
    return render_template('login.html', form=form, logged_in_users=get_logged_in_users())


@app.route('/switch/<int:user_id>')
@login_required
def switch_user(user_id):
    """切换到其他已登录用户"""
    logged_in = get_logged_in_users()
    for user in logged_in:
        if user['id'] == user_id:
            session['active_user_id'] = user_id
            user_obj = User.query.get(user_id)
            login_user(user_obj)
            # 更新g对象，确保同一请求内后续访问一致
            g.current_user = user_obj
            flash(f'已切换到用户: {user["username"]}')
            return redirect(url_for('show_todo_list'))
    flash('用户未登录或不存在')
    return redirect(url_for('show_todo_list'))


@app.route('/logout/<int:user_id>')
@login_required
def logout_user_id(user_id):
    """登出指定用户"""
    active_user = get_current_active_user()
    
    if user_id == active_user.id:
        # 登出当前活跃用户
        remove_logged_in_user(user_id)
        logout_user()
        
        # 切换到其他已登录用户
        logged_in = get_logged_in_users()
        if logged_in:
            session['active_user_id'] = logged_in[0]['id']
            new_user = User.query.get(logged_in[0]['id'])
            login_user(new_user)
            flash(f'已登出，自动切换到用户: {logged_in[0]["username"]}')
            return redirect(url_for('show_todo_list'))
        else:
            session.pop('active_user_id', None)
            flash('你已登出所有账号!')
            return redirect(url_for('login'))
    else:
        # 登出其他用户
        remove_logged_in_user(user_id)
        flash(f'已登出指定账号')
        return redirect(url_for('show_todo_list'))


@app.route('/logout')
@login_required
def logout():
    """登出当前用户"""
    active_user = get_current_active_user()
    if active_user:
        return logout_user_id(active_user.id)
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    """将时间戳转换为可读的日期时间格式"""
    import datetime
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def init_default_data():
    # 检查是否已经有用户，如果没有则添加默认用户
    existing_user = User.query.first()
    if not existing_user:
        # 5个默认账户
        default_users = [
            {'username': 'admin', 'password': 'admin'},
            {'username': 'user1', 'password': '123456'},
            {'username': 'user2', 'password': '123456'},
            {'username': 'user3', 'password': '123456'},
            {'username': 'user4', 'password': '123456'},
        ]
        
        # 每个用户的预置待办事项
        default_todos = [
            ['完成项目报告', '参加团队会议', '回复客户邮件', '学习新技术'],
            ['整理工作文档', '检查系统备份', '更新项目进度'],
            ['写技术文档', '代码审查', '部署测试环境'],
            ['分析用户反馈', '优化数据库', '编写单元测试'],
            ['制定周报告', '团队培训', '产品需求评审'],
        ]
        
        for i, user_data in enumerate(default_users):
            user = User(username=user_data['username'], password=user_data['password'])
            db.session.add(user)
            db.session.flush()  # 获取用户ID
            
            # 为每个用户添加至少3条待办事项
            for todo_title in default_todos[i]:
                todo = TodoList(user_id=user.id, title=todo_title, status=0)
                db.session.add(todo)
        
        db.session.commit()
        print("数据库初始化完成，已添加5个默认用户和预置待办事项")


if __name__ == '__main__':
    # 初始化数据库
    with app.app_context():
        db.create_all()
        init_default_data()
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
