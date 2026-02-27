#!/usr/bin/python
#-*- coding: UTF-8 -*-
from app import app, db
from models import User, TodoList

with app.app_context():
    # 查询所有用户
    users = User.query.all()
    print("用户列表：")
    for user in users:
        print(f"ID: {user.id}, 用户名: {user.username}")
        # 查询每个用户的待办事项
        todos = TodoList.query.filter_by(user_id=user.id).all()
        print(f"  待办事项数量: {len(todos)}")
        for todo in todos:
            print(f"  - {todo.title} (状态: {todo.status})")
        print()