#!/usr/bin/python
#-*- coding: UTF-8 -*-
import time

from ext import db
from flask_login import UserMixin


class TodoList(db.Model):
    __tablename__ = 'todolist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(1024), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    create_time = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(32), nullable=False, default='工作')
    priority = db.Column(db.Integer, nullable=False, default=1)
    due_time = db.Column(db.Integer, nullable=True)

    def __init__(self, user_id, title, status, category='工作', priority=1, due_time=None):
        self.user_id = user_id
        self.title = title
        self.status = status
        self.create_time = time.time()
        self.category = category
        self.priority = priority
        self.due_time = due_time

    def get_overdue_info(self):
        if self.due_time and time.time() > self.due_time and self.status == 0:
            overdue_seconds = time.time() - self.due_time
            if overdue_seconds >= 365 * 24 * 3600:
                years = int(overdue_seconds // (365 * 24 * 3600))
                return f"逾期{years}年"
            elif overdue_seconds >= 30 * 24 * 3600:
                months = int(overdue_seconds // (30 * 24 * 3600))
                return f"逾期{months}月"
            elif overdue_seconds >= 24 * 3600:
                days = int(overdue_seconds // (24 * 3600))
                return f"逾期{days}天"
            elif overdue_seconds >= 3600:
                hours = int(overdue_seconds // 3600)
                return f"逾期{hours}小时"
            elif overdue_seconds >= 60:
                minutes = int(overdue_seconds // 60)
                return f"逾期{minutes}分钟"
            else:
                return f"逾期{int(overdue_seconds)}秒"
        return None


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False)
    password = db.Column(db.String(24), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password
