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


db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

# 获取当前登录的所有账号
@app.context_processor
def inject_logged_in_users():
    logged_in_users = session.get('logged_in_users', [])
    users = []
    for user_id in logged_in_users:
        user = User.query.filter_by(id=user_id).first()
        if user:
            users.append(user)
    return dict(logged_in_users=users, current_user_id=session.get('current_user_id'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        # 只显示当前账号的待办事项
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
            login_user(user)
            # 添加到已登录用户列表
            logged_in_users = session.get('logged_in_users', [])
            if user.id not in logged_in_users:
                # 最多支持3个账号同时登录
                if len(logged_in_users) >= 3:
                    logged_in_users.pop(0)  # 移除最早登录的
                logged_in_users.append(user.id)
            session['logged_in_users'] = logged_in_users
            session['current_user_id'] = user.id
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/switch_user/<int:user_id>')
@login_required
def switch_user(user_id):
    """切换到指定账号"""
    logged_in_users = session.get('logged_in_users', [])
    if user_id in logged_in_users:
        user = User.query.filter_by(id=user_id).first()
        if user:
            login_user(user)
            session['current_user_id'] = user.id
            flash('Switched to user: {}'.format(user.username))
        else:
            flash('User not found')
    else:
        flash('User not in logged in list')
    return redirect(url_for('show_todo_list'))


@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    """添加新账号登录"""
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            logged_in_users = session.get('logged_in_users', [])
            if user.id in logged_in_users:
                flash('User already logged in')
                return redirect(url_for('show_todo_list'))
            # 检查是否超过3个账号
            if len(logged_in_users) >= 3:
                flash('Maximum 3 accounts allowed. Please logout one first.')
                return redirect(url_for('show_todo_list'))
            login_user(user)
            logged_in_users.append(user.id)
            session['logged_in_users'] = logged_in_users
            session['current_user_id'] = user.id
            flash('Account added and switched to: {}'.format(user.username))
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form, add_account=True)


@app.route('/logout')
@login_required
def logout():
    # 从已登录列表中移除当前用户
    logged_in_users = session.get('logged_in_users', [])
    if current_user.id in logged_in_users:
        logged_in_users.remove(current_user.id)
    session['logged_in_users'] = logged_in_users
    
    # 如果还有其他登录的账号，切换到其中一个
    if logged_in_users:
        next_user_id = logged_in_users[-1]
        next_user = User.query.filter_by(id=next_user_id).first()
        if next_user:
            login_user(next_user)
            session['current_user_id'] = next_user.id
            flash('Logout current user. Switched to: {}'.format(next_user.username))
            return redirect(url_for('show_todo_list'))
    
    logout_user()
    session.pop('current_user_id', None)
    flash('you have logout!')
    return redirect(url_for('login'))


@app.route('/logout_all')
@login_required
def logout_all():
    """登出所有账号"""
    session.pop('logged_in_users', None)
    session.pop('current_user_id', None)
    logout_user()
    flash('All accounts logged out!')
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
            # 定义5个默认账户
            default_users = [
                {'username': 'admin', 'password': 'admin'},
                {'username': 'user1', 'password': 'user1'},
                {'username': 'user2', 'password': 'user2'},
                {'username': 'user3', 'password': 'user3'},
                {'username': 'user4', 'password': 'user4'},
            ]
            
            # 每个用户的预置待办事项
            default_todos = {
                'admin': [
                    {'title': '完成项目文档编写', 'status': 0},
                    {'title': '审查代码提交', 'status': 1},
                    {'title': '安排团队会议', 'status': 0},
                ],
                'user1': [
                    {'title': '学习Python基础', 'status': 1},
                    {'title': '完成Flask教程', 'status': 0},
                    {'title': '练习数据库操作', 'status': 0},
                ],
                'user2': [
                    {'title': '购买生活用品', 'status': 0},
                    {'title': '预约体检', 'status': 1},
                    {'title': '整理房间', 'status': 0},
                ],
                'user3': [
                    {'title': '阅读技术书籍', 'status': 1},
                    {'title': '写读书笔记', 'status': 0},
                    {'title': '分享学习心得', 'status': 0},
                ],
                'user4': [
                    {'title': '制定健身计划', 'status': 0},
                    {'title': '晨跑5公里', 'status': 1},
                    {'title': '健康饮食记录', 'status': 0},
                ],
            }
            
            # 添加默认用户和待办事项
            for user_data in default_users:
                user = User(username=user_data['username'], password=user_data['password'])
                db.session.add(user)
                db.session.commit()
                
                # 为该用户添加预置待办事项
                todos = default_todos.get(user_data['username'], [])
                for todo_data in todos:
                    todo = TodoList(
                        user_id=user.id,
                        title=todo_data['title'],
                        status=todo_data['status']
                    )
                    db.session.add(todo)
                db.session.commit()
                print("已创建用户: {} 并添加 {} 条待办事项".format(user_data['username'], len(todos)))
            
            print("数据库初始化完成，已添加5个默认用户和预置待办事项")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
