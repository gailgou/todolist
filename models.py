#!/usr/bin/python
#-*- coding: UTF-8 -*-
import time
from werkzeug.security import generate_password_hash, check_password_hash

from ext import db
from flask_login import UserMixin


class TodoList(db.Model):
    __tablename__ = 'todolist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(1024), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    create_time = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.Integer, nullable=True)

    def __init__(self, user_id, title, status, deadline=None):
        self.user_id = user_id
        self.title = title
        self.status = status
        self.create_time = time.time()
        self.deadline = deadline

    def is_overdue(self):
        if self.deadline is None or self.status == 1:
            return False
        return time.time() > self.deadline


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
