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


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    if request.method == 'GET':
        todolists = TodoList.query.filter_by(user_id=current_user.id).all()
        logged_users = session.get('logged_users', [])
        logged_user_objects = User.query.filter(User.id.in_(logged_users)).all()
        return render_template('index.html', todolists=todolists, form=form, logged_users=logged_user_objects)
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
            logged_users = session.get('logged_users', [])
            if user.id not in logged_users:
                logged_users.append(user.id)
                session['logged_users'] = logged_users
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/logout_single/<int:user_id>')
@login_required
def logout_single(user_id):
    logged_users = session.get('logged_users', [])
    if user_id in logged_users:
        logged_users.remove(user_id)
        session['logged_users'] = logged_users
    
    if user_id == current_user.id:
        logout_user()
        
        if logged_users:
            next_user_id = logged_users[0]
            next_user = User.query.filter_by(id=next_user_id).first()
            if next_user:
                login_user(next_user)
                flash('已登出当前账号，切换到账号: {}'.format(next_user.username))
                return redirect(url_for('show_todo_list'))
        
        flash('you have logout!')
        return redirect(url_for('login'))
    else:
        flash('已登出账号')
        return redirect(url_for('show_todo_list'))


@app.route('/logout')
@login_required
def logout():
    logged_users = session.get('logged_users', [])
    if current_user.id in logged_users:
        logged_users.remove(current_user.id)
        session['logged_users'] = logged_users
    
    logout_user()
    
    if logged_users:
        next_user_id = logged_users[0]
        next_user = User.query.filter_by(id=next_user_id).first()
        if next_user:
            login_user(next_user)
            flash('已登出当前账号，切换到账号: {}'.format(next_user.username))
            return redirect(url_for('show_todo_list'))
    
    flash('you have logout!')
    return redirect(url_for('login'))


@app.route('/switch_account/<int:user_id>')
@login_required
def switch_account(user_id):
    logged_users = session.get('logged_users', [])
    if user_id in logged_users:
        user = User.query.filter_by(id=user_id).first()
        if user:
            logout_user()
            login_user(user)
            flash('Switched to account: {}'.format(user.username))
            return redirect(url_for('show_todo_list'))
    flash('Cannot switch to this account')
    return redirect(url_for('show_todo_list'))


@app.route('/add_account')
@login_required
def add_account():
    logout_user()
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
            users_data = [
                {'username': 'admin', 'password': 'admin', 'todos': ['完成项目报告', '准备会议材料', '回复客户邮件']},
                {'username': 'user1', 'password': 'user1', 'todos': ['学习Python', '阅读技术文档', '练习编程']},
                {'username': 'user2', 'password': 'user2', 'todos': ['健身锻炼', '购买日用品', '整理房间']},
                {'username': 'user3', 'password': 'user3', 'todos': ['制定学习计划', '复习课程', '完成作业']},
                {'username': 'user4', 'password': 'user4', 'todos': ['准备面试', '更新简历', '投递简历']}
            ]
            
            for user_info in users_data:
                user = User(username=user_info['username'], password=user_info['password'])
                db.session.add(user)
                db.session.flush()
                
                for todo_title in user_info['todos']:
                    todo = TodoList(user_id=user.id, title=todo_title, status=0)
                    db.session.add(todo)
            
            db.session.commit()
            print("数据库初始化完成，已添加5个默认用户和预置待办事项")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
