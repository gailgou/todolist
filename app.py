#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
            login_user(user)
            # 初始化已登录账号列表
            logged_in_users = session.get('logged_in_users', [])
            if user.id not in logged_in_users:
                logged_in_users.append(user.id)
                session['logged_in_users'] = logged_in_users
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


@app.route('/switch_account', methods=['GET', 'POST'])
@login_required
def switch_account():
    # 获取已登录的账号列表
    logged_in_users = session.get('logged_in_users', [])
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if user_id:
            # 切换到指定账号
            user = User.query.get(int(user_id))
            if user:
                logout_user()
                login_user(user)
                flash('账号切换成功！')
                return redirect(url_for('show_todo_list'))
            else:
                flash('用户不存在')
    
    # 获取所有用户列表
    users = User.query.all()
    return render_template('switch_account.html', users=users, logged_in_users=logged_in_users)


@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    # 获取已登录的账号列表
    logged_in_users = session.get('logged_in_users', [])
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 验证用户凭据
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            # 检查是否已经登录
            if user.id in logged_in_users:
                flash('该账号已经登录')
            else:
                # 检查登录账号数量是否超过限制
                if len(logged_in_users) >= 3:
                    flash('最多只能同时登录3个账号')
                else:
                    # 添加到已登录账号列表
                    logged_in_users.append(user.id)
                    session['logged_in_users'] = logged_in_users
                    flash('账号登录成功！')
                    return redirect(url_for('switch_account'))
        else:
            flash('用户名或密码错误')
    
    return render_template('add_account.html')


@app.route('/remove_account/<int:user_id>')
@login_required
def remove_account(user_id):
    # 获取已登录的账号列表
    logged_in_users = session.get('logged_in_users', [])
    
    # 从列表中移除指定账号
    if user_id in logged_in_users:
        logged_in_users.remove(user_id)
        session['logged_in_users'] = logged_in_users
        flash('账号已从登录列表中移除')
    
    return redirect(url_for('switch_account'))


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
            users = [
                User(username='user1', password='password1'),
                User(username='user2', password='password2'),
                User(username='user3', password='password3'),
                User(username='user4', password='password4'),
                User(username='user5', password='password5')
            ]
            
            # 为每个用户添加至少3条预置待办事项
            import time
            now = int(time.time())
            
            for user in users:
                db.session.add(user)
                db.session.commit()
                
                # 为每个用户添加3条待办事项
                todo1 = TodoList(user_id=user.id, title=f'{user.username}的待办事项1', status=0)
                todo2 = TodoList(user_id=user.id, title=f'{user.username}的待办事项2', status=1)
                todo3 = TodoList(user_id=user.id, title=f'{user.username}的待办事项3', status=0)
                db.session.add(todo1)
                db.session.add(todo2)
                db.session.add(todo3)
                db.session.commit()
            
            print("数据库初始化完成，已添加5个默认用户和每个用户的预置待办事项")
    
    app.run(host='0.0.0.0', port=5004, debug=False)
