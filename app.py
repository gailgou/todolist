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

# 多账号管理：最多同时登录3个账号
MAX_LOGGED_IN_USERS = 3


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        # 只显示当前登录用户的待办事项
        todolists = TodoList.query.filter_by(user_id=current_user.id).all()
        # 获取已登录的所有账号
        logged_in_users = session.get('logged_in_users', [])
        return render_template('index.html', todolists=todolists, form=form, 
                               logged_in_users=logged_in_users, current_user=current_user)
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
            # 检查该用户是否已在登录列表中
            logged_in_users = session.get('logged_in_users', [])
            user_ids = [u['id'] for u in logged_in_users]
            
            if user.id not in user_ids:
                # 检查是否已达到最大登录数
                if len(logged_in_users) >= MAX_LOGGED_IN_USERS:
                    # 移除最早登录的账号
                    logged_in_users.pop(0)
                
                # 添加新登录的账号
                logged_in_users.append({
                    'id': user.id,
                    'username': user.username
                })
                session['logged_in_users'] = logged_in_users
            
            login_user(user)
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/switch_user/<int:user_id>')
@login_required
def switch_user(user_id):
    """切换到已登录的账号"""
    logged_in_users = session.get('logged_in_users', [])
    user_ids = [u['id'] for u in logged_in_users]
    
    if user_id in user_ids:
        user = User.query.filter_by(id=user_id).first()
        if user:
            login_user(user)
            flash(f'Switched to user: {user.username}')
    
    return redirect(url_for('show_todo_list'))


@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    """添加新的登录账号"""
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            logged_in_users = session.get('logged_in_users', [])
            user_ids = [u['id'] for u in logged_in_users]
            
            # 检查是否已登录
            if user.id in user_ids:
                flash('This account is already logged in')
                return redirect(url_for('add_account'))
            
            # 检查是否已达到最大登录数
            if len(logged_in_users) >= MAX_LOGGED_IN_USERS:
                flash(f'Maximum {MAX_LOGGED_IN_USERS} accounts can be logged in simultaneously. Please logout one first.')
                return redirect(url_for('add_account'))
            
            # 添加新账号到登录列表
            logged_in_users.append({
                'id': user.id,
                'username': user.username
            })
            session['logged_in_users'] = logged_in_users
            
            # 切换到新添加的账号
            login_user(user)
            flash(f'Added and switched to account: {user.username}')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    
    form = LoginForm()
    # 修改表单提交文本
    form.submit.label.text = 'Add Account'
    return render_template('login.html', form=form, add_account=True)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have logout!')
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


def init_default_data():
    """初始化默认用户和待办事项数据"""
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
                    {'title': '组织团队周会', 'status': 1},
                    {'title': '审核代码提交', 'status': 0},
                ],
                'user1': [
                    {'title': '学习Flask框架', 'status': 1},
                    {'title': '完成前端页面设计', 'status': 0},
                    {'title': '修复登录页面bug', 'status': 0},
                ],
                'user2': [
                    {'title': '准备周会汇报材料', 'status': 0},
                    {'title': '更新数据库结构', 'status': 1},
                    {'title': '测试新功能模块', 'status': 0},
                ],
                'user3': [
                    {'title': '整理客户需求文档', 'status': 1},
                    {'title': '优化查询性能', 'status': 0},
                    {'title': '部署测试环境', 'status': 0},
                ],
                'user4': [
                    {'title': '编写单元测试', 'status': 0},
                    {'title': 'Code Review', 'status': 1},
                    {'title': '更新项目依赖', 'status': 0},
                ],
            }
            
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
            
            print("数据库初始化完成，已添加5个默认用户和预置待办事项")


if __name__ == '__main__':
    init_default_data()
    app.run(host='0.0.0.0', port=5003, debug=True)
