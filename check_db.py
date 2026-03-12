#!/usr/bin/python
#-*- coding: UTF-8 -*-
from app import app, db
from models import User, TodoList

with app.app_context():
    print('Users:', User.query.count())
    for u in User.query.all():
        todo_count = TodoList.query.filter_by(user_id=u.id).count()
        print(f'  {u.username}: {todo_count} todos')
        for todo in TodoList.query.filter_by(user_id=u.id).all():
            print(f'    - {todo.title}')
