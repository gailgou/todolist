#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash, session)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user, LoginManager

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
        # 只显示当前用户的待办事项
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
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    # 从session中移除当前用户
    if 'logged_users' in session:
        logged_users = session['logged_users']
        if current_user.id in logged_users:
            logged_users.remove(current_user.id)
            session['logged_users'] = logged_users
    logout_user()
    flash('you have logout!')
    return redirect(url_for('login'))


@app.route('/switch_account', methods=['GET', 'POST'])
@login_required
def switch_account():
    # 初始化已登录用户列表
    if 'logged_users' not in session:
        session['logged_users'] = [current_user.id]
    
    if request.method == 'POST':
        # 添加新账号
        if 'add_username' in request.form and 'add_password' in request.form:
            username = request.form['add_username']
            password = request.form['add_password']
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                logged_users = session['logged_users']
                # 检查是否已登录
                if user.id not in logged_users:
                    # 检查是否超过3个
                    if len(logged_users) < 3:
                        logged_users.append(user.id)
                        session['logged_users'] = logged_users
                        flash(f'Account {username} added successfully!')
                    else:
                        flash('Cannot login more than 3 accounts at the same time!')
                else:
                    flash(f'Account {username} is already logged in!')
            else:
                flash('Invalid username or password!')
        # 切换账号
        elif 'user_id' in request.form:
            user_id = int(request.form['user_id'])
            user = User.query.filter_by(id=user_id).first()
            if user and user.id in session.get('logged_users', []):
                login_user(user)
                flash(f'Switched to account: {user.username}')
                return redirect(url_for('show_todo_list'))
    
    # 获取已登录用户信息
    logged_users = session.get('logged_users', [current_user.id])
    users = User.query.filter(User.id.in_(logged_users)).all()
    return render_template('switch_account.html', users=users, current_user=current_user)


@app.route('/remove_account/<int:user_id>', methods=['POST'])
@login_required
def remove_account(user_id):
    # 不能移除当前登录的账号
    if user_id == current_user.id:
        flash('Cannot remove the currently logged in account!')
        return redirect(url_for('switch_account'))
    
    if 'logged_users' in session:
        logged_users = session['logged_users']
        if user_id in logged_users:
            logged_users.remove(user_id)
            session['logged_users'] = logged_users
            flash('Account removed successfully!')
    
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
                User(username='user1', password='123456'),
                User(username='user2', password='123456'),
                User(username='user3', password='123456'),
                User(username='user4', password='123456'),
                User(username='user5', password='123456')
            ]
            for user in users:
                db.session.add(user)
            db.session.commit()
            
            # 为每个用户添加至少3个待办事项
            todos = [
                # User1的待办事项
                TodoList(user_id=1, title='完成项目文档编写', status=0),
                TodoList(user_id=1, title='参加团队会议', status=1),
                TodoList(user_id=1, title='提交代码审查', status=0),
                # User2的待办事项
                TodoList(user_id=2, title='整理项目报告', status=1),
                TodoList(user_id=2, title='联系客户确认需求', status=0),
                TodoList(user_id=2, title='更新项目进度', status=0),
                # User3的待办事项
                TodoList(user_id=3, title='修复Bug #123', status=1),
                TodoList(user_id=3, title='优化数据库查询', status=0),
                TodoList(user_id=3, title='编写单元测试', status=0),
                # User4的待办事项
                TodoList(user_id=4, title='设计新功能界面', status=1),
                TodoList(user_id=4, title='实现API接口', status=0),
                TodoList(user_id=4, title='测试集成功能', status=0),
                # User5的待办事项
                TodoList(user_id=5, title='安排下周计划', status=1),
                TodoList(user_id=5, title='备份重要数据', status=0),
                TodoList(user_id=5, title='学习新技术', status=0)
            ]
            for todo in todos:
                db.session.add(todo)
            db.session.commit()
            
            print("数据库初始化完成，已添加5个默认用户和测试数据")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
