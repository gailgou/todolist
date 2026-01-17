#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash, session, g)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user, LoginManager
from flask_login import user_logged_in, user_logged_out
import json

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


@app.before_request
def ensure_logged_users_format():
    """确保session中的logged_users是正确的格式"""
    if 'logged_users' in session:
        logged_users = session['logged_users']
        # 检查是否为列表且每个元素都是字典
        if not isinstance(logged_users, list):
            session['logged_users'] = []
        else:
            # 过滤掉无效的元素
            valid_users = []
            for u in logged_users:
                if isinstance(u, dict) and 'id' in u and 'username' in u:
                    valid_users.append(u)
            session['logged_users'] = valid_users


@app.context_processor
def inject_logged_users():
    """将logged_users注入到所有模板中"""
    return dict(logged_users=session.get('logged_users', []))


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
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            # 管理已登录账号列表
            logged_users = session.get('logged_users', [])
            
            # 检查用户是否已登录
            user_exists = any(u['id'] == user.id for u in logged_users)
            
            if not user_exists:
                # 最多3个账号
                if len(logged_users) >= 3:
                    # 移除最早登录的账号
                    logged_users.pop(0)
                logged_users.append({'id': user.id, 'username': user.username})
            
            session['logged_users'] = logged_users
            session['current_user_id'] = user.id
            
            login_user(user, remember=False)
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    logout_user()
    
    # 从已登录列表中移除
    logged_users = session.get('logged_users', [])
    logged_users = [u for u in logged_users if u['id'] != user_id]
    session['logged_users'] = logged_users
    
    if logged_users:
        # 切换到下一个账号
        next_user = User.query.get(logged_users[0]['id'])
        login_user(next_user)
        session['current_user_id'] = next_user.id
        flash(f'Switched to user: {next_user.username}')
        return redirect(url_for('show_todo_list'))
    else:
        flash('you have logout!')
        return redirect(url_for('login'))


@app.route('/switch_user/<int:user_id>')
@login_required
def switch_user(user_id):
    logged_users = session.get('logged_users', [])
    user_data = next((u for u in logged_users if u['id'] == user_id), None)
    
    if user_data:
        user = User.query.get(user_id)
        if user:
            logout_user()
            login_user(user)
            session['current_user_id'] = user.id
            flash(f'Switched to user: {user.username}')
    else:
        flash('User not found in logged users')
    
    return redirect(url_for('show_todo_list'))


@app.route('/remove_user/<int:user_id>')
@login_required
def remove_user(user_id):
    if user_id == current_user.id:
        flash('Cannot remove current user')
        return redirect(url_for('show_todo_list'))
    
    logged_users = session.get('logged_users', [])
    logged_users = [u for u in logged_users if u['id'] != user_id]
    session['logged_users'] = logged_users
    
    flash('User removed from logged users')
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
            # 添加5个默认账户
            users_data = [
                {'username': 'user1', 'password': 'pass1', 'todos': [
                    '完成项目报告', '准备会议材料', '回复邮件'
                ]},
                {'username': 'user2', 'password': 'pass2', 'todos': [
                    '购买生活用品', '锻炼身体', '学习新技能'
                ]},
                {'username': 'user3', 'password': 'pass3', 'todos': [
                    '阅读技术文档', '代码审查', '优化数据库'
                ]},
                {'username': 'user4', 'password': 'pass4', 'todos': [
                    '参加培训课程', '整理桌面', '制定计划'
                ]},
                {'username': 'user5', 'password': 'pass5', 'todos': [
                    '学习Python', '开发新功能', '测试系统'
                ]}
            ]
            
            for user_data in users_data:
                user = User(username=user_data['username'], password=user_data['password'])
                db.session.add(user)
                db.session.commit()
                
                # 为每个用户添加待办事项
                for i, title in enumerate(user_data['todos']):
                    todo = TodoList(user_id=user.id, title=title, status=i % 2)
                    db.session.add(todo)
                db.session.commit()
            
            print("数据库初始化完成，已添加5个默认用户和待办事项")
    
    app.run(host='0.0.0.0', port=5004, debug=True)
