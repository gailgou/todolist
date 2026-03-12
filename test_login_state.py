#!/usr/bin/python
#-*- coding: UTF-8 -*-
from app import app, login_manager
from models import User

client = app.test_client()

# 登录一个用户并检查
response = client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
print(f"Login response status: {response.status_code}")

with client.session_transaction() as sess:
    print('Session keys:', list(sess.keys()))
    print('_user_id:', sess.get('_user_id'))
    print('active_user_id:', sess.get('active_user_id'))
    print('logged_in_users:', sess.get('logged_in_users'))

# 检查user_loader
with app.app_context():
    user = User.query.get(1)
    print('User 1:', user.username)
    
    loaded = login_manager.user_callback('1')
    print('Loaded user by id 1:', loaded)

# 检查访问主页
response = client.get('/')
print(f"Access / status: {response.status_code}")

# 在请求上下文中检查
with client:
    response = client.get('/')
    from flask import request, g
    from flask_login import current_user
    
    print(f"current_user.is_authenticated: {current_user.is_authenticated}")
    print(f"current_user: {current_user}")
    print(f"g.current_user: {g.get('current_user')}")
    print(f"g.logged_in_users: {g.get('logged_in_users')}")
