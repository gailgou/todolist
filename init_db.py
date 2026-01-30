#!/usr/bin/python
#-*- coding: UTF-8 -*-

from app import app, db
from models import User, TodoList
import time

# 初始化数据库
def init_db():
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 检查是否已经有用户，如果没有则添加默认用户
        existing_user = User.query.first()
        if not existing_user:
            # 添加默认用户
            user = User(username='admin', password='admin')
            db.session.add(user)
            db.session.commit()
            
            # 添加默认的待办事项
            now = int(time.time())
            todo1 = TodoList(user_id=user.id, title='习近平五谈稳中求进织密扎牢民生保障网', status=0)
            todo2 = TodoList(user_id=user.id, title='特朗普获超270张选举人票将入主白宫', status=1)
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.commit()
            
            print("数据库初始化完成，已添加默认用户和测试数据")
        else:
            print("数据库已存在，跳过初始化")

if __name__ == '__main__':
    init_db()
