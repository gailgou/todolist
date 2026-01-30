#!/usr/bin/python
#-*- coding: UTF-8 -*-
import time

from ext import db
from flask_login import UserMixin


CATEGORIES = [
    ('work', '工作'),
    ('life', '生活'),
    ('study', '学习'),
    ('parenting', '亲子'),
    ('family', '家庭')
]

PRIORITIES = [
    ('P0', 'P0 - 紧急'),
    ('P1', 'P1 - 重要'),
    ('P2', 'P2 - 普通')
]

class TodoList(db.Model):
    __tablename__ = 'todolist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(1024), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(20), nullable=False, default='work')
    priority = db.Column(db.String(10), nullable=False, default='P2')
    deadline = db.Column(db.Integer, nullable=True)
    create_time = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, title, status, category='work', priority='P2', deadline=None):
        self.user_id = user_id
        self.title = title
        self.status = status
        self.category = category
        self.priority = priority
        self.deadline = deadline
        self.create_time = time.time()


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False)
    password = db.Column(db.String(24), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password
