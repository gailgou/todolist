#!/usr/bin/python
#-*- coding: UTF-8 -*-
import time
from datetime import datetime
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
    priority = db.Column(db.String(2), nullable=False, default='P2')
    due_date = db.Column(db.String(20), nullable=True)

    def __init__(self, user_id, title, status, priority='P2', due_date=None):
        self.user_id = user_id
        self.title = title
        self.status = status
        self.create_time = time.time()
        self.priority = priority
        self.due_date = due_date

    def is_overdue(self):
        if self.status == 1:
            return False
        if not self.due_date:
            return False
        try:
            due = datetime.strptime(self.due_date, '%Y-%m-%d %H:%M:%S')
            return datetime.now() > due
        except:
            try:
                due = datetime.strptime(self.due_date, '%Y-%m-%d')
                return datetime.now() > due
            except:
                return False


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __init__(self, username, password, hash_password=True):
        self.username = username
        if hash_password:
            self.password = generate_password_hash(password)
        else:
            self.password = password

    def check_password(self, password):
        if self._is_hashed():
            return check_password_hash(self.password, password)
        else:
            return self.password == password

    def _is_hashed(self):
        return self.password.startswith('pbkdf2:') or self.password.startswith('scrypt:')

    def set_password(self, password):
        self.password = generate_password_hash(password)
