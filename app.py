#!/usr/bin/python
#-*- coding: UTF-8 -*-
from __future__ import unicode_literals

from flask import (Flask, render_template, redirect, url_for, request, flash, jsonify)
from flask_bootstrap import Bootstrap
from flask_login import login_required, login_user, logout_user, current_user
import time

from forms import TodoListForm, LoginForm, RegistrationForm
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


def timestamp_to_date(timestamp):
    if timestamp:
        return time.strftime('%Y-%m-%d', time.localtime(timestamp))
    return ''


app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date


@app.context_processor
def inject_current_time():
    return dict(current_time=int(time.time()))


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_todo_list():
    form = TodoListForm()
    sort = request.args.get('sort', 'desc')
    
    if sort == 'asc':
        order = TodoList.create_time.asc()
    else:
        order = TodoList.create_time.desc()
    
    if request.method == 'GET':
        pending_todos = TodoList.query.filter_by(status=0).order_by(order).all()
        completed_todos = TodoList.query.filter_by(status=1).order_by(order).all()
        return render_template('index.html', pending_todos=pending_todos, completed_todos=completed_todos, form=form, sort=sort)
    else:
        if form.validate_on_submit():
            deadline = None
            if form.deadline.data:
                deadline = int(time.mktime(form.deadline.data.timetuple()))
            todolist = TodoList(current_user.id, form.title.data, form.status.data, deadline)
            db.session.add(todolist)
            db.session.commit()
            flash('You have add a new todo list')
        else:
            flash(form.errors)
        return redirect(url_for('show_todo_list', sort=sort))


@app.route('/delete/<int:id>')
@login_required
def delete_todo_list(id):
     todolist = TodoList.query.filter_by(id=id).first_or_404()
     db.session.delete(todolist)
     db.session.commit()
     flash('You have delete a todo list')
     sort = request.args.get('sort', 'desc')
     return redirect(url_for('show_todo_list', sort=sort))


@app.route('/change/<int:id>', methods=['GET', 'POST'])
@login_required
def change_todo_list(id):
    from datetime import date
    if request.method == 'GET':
        todolist = TodoList.query.filter_by(id=id).first_or_404()
        form = TodoListForm()
        form.title.data = todolist.title
        form.status.data = str(todolist.status)
        if todolist.deadline:
            form.deadline.data = date.fromtimestamp(todolist.deadline)
        return render_template('modify.html', form=form)
    else:
        form = TodoListForm()
        if form.validate_on_submit():
            todolist = TodoList.query.filter_by(id=id).first_or_404()
            todolist.title = form.title.data
            todolist.status = form.status.data
            if form.deadline.data:
                todolist.deadline = int(time.mktime(form.deadline.data.timetuple()))
            else:
                todolist.deadline = None
            db.session.commit()
            flash('You have modify a todolist')
        else:
            flash(form.errors)
        return redirect(url_for('show_todo_list'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            flash('you have logged in!')
            return redirect(url_for('show_todo_list'))
        else:
            flash('Invalid username or password')
    form = LoginForm()
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = RegistrationForm()
        if form.validate_on_submit():
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('用户名已存在')
                return redirect(url_for('register'))
            
            user = User(username=form.username.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(error)
    form = RegistrationForm()
    return render_template('register.html', form=form)


@app.route('/batch_complete', methods=['POST'])
@login_required
def batch_complete():
    ids = request.form.getlist('ids[]')
    if ids:
        for todo_id in ids:
            todolist = TodoList.query.filter_by(id=int(todo_id)).first()
            if todolist:
                todolist.status = 1
        db.session.commit()
        flash('批量完成成功')
    return jsonify({'success': True})


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have logout!')
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
            # 添加默认用户
            user = User(username='admin', password='admin')
            db.session.add(user)
            db.session.commit()
            
            # 添加默认的待办事项
            import time
            now = int(time.time())
            todo1 = TodoList(user_id=user.id, title='习近平五谈稳中求进织密扎牢民生保障网', status=0)
            todo2 = TodoList(user_id=user.id, title='特朗普获超270张选举人票将入主白宫', status=1)
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.commit()
            
            print("数据库初始化完成，已添加默认用户和测试数据")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
