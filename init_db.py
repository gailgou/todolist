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
        else:
            print("数据库已存在，跳过初始化")

if __name__ == '__main__':
    init_db()
