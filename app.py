#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user

from forms import TodoListForm, LoginForm
from ext import db, login_manager
from models import TodoList, User, LoggedInUser

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
            logged_in_count = LoggedInUser.query.count()
            existing_login = LoggedInUser.query.filter_by(user_id=user.id).first()
            if not existing_login:
                if logged_in_count >= 3:
                    flash('已达到最大登录数量(3个)，请先切换到已登录账号')
                    form = LoginForm()
                    return render_template('login.html', form=form)
                logged_in_user = LoggedInUser(user_id=user.id)
                db.session.add(logged_in_user)
                db.session.commit()
            login_user(user)
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    logged_in_users = get_logged_in_users()
    return render_template('login.html', form=form, logged_in_users=logged_in_users)


@app.route('/logout')
@login_required
def logout():
    LoggedInUser.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    logout_user()
    flash('you have logout!')
    return redirect(url_for('login'))


@app.route('/switch/<int:user_id>')
@login_required
def switch_account(user_id):
    logged_in = LoggedInUser.query.filter_by(user_id=user_id).first()
    if logged_in:
        user = User.query.filter_by(id=user_id).first()
        if user:
            login_user(user)
            flash(f'已切换到账号: ' + user.username)
            return redirect(url_for('show_todo_list'))
    else:
        flash('该账号未登录')
    return redirect(url_for('login'))


def get_logged_in_users():
    logged_in = LoggedInUser.query.all()
    users = []
    for li in logged_in:
        user = User.query.filter_by(id=li.user_id).first()
        if user:
            users.append(user)
    return users


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


@app.context_processor
def inject_logged_in_users():
    if current_user.is_authenticated:
        logged_in_users = get_logged_in_users()
        return dict(logged_in_users=logged_in_users)
    return dict(logged_in_users=[])


if __name__ == '__main__':
    # 初始化数据库
    with app.app_context():
        db.create_all()
        existing_user = User.query.first()
        if not existing_user:
            default_users = [
                ('admin', 'admin'),
                ('user1', '123456'),
                ('user2', '123456'),
                ('user3', '123456'),
                ('user4', '123456'),
            ]
            
            user_todos = {
                'admin': [
                    ('习近平五谈稳中求进织密扎牢民生保障网', 0),
                    ('特朗普获超270张选举人票将入主白宫', 1),
                    ('完成项目文档编写', 0),
                ],
                'user1': [
                    ('学习Python编程', 0),
                    ('完成Flask项目', 1),
                    ('阅读技术文档', 0),
                ],
                'user2': [
                    ('整理工作汇报', 1),
                    ('参加团队会议', 0),
                    ('代码复审', 0),
                ],
                'user3': [
                    ('数据库优化', 0),
                    ('性能测试', 0),
                    ('代码重构', 1),
                ],
                'user4': [
                    ('需求分析', 0),
                    ('设计评审', 0),
                    ('单元测试', 1),
                ],
            }
            
            for username, password in default_users:
                user = User(username=username, password=password)
                db.session.add(user)
                db.session.commit()
                todos = user_todos.get(username, [])
                for title, status in todos:
                    todo = TodoList(user_id=user.id, title=title, status=status)
                    db.session.add(todo)
                db.session.commit()
            
            print("数据库初始化完成，已添加5个默认用户和待办事项")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
