#!/usr/bin/python
#-*- coding: UTF-8 -*-
import time
import bcrypt

from ext import db
from flask_login import UserMixin


class TodoList(db.Model):
    __tablename__ = 'todolist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(1024), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    create_time = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.Integer, nullable=True)  # 添加截止时间字段

    def __init__(self, user_id, title, status, deadline=None):
        self.user_id = user_id
        self.title = title
        self.status = status
        self.create_time = time.time()
        self.deadline = deadline


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)
    
    def set_password(self, password):
        """设置密码，进行哈希处理"""
        password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password, salt).decode('utf-8')
    
    def check_password(self, password):
        """验证密码"""
        password = password.encode('utf-8')
        try:
            # 尝试使用新格式验证密码
            return bcrypt.checkpw(password, self.password_hash.encode('utf-8'))
        except AttributeError:
            # 处理旧格式密码（字节串）
            return bcrypt.checkpw(password, self.password_hash)
