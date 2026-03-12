#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash, session)
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

# 最多同时登录的账号数量
MAX_LOGGED_IN_USERS = 3

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        todolists = TodoList.query.filter_by(user_id=current_user.id).all()
        return render_template('index.html', todolists=todolists, form=form)
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
            # 记录已登录的用户
            if 'logged_in_users' not in session:
                session['logged_in_users'] = []
            
            # 检查用户是否已登录
            if user.id not in session['logged_in_users']:
                # 检查是否超过最大登录数
                if len(session['logged_in_users']) >= MAX_LOGGED_IN_USERS:
                    flash(f'最多只能同时登录 {MAX_LOGGED_IN_USERS} 个账号')
                    return redirect(url_for('login'))
                session['logged_in_users'].append(user.id)
                session.modified = True
            
            login_user(user)
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/switch/<int:user_id>')
@login_required
def switch_account(user_id):
    # 检查用户是否在已登录列表中
    if 'logged_in_users' in session and user_id in session['logged_in_users']:
        user = User.query.get(user_id)
        if user:
            logout_user()
            login_user(user)
            flash(f'已切换到账号: {user.username}')
            return redirect(url_for('show_todo_list'))
    flash('切换账号失败')
    return redirect(url_for('show_todo_list'))


@app.route('/logout')
@login_required
def logout():
    # 从已登录列表中移除
    if 'logged_in_users' in session and current_user.id in session['logged_in_users']:
        session['logged_in_users'].remove(current_user.id)
        session.modified = True
    logout_user()
    flash('you have logout!')
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


@app.context_processor
def inject_logged_in_users():
    """将已登录用户的信息传递给模板"""
    if 'logged_in_users' in session and session['logged_in_users']:
        users_info = []
        for user_id in session['logged_in_users']:
            user = User.query.get(user_id)
            if user:
                users_info.append((user.id, user.username))
        return dict(logged_in_users_info=users_info)
    return dict(logged_in_users_info=[])


if __name__ == '__main__':
    # 初始化数据库
    with app.app_context():
        db.create_all()
        # 检查是否已经有用户，如果没有则添加默认用户
        existing_user = User.query.first()
        if not existing_user:
            # 定义5个默认用户
            default_users = [
                {'username': 'admin', 'password': 'admin'},
                {'username': 'user1', 'password': '123456'},
                {'username': 'user2', 'password': '123456'},
                {'username': 'user3', 'password': '123456'},
                {'username': 'user4', 'password': '123456'}
            ]
            
            # 为每个用户定义预置待办事项
            default_todos = [
                ['完成项目报告', '参加团队会议', '回复客户邮件'],
                ['学习Python编程', '阅读技术文档', '整理工作笔记'],
                ['健身运动30分钟', '阅读书籍', '准备晚餐'],
                ['完成周报', '预约牙医', '购买生活用品'],
                ['学习新技能', '看一部电影', '与朋友聚会']
            ]
            
            # 添加用户和待办事项
            for i, user_data in enumerate(default_users):
                user = User(username=user_data['username'], password=user_data['password'])
                db.session.add(user)
                db.session.commit()
                
                # 为每个用户添加至少3条预置待办事项
                for todo_title in default_todos[i]:
                    todo = TodoList(user_id=user.id, title=todo_title, status=0)
                    db.session.add(todo)
                db.session.commit()
            
            print("数据库初始化完成，已添加5个默认用户和预置待办事项")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
